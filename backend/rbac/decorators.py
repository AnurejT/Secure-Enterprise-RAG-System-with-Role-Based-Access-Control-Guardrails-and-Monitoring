"""
backend/rbac/decorators.py
Flask route decorators for role-based access control.
"""
from functools import wraps
from flask import jsonify, request


def require_role(*allowed_roles: str):
    """
    Decorator to restrict a route to specific roles.
    Must be used after @token_required so request.user is populated.

    Usage:
        @app.route("/admin-only")
        @token_required
        @require_role("admin")
        def admin_only():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(request, "user", {})
            role = user.get("role", "")
            if role not in allowed_roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_admin(f):
    """Shortcut decorator that requires the 'admin' role."""
    return require_role("admin")(f)
