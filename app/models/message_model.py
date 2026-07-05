from app.extensions import db
from app.utils import utc_now


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    swap_request_id = db.Column(
        db.Integer, db.ForeignKey("swap_requests.id"), nullable=False
    )
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    swap_request = db.relationship("SwapRequest", back_populates="messages")
    sender = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "swap_request_id": self.swap_request_id,
            "sender_id": self.sender_id,
            "body": self.body,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sender": self.sender.to_public_dict() if self.sender else None,
        }
