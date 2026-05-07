"""
backend/core/security.py
JWT generation, verification, and the token_required decorator.
Extracted from api/auth.py so it can be reused across blueprints.
"""
import datetime
from functools import wraps

import jwt
from flask import request, jsonify

from backend.core import config


def generate_token(email: str, role: str) -> str:
    """Encode a signed JWT for the given user."""
    payload = {
        "email": email,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=config.JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Decode a JWT. Returns payload dict or None on any error."""
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def token_required(f):
    """Flask route decorator that enforces JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow CORS preflight through without auth
        if request.method == "OPTIONS":
            return "", 204

        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return jsonify({"error": "Token missing"}), 401

        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0] != "Bearer":
            return jsonify({"error": "Invalid token format"}), 401

        data = verify_token(parts[1])
        if not data:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.user = data
        return f(*args, **kwargs)

    return decorated
