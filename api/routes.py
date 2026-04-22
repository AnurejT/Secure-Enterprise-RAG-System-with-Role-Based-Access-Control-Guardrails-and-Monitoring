from flask import Blueprint, request, jsonify, Response, stream_with_context
import os
import json

from rag.ingestion import ingest_pdf
from services.rag_service import process_query, process_query_stream
from api.auth import token_required
from extensions import db
from models.message import Message

api_routes = Blueprint("api_routes", __name__)

DATA_FOLDER = "data"
METADATA_FILE = os.path.join(DATA_FOLDER, "roles.json")

def load_metadata():
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_metadata(md):
    os.makedirs(DATA_FOLDER, exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(md, f)

# =========================
# ✅ UPLOAD PDF WITH ROLE
# =========================
@api_routes.route("/upload", methods=["POST"])
def upload_file():
    try:
        file = request.files.get("file")
        role = request.form.get("role", "employee").lower()
        if not file: return jsonify({"error": "No file uploaded"}), 400
        ALLOWED_EXTENSIONS = {".pdf", ".docx", ".csv", ".xlsx", ".md"}

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({"error": f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

        
        from werkzeug.utils import secure_filename
        safe_filename = secure_filename(file.filename)
        os.makedirs(DATA_FOLDER, exist_ok=True)
        filepath = os.path.join(DATA_FOLDER, safe_filename)
        file.save(filepath)

        md = load_metadata()
        md[safe_filename] = role
        save_metadata(md)

        ingest_pdf(filepath, role)
        return jsonify({"message": "File uploaded & indexed successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# ✅ QUERY (STANDARD)
# =========================
@api_routes.route("/query", methods=["POST"])
@token_required
def query():
    try:
        data = request.json
        user_query = data.get("query")
        role = data.get("role", "employee").lower()
        user_email = request.user.get("email")
        
        from models.user import User
        user = User.query.filter_by(email=user_email).first()

        # Save User Message
        user_msg = Message(user_id=user.id, role=role, type="user", text=user_query)
        db.session.add(user_msg)
        db.session.commit()

        result = process_query(user_query, role)
        
        # Save Bot Message
        bot_msg = Message(user_id=user.id, role=role, type="bot", text=result["answer"], sources=json.dumps(result["sources"]))
        db.session.add(bot_msg)
        db.session.commit()

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# ✅ QUERY (STREAMING)
# =========================
@api_routes.route("/query_stream", methods=["POST"])
@token_required
def query_stream():
    try:
        data = request.json
        user_query = data.get("query")
        role = data.get("role", "employee").lower()
        user_email = request.user.get("email")

        from models.user import User
        user = User.query.filter_by(email=user_email).first()

        def generate():
            # Initial User Message Save
            user_msg = Message(user_id=user.id, role=role, type="user", text=user_query)
            db.session.add(user_msg)
            db.session.commit()

            full_answer = ""
            sources_json = "[]"
            
            for chunk in process_query_stream(user_query, role):
                if chunk.startswith("SOURCES_JSON:"):
                    sources_json = chunk.replace("SOURCES_JSON:", "")
                else:
                    full_answer += chunk
                    yield chunk

            # Final Bot Message Save
            bot_msg = Message(user_id=user.id, role=role, type="bot", text=full_answer, sources=sources_json)
            db.session.add(bot_msg)
            db.session.commit()

        return Response(stream_with_context(generate()), mimetype="text/plain")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# ✅ CHAT HISTORY
# =========================
@api_routes.route("/history", methods=["GET"])
@token_required
def get_history():
    try:
        user_email = request.user.get("email")
        from models.user import User
        user = User.query.filter_by(email=user_email).first()
        messages = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.asc()).all()
        return jsonify({"history": [m.to_dict() for m in messages]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# ✅ LIST FILES
# =========================
@api_routes.route("/files", methods=["GET"])
def list_files():
    try:
        if not os.path.exists(DATA_FOLDER): return jsonify({"files": []})
        files = os.listdir(DATA_FOLDER)
        md = load_metadata()
        file_list = []
        ALLOWED_EXTENSIONS = {".pdf", ".docx", ".csv", ".xlsx", ".md"}
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                size_kb = os.path.getsize(os.path.join(DATA_FOLDER, f)) // 1024
                file_list.append({"name": f, "size_kb": size_kb, "role": md.get(f, "employee")})

        return jsonify({"files": file_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# ✅ DELETE FILE
# =========================
@api_routes.route("/files/<filename>", methods=["DELETE"])
@token_required
def delete_file(filename):
    try:
        filepath = os.path.join(DATA_FOLDER, filename)
        if os.path.exists(filepath):
            try:
                from rag.vector_store import delete_doc_from_db
                from rag.embeddings import get_embeddings
                delete_doc_from_db(filepath, get_embeddings())
            except Exception as e: print(f"[DB DELETE ERROR] {str(e)}")
            os.remove(filepath)
            md = load_metadata()
            if filename in md:
                del md[filename]
                save_metadata(md)
            return jsonify({"message": "File and indexed chunks deleted successfully"})
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500