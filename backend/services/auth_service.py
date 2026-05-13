"""
backend/services/auth_service.py
Service for authentication and authorization logic.
"""
from backend.core.extensions import bcrypt
from backend.core.security import generate_access_token, generate_refresh_token
from backend.repositories import user_repo

def authenticate_user(email: str, password: str) -> dict | None:
    user = user_repo.get_user_by_email(email)
    if user and bcrypt.check_password_hash(user.password_hash, password):
        return {
            "access_token": generate_access_token(user.email, user.role),
            "refresh_token": generate_refresh_token(user.email),
            "user": {"email": user.email, "role": user.role, "name": user.name}
        }
    return None

def register_user(name: str, email: str, password: str, role: str = "general") -> dict | None:
    if user_repo.get_user_by_email(email):
        return None
    
    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    user = user_repo.create_user(name, email, hashed_pw, role)
    
    return {
        "access_token": generate_access_token(user.email, user.role),
        "refresh_token": generate_refresh_token(user.email),
        "user": {"email": user.email, "role": user.role, "name": user.name}
    }
