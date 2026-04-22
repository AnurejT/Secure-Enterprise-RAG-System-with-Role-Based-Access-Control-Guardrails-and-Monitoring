from flask import Blueprint, request, jsonify
import os

from rag.ingestion import ingest_pdf
from services.rag_service import process_query

api_routes = Blueprint("api_routes", __name__)

DATA_FOLDER = "data"

# =========================
# ✅ UPLOAD PDF WITH ROLE
# =========================
@api_routes.route("/upload", methods=["POST"])
def upload_file():
    try:
        file = request.files.get("file")

        # 🔥 CRITICAL: role from frontend
        role = request.form.get("role", "employee").lower()

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        if not file.filename.endswith(".pdf"):
            return jsonify({"error": "Only PDF allowed"}), 400

        from werkzeug.utils import secure_filename
        safe_filename = secure_filename(file.filename)
        if not safe_filename:
            safe_filename = "uploaded_file.pdf" # Fallback if name is totally stripped

        os.makedirs(DATA_FOLDER, exist_ok=True)

        filepath = os.path.join(DATA_FOLDER, safe_filename)
        file.save(filepath)

        print(f"\n[UPLOAD] File: {safe_filename}")
        print(f"[UPLOAD] Role: {role}")

        # 🔥 SEND ROLE TO INGESTION
        ingest_pdf(filepath, role)

        return jsonify({"message": "File uploaded & indexed successfully"})

    except Exception as e:
        print("[UPLOAD ERROR]", str(e))
        return jsonify({"error": str(e)}), 500


# =========================
# ✅ QUERY
# =========================
@api_routes.route("/query", methods=["POST"])
def query():
    try:
        data = request.json
        user_query = data.get("query")
        role = data.get("role", "employee").lower()

        if not user_query:
            return jsonify({"error": "Query is required"}), 400

        print("\n[API QUERY]")
        print("Query:", user_query)
        print("Role:", role)

        result = process_query(user_query, role)

        return jsonify(result)

    except Exception as e:
        print("[QUERY ERROR]", str(e))
        return jsonify({"error": str(e)}), 500


# =========================
# ✅ LIST FILES
# =========================
@api_routes.route("/files", methods=["GET"])
def list_files():
    try:
        if not os.path.exists(DATA_FOLDER):
            return jsonify({"files": []})

        files = os.listdir(DATA_FOLDER)

        return jsonify({
            "files": [{"name": f} for f in files if f.endswith(".pdf")]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# ✅ DELETE FILE
# =========================
@api_routes.route("/files/<filename>", methods=["DELETE"])
def delete_file(filename):
    try:
        filepath = os.path.join(DATA_FOLDER, filename)

        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({"message": "File deleted"})

        return jsonify({"error": "File not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500