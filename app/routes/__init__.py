from app.routes.auth_routes import auth_bp
from app.routes.dashboard_routes import dashboard_bp
from app.routes.member_routes import members_bp
from app.routes.my_skill_routes import my_skills_bp
from app.routes.session_routes import sessions_bp
from app.routes.skill_routes import skills_bp
from app.routes.swap_request_routes import swap_requests_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(skills_bp)
    app.register_blueprint(my_skills_bp)
    app.register_blueprint(swap_requests_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(dashboard_bp)
