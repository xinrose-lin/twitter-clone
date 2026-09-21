from flask import Blueprint, jsonify, request
from pydantic import ValidationError
import json

from app.db import pool
from app.feed import FANOUT_ENABLED, build_feed_query
from app.cache import FEED_TTL_SECONDS, CACHE_ENABLED, feed_cache_key, redis_client
from app.validation import FeedQuery

feed_bp = Blueprint("feed", __name__)


def _query_postgres_feed(query): 
    text, params = build_feed_query(str(query.user_id), query.cursor)
    with pool.connection() as conn:
        rows = conn.execute(text, params).fetchall()
    return rows

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

    strategy = request.args.get("strategy", "nocache")
    # print(f"strategy requested: {strategy}")
    if strategy == "fanout": 
       ##get lrange timeline from redis 
        timeline_key = f"timeline:{query.user_id}"
        cached_feed = redis_client.lrange(timeline_key, 0, 19)
        ## i want to see the data strcuture of this output
        print(f"cached_feed: {cached_feed}")

        return jsonify({"items": [json.loads(post) for post in cached_feed]})

    elif strategy == "cacheaside":
        cache_key = feed_cache_key(query.user_id, query.cursor)
        cached_feed = redis_client.get(cache_key)
        if cached_feed: 
            return jsonify({"items": json.loads(cached_feed)}) 

        rows = _query_postgres_feed(query)
        redis_client.set(cache_key, json.dumps(rows, default=str), ex=FEED_TTL_SECONDS)
        return jsonify({"items": rows})

    elif strategy == "nocache": 
        ##code repeated here tho
        rows = _query_postgres_feed(query)
    else: 
        return "Invalid strategy. Must be one of 'fanout', 'cacheaside', or 'nocache'." , 400
    
    return jsonify({"items": rows})

