from flask import Blueprint

from app.controllers import dashboard_controller as ctrl
from app.middleware import roles_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/me")


@dashboard_bp.get("/dashboard")
@roles_required("member", "admin")
def get_dashboard():
    return ctrl.get_dashboard()


@dashboard_bp.get("/dashboard/pdf")
@roles_required("member", "admin")
def export_dashboard_pdf():
    return ctrl.export_dashboard_pdf()
