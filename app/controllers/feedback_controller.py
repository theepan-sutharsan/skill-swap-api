from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity
from sqlalchemy import func

from app.extensions import db
from app.models.feedback_model import Feedback
from app.models.session_model import Session


def create_feedback(session_id, data):
    user_id = int(get_jwt_identity())
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    if user_id not in session.participant_ids():
        return jsonify({"error": "Insufficient permissions."}), 403
    if session.status != "completed":
        return jsonify({"error": "Session must be completed before feedback."}), 400

    reviewee_id = data.get("reviewee_id")
    rating = data.get("rating")
    if not reviewee_id:
        return jsonify({"errors": ["reviewee_id is required."]}), 400
    if rating is None or not (1 <= int(rating) <= 5):
        return jsonify({"errors": ["rating must be between 1 and 5."]}), 400

    reviewee_id = int(reviewee_id)
    if reviewee_id not in session.participant_ids():
        return jsonify({"error": "Reviewee must be a session participant."}), 400
    if reviewee_id == user_id:
        return jsonify({"error": "Cannot review yourself."}), 400

    existing = Feedback.query.filter_by(
        session_id=session_id, reviewer_id=user_id, reviewee_id=reviewee_id
    ).first()
    if existing:
        return jsonify({"error": "Feedback already submitted."}), 400

    try:
        feedback = Feedback(
            session_id=session_id,
            reviewer_id=user_id,
            reviewee_id=reviewee_id,
            rating=int(rating),
            comment=data.get("comment", "").strip() or None,
        )
        db.session.add(feedback)
        db.session.commit()
        return jsonify({"message": "Feedback submitted.", "feedback": feedback.to_dict()}), 201
    except Exception:
        db.session.rollback()
        raise


def get_session_feedback(session_id):
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    if role != "admin" and user_id not in session.participant_ids():
        return jsonify({"error": "Insufficient permissions."}), 403

    feedback_list = Feedback.query.filter_by(session_id=session_id).all()
    return jsonify({"feedback": [f.to_dict() for f in feedback_list]}), 200


def get_member_feedback(member_id):
    feedback_list = Feedback.query.filter_by(reviewee_id=member_id).all()
    avg_rating = (
        db.session.query(func.avg(Feedback.rating))
        .filter(Feedback.reviewee_id == member_id)
        .scalar()
    )
    return jsonify(
        {
            "feedback": [f.to_dict() for f in feedback_list],
            "average_rating": round(float(avg_rating), 2) if avg_rating else None,
        }
    ), 200
