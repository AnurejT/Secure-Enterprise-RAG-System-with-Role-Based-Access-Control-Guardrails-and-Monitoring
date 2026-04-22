from extensions import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = "messages"

    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role      = db.Column(db.String(50), nullable=False)
    type      = db.Column(db.String(20), nullable=False) # 'user' or 'bot'
    text      = db.Column(db.Text, nullable=False)
    sources   = db.Column(db.Text, nullable=True) # JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "sources": json.loads(self.sources) if self.sources else [],
            "timestamp": self.timestamp.isoformat()
        }
