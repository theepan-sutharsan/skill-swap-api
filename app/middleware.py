from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in roles:
                return jsonify({"error": "Insufficient permissions."}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def owner_or_admin(user_id_param="id"):
    """Allow admin or the user whose id matches the route param."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            current_user_id = int(claims.get("sub"))
            target_id = kwargs.get(user_id_param)
            if user_role == "admin":
                return fn(*args, **kwargs)
            if target_id is not None and int(target_id) == current_user_id:
                return fn(*args, **kwargs)
            return jsonify({"error": "Insufficient permissions."}), 403

        return wrapper

    return decorator
