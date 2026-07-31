from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.db import pool
from app.feed import build_feed_query
from app.validation import FeedQuery

feed_bp = Blueprint("feed", __name__)


@feed_bp.get("/feed")
def feed():
    try:
        query = FeedQuery(
            user_id=request.args.get("userId"),
            cursor=request.args.get("cursor"),
        )
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    text, params = build_feed_query(str(query.user_id), query.cursor)

    with pool.connection() as conn:
        rows = conn.execute(text, params).fetchall()

    return jsonify({"items": rows})