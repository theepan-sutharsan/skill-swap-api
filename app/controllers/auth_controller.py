from flask import jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity

from app.extensions import db
from app.models.user_model import User


def _validate_register_payload(data):
    errors = []
    if not data.get("email"):
        errors.append("Email is required.")
    if not data.get("password"):
        errors.append("Password is required.")
    elif len(data["password"]) < 6:
        errors.append("Password must be at least 6 characters.")
    if not data.get("full_name"):
        errors.append("Full name is required.")
    return errors


def register(data):
    errors = _validate_register_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 400

    role = data.get("role", "member")
    if role not in ("admin", "member"):
        role = "member"

    try:
        user = User(
            email=email,
            full_name=data["full_name"].strip(),
            location=data.get("location", "").strip() or None,
            bio=data.get("bio", "").strip() or None,
            role=role,
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()
        token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role},
        )
        return (
            jsonify(
                {
                    "message": "Registration successful.",
                    "access_token": token,
                    "user": user.to_dict(),
                }
            ),
            201,
        )
    except Exception:
        db.session.rollback()
        raise


def login(data):
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"errors": ["Email and password are required."]}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password."}), 401
    if not user.is_active:
        return jsonify({"error": "Account is deactivated."}), 403

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )
    return jsonify({"access_token": token, "user": user.to_dict()}), 200


def logout():
    return jsonify({"message": "Logged out successfully."}), 200


def get_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"user": user.to_dict()}), 200


def update_profile(data):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    if "full_name" in data and data["full_name"]:
        user.full_name = data["full_name"].strip()
    if "bio" in data:
        user.bio = data["bio"].strip() if data["bio"] else None
    if "location" in data:
        user.location = data["location"].strip() if data["location"] else None
    if "avatar_url" in data:
        user.avatar_url = data["avatar_url"].strip() if data["avatar_url"] else None
    if "password" in data and data["password"]:
        if len(data["password"]) < 6:
            return jsonify({"errors": ["Password must be at least 6 characters."]}), 400
        user.set_password(data["password"])

    try:
        db.session.commit()
        return jsonify({"message": "Profile updated.", "user": user.to_dict()}), 200
    except Exception:
        db.session.rollback()
        raise
