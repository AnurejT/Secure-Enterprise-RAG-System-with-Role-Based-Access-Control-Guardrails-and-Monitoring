"""
backend/api/v1/auth.py
Authentication blueprint — login, register, JWT management.
"""
import re
from flask import Blueprint, request, jsonify

from backend.core.extensions import db, bcrypt
from backend.core.security import generate_access_token, generate_refresh_token, verify_token
from backend.models.user import User

auth_bp = Blueprint("auth", __name__)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Ensure password meets enterprise complexity requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    return True, ""


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Missing email or password"}), 400

    email = data["email"].strip().lower()
    password = data["password"]
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        print(f"[Auth] Login failed: User {email} not found.")
        return jsonify({"error": "Invalid credentials"}), 401

    is_match = bcrypt.check_password_hash(user.password_hash, password)
    print(f"[Auth] Login attempt: {email}, match: {is_match}")

    if not is_match:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "access_token":  generate_access_token(user.email, user.role),
        "refresh_token": generate_refresh_token(user.email),
        "user":          {"email": user.email, "role": user.role, "name": user.name},
    })


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """Exchange a refresh token for a new access token."""
    data = request.json or {}
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        return jsonify({"error": "Refresh token missing"}), 400

    decoded = verify_token(refresh_token, expected_type="refresh")
    if not decoded:
        return jsonify({"error": "Invalid or expired refresh token"}), 401

    email = decoded["email"]
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User no longer exists"}), 404

    return jsonify({
        "access_token": generate_access_token(user.email, user.role),
    })


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    required = ("email", "password", "name")
    if not all(data.get(f) for f in required):
        return jsonify({"error": "Missing required fields"}), 400

    email = data["email"].lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered"}), 400

    # ── Password Policy ────────────────────────────────────────────
    is_strong, msg = validate_password_strength(data["password"])
    if not is_strong:
        return jsonify({"error": msg}), 400

    frontend_role = data.get("role", "general")
    department    = data.get("department", "general")
    final_role    = department if frontend_role != "admin" else "admin"

    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    new_user  = User(name=data["name"], email=email, password_hash=hashed_pw, role=final_role)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User created successfully",
        "access_token":  generate_access_token(new_user.email, new_user.role),
        "refresh_token": generate_refresh_token(new_user.email),
        "user":          {"email": new_user.email, "role": new_user.role, "name": new_user.name},
    }), 201
