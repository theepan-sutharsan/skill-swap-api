from datetime import datetime

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from app.models.session_model import Session
from app.models.swap_request_model import SwapRequest
from app.models.user_model import User
from app.models.user_skill_model import UserSkill
from app.utils.pdf_utils import document_pdf_response


def get_dashboard():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    offered = UserSkill.query.filter_by(user_id=user_id, type="offered").all()
    wanted = UserSkill.query.filter_by(user_id=user_id, type="wanted").all()
    sent = SwapRequest.query.filter_by(requester_id=user_id).order_by(
        SwapRequest.created_at.desc()
    ).limit(5).all()
    received = SwapRequest.query.filter_by(recipient_id=user_id).order_by(
        SwapRequest.created_at.desc()
    ).limit(5).all()
    sessions = (
        Session.query.join(SwapRequest)
        .filter(
            (SwapRequest.requester_id == user_id)
            | (SwapRequest.recipient_id == user_id)
        )
        .order_by(Session.scheduled_at.desc())
        .limit(5)
        .all()
    )

    return jsonify(
        {
            "dashboard": {
                "counts": {
                    "offered_skills": len(offered),
                    "wanted_skills": len(wanted),
                    "requests_sent": SwapRequest.query.filter_by(
                        requester_id=user_id
                    ).count(),
                    "requests_received": SwapRequest.query.filter_by(
                        recipient_id=user_id
                    ).count(),
                    "sessions": Session.query.join(SwapRequest)
                    .filter(
                        (SwapRequest.requester_id == user_id)
                        | (SwapRequest.recipient_id == user_id)
                    )
                    .count(),
                },
                "offered_skills": [s.to_dict() for s in offered],
                "wanted_skills": [s.to_dict() for s in wanted],
                "requests_sent": [r.to_dict() for r in sent],
                "requests_received": [r.to_dict() for r in received],
                "sessions": [s.to_dict() for s in sessions],
            }
        }
    ), 200


def export_dashboard_pdf():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    offered = UserSkill.query.filter_by(user_id=user_id, type="offered").all()
    wanted = UserSkill.query.filter_by(user_id=user_id, type="wanted").all()
    sent_count = SwapRequest.query.filter_by(requester_id=user_id).count()
    received_count = SwapRequest.query.filter_by(recipient_id=user_id).count()
    session_count = (
        Session.query.join(SwapRequest)
        .filter(
            (SwapRequest.requester_id == user_id)
            | (SwapRequest.recipient_id == user_id)
        )
        .count()
    )

    offered_str = ", ".join(us.skill.name for us in offered if us.skill) or "None"
    wanted_str = ", ".join(us.skill.name for us in wanted if us.skill) or "None"

    sections = [
        (
            "Summary",
            [
                ("Member", user.full_name),
                ("Offered Skills", len(offered)),
                ("Wanted Skills", len(wanted)),
                ("Requests Sent", sent_count),
                ("Requests Received", received_count),
                ("Sessions", session_count),
            ],
        ),
        ("Skills Offered", [("List", offered_str)]),
        ("Skills Wanted", [("List", wanted_str)]),
    ]
    filename = f"dashboard-{datetime.utcnow().strftime('%Y-%m-%d')}.pdf"
    return document_pdf_response(filename, f"Dashboard: {user.full_name}", sections)
