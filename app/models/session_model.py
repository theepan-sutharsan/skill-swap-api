from app.extensions import db
from app.utils import utc_now


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    swap_request_id = db.Column(
        db.Integer, db.ForeignKey("swap_requests.id"), unique=True, nullable=False
    )
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60, nullable=False)
    mode = db.Column(
        db.Enum("online", "in_person", name="session_mode"), nullable=False
    )
    location = db.Column(db.String(512), nullable=True)
    status = db.Column(
        db.Enum("scheduled", "completed", "cancelled", name="session_status"),
        default="scheduled",
        nullable=False,
    )
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    swap_request = db.relationship("SwapRequest", back_populates="session")
    feedback_entries = db.relationship("Feedback", back_populates="session", lazy="dynamic")

    def to_dict(self):
        data = {
            "id": self.id,
            "swap_request_id": self.swap_request_id,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "duration_minutes": self.duration_minutes,
            "mode": self.mode,
            "location": self.location,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if self.swap_request:
            data["swap_request"] = self.swap_request.to_dict()
        return data

    def participant_ids(self):
        if not self.swap_request:
            return []
        return [self.swap_request.requester_id, self.swap_request.recipient_id]
