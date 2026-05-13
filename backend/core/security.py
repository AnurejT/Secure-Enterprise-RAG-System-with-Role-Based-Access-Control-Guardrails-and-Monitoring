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


def generate_access_token(email: str, role: str) -> str:
    """Encode a short-lived access JWT."""
    payload = {
        "email": email,
        "role": role,
        "type": "access",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=config.JWT_ACCESS_EXPIRY_MINUTES),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def generate_refresh_token(email: str) -> str:
    """Encode a long-lived refresh JWT."""
    payload = {
        "email": email,
        "type": "refresh",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=config.JWT_REFRESH_EXPIRY_DAYS),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def verify_token(token: str, expected_type: str = "access") -> dict | None:
    """Decode and verify a JWT. Checks type to prevent token swapping."""
    try:
        data = jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        if data.get("type") != expected_type:
            return None
        return data
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
