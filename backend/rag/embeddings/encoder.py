"""
backend/rag/embeddings/encoder.py
Singleton HuggingFace embedding model.
"""
from langchain_huggingface import HuggingFaceEmbeddings
from backend.core.config import EMBEDDING_MODEL

_embeddings_cache = None


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings_cache
    if _embeddings_cache is None:
        _embeddings_cache = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings_cache
