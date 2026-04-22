import sys
import io

# 🔥 CRITICAL FIX: Force UTF-8 encoding for stdout/stderr to prevent Windows charmap crashes with emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='backslashreplace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='backslashreplace')

import os
from flask import Flask
from flask_cors import CORS
from extensions import db, bcrypt
from api.routes import api_routes
from api.auth import auth_bp
from api.monitoring_routes import monitoring_bp
from monitoring.langsmith_tracer import configure_langsmith
from models.user import User
from models.message import Message # Register for db.create_all()

app = Flask(__name__)
CORS(app)

# ─── Config ───────────────────────────────────────────────────────────────────
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "enterprise-rag-secret-key-2026")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ─── Init extensions ──────────────────────────────────────────────────────────
db.init_app(app)
bcrypt.init_app(app)

# ─── Enable LangSmith tracing (if LANGCHAIN_API_KEY is set in .env) ──────────
configure_langsmith()

# ─── Blueprints ───────────────────────────────────────────────────────────────
app.register_blueprint(api_routes,   url_prefix="/api")
app.register_blueprint(auth_bp,      url_prefix="/api/auth")
app.register_blueprint(monitoring_bp, url_prefix="/api/monitoring")

# ─── Create tables on first run ───────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)