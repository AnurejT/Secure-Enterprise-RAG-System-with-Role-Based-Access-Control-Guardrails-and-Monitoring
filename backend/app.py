"""
backend/app.py
Flask application factory — the single entry point for the backend.
Run with: python -m backend.app
"""
import sys
import io

# Force UTF-8 for Windows consoles to avoid emoji/charmap crashes
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="backslashreplace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="backslashreplace")

import os
# pyrefly: ignore [missing-import]
from flask import Flask
from flask_cors import CORS

from backend.core import config
from backend.core.extensions import db, bcrypt
from backend.api.v1.auth import auth_bp
from backend.api.v1.routes import api_routes
from backend.api.v1.monitoring import monitoring_bp
from backend.monitoring.tracer import configure_langsmith

# Import models so db.create_all() registers their tables
from backend.models import user, message  # noqa: F401


def create_app() -> Flask:
    app = Flask(__name__)

    # ── Configuration ──────────────────────────────────────────────
    app.config["SECRET_KEY"]                  = config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"]     = config.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS

    # ── CORS ───────────────────────────────────────────────────────
    CORS(app, resources={r"/api/*": {
        "origins":          config.CORS_ORIGINS,
        "methods":          ["GET", "POST", "DELETE", "PUT", "PATCH", "OPTIONS"],
        "allow_headers":    ["Content-Type", "Authorization"],
        "expose_headers":   ["Content-Type", "Authorization"],
        "supports_credentials": False,
        "max_age":          3600,
    }})

    # ── Extensions ─────────────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)

    # ── Blueprints ─────────────────────────────────────────────────
    app.register_blueprint(api_routes,    url_prefix="/api")
    app.register_blueprint(auth_bp,       url_prefix="/api/auth")
    app.register_blueprint(monitoring_bp, url_prefix="/api/monitoring")

    # ── Database ───────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    return app


# ── LangSmith (once at import time) ────────────────────────────────
configure_langsmith()

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
