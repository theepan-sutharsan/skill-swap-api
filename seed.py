"""Seed demo data for viva presentation."""

from app import create_app
from app.extensions import db
from app.models.skill_model import Skill
from app.models.swap_request_model import SwapRequest
from app.models.user_model import User
from app.models.user_skill_model import UserSkill


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        if User.query.filter_by(email="admin@skillswap.test").first():
            print("Seed data already exists. Skipping.")
            return

        admin = User(
            email="admin@skillswap.test",
            full_name="Platform Admin",
            role="admin",
            location="London",
        )
        admin.set_password("Admin123")

        alice = User(
            email="alice@skillswap.test",
            full_name="Alice Martin",
            role="member",
            location="London",
            bio="Music enthusiast learning to code.",
        )
        alice.set_password("ChangeMe123")

        bob = User(
            email="bob@skillswap.test",
            full_name="Bob Chen",
            role="member",
            location="Manchester",
            bio="Python developer learning guitar.",
        )
        bob.set_password("ChangeMe123")

        db.session.add_all([admin, alice, bob])
        db.session.flush()

        catalog = [
            ("Guitar", "Music", "Acoustic & electric basics"),
            ("Python Programming", "Technology", "From zero to web apps"),
            ("Spanish", "Language", "Conversational Spanish"),
            ("Cooking", "Culinary", "Home cooking essentials"),
            ("Photography", "Art", "Digital photography fundamentals"),
        ]
        skills = {}
        for name, category, description in catalog:
            skill = Skill(name=name, category=category, description=description)
            db.session.add(skill)
            skills[name] = skill
        db.session.flush()

        user_skills = [
            (alice.id, skills["Guitar"].id, "offered", "advanced", "10 years playing"),
            (alice.id, skills["Python Programming"].id, "wanted", "beginner", "Want to build a website"),
            (bob.id, skills["Python Programming"].id, "offered", "expert", "Professional developer"),
            (bob.id, skills["Guitar"].id, "wanted", "beginner", "Just starting out"),
        ]
        for user_id, skill_id, stype, level, notes in user_skills:
            db.session.add(
                UserSkill(
                    user_id=user_id,
                    skill_id=skill_id,
                    type=stype,
                    level=level,
                    notes=notes,
                )
            )

        pending = SwapRequest(
            requester_id=alice.id,
            recipient_id=bob.id,
            offered_skill_id=skills["Guitar"].id,
            requested_skill_id=skills["Python Programming"].id,
            message="Hi Bob! I'd love to swap Guitar lessons for Python help.",
            status="pending",
        )
        db.session.add(pending)
        db.session.commit()
        print("Seed data created successfully.")
        print("  Admin: admin@skillswap.test / Admin123")
        print("  Alice: alice@skillswap.test / ChangeMe123")
        print("  Bob:   bob@skillswap.test / ChangeMe123")


if __name__ == "__main__":
    seed()
