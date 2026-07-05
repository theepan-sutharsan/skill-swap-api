from datetime import datetime

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.extensions import db
from app.models.session_model import Session
from app.models.swap_request_model import SwapRequest
from app.models.user_model import User
from app.models.user_skill_model import UserSkill
from app.utils.csv_utils import rows_to_csv_response


def _validate_swap_request_payload(data):
    errors = []
    for field in ("recipient_id", "offered_skill_id", "requested_skill_id"):
        if not data.get(field):
            errors.append(f"{field} is required.")
    return errors


def _can_access_swap_request(swap_request, user_id, role):
    if role == "admin":
        return True
    return user_id in (swap_request.requester_id, swap_request.recipient_id)


def create_swap_request(data):
    requester_id = int(get_jwt_identity())
    errors = _validate_swap_request_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    recipient_id = int(data["recipient_id"])
    if recipient_id == requester_id:
        return jsonify({"error": "Cannot send a swap request to yourself."}), 400

    recipient = User.query.get(recipient_id)
    if not recipient or not recipient.is_active:
        return jsonify({"error": "Recipient not found."}), 404

    offered_skill_id = int(data["offered_skill_id"])
    requested_skill_id = int(data["requested_skill_id"])

    offered = UserSkill.query.filter_by(
        user_id=requester_id, skill_id=offered_skill_id, type="offered"
    ).first()
    if not offered:
        return jsonify({"error": "You must offer the selected skill."}), 400

    wanted = UserSkill.query.filter_by(
        user_id=recipient_id, skill_id=requested_skill_id, type="offered"
    ).first()
    if not wanted:
        return jsonify({"error": "Recipient does not offer the requested skill."}), 400

    try:
        swap_request = SwapRequest(
            requester_id=requester_id,
            recipient_id=recipient_id,
            offered_skill_id=offered_skill_id,
            requested_skill_id=requested_skill_id,
            message=data.get("message", "").strip() or None,
        )
        db.session.add(swap_request)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Swap request sent.",
                    "swap_request": swap_request.to_dict(),
                }
            ),
            201,
        )
    except Exception:
        db.session.rollback()
        raise


def get_swap_requests_sent():
    user_id = int(get_jwt_identity())
    requests = (
        SwapRequest.query.filter_by(requester_id=user_id)
        .order_by(SwapRequest.created_at.desc())
        .all()
    )
    return jsonify({"swap_requests": [r.to_dict() for r in requests]}), 200


def get_swap_requests_received():
    user_id = int(get_jwt_identity())
    requests = (
        SwapRequest.query.filter_by(recipient_id=user_id)
        .order_by(SwapRequest.created_at.desc())
        .all()
    )
    return jsonify({"swap_requests": [r.to_dict() for r in requests]}), 200


def get_all_swap_requests():
    requests = SwapRequest.query.order_by(SwapRequest.created_at.desc()).all()
    return jsonify({"swap_requests": [r.to_dict() for r in requests]}), 200


def get_swap_request(swap_request_id):
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")
    swap_request = SwapRequest.query.get(swap_request_id)
    if not swap_request:
        return jsonify({"error": "Swap request not found."}), 404
    if not _can_access_swap_request(swap_request, user_id, role):
        return jsonify({"error": "Insufficient permissions."}), 403
    return jsonify({"swap_request": swap_request.to_dict()}), 200


def accept_swap_request(swap_request_id):
    user_id = int(get_jwt_identity())
    swap_request = SwapRequest.query.get(swap_request_id)
    if not swap_request:
        return jsonify({"error": "Swap request not found."}), 404
    if swap_request.recipient_id != user_id:
        return jsonify({"error": "Only the recipient can accept."}), 403
    if swap_request.status != "pending":
        return jsonify({"error": "Request is not pending."}), 400

    swap_request.status = "accepted"
    try:
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Swap request accepted.",
                    "swap_request": swap_request.to_dict(),
                }
            ),
            200,
        )
    except Exception:
        db.session.rollback()
        raise


def decline_swap_request(swap_request_id):
    user_id = int(get_jwt_identity())
    swap_request = SwapRequest.query.get(swap_request_id)
    if not swap_request:
        return jsonify({"error": "Swap request not found."}), 404
    if swap_request.recipient_id != user_id:
        return jsonify({"error": "Only the recipient can decline."}), 403
    if swap_request.status != "pending":
        return jsonify({"error": "Request is not pending."}), 400

    swap_request.status = "declined"
    try:
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Swap request declined.",
                    "swap_request": swap_request.to_dict(),
                }
            ),
            200,
        )
    except Exception:
        db.session.rollback()
        raise


def cancel_swap_request(swap_request_id):
    user_id = int(get_jwt_identity())
    swap_request = SwapRequest.query.get(swap_request_id)
    if not swap_request:
        return jsonify({"error": "Swap request not found."}), 404
    if swap_request.requester_id != user_id:
        return jsonify({"error": "Only the requester can cancel."}), 403
    if swap_request.status not in ("pending", "accepted"):
        return jsonify({"error": "Request cannot be cancelled."}), 400

    swap_request.status = "cancelled"
    try:
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Swap request cancelled.",
                    "swap_request": swap_request.to_dict(),
                }
            ),
            200,
        )
    except Exception:
        db.session.rollback()
        raise


def delete_swap_request(swap_request_id):
    swap_request = SwapRequest.query.get(swap_request_id)
    if not swap_request:
        return jsonify({"error": "Swap request not found."}), 404
    try:
        db.session.delete(swap_request)
        db.session.commit()
        return jsonify({"message": "Swap request deleted."}), 200
    except Exception:
        db.session.rollback()
        raise


def export_swap_requests():
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")
    if role == "admin":
        requests = SwapRequest.query.order_by(SwapRequest.created_at.desc()).all()
    else:
        requests = (
            SwapRequest.query.filter(
                (SwapRequest.requester_id == user_id)
                | (SwapRequest.recipient_id == user_id)
            )
            .order_by(SwapRequest.created_at.desc())
            .all()
        )

    headers = [
        "id",
        "requester",
        "recipient",
        "offered_skill",
        "requested_skill",
        "status",
        "created_at",
    ]
    rows = []
    for r in requests:
        rows.append(
            [
                r.id,
                r.requester.full_name if r.requester else "",
                r.recipient.full_name if r.recipient else "",
                r.offered_skill.name if r.offered_skill else "",
                r.requested_skill.name if r.requested_skill else "",
                r.status,
                r.created_at.isoformat() if r.created_at else "",
            ]
        )
    filename = f"swap-requests-{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
    return rows_to_csv_response(filename, headers, rows)
