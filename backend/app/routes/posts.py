from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from app.db import pool 
from app.validation import CreatePostRequest

posts_bp = Blueprint("posts", __name__)

@posts_bp.post("/posts")
def create_post():
    try:
        data = CreatePostRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    with pool.connection() as conn:
        row = conn.execute(
            "INSERT INTO posts (author_id, content) VALUES (%s, %s) RETURNING *",
            (str(data.author_id), data.content),
        ).fetchone()

    return jsonify(row)