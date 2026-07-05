from app import create_app
from app.extensions import db

# Import all models before db.create_all()
from app.models.feedback_model import Feedback  # noqa: F401
from app.models.message_model import Message  # noqa: F401
from app.models.session_model import Session  # noqa: F401
from app.models.skill_model import Skill  # noqa: F401
from app.models.swap_request_model import SwapRequest  # noqa: F401
from app.models.user_model import User  # noqa: F401
from app.models.user_skill_model import UserSkill  # noqa: F401

app = create_app()

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=app.config.get("FLASK_DEBUG", False), host="0.0.0.0", port=5000)
