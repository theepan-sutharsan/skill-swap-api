from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.utils import utc_now


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "member", name="user_role"), default="member", nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    avatar_url = db.Column(db.String(512), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    user_skills = db.relationship("UserSkill", back_populates="user", lazy="dynamic")
    swap_requests_sent = db.relationship(
        "SwapRequest",
        foreign_keys="SwapRequest.requester_id",
        back_populates="requester",
        lazy="dynamic",
    )
    swap_requests_received = db.relationship(
        "SwapRequest",
        foreign_keys="SwapRequest.recipient_id",
        back_populates="recipient",
        lazy="dynamic",
    )

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self, include_email=True):
        data = {
            "id": self.id,
            "role": self.role,
            "full_name": self.full_name,
            "bio": self.bio,
            "location": self.location,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_email:
            data["email"] = self.email
        return data

    def to_public_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "bio": self.bio,
            "location": self.location,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
