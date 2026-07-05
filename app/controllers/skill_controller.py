from datetime import datetime

from flask import jsonify, request
from sqlalchemy import or_

from app.extensions import db
from app.models.skill_model import Skill
from app.utils.csv_utils import parse_csv_file, rows_to_csv_response
from app.utils.pdf_utils import table_pdf_response


def _validate_skill_payload(data, skill_id=None):
    errors = []
    if not data.get("name"):
        errors.append("Name is required.")
    if not data.get("category"):
        errors.append("Category is required.")
    if data.get("name"):
        name = data["name"].strip()
        existing = Skill.query.filter_by(name=name).first()
        if existing and (skill_id is None or existing.id != skill_id):
            errors.append("Skill name already exists.")
    return errors


def create_skill(data):
    errors = _validate_skill_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400
    try:
        skill = Skill(
            name=data["name"].strip(),
            category=data["category"].strip(),
            description=data.get("description", "").strip() or None,
        )
        db.session.add(skill)
        db.session.commit()
        return jsonify({"message": "Skill created.", "skill": skill.to_dict()}), 201
    except Exception:
        db.session.rollback()
        raise


def get_skills(q=None, category=None):
    query = Skill.query
    if q:
        term = f"%{q}%"
        query = query.filter(
            or_(Skill.name.ilike(term), Skill.description.ilike(term))
        )
    if category:
        query = query.filter(Skill.category.ilike(f"%{category}%"))
    skills = query.order_by(Skill.name).all()
    return jsonify({"skills": [s.to_dict() for s in skills]}), 200


def get_skill(skill_id):
    skill = Skill.query.get(skill_id)
    if not skill:
        return jsonify({"error": "Skill not found."}), 404
    return jsonify({"skill": skill.to_dict()}), 200


def update_skill(skill_id, data):
    skill = Skill.query.get(skill_id)
    if not skill:
        return jsonify({"error": "Skill not found."}), 404
    errors = _validate_skill_payload(data, skill_id)
    if errors:
        return jsonify({"errors": errors}), 400
    skill.name = data.get("name", skill.name).strip()
    skill.category = data.get("category", skill.category).strip()
    if "description" in data:
        skill.description = data["description"].strip() if data["description"] else None
    try:
        db.session.commit()
        return jsonify({"message": "Skill updated.", "skill": skill.to_dict()}), 200
    except Exception:
        db.session.rollback()
        raise


def delete_skill(skill_id):
    skill = Skill.query.get(skill_id)
    if not skill:
        return jsonify({"error": "Skill not found."}), 404
    try:
        db.session.delete(skill)
        db.session.commit()
        return jsonify({"message": "Skill deleted."}), 200
    except Exception:
        db.session.rollback()
        raise


def export_skills(format_type="csv"):
    skills = Skill.query.order_by(Skill.category, Skill.name).all()
    if format_type == "pdf":
        headers = ["Name", "Category", "Description"]
        rows = [[s.name, s.category, s.description or ""] for s in skills]
        filename = f"skills-{datetime.utcnow().strftime('%Y-%m-%d')}.pdf"
        return table_pdf_response(filename, "Skills Catalog", headers, rows)

    headers = ["name", "category", "description"]
    rows = [[s.name, s.category, s.description or ""] for s in skills]
    filename = f"skills-{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
    return rows_to_csv_response(filename, headers, rows)


def import_skills_csv(file):
    rows, header_errors = parse_csv_file(file, ["name", "category", "description"])
    if header_errors:
        return jsonify({"errors": header_errors}), 400

    created = 0
    skipped = 0
    errors = []
    for i, row in enumerate(rows, start=2):
        name = row.get("name", "").strip()
        if not name:
            errors.append({"row": i, "message": "Name is required."})
            continue
        if Skill.query.filter_by(name=name).first():
            skipped += 1
            continue
        if not row.get("category", "").strip():
            errors.append({"row": i, "message": "Category is required."})
            continue
        try:
            skill = Skill(
                name=name,
                category=row["category"].strip(),
                description=row.get("description", "").strip() or None,
            )
            db.session.add(skill)
            created += 1
        except Exception as exc:
            errors.append({"row": i, "message": str(exc)})

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({"created": created, "skipped": skipped, "errors": errors}), 200
