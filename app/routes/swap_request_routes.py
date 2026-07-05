from flask import Blueprint, request

from app.controllers import message_controller, swap_request_controller as ctrl
from app.middleware import roles_required
from flask_jwt_extended import jwt_required

swap_requests_bp = Blueprint("swap_requests", __name__, url_prefix="/api/swap-requests")


@swap_requests_bp.post("")
@roles_required("member")
def create_swap_request():
    return ctrl.create_swap_request(request.get_json(silent=True) or {})


@swap_requests_bp.get("/sent")
@roles_required("member")
def list_sent():
    return ctrl.get_swap_requests_sent()


@swap_requests_bp.get("/received")
@roles_required("member")
def list_received():
    return ctrl.get_swap_requests_received()


@swap_requests_bp.get("/export")
@roles_required("member", "admin")
def export_swap_requests():
    return ctrl.export_swap_requests()


@swap_requests_bp.get("")
@roles_required("admin")
def list_all():
    return ctrl.get_all_swap_requests()


@swap_requests_bp.get("/<int:swap_request_id>")
@roles_required("member", "admin")
def get_swap_request(swap_request_id):
    return ctrl.get_swap_request(swap_request_id)


@swap_requests_bp.patch("/<int:swap_request_id>/accept")
@roles_required("member")
def accept_swap_request(swap_request_id):
    return ctrl.accept_swap_request(swap_request_id)


@swap_requests_bp.patch("/<int:swap_request_id>/decline")
@roles_required("member")
def decline_swap_request(swap_request_id):
    return ctrl.decline_swap_request(swap_request_id)


@swap_requests_bp.patch("/<int:swap_request_id>/cancel")
@roles_required("member")
def cancel_swap_request(swap_request_id):
    return ctrl.cancel_swap_request(swap_request_id)


@swap_requests_bp.delete("/<int:swap_request_id>")
@roles_required("admin")
def delete_swap_request(swap_request_id):
    return ctrl.delete_swap_request(swap_request_id)


@swap_requests_bp.get("/<int:swap_request_id>/messages")
@roles_required("member")
def get_messages(swap_request_id):
    return message_controller.get_messages(swap_request_id)


@swap_requests_bp.post("/<int:swap_request_id>/messages")
@roles_required("member")
def create_message(swap_request_id):
    return message_controller.create_message(
        swap_request_id, request.get_json(silent=True) or {}
    )
