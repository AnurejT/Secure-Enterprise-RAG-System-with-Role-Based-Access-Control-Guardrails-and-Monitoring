from backend.app import create_app
from backend.core.extensions import db, bcrypt
from backend.models.user import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(email="admin@company.com").first()
    if admin:
        print(f"DEBUG: Found user {admin.email}")
        print(f"DEBUG: Stored Hash: {admin.password_hash}")
        test_pw = "Admin@123"
        is_match = bcrypt.check_password_hash(admin.password_hash, test_pw)
        print(f"DEBUG: Verification with '{test_pw}': {is_match}")
    else:
        print("DEBUG: Admin user not found!")
