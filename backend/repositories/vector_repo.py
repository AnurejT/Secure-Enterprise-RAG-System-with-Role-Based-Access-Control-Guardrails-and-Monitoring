"""
backend/repositories/vector_repo.py
FAISS vector store repository — thread-safe singleton.
Moved from rag/vector_store.py; storage path updated to storage/vector/.
"""
import os
from threading import Lock

from backend.core.config import VECTOR_DIR

_VECTOR_DB = None
_DB_LOCK = Lock()


def _load_or_create(embeddings):
    """Load existing FAISS index from disk, or create a fresh empty one."""
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document

    global _VECTOR_DB

    if _VECTOR_DB is not None:
        return _VECTOR_DB

    with _DB_LOCK:
        if _VECTOR_DB is not None:
            return _VECTOR_DB

        index_path_faiss = VECTOR_DIR + ".faiss"
        index_path_dir   = os.path.join(VECTOR_DIR, "index.faiss")

        if os.path.exists(index_path_faiss) or os.path.exists(index_path_dir):
            try:
                print("[VectorRepo] Loading FAISS index from disk...")
                _VECTOR_DB = FAISS.load_local(
                    VECTOR_DIR,
                    embeddings,
                    allow_dangerous_deserialization=True,
                )
                return _VECTOR_DB
            except Exception as e:
                print(f"[VectorRepo] Load failed — creating new index: {e}")

        print("[VectorRepo] Creating new FAISS index...")
        os.makedirs(os.path.dirname(VECTOR_DIR), exist_ok=True)
        _VECTOR_DB = FAISS.from_documents(
            [Document(page_content="init", metadata={"role_allowed": ["none"]})],
            embeddings,
        )
        _VECTOR_DB.save_local(VECTOR_DIR)
        return _VECTOR_DB


def add_documents(docs: list, embeddings) -> None:
    """Append documents to the FAISS store and persist."""
    db = _load_or_create(embeddings)
    with _DB_LOCK:
        db.add_documents(docs)
        db.save_local(VECTOR_DIR)
    print(f"[VectorRepo] Added {len(docs)} documents")


def similarity_search(query: str, embeddings, k: int = 20) -> list:
    """Return k most similar documents (no RBAC filtering here)."""
    db = _load_or_create(embeddings)
    return db.similarity_search(query, k=k)


def delete_by_source(file_path: str, embeddings) -> None:
    """Delete all chunks belonging to a source file."""
    global _VECTOR_DB
    db = _load_or_create(embeddings)

    with _DB_LOCK:
        ids_to_delete = [
            doc_id
            for doc_id, doc in db.docstore._dict.items()
            if doc.metadata.get("source") == file_path
        ]

        if ids_to_delete:
            db.delete(ids_to_delete)
            db.save_local(VECTOR_DIR)
            print(f"[VectorRepo] Deleted {len(ids_to_delete)} chunks for: {file_path}")
        else:
            print(f"[VectorRepo] No chunks found for: {file_path}")


def clear_all(embeddings) -> None:
    """Wipe the entire vector store and start fresh."""
    global _VECTOR_DB
    with _DB_LOCK:
        _VECTOR_DB = None
        import shutil
        if os.path.exists(VECTOR_DIR):
            shutil.rmtree(VECTOR_DIR, ignore_errors=True)
        print("[VectorRepo] Index wiped.")
    _load_or_create(embeddings)
