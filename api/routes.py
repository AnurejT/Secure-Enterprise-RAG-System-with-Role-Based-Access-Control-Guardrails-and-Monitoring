from flask import Blueprint, request, jsonify
from services.rag_service import process_query
from rag.ingestion import ingest_pdf
import os

api_routes = Blueprint("api_routes", __name__)

# -------------------------
# QUERY ENDPOINT
# -------------------------
@api_routes.route("/query", methods=["POST"])
def query():
    data = request.json

    user_query = data.get("query")
    role = data.get("role", "employee")

    if not user_query:
        return jsonify({"error": "Missing query"}), 400

    answer = process_query(user_query, role)

    return jsonify(answer)


# -------------------------
# UPLOAD ENDPOINT
# -------------------------
@api_routes.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", file.filename)

    file.save(file_path)

    ingest_pdf(file_path)

    return jsonify({"message": "File uploaded & indexed"})