"""
backend/repositories/user_repo.py
Repository for User-related database operations.
"""
from backend.core.extensions import db
from backend.models.user import User

def get_user_by_email(email: str) -> User | None:
    return User.query.filter_by(email=email.lower()).first()

def create_user(name: str, email: str, password_hash: str, role: str) -> User:
    new_user = User(name=name, email=email.lower(), password_hash=password_hash, role=role)
    db.session.add(new_user)
    db.session.commit()
    return new_user
