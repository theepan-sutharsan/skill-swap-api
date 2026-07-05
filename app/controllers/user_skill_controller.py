from datetime import datetime

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from app.extensions import db
from app.models.skill_model import Skill
from app.models.user_skill_model import UserSkill
from app.utils.csv_utils import parse_csv_file, rows_to_csv_response

VALID_TYPES = ("offered", "wanted")
VALID_LEVELS = ("beginner", "intermediate", "advanced", "expert")


def _validate_user_skill_payload(data, user_skill_id=None, user_id=None):
    errors = []
    skill_id = data.get("skill_id")
    if not user_skill_id and not skill_id and not data.get("skill_name"):
        errors.append("skill_id or skill_name is required.")
    if "type" in data and data["type"] not in VALID_TYPES:
        errors.append(f"type must be one of: {', '.join(VALID_TYPES)}")
    if "level" in data and data["level"] not in VALID_LEVELS:
        errors.append(f"level must be one of: {', '.join(VALID_LEVELS)}")
    if not user_skill_id:
        if not data.get("type"):
            errors.append("type is required.")
        if not data.get("level"):
            errors.append("level is required.")
        uid = user_id or data.get("user_id")
        stype = data.get("type")
        sid = skill_id
        if uid and sid and stype:
            existing = UserSkill.query.filter_by(
                user_id=uid, skill_id=sid, type=stype
            ).first()
            if existing:
                errors.append("Duplicate entry for this skill and type.")
    return errors


def _resolve_skill(data):
    skill_id = data.get("skill_id")
    if skill_id:
        return Skill.query.get(skill_id)
    skill_name = (data.get("skill_name") or "").strip()
    if not skill_name:
        return None
    skill = Skill.query.filter_by(name=skill_name).first()
    if not skill:
        category = data.get("category", "General").strip()
        skill = Skill(name=skill_name, category=category)
        db.session.add(skill)
        db.session.flush()
    return skill


def create_user_skill(data, user_id=None):
    uid = user_id or int(get_jwt_identity())
    errors = _validate_user_skill_payload(data, user_id=uid)
    if errors:
        return jsonify({"errors": errors}), 400

    skill = _resolve_skill(data)
    if not skill:
        return jsonify({"error": "Skill not found."}), 400

    data["skill_id"] = skill.id
    errors = _validate_user_skill_payload(data, user_id=uid)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        user_skill = UserSkill(
            user_id=uid,
            skill_id=skill.id,
            type=data["type"],
            level=data["level"],
            notes=data.get("notes", "").strip() or None,
        )
        db.session.add(user_skill)
        db.session.commit()
        return (
            jsonify({"message": "User skill created.", "user_skill": user_skill.to_dict()}),
            201,
        )
    except Exception:
        db.session.rollback()
        raise


def get_my_skills(skill_type=None, user_id=None):
    uid = user_id or int(get_jwt_identity())
    query = UserSkill.query.filter_by(user_id=uid)
    if skill_type in VALID_TYPES:
        query = query.filter_by(type=skill_type)
    skills = query.order_by(UserSkill.created_at.desc()).all()
    return jsonify({"user_skills": [s.to_dict() for s in skills]}), 200


def get_user_skill(user_skill_id, user_id=None):
    uid = user_id or int(get_jwt_identity())
    user_skill = UserSkill.query.get(user_skill_id)
    if not user_skill or user_skill.user_id != uid:
        return jsonify({"error": "User skill not found."}), 404
    return jsonify({"user_skill": user_skill.to_dict()}), 200


def update_user_skill(user_skill_id, data, user_id=None):
    uid = user_id or int(get_jwt_identity())
    user_skill = UserSkill.query.get(user_skill_id)
    if not user_skill or user_skill.user_id != uid:
        return jsonify({"error": "User skill not found."}), 404

    errors = _validate_user_skill_payload(data, user_skill_id=user_skill_id)
    if errors:
        return jsonify({"errors": errors}), 400

    if "type" in data:
        user_skill.type = data["type"]
    if "level" in data:
        user_skill.level = data["level"]
    if "notes" in data:
        user_skill.notes = data["notes"].strip() if data["notes"] else None
    if "skill_id" in data:
        skill = Skill.query.get(data["skill_id"])
        if not skill:
            return jsonify({"error": "Skill not found."}), 404
        dup = UserSkill.query.filter_by(
            user_id=uid, skill_id=skill.id, type=user_skill.type
        ).filter(UserSkill.id != user_skill_id).first()
        if dup:
            return jsonify({"error": "Duplicate entry for this skill and type."}), 400
        user_skill.skill_id = skill.id

    try:
        db.session.commit()
        return (
            jsonify({"message": "User skill updated.", "user_skill": user_skill.to_dict()}),
            200,
        )
    except Exception:
        db.session.rollback()
        raise


def delete_user_skill(user_skill_id, user_id=None):
    uid = user_id or int(get_jwt_identity())
    user_skill = UserSkill.query.get(user_skill_id)
    if not user_skill or user_skill.user_id != uid:
        return jsonify({"error": "User skill not found."}), 404
    try:
        db.session.delete(user_skill)
        db.session.commit()
        return jsonify({"message": "User skill deleted."}), 200
    except Exception:
        db.session.rollback()
        raise


def export_my_skills_csv(user_id=None):
    uid = user_id or int(get_jwt_identity())
    skills = UserSkill.query.filter_by(user_id=uid).all()
    headers = ["skill_name", "category", "type", "level", "notes"]
    rows = [
        [
            us.skill.name if us.skill else "",
            us.skill.category if us.skill else "",
            us.type,
            us.level,
            us.notes or "",
        ]
        for us in skills
    ]
    filename = f"my-skills-{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
    return rows_to_csv_response(filename, headers, rows)


def import_my_skills_csv(file, user_id=None):
    uid = user_id or int(get_jwt_identity())
    rows, header_errors = parse_csv_file(
        file, ["skill_name", "category", "type", "level", "notes"]
    )
    if header_errors:
        return jsonify({"errors": header_errors}), 400

    created = 0
    skipped = 0
    errors = []
    for i, row in enumerate(rows, start=2):
        payload = {
            "skill_name": row.get("skill_name", "").strip(),
            "category": row.get("category", "General").strip(),
            "type": row.get("type", "").strip(),
            "level": row.get("level", "").strip(),
            "notes": row.get("notes", "").strip(),
        }
        val_errors = _validate_user_skill_payload(payload, user_id=uid)
        if val_errors:
            errors.append({"row": i, "message": "; ".join(val_errors)})
            continue
        skill = _resolve_skill(payload)
        if UserSkill.query.filter_by(
            user_id=uid, skill_id=skill.id, type=payload["type"]
        ).first():
            skipped += 1
            continue
        try:
            us = UserSkill(
                user_id=uid,
                skill_id=skill.id,
                type=payload["type"],
                level=payload["level"],
                notes=payload["notes"] or None,
            )
            db.session.add(us)
            created += 1
        except Exception as exc:
            errors.append({"row": i, "message": str(exc)})

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({"created": created, "skipped": skipped, "errors": errors}), 200
