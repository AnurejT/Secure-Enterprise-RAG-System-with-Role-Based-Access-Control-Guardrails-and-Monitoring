# api/auth.py
import jwt
import datetime
from functools import wraps
from flask import Blueprint, request, jsonify
from extensions import db, bcrypt
from models.user import User

# ✅ Added Blueprint for auth routes
auth_bp = Blueprint("auth", __name__)

SECRET_KEY = "enterprise-rag-secret-key-2026"  # move to .env in production

# 🔑 Generate JWT
def generate_token(email, role):
    payload = {
        "email": email,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

# 🔍 Verify JWT
def verify_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# 🔐 Decorator for protected routes
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Token missing"}), 401

        try:
            token = auth_header.split(" ")[1]  # Bearer <token>
        except:
            return jsonify({"error": "Invalid token format"}), 401

        data = verify_token(token)

        if not data:
            return jsonify({"error": "Invalid or expired token"}), 401

        # attach user info to request
        request.user = data

        return f(*args, **kwargs)

    return decorated

# -------------------------
# AUTH ROUTES 🔐
# -------------------------

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Missing email or password"}), 400

    email = data.get("email").lower()
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token(user.email, user.role)

    return jsonify({
        "token": token,
        "user": {
            "email": user.email,
            "role": user.role,
            "name": user.name
        }
    })

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    if not data or not data.get("email") or not data.get("password") or not data.get("name"):
        return jsonify({"error": "Missing required fields"}), 400

    email = data.get("email").lower()
    password = data.get("password")
    name = data.get("name")
    
    frontend_role = data.get("role", "employee")
    department = data.get("department", "employee")
    
    # if admin is selected but they don't have a special key or it's not allowed, we just let them for the demo
    final_role = department if frontend_role != "admin" else "admin"

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email is already registered"}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    
    new_user = User(
        name=name,
        email=email,
        password_hash=hashed_pw,
        role=final_role
    )
    
    db.session.add(new_user)
    db.session.commit()

    token = generate_token(new_user.email, new_user.role)

    return jsonify({
        "message": "User created successfully",
        "token": token,
        "user": {
            "email": new_user.email,
            "role": new_user.role,
            "name": new_user.name
        }
    }), 201