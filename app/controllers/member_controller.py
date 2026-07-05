from datetime import datetime

from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func, or_

from app.extensions import db
from app.models.feedback_model import Feedback
from app.models.skill_model import Skill
from app.models.user_model import User
from app.models.user_skill_model import UserSkill
from app.utils.csv_utils import parse_csv_file, rows_to_csv_response
from app.utils.pdf_utils import document_pdf_response


def _validate_member_payload(data, member_id=None):
    errors = []
    if not data.get("full_name"):
        errors.append("Full name is required.")
    if "email" in data:
        email = data["email"].strip().lower()
        existing = User.query.filter_by(email=email).first()
        if existing and (member_id is None or existing.id != member_id):
            errors.append("Email already in use.")
    return errors


def get_members(q=None, location=None, skill=None, category=None):
    query = User.query.filter_by(role="member", is_active=True)

    if q:
        term = f"%{q}%"
        query = query.filter(
            or_(User.full_name.ilike(term), User.bio.ilike(term), User.location.ilike(term))
        )
    if location:
        query = query.filter(User.location.ilike(f"%{location}%"))
    if skill or category:
        query = query.join(UserSkill).join(Skill)
        if skill:
            query = query.filter(Skill.name.ilike(f"%{skill}%"))
        if category:
            query = query.filter(Skill.category.ilike(f"%{category}%"))
        query = query.distinct()

    members = query.order_by(User.full_name).all()
    return jsonify({"members": [m.to_public_dict() for m in members]}), 200


def get_member(member_id):
    user = User.query.get(member_id)
    if not user or user.role != "member":
        return jsonify({"error": "Member not found."}), 404

    offered = (
        UserSkill.query.filter_by(user_id=member_id, type="offered")
        .join(Skill)
        .all()
    )
    wanted = (
        UserSkill.query.filter_by(user_id=member_id, type="wanted")
        .join(Skill)
        .all()
    )
    avg_rating = (
        db.session.query(func.avg(Feedback.rating))
        .filter(Feedback.reviewee_id == member_id)
        .scalar()
    )

    data = user.to_public_dict()
    data["offered_skills"] = [us.to_dict() for us in offered]
    data["wanted_skills"] = [us.to_dict() for us in wanted]
    data["average_rating"] = round(float(avg_rating), 2) if avg_rating else None
    return jsonify({"member": data}), 200


def get_member_skills(member_id):
    user = User.query.get(member_id)
    if not user:
        return jsonify({"error": "Member not found."}), 404
    skills = UserSkill.query.filter_by(user_id=member_id).all()
    return jsonify({"user_skills": [s.to_dict() for s in skills]}), 200


def update_member(member_id, data):
    user = User.query.get(member_id)
    if not user:
        return jsonify({"error": "Member not found."}), 404

    errors = _validate_member_payload(data, member_id)
    if errors:
        return jsonify({"errors": errors}), 400

    if "full_name" in data:
        user.full_name = data["full_name"].strip()
    if "email" in data:
        user.email = data["email"].strip().lower()
    if "bio" in data:
        user.bio = data["bio"].strip() if data["bio"] else None
    if "location" in data:
        user.location = data["location"].strip() if data["location"] else None
    if "avatar_url" in data:
        user.avatar_url = data["avatar_url"].strip() if data["avatar_url"] else None
    if "password" in data and data["password"]:
        user.set_password(data["password"])

    try:
        db.session.commit()
        return jsonify({"message": "Member updated.", "member": user.to_dict()}), 200
    except Exception:
        db.session.rollback()
        raise


def patch_member_status(member_id, data):
    user = User.query.get(member_id)
    if not user:
        return jsonify({"error": "Member not found."}), 404
    if "is_active" not in data:
        return jsonify({"errors": ["is_active is required."]}), 400

    user.is_active = bool(data["is_active"])
    try:
        db.session.commit()
        return jsonify({"message": "Member status updated.", "member": user.to_dict()}), 200
    except Exception:
        db.session.rollback()
        raise


def delete_member(member_id):
    user = User.query.get(member_id)
    if not user:
        return jsonify({"error": "Member not found."}), 404
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Member deleted."}), 200
    except Exception:
        db.session.rollback()
        raise


def export_members_csv():
    members = User.query.filter_by(role="member").order_by(User.full_name).all()
    headers = ["email", "full_name", "location", "role", "is_active", "created_at"]
    rows = [
        [m.email, m.full_name, m.location or "", m.role, m.is_active, m.created_at.isoformat()]
        for m in members
    ]
    filename = f"members-{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
    return rows_to_csv_response(filename, headers, rows)


def import_members_csv(file):
    rows, header_errors = parse_csv_file(
        file, ["email", "full_name", "location", "password"]
    )
    if header_errors:
        return jsonify({"errors": header_errors}), 400

    created = 0
    skipped = 0
    errors = []
    for i, row in enumerate(rows, start=2):
        email = row.get("email", "").strip().lower()
        if not email:
            errors.append({"row": i, "message": "Email is required."})
            continue
        if User.query.filter_by(email=email).first():
            skipped += 1
            continue
        try:
            user = User(
                email=email,
                full_name=row.get("full_name", "").strip() or email,
                location=row.get("location", "").strip() or None,
                role="member",
            )
            user.set_password(row.get("password", "ChangeMe123"))
            db.session.add(user)
            created += 1
        except Exception as exc:
            errors.append({"row": i, "message": str(exc)})

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({"created": created, "skipped": skipped, "errors": errors}), 200


def export_member_pdf(member_id):
    user = User.query.get(member_id)
    if not user:
        return jsonify({"error": "Member not found."}), 404

    offered = UserSkill.query.filter_by(user_id=member_id, type="offered").all()
    wanted = UserSkill.query.filter_by(user_id=member_id, type="wanted").all()
    avg_rating = (
        db.session.query(func.avg(Feedback.rating))
        .filter(Feedback.reviewee_id == member_id)
        .scalar()
    )

    offered_str = ", ".join(
        f"{us.skill.name} ({us.level})" for us in offered if us.skill
    ) or "None"
    wanted_str = ", ".join(
        f"{us.skill.name} ({us.level})" for us in wanted if us.skill
    ) or "None"

    sections = [
        (
            "Profile",
            [
                ("Name", user.full_name),
                ("Location", user.location or "—"),
                ("Bio", user.bio or "—"),
                ("Average Rating", round(float(avg_rating), 2) if avg_rating else "—"),
            ],
        ),
        ("Skills Offered", [("Skills", offered_str)]),
        ("Skills Wanted", [("Skills", wanted_str)]),
    ]
    filename = f"member-{user.id}-profile.pdf"
    return document_pdf_response(filename, f"Member Profile: {user.full_name}", sections)
