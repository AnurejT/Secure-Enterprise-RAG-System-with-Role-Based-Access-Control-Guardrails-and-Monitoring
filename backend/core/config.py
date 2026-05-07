"""
backend/core/config.py
Centralised application configuration loaded from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Flask ─────────────────────────────────────────────────────────────
SECRET_KEY: str = os.getenv("SECRET_KEY", "enterprise-rag-secret-key-2026")
SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'db', 'users.db'))}"
SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

# ── JWT ───────────────────────────────────────────────────────────────
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRY_HOURS: int = 2

# ── LLM ───────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ── Embeddings ────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

# ── Storage ───────────────────────────────────────────────────────────
STORAGE_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
VECTOR_DIR: str = os.path.join(STORAGE_ROOT, "vector", "faiss")
DOCUMENTS_DIR: str = os.path.join(STORAGE_ROOT, "documents", "raw")
METADATA_FILE: str = os.path.join(DOCUMENTS_DIR, "roles.json")

# ── Monitoring ────────────────────────────────────────────────────────
LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "enterprise-rag")

# ── CORS ──────────────────────────────────────────────────────────────
CORS_ORIGINS: str = "*"

# ── Ingestion ─────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".csv", ".xlsx", ".md"}
