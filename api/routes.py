from flask import Blueprint, request, jsonify
from services.rag_service import process_query
from rag.ingestion import ingest_pdf
from rag.vector_store import load_vector_store
from rag.embeddings import get_embeddings
import os

api_routes = Blueprint("api_routes", __name__)

DATA_DIR = "data"


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

    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, file.filename)

    file.save(file_path)

    ingest_pdf(file_path)

    return jsonify({"message": "File uploaded & indexed"})


# -------------------------
# LIST FILES ENDPOINT
# -------------------------
@api_routes.route("/files", methods=["GET"])
def list_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    files = []
    for fname in os.listdir(DATA_DIR):
        if fname.lower().endswith(".pdf"):
            fpath = os.path.join(DATA_DIR, fname)
            size_kb = round(os.path.getsize(fpath) / 1024, 1)
            files.append({
                "name": fname,
                "size_kb": size_kb,
                "path": fpath,
            })
    # Sort by name
    files.sort(key=lambda f: f["name"].lower())
    return jsonify({"files": files})


# -------------------------
# DELETE FILE ENDPOINT
# -------------------------
@api_routes.route("/files/<path:filename>", methods=["DELETE"])
def delete_file(filename):
    # Security: strip any path traversal
    filename = os.path.basename(filename)
    file_path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    # 1. Remove from disk
    os.remove(file_path)

    # 2. Remove all vectors with this source from ChromaDB
    try:
        embeddings = get_embeddings()
        db = load_vector_store(embeddings)
        # Chroma: delete by metadata filter
        collection = db._collection
        results = collection.get(where={"source": file_path})
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            print(f"[DB] Deleted {len(ids_to_delete)} vectors for '{filename}'")
        else:
            print(f"[DB] No vectors found for source '{file_path}'")
    except Exception as e:
        print(f"[WARN] Vector deletion error: {e}")
        # File is already deleted from disk; don't fail the request

    return jsonify({"message": f"'{filename}' deleted successfully"})