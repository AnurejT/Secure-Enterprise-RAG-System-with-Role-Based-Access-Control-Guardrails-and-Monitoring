"""
backend/core/config.py
Centralised application configuration loaded from .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ── Flask ─────────────────────────────────────────────────────────────
SECRET_KEY: str = os.getenv("SECRET_KEY", "enterprise-rag-secret-key-2026")
# Priority: 1. ENV, 2. PostgreSQL (Docker default)
DEFAULT_PG_URL = "postgresql://postgres:postgres@localhost:5432/enterprise_rag"

# ── Smart Fallback ───────────────────────────────────────────────────
# We check if Postgres is reachable. If not, we fallback to SQLite 
# to ensure the app remains functional for local dev.
def _get_db_url():
    import socket
    url = os.getenv("DATABASE_URL", DEFAULT_PG_URL)
    
    # Simple check for localhost postgres
    if "localhost" in url or "127.0.0.1" in url:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(("localhost", 5432)) != 0:
                    sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "db", "users.db"))
                    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
                    print(f"[Config] PostgreSQL not found. Using local fallback: {sqlite_path}")
                    return f"sqlite:///{sqlite_path}"
        except:
            pass
    return url

SQLALCHEMY_DATABASE_URI: str = _get_db_url()
SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

# ── JWT ───────────────────────────────────────────────────────────────
JWT_ALGORITHM: str = "HS256"
JWT_ACCESS_EXPIRY_MINUTES: int = 30
JWT_REFRESH_EXPIRY_DAYS: int = 7

# ── LLM ───────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ── Embeddings ────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

# ── Storage ───────────────────────────────────────────────────────────
STORAGE_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
VECTOR_DIR: str = os.path.join(STORAGE_ROOT, "vector", "qdrant")
DOCUMENTS_DIR: str = os.path.join(STORAGE_ROOT, "documents", "raw")
METADATA_FILE: str = os.path.join(DOCUMENTS_DIR, "roles.json")

# ── Monitoring ────────────────────────────────────────────────────────
LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "enterprise-rag")

# ── CORS ──────────────────────────────────────────────────────────────
CORS_ORIGINS: str = "*"

# ── Ingestion ─────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".csv", ".xlsx", ".md"}

# ── Celery + Redis ───────────────────────────────────────────────────
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL: str = REDIS_URL
CELERY_RESULT_BACKEND: str = REDIS_URL
CELERY_TASK_SERIALIZER: str = "json"
CELERY_ACCEPT_CONTENT: list = ["json"]
CELERY_RESULT_SERIALIZER: str = "json"
CELERY_TIMEZONE: str = "UTC"
CELERY_TASK_TRACK_STARTED: bool = True
CELERY_TASK_TIME_LIMIT: int = 3600  # 1 hour max per task
