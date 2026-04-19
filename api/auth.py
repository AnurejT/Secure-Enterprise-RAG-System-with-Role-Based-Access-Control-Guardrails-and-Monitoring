import jwt
import datetime
from flask import Blueprint, request, jsonify, current_app
from extensions import db, bcrypt
from models.user import User, VALID_ROLES

auth_bp = Blueprint("auth", __name__)


# ─── REGISTER ────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role     = (data.get("role") or "employee").strip().lower()
    dept     = (data.get("department") or "employee").strip().lower()

    # Validation
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not email or "@" not in email:
        return jsonify({"error": "Valid email is required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    # Determine final role
    if role == "admin":
        final_role = "admin"
    else:
        final_role = dept if dept in VALID_ROLES else "employee"

    if final_role not in VALID_ROLES:
        return jsonify({"error": "Invalid role"}), 400

    # Check duplicate
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(name=name, email=email, password_hash=password_hash, role=final_role)
    db.session.add(user)
    db.session.commit()

    token = _generate_token(user)
    return jsonify({"token": token, "user": user.to_dict()}), 201


# ─── LOGIN ────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = _generate_token(user)
    return jsonify({"token": token, "user": user.to_dict()}), 200


# ─── Helper ───────────────────────────────────────────────────────────────────
def _generate_token(user):
    payload = {
        "user_id": user.id,
        "email":   user.email,
        "role":    user.role,
        "exp":     datetime.datetime.utcnow() + datetime.timedelta(days=7),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
