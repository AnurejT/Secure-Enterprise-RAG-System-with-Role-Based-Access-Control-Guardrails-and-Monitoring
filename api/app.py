import os
from flask import Flask
from flask_cors import CORS
from extensions import db, bcrypt
from api.routes import api_routes
from api.auth import auth_bp

app = Flask(__name__)
CORS(app)

# ─── Config ───────────────────────────────────────────────────────────────────
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "enterprise-rag-secret-key-2026")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ─── Init extensions ──────────────────────────────────────────────────────────
db.init_app(app)
bcrypt.init_app(app)

# ─── Blueprints ───────────────────────────────────────────────────────────────
app.register_blueprint(api_routes, url_prefix="/api")
app.register_blueprint(auth_bp, url_prefix="/api/auth")

# ─── Create tables on first run ───────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)