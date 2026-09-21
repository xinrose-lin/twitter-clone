from flask import Blueprint, jsonify, request
from pydantic import ValidationError
 
from app.feed import FANOUT_ENABLED, get_follower_ids, fanout_post

from app.db import pool
from app.validation import CreatePostRequest

posts_bp = Blueprint("posts", __name__)

@posts_bp.post("/posts")
def create_post():
    try:
        data = CreatePostRequest(**request.get_json())
        print('data', data)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    with pool.connection() as conn:
        rows = conn.execute(
            "INSERT INTO posts (author_id, content) VALUES (%s, %s) RETURNING *",
            (str(data.author_id), data.content),
        ).fetchone()

    if FANOUT_ENABLED: 
        # get follower ids
        follower_ids = get_follower_ids(data.author_id)
        # fanout to redis cache for each follower
        fanout_post(rows, follower_ids)

    return jsonify(rows)