from flask import Blueprint, request

from app.controllers import skill_controller as ctrl
from app.middleware import roles_required

skills_bp = Blueprint("skills", __name__, url_prefix="/api/skills")


@skills_bp.get("")
def list_skills():
    return ctrl.get_skills(
        q=request.args.get("q"),
        category=request.args.get("category"),
    )


@skills_bp.get("/export")
def export_skills():
    format_type = request.args.get("format", "csv")
    return ctrl.export_skills(format_type)


@skills_bp.post("/import")
@roles_required("admin")
def import_skills():
    file = request.files.get("file")
    return ctrl.import_skills_csv(file)


@skills_bp.post("")
@roles_required("admin")
def create_skill():
    return ctrl.create_skill(request.get_json(silent=True) or {})


@skills_bp.get("/<int:skill_id>")
def get_skill(skill_id):
    return ctrl.get_skill(skill_id)


@skills_bp.put("/<int:skill_id>")
@roles_required("admin")
def update_skill(skill_id):
    return ctrl.update_skill(skill_id, request.get_json(silent=True) or {})


@skills_bp.delete("/<int:skill_id>")
@roles_required("admin")
def delete_skill(skill_id):
    return ctrl.delete_skill(skill_id)
