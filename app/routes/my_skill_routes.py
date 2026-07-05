from flask import Blueprint, request

from app.controllers import user_skill_controller as ctrl
from app.middleware import roles_required

my_skills_bp = Blueprint("my_skills", __name__, url_prefix="/api/my/skills")


@my_skills_bp.get("")
@roles_required("member", "admin")
def list_my_skills():
    return ctrl.get_my_skills(skill_type=request.args.get("type"))


@my_skills_bp.get("/export")
@roles_required("member", "admin")
def export_my_skills():
    return ctrl.export_my_skills_csv()


@my_skills_bp.post("/import")
@roles_required("member", "admin")
def import_my_skills():
    file = request.files.get("file")
    return ctrl.import_my_skills_csv(file)


@my_skills_bp.post("")
@roles_required("member", "admin")
def create_my_skill():
    return ctrl.create_user_skill(request.get_json(silent=True) or {})


@my_skills_bp.get("/<int:user_skill_id>")
@roles_required("member", "admin")
def get_my_skill(user_skill_id):
    return ctrl.get_user_skill(user_skill_id)


@my_skills_bp.put("/<int:user_skill_id>")
@roles_required("member", "admin")
def update_my_skill(user_skill_id):
    return ctrl.update_user_skill(user_skill_id, request.get_json(silent=True) or {})


@my_skills_bp.delete("/<int:user_skill_id>")
@roles_required("member", "admin")
def delete_my_skill(user_skill_id):
    return ctrl.delete_user_skill(user_skill_id)
