"""
backend/api/v1/routes.py
Core API blueprint — document upload/delete, query, chat history.
"""
import json
import os
import re

from flask import Blueprint, Response, jsonify, request, stream_with_context
from werkzeug.utils import secure_filename

from backend.core.security import token_required
from backend.core.extensions import db
from backend.core.config import DOCUMENTS_DIR, METADATA_FILE, ALLOWED_EXTENSIONS
from backend.models.message import Message
from backend.models.user import User
from backend.rag.ingestion.document_ingestor import ingest_document
from backend.services.rag_pipeline import process_query, process_query_stream
from backend.tasks.ingestion_tasks import ingest_document_task
from backend.tasks.eval_tasks import run_ragas_eval_task
from celery.result import AsyncResult

api_routes = Blueprint("api_routes", __name__)

# ── Metadata helpers ─────────────────────────────────────────────────

def _load_metadata() -> dict:
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_metadata(md: dict) -> None:
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(md, f)


# ── Upload ────────────────────────────────────────────────────────────

@api_routes.route("/upload", methods=["POST"])
@token_required
def upload_file():
    try:
        file = request.files.get("file")
        role = request.form.get("role", "general").lower()
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({"error": f"Unsupported type: {ext}"}), 400

        safe_name = secure_filename(file.filename)
        os.makedirs(DOCUMENTS_DIR, exist_ok=True)
        filepath  = os.path.join(DOCUMENTS_DIR, safe_name)
        file.save(filepath)

        md = _load_metadata()
        md[safe_name] = role
        _save_metadata(md)

        # Cleanup old chunks if re-uploading
        try:
            from backend.repositories.vector_repo import delete_by_source
            from backend.rag.embeddings.encoder import get_embeddings
            delete_by_source(filepath, get_embeddings())
        except Exception as ve:
            print(f"[Upload] Vector store cleanup warning: {ve}")

        # ingest_document(filepath, role) -- REPLACED BY CELERY
        try:
            task = ingest_document_task.delay(filepath, role)
            return jsonify({
                "message": "File upload accepted. Processing in background.",
                "task_id": task.id
            })
        except Exception as celery_err:
            print(f"[Upload] Celery/Redis error, falling back to sync: {celery_err}")
            # Fallback to synchronous ingestion
            try:
                ingest_document(filepath, role)
                return jsonify({"message": "File uploaded & indexed successfully (Synchronous fallback)"})
            except Exception as ingest_err:
                return jsonify({"error": f"Ingestion failed: {str(ingest_err)}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Query (standard) ─────────────────────────────────────────────────

@api_routes.route("/query", methods=["POST"])
@token_required
def query():
    try:
        data       = request.json or {}
        user_query = data.get("query", "")
        user_email = request.user.get("email")
        user       = User.query.filter_by(email=user_email).first()
        user_role  = user.role.lower() if user else "general"

        # RBAC Leakage Fix: Ensure non-admins can't request other departments' roles
        requested_role = data.get("role", "general").lower()
        if user_role != "admin" and requested_role not in (user_role, "general"):
            print(f"[RBAC] Leakage attempt: {user_email} ({user_role}) requested {requested_role}. Reverting to {user_role}.")
            role = user_role
        else:
            role = requested_role

        # Save user message
        user_msg = Message()
        user_msg.user_id = user.id
        user_msg.role = role
        user_msg.type = "user"
        user_msg.text = user_query
        db.session.add(user_msg)
        db.session.commit()

        emp_match   = re.search(r"FINEMP\d+", user_query, re.IGNORECASE)
        employee_id = emp_match.group(0).upper() if emp_match else None

        result = process_query(user_query, role, employee_id=employee_id)

        # Save bot message
        bot_msg = Message()
        bot_msg.user_id = user.id
        bot_msg.role = role
        bot_msg.type = "bot"
        bot_msg.text = result["answer"]
        bot_msg.sources = json.dumps(result["sources"])
        db.session.add(bot_msg)
        db.session.commit()

        # Async Ragas eval (non-blocking via Celery)
        try:
            run_ragas_eval_task.delay(
                query=user_query, answer=result["answer"],
                contexts=[], role=role,
                token_usage=result.get("usage"), latency_ms=result.get("latency_ms"),
            )
        except Exception as celery_err:
            print(f"[Query] Celery/Redis error for eval, falling back to sync: {celery_err}")
            try:
                from backend.monitoring.service import evaluate_and_record
                evaluate_and_record(
                    query=user_query, answer=result["answer"],
                    contexts=[], role=role,
                    token_usage=result.get("usage"), latency_ms=result.get("latency_ms"),
                )
            except Exception as eval_err:
                print(f"[Query] Sync eval fallback failed: {eval_err}")

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Query (streaming) ────────────────────────────────────────────────

@api_routes.route("/query_stream", methods=["POST"])
@token_required
def query_stream():
    try:
        data       = request.json or {}
        user_query = data.get("query", "")
        user_email = request.user.get("email")
        user       = User.query.filter_by(email=user_email).first()
        user_role  = user.role.lower() if user else "general"

        # RBAC Leakage Fix: Ensure non-admins can't request other departments' roles
        requested_role_raw = data.get("role", "general")
        requested_role = requested_role_raw.lower() if requested_role_raw else "general"
        if user_role != "admin" and requested_role not in (user_role, "general"):
            print(f"[RBAC] Leakage attempt (stream): {user_email} ({user_role}) requested {requested_role}. Reverting to {user_role}.")
            role = user_role
        else:
            role = requested_role

        def generate():
            try:
                user_msg = Message()
                user_msg.user_id = user.id
                user_msg.role = role
                user_msg.type = "user"
                user_msg.text = user_query
                db.session.add(user_msg)
                db.session.commit()

                emp_match   = re.search(r"FINEMP\d+", user_query, re.IGNORECASE)
                employee_id = emp_match.group(0).upper() if emp_match else None

                full_answer = ""
                sources_json = "[]"

                for chunk in process_query_stream(user_query, role, employee_id=employee_id):
                    if chunk.strip().startswith("SOURCES_JSON:"):
                        sources_json = chunk.strip().replace("SOURCES_JSON:", "")
                    else:
                        full_answer += chunk
                    
                    # Always yield to frontend so it can parse sources, but full_answer (for DB) excludes it
                    yield chunk

                bot_msg = Message()
                bot_msg.user_id = user.id
                bot_msg.role = role
                bot_msg.type = "bot"
                bot_msg.text = full_answer
                bot_msg.sources = sources_json
                db.session.add(bot_msg)
                db.session.commit()

                # Async Ragas eval (non-blocking via Celery)
                try:
                    contexts = [e.get("source", "") for e in json.loads(sources_json)]
                except Exception:
                    contexts = []
                
                try:
                    run_ragas_eval_task.delay(query=user_query, answer=full_answer, contexts=contexts, role=role)
                except Exception as celery_err:
                    print(f"[Stream] Celery/Redis error for eval, falling back to sync: {celery_err}")
                    try:
                        from backend.monitoring.service import evaluate_and_record
                        evaluate_and_record(query=user_query, answer=full_answer, contexts=contexts, role=role)
                    except Exception as eval_err:
                        print(f"[Stream] Sync eval fallback failed: {eval_err}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                yield f"\n\n[Server Error]: {str(e)}"

        return Response(stream_with_context(generate()), mimetype="text/plain")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Chat history ──────────────────────────────────────────────────────

@api_routes.route("/history", methods=["GET", "DELETE"])
@token_required
def history():
    try:
        user_email = request.user.get("email")
        user = User.query.filter_by(email=user_email).first()
        
        if request.method == "DELETE":
            Message.query.filter_by(user_id=user.id).delete()
            db.session.commit()
            return jsonify({"message": "Chat history cleared successfully"})
            
        messages = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.asc()).all()
        return jsonify({"history": [m.to_dict() for m in messages]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── List files ────────────────────────────────────────────────────────

@api_routes.route("/files", methods=["GET"])
@token_required
def list_files():
    try:
        if not os.path.exists(DOCUMENTS_DIR):
            return jsonify({"files": []})
        md = _load_metadata()
        file_list = []
        for f in os.listdir(DOCUMENTS_DIR):
            ext = os.path.splitext(f)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                size_kb = os.path.getsize(os.path.join(DOCUMENTS_DIR, f)) // 1024
                file_list.append({"name": f, "size_kb": size_kb, "role": md.get(f, "general")})
        return jsonify({"files": file_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Delete file ───────────────────────────────────────────────────────

@api_routes.route("/files/<filename>", methods=["DELETE", "OPTIONS"])
@token_required
def delete_file(filename):
    print(f"[Delete] Request received for: {filename}")
    if ".." in filename or "/" in filename or "\\" in filename:
        return jsonify({"error": "Invalid filename"}), 400

    try:
        filepath = os.path.join(DOCUMENTS_DIR, filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404

        try:
            from backend.repositories.vector_repo import delete_by_source
            from backend.rag.embeddings.encoder import get_embeddings
            delete_by_source(filepath, get_embeddings())
        except Exception as ve:
            print(f"[Delete] Vector store warning: {ve}")

        os.remove(filepath)

        md = _load_metadata()
        md.pop(filename, None)
        _save_metadata(md)

        return jsonify({"message": f'"{filename}" deleted successfully'})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Task Status ───────────────────────────────────────────────────────

@api_routes.route("/tasks/<task_id>", methods=["GET"])
@token_required
def get_task_status(task_id):
    """
    Check status of a background Celery task.
    """
    task_result = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status":  task_result.status,
        "progress": 0,
        "message": ""
    }
    
    if task_result.status == "PROGRESS":
        response["progress"] = task_result.info.get("progress", 0)
        response["message"]  = task_result.info.get("message", "")
    elif task_result.status == "SUCCESS":
        response["progress"] = 100
        response["result"]   = task_result.result
    elif task_result.status == "FAILURE":
        response["error"]    = str(task_result.info)
        
    return jsonify(response)
