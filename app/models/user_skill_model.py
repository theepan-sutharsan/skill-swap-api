from app.extensions import db
from app.utils import utc_now


class UserSkill(db.Model):
    __tablename__ = "user_skills"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    type = db.Column(
        db.Enum("offered", "wanted", name="user_skill_type"), nullable=False
    )
    level = db.Column(
        db.Enum("beginner", "intermediate", "advanced", "expert", name="skill_level"),
        nullable=False,
    )
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "skill_id", "type", name="uq_user_skill_type"),
    )

    user = db.relationship("User", back_populates="user_skills")
    skill = db.relationship("Skill", back_populates="user_skills")

    def to_dict(self):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "skill_id": self.skill_id,
            "type": self.type,
            "level": self.level,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if self.skill:
            data["skill"] = self.skill.to_dict()
        return data
