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
from flask import Flask, request, jsonify
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
    from backend.core.extensions import db, bcrypt, migrate
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # ── Blueprints ─────────────────────────────────────────────────
    app.register_blueprint(api_routes,    url_prefix="/api")
    app.register_blueprint(auth_bp,       url_prefix="/api/auth")
    app.register_blueprint(monitoring_bp, url_prefix="/api/monitoring")

    # ── Database ───────────────────────────────────────────────────
    with app.app_context():
        if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
            print("[Database] SQLite detected. Initializing tables and seeding admin...")
            db.create_all()
            from backend.models.user import User
            if not User.query.filter_by(email="admin@company.com").first():
                admin = User(
                    name="System Admin",
                    email="admin@company.com",
                    password_hash=bcrypt.generate_password_hash("Admin@123").decode("utf-8"),
                    role="admin"
                )
                db.session.add(admin)
                db.session.commit()
                print("[Database] Admin user seeded.")

    @app.before_request
    def log_request_info():
        print(f"[Request] {request.method} {request.path}")

    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        error_msg = str(e)
        print(f"[Error] Global error handler: {error_msg}")
        traceback.print_exc()
        
        # Help diagnose DB issues
        if "psycopg2" in error_msg or "SQLALCHEMY_DATABASE_URI" in error_msg or "connection" in error_msg.lower():
            return jsonify({
                "error": "Database Connection Error", 
                "details": "The backend cannot connect to PostgreSQL. Ensure your database is running and DATABASE_URL is set correctly.",
                "original_error": error_msg
            }), 500
            
        return jsonify({"error": "Internal Server Error", "details": error_msg}), 500

    return app


# ── LangSmith (once at import time) ────────────────────────────────
configure_langsmith()

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
