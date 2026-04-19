from extensions import db

VALID_ROLES = {"admin", "employee", "finance", "hr", "marketing"}


class User(db.Model):
    __tablename__ = "users"

    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(120), nullable=False)
    email        = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role         = db.Column(db.String(50), nullable=False, default="employee")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}
