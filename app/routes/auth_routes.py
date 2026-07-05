from flask import Blueprint, request

from app.controllers import auth_controller as ctrl
from app.middleware import roles_required
from flask_jwt_extended import jwt_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    return ctrl.register(request.get_json(silent=True) or {})


@auth_bp.post("/login")
def login():
    return ctrl.login(request.get_json(silent=True) or {})


@auth_bp.post("/logout")
@jwt_required()
def logout():
    return ctrl.logout()


@auth_bp.get("/profile")
@jwt_required()
def get_profile():
    return ctrl.get_profile()


@auth_bp.put("/profile")
@jwt_required()
def update_profile():
    return ctrl.update_profile(request.get_json(silent=True) or {})
