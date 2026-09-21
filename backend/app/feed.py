from app.db import pool 
from app.cache import redis_client
import json
import os

FANOUT_ENABLED = os.environ.get("FANOUT_ENABLED", "false").lower() == "true"

def build_feed_query(user_id, cursor=None):
    params = [str(user_id)]
    cursor_clause = ""

    if cursor:
        params.append(cursor)
        cursor_clause = "AND p.created_at < %s"

    text = f"""
        SELECT p.id, p.content, p.author_id, p.created_at
        FROM posts p
        WHERE p.author_id = ANY(
            SELECT following_id FROM follows WHERE follower_id = %s
        )
        {cursor_clause}
        ORDER BY p.created_at DESC
        LIMIT 20
    """
    return text, params

def get_follower_ids(user_id):
    with pool.connection() as conn:
        rows = conn.execute(
            "SELECT follower_id FROM follows WHERE following_id = %s",
            [str(user_id)]
        ).fetchall()
        print(f"follower_ids: {rows}")
    return [row['follower_id'] for row in rows]

def fanout_post(post, follower_ids):
    ## fanout to redis cache for each follower, batched into one pipeline
    ## to avoid N sequential round-trips (was: lpush+ltrim per follower)
    pipe = redis_client.pipeline()
    for follower_id in follower_ids:
        # lpush serialised post onto timeline:<follower_id>
        pipe.lpush(f"timeline:{follower_id}",
                   json.dumps(post, default=str))
        # ltrim to cap timeline at 200
        pipe.ltrim(f"timeline:{follower_id}", 0, 199)
    pipe.execute()