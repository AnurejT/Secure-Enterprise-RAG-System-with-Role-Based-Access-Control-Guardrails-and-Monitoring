from backend.app import create_app
from backend.core.extensions import db, bcrypt
from backend.models.user import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(email="admin@company.com").first()
    if not admin:
        print("Admin user not found. Creating default admin...")
        hashed_pw = bcrypt.generate_password_hash("Admin@123").decode("utf-8")
        new_admin = User(
            name="System Admin",
            email="admin@company.com",
            password_hash=hashed_pw,
            role="admin"
        )
        db.session.add(new_admin)
        db.session.commit()
        print("Admin user 'admin@company.com' created with password 'Admin@123'.")
    else:
        print(f"Admin user found: {admin.email}, Role: {admin.role}")
        # Reset password just in case the user forgot it
        hashed_pw = bcrypt.generate_password_hash("Admin@123").decode("utf-8")
        admin.password_hash = hashed_pw
        db.session.commit()
        print("Admin password reset to 'Admin@123'.")
