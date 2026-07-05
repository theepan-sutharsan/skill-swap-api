from datetime import datetime

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.extensions import db
from app.models.session_model import Session
from app.models.swap_request_model import SwapRequest
from app.utils.csv_utils import rows_to_csv_response
from app.utils.pdf_utils import document_pdf_response, table_pdf_response


def _parse_datetime(value):
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _validate_session_payload(data, session_id=None):
    errors = []
    if not session_id and not data.get("swap_request_id"):
        errors.append("swap_request_id is required.")
    if "scheduled_at" in data or not session_id:
        if not data.get("scheduled_at"):
            errors.append("scheduled_at is required.")
    if "mode" in data or not session_id:
        if data.get("mode") not in ("online", "in_person"):
            errors.append("mode must be online or in_person.")
    return errors


def _is_participant(session, user_id):
    return user_id in session.participant_ids()


def create_session(data):
    user_id = int(get_jwt_identity())
    errors = _validate_session_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    swap_request = SwapRequest.query.get(int(data["swap_request_id"]))
    if not swap_request:
        return jsonify({"error": "Swap request not found."}), 404
    if swap_request.status != "accepted":
        return jsonify({"error": "Swap request must be accepted first."}), 400
    if user_id not in (swap_request.requester_id, swap_request.recipient_id):
        return jsonify({"error": "Insufficient permissions."}), 403
    if Session.query.filter_by(swap_request_id=swap_request.id).first():
        return jsonify({"error": "Session already exists for this request."}), 400

    scheduled_at = _parse_datetime(data["scheduled_at"])
    if not scheduled_at:
        return jsonify({"errors": ["Invalid scheduled_at format."]}), 400

    try:
        session = Session(
            swap_request_id=swap_request.id,
            scheduled_at=scheduled_at,
            duration_minutes=int(data.get("duration_minutes", 60)),
            mode=data["mode"],
            location=data.get("location", "").strip() or None,
            notes=data.get("notes", "").strip() or None,
        )
        db.session.add(session)
        db.session.commit()
        return jsonify({"message": "Session scheduled.", "session": session.to_dict()}), 201
    except Exception:
        db.session.rollback()
        raise


def get_my_sessions():
    user_id = int(get_jwt_identity())
    sessions = (
        Session.query.join(SwapRequest)
        .filter(
            (SwapRequest.requester_id == user_id) | (SwapRequest.recipient_id == user_id)
        )
        .order_by(Session.scheduled_at.desc())
        .all()
    )
    return jsonify({"sessions": [s.to_dict() for s in sessions]}), 200


def get_all_sessions():
    sessions = Session.query.order_by(Session.scheduled_at.desc()).all()
    return jsonify({"sessions": [s.to_dict() for s in sessions]}), 200


def get_session(session_id):
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    if role != "admin" and not _is_participant(session, user_id):
        return jsonify({"error": "Insufficient permissions."}), 403
    return jsonify({"session": session.to_dict()}), 200


def update_session(session_id, data):
    user_id = int(get_jwt_identity())
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    if not _is_participant(session, user_id):
        return jsonify({"error": "Insufficient permissions."}), 403

    errors = _validate_session_payload(data, session_id=session_id)
    if errors:
        return jsonify({"errors": errors}), 400

    if "scheduled_at" in data:
        scheduled_at = _parse_datetime(data["scheduled_at"])
        if not scheduled_at:
            return jsonify({"errors": ["Invalid scheduled_at format."]}), 400
        session.scheduled_at = scheduled_at
    if "duration_minutes" in data:
        session.duration_minutes = int(data["duration_minutes"])
    if "mode" in data:
        session.mode = data["mode"]
    if "location" in data:
        session.location = data["location"].strip() if data["location"] else None
    if "notes" in data:
        session.notes = data["notes"].strip() if data["notes"] else None

    try:
        db.session.commit()
        return jsonify({"message": "Session updated.", "session": session.to_dict()}), 200
    except Exception:
        db.session.rollback()
        raise


def complete_session(session_id):
    user_id = int(get_jwt_identity())
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    if not _is_participant(session, user_id):
        return jsonify({"error": "Insufficient permissions."}), 403
    if session.status != "scheduled":
        return jsonify({"error": "Session is not scheduled."}), 400

    session.status = "completed"
    try:
        db.session.commit()
        return jsonify({"message": "Session completed.", "session": session.to_dict()}), 200
    except Exception:
        db.session.rollback()
        raise


def cancel_session(session_id):
    user_id = int(get_jwt_identity())
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    if not _is_participant(session, user_id):
        return jsonify({"error": "Insufficient permissions."}), 403
    if session.status != "scheduled":
        return jsonify({"error": "Session is not scheduled."}), 400

    session.status = "cancelled"
    try:
        db.session.commit()
        return jsonify({"message": "Session cancelled.", "session": session.to_dict()}), 200
    except Exception:
        db.session.rollback()
        raise


def delete_session(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    try:
        db.session.delete(session)
        db.session.commit()
        return jsonify({"message": "Session deleted."}), 200
    except Exception:
        db.session.rollback()
        raise


def export_session_pdf(session_id):
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    if role != "admin" and not _is_participant(session, user_id):
        return jsonify({"error": "Insufficient permissions."}), 403

    sr = session.swap_request
    sections = [
        (
            "Session Confirmation",
            [
                ("Session ID", session.id),
                ("Status", session.status),
                ("Scheduled", session.scheduled_at.isoformat() if session.scheduled_at else ""),
                ("Duration (min)", session.duration_minutes),
                ("Mode", session.mode),
                ("Location", session.location or "—"),
            ],
        ),
        (
            "Participants",
            [
                ("Requester", sr.requester.full_name if sr and sr.requester else "—"),
                ("Recipient", sr.recipient.full_name if sr and sr.recipient else "—"),
            ],
        ),
        (
            "Skills",
            [
                ("Offered", sr.offered_skill.name if sr and sr.offered_skill else "—"),
                ("Requested", sr.requested_skill.name if sr and sr.requested_skill else "—"),
            ],
        ),
    ]
    filename = f"session-{session.id}-confirmation.pdf"
    return document_pdf_response(filename, "Session Confirmation", sections)


def export_sessions(format_type="csv"):
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")

    if role == "admin":
        sessions = Session.query.order_by(Session.scheduled_at.desc()).all()
    else:
        sessions = (
            Session.query.join(SwapRequest)
            .filter(
                (SwapRequest.requester_id == user_id)
                | (SwapRequest.recipient_id == user_id)
            )
            .order_by(Session.scheduled_at.desc())
            .all()
        )

    headers = ["id", "scheduled_at", "mode", "location", "status", "duration_minutes"]
    rows = [
        [
            s.id,
            s.scheduled_at.isoformat() if s.scheduled_at else "",
            s.mode,
            s.location or "",
            s.status,
            s.duration_minutes,
        ]
        for s in sessions
    ]

    if format_type == "pdf":
        filename = f"sessions-{datetime.utcnow().strftime('%Y-%m-%d')}.pdf"
        return table_pdf_response(filename, "Sessions Schedule", headers, rows)

    filename = f"sessions-{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
    return rows_to_csv_response(filename, headers, rows)
