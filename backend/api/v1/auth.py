"""
backend/api/v1/auth.py
Authentication blueprint — login, register, JWT management.
"""
from flask import Blueprint, request, jsonify

from backend.core.extensions import db, bcrypt
from backend.core.security import generate_token
from backend.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Missing email or password"}), 400

    email = data["email"].lower()
    user  = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "token": generate_token(user.email, user.role),
        "user":  {"email": user.email, "role": user.role, "name": user.name},
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

    frontend_role = data.get("role", "general")
    department    = data.get("department", "general")
    final_role    = department if frontend_role != "admin" else "admin"

    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    new_user  = User(name=data["name"], email=email, password_hash=hashed_pw, role=final_role)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User created successfully",
        "token":   generate_token(new_user.email, new_user.role),
        "user":    {"email": new_user.email, "role": new_user.role, "name": new_user.name},
    }), 201
