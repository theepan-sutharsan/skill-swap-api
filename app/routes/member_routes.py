from flask import Blueprint, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.controllers import member_controller as ctrl
from app.middleware import owner_or_admin, roles_required

members_bp = Blueprint("members", __name__, url_prefix="/api/members")


@members_bp.get("")
def list_members():
    return ctrl.get_members(
        q=request.args.get("q"),
        location=request.args.get("location"),
        skill=request.args.get("skill"),
        category=request.args.get("category"),
    )


@members_bp.get("/export")
@roles_required("admin")
def export_members():
    return ctrl.export_members_csv()


@members_bp.post("/import")
@roles_required("admin")
def import_members():
    file = request.files.get("file")
    return ctrl.import_members_csv(file)


@members_bp.get("/<int:member_id>")
def get_member(member_id):
    return ctrl.get_member(member_id)


@members_bp.get("/<int:member_id>/skills")
def get_member_skills(member_id):
    return ctrl.get_member_skills(member_id)


@members_bp.get("/<int:member_id>/pdf")
@jwt_required()
def export_member_pdf(member_id):
    return ctrl.export_member_pdf(member_id)


@members_bp.get("/<int:member_id>/feedback")
def get_member_feedback(member_id):
    from app.controllers import feedback_controller

    return feedback_controller.get_member_feedback(member_id)


@members_bp.put("/<int:member_id>")
@owner_or_admin("member_id")
def update_member(member_id):
    return ctrl.update_member(member_id, request.get_json(silent=True) or {})


@members_bp.patch("/<int:member_id>/status")
@roles_required("admin")
def patch_member_status(member_id):
    return ctrl.patch_member_status(member_id, request.get_json(silent=True) or {})


@members_bp.delete("/<int:member_id>")
@roles_required("admin")
def delete_member(member_id):
    return ctrl.delete_member(member_id)
