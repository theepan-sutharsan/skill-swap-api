from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from app.extensions import db
from app.models.message_model import Message
from app.models.swap_request_model import SwapRequest


def _is_participant(swap_request, user_id):
    return user_id in (swap_request.requester_id, swap_request.recipient_id)


def get_messages(swap_request_id):
    user_id = int(get_jwt_identity())
    swap_request = SwapRequest.query.get(swap_request_id)
    if not swap_request:
        return jsonify({"error": "Swap request not found."}), 404
    if not _is_participant(swap_request, user_id):
        return jsonify({"error": "Insufficient permissions."}), 403

    messages = (
        Message.query.filter_by(swap_request_id=swap_request_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return jsonify({"messages": [m.to_dict() for m in messages]}), 200


def create_message(swap_request_id, data):
    user_id = int(get_jwt_identity())
    swap_request = SwapRequest.query.get(swap_request_id)
    if not swap_request:
        return jsonify({"error": "Swap request not found."}), 404
    if not _is_participant(swap_request, user_id):
        return jsonify({"error": "Insufficient permissions."}), 403

    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"errors": ["body is required."]}), 400

    try:
        message = Message(
            swap_request_id=swap_request_id,
            sender_id=user_id,
            body=body,
        )
        db.session.add(message)
        db.session.commit()
        return jsonify({"message": "Message sent.", "chat_message": message.to_dict()}), 201
    except Exception:
        db.session.rollback()
        raise
