from flask import Blueprint, jsonify, request
from pydantic import ValidationError
import json

from app.db import pool
from app.feed import FANOUT_ENABLED, build_feed_query
from app.cache import FEED_TTL_SECONDS, CACHE_ENABLED, feed_cache_key, redis_client
from app.validation import FeedQuery

feed_bp = Blueprint("feed", __name__)


@feed_bp.get("/feed")
def feed():

    # parse and validate query parameters
    try:
        query = FeedQuery(
            user_id=request.args.get("userId"),
            cursor=request.args.get("cursor"),
        )
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    ## build cache key 
    cache_key = feed_cache_key(query.user_id, query.cursor)
    ## get from cache
    if CACHE_ENABLED and not FANOUT_ENABLED: 
        cached_feed = redis_client.get(cache_key)
        if cached_feed: 
            return jsonify({"items": json.loads(cached_feed)})

    elif FANOUT_ENABLED:
        ##get lrange timeline from redis 
        timeline_key = f"timeline:{query.user_id}"
        cached_feed = redis_client.lrange(timeline_key, 0, 19)
        ## i want to see the data strcuture of this output
        print(f"cached_feed: {cached_feed}")

        return jsonify({"items": [json.loads(post) for post in cached_feed]})
    ## build SQL query and params
    text, params = build_feed_query(str(query.user_id), query.cursor)
    with pool.connection() as conn:
        rows = conn.execute(text, params).fetchall()

    ## if cache missed; store db text, params to cache
    if CACHE_ENABLED: 
        redis_client.set(cache_key, json.dumps(rows, default=str), ex=FEED_TTL_SECONDS)



    return jsonify({"items": rows})

