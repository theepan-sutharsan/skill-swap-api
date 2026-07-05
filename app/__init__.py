from datetime import timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.config import Config
from app.extensions import db, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
        minutes=Config.JWT_ACCESS_TOKEN_EXPIRES_MINUTES
    )

    CORS(app)
    db.init_app(app)
    jwt.init_app(app)

    from app.models.user_model import User

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.query.get(int(identity))

    @app.errorhandler(OperationalError)
    @app.errorhandler(ProgrammingError)
    def handle_db_error(error):
        db.session.rollback()
        return jsonify({"error": "Database connection error.", "details": str(error)}), 500

    from app.routes import register_blueprints

    register_blueprints(app)

    return app
