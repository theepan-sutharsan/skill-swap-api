from flask import Blueprint, request

from app.controllers import feedback_controller, session_controller as ctrl
from app.middleware import roles_required

sessions_bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")


@sessions_bp.post("")
@roles_required("member", "admin")
def create_session():
    return ctrl.create_session(request.get_json(silent=True) or {})


@sessions_bp.get("/my")
@roles_required("member", "admin")
def list_my_sessions():
    return ctrl.get_my_sessions()


@sessions_bp.get("/export")
@roles_required("member", "admin")
def export_sessions():
    format_type = request.args.get("format", "csv")
    return ctrl.export_sessions(format_type)


@sessions_bp.get("")
@roles_required("admin")
def list_all_sessions():
    return ctrl.get_all_sessions()


@sessions_bp.get("/<int:session_id>")
@roles_required("member", "admin")
def get_session(session_id):
    return ctrl.get_session(session_id)


@sessions_bp.put("/<int:session_id>")
@roles_required("member", "admin")
def update_session(session_id):
    return ctrl.update_session(session_id, request.get_json(silent=True) or {})


@sessions_bp.patch("/<int:session_id>/complete")
@roles_required("member", "admin")
def complete_session(session_id):
    return ctrl.complete_session(session_id)


@sessions_bp.patch("/<int:session_id>/cancel")
@roles_required("member", "admin")
def cancel_session(session_id):
    return ctrl.cancel_session(session_id)


@sessions_bp.delete("/<int:session_id>")
@roles_required("admin")
def delete_session(session_id):
    return ctrl.delete_session(session_id)


@sessions_bp.get("/<int:session_id>/pdf")
@roles_required("member", "admin")
def export_session_pdf(session_id):
    return ctrl.export_session_pdf(session_id)


@sessions_bp.post("/<int:session_id>/feedback")
@roles_required("member")
def create_feedback(session_id):
    return feedback_controller.create_feedback(
        session_id, request.get_json(silent=True) or {}
    )


@sessions_bp.get("/<int:session_id>/feedback")
@roles_required("member", "admin")
def get_session_feedback(session_id):
    return feedback_controller.get_session_feedback(session_id)
