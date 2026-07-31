from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.db import pool
from app.validation import FollowRequest

follow_bp = Blueprint("follow", __name__)


@follow_bp.post("/follow")
def follow():
    try:
        data = FollowRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    with pool.connection() as conn:
        conn.execute(
            "INSERT INTO follows (follower_id, following_id) VALUES (%s, %s) "
            "ON CONFLICT DO NOTHING",
            (str(data.follower_id), str(data.following_id)),
        )

    return jsonify({"success": True})