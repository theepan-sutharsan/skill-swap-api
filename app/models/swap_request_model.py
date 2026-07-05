from app.extensions import db
from app.utils import utc_now


class SwapRequest(db.Model):
    __tablename__ = "swap_requests"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    offered_skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    requested_skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum("pending", "accepted", "declined", "cancelled", name="swap_status"),
        default="pending",
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    requester = db.relationship(
        "User", foreign_keys=[requester_id], back_populates="swap_requests_sent"
    )
    recipient = db.relationship(
        "User", foreign_keys=[recipient_id], back_populates="swap_requests_received"
    )
    offered_skill = db.relationship("Skill", foreign_keys=[offered_skill_id])
    requested_skill = db.relationship("Skill", foreign_keys=[requested_skill_id])
    session = db.relationship("Session", back_populates="swap_request", uselist=False)
    messages = db.relationship("Message", back_populates="swap_request", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "requester_id": self.requester_id,
            "recipient_id": self.recipient_id,
            "offered_skill_id": self.offered_skill_id,
            "requested_skill_id": self.requested_skill_id,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "requester": self.requester.to_public_dict() if self.requester else None,
            "recipient": self.recipient.to_public_dict() if self.recipient else None,
            "offered_skill": self.offered_skill.to_dict() if self.offered_skill else None,
            "requested_skill": self.requested_skill.to_dict() if self.requested_skill else None,
        }
