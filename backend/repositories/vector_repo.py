"""
backend/repositories/vector_repo.py
Qdrant vector store repository — thread-safe singleton.
"""
import os
from threading import Lock

from backend.core.config import VECTOR_DIR

_VECTOR_DB = None
_QDRANT_CLIENT = None
_DB_LOCK = Lock()
COLLECTION_NAME = "enterprise_rag"


def _get_qdrant_client():
    """Singleton helper to get the Qdrant client."""
    global _QDRANT_CLIENT
    if _QDRANT_CLIENT is not None:
        return _QDRANT_CLIENT
    
    from qdrant_client import QdrantClient
    os.makedirs(os.path.dirname(VECTOR_DIR), exist_ok=True)
    _QDRANT_CLIENT = QdrantClient(path=VECTOR_DIR)
    return _QDRANT_CLIENT


def _load_or_create(embeddings):
    """Load existing Qdrant collection from disk, or create a fresh empty one."""
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client.http.models import Distance, VectorParams

    global _VECTOR_DB

    if _VECTOR_DB is not None:
        return _VECTOR_DB

    with _DB_LOCK:
        if _VECTOR_DB is not None:
            return _VECTOR_DB

        client = _get_qdrant_client()

        if not client.collection_exists(collection_name=COLLECTION_NAME):
            print(f"[VectorRepo] Creating new Qdrant collection '{COLLECTION_NAME}'...")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        else:
            print(f"[VectorRepo] Loading Qdrant collection '{COLLECTION_NAME}' from disk...")

        _VECTOR_DB = QdrantVectorStore(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
        )
        return _VECTOR_DB


def add_documents(docs: list, embeddings) -> None:
    """Append documents to the Qdrant store and persist."""
    db = _load_or_create(embeddings)
    with _DB_LOCK:
        db.add_documents(docs)
    print(f"[VectorRepo] Added {len(docs)} documents to Qdrant")


def similarity_search(query: str, embeddings, k: int = 20, filter_dict: dict | None = None) -> list:
    """
    Return k most similar documents.
    Supports Qdrant metadata filtering if filter_dict is provided.
    """
    db = _load_or_create(embeddings)
    
    if not filter_dict:
        return db.similarity_search(query, k=k)

    from qdrant_client.http import models
    
    must_filters = []
    for key, value in filter_dict.items():
        if isinstance(value, list):
            # If value is a list, we use MatchAny or similar if needed, 
            # but for role_allowed we usually check if user_role is IN the list.
            # In Qdrant, if the field is a list, MatchValue(value=X) returns true if X is in the list.
            must_filters.append(
                models.FieldCondition(
                    key=f"metadata.{key}",
                    match=models.MatchValue(value=value[0] if len(value) == 1 else value)
                )
            )
        else:
            must_filters.append(
                models.FieldCondition(
                    key=f"metadata.{key}",
                    match=models.MatchValue(value=value)
                )
            )

    qdrant_filter = models.Filter(must=must_filters)
    return db.similarity_search(query, k=k, filter=qdrant_filter)


def delete_by_source(file_path: str, embeddings) -> None:
    """Delete all chunks belonging to a source file."""
    from qdrant_client.http import models
    
    # Ensure _VECTOR_DB is loaded first so we use the same client
    _load_or_create(embeddings)
    client = _get_qdrant_client()

    with _DB_LOCK:
        if client.collection_exists(collection_name=COLLECTION_NAME):
            client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="metadata.source",
                                match=models.MatchValue(value=file_path),
                            )
                        ]
                    )
                ),
            )
            print(f"[VectorRepo] Deleted chunks for: {file_path}")
        else:
            print(f"[VectorRepo] No collection found, cannot delete: {file_path}")


def clear_all(embeddings) -> None:
    """Wipe the entire vector store and start fresh."""
    global _VECTOR_DB, _QDRANT_CLIENT
    
    client = _get_qdrant_client()
    with _DB_LOCK:
        if client.collection_exists(collection_name=COLLECTION_NAME):
            client.delete_collection(collection_name=COLLECTION_NAME)
            print("[VectorRepo] Collection wiped.")
        _VECTOR_DB = None
    _load_or_create(embeddings)
