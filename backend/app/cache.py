import os

import redis

CACHE_ENABLED = os.environ.get("CACHE_ENABLED", "false").lower() == "true"

# Seconds-to-a-minute staleness is explicitly acceptable per architecture.md's
# NFRs, so this TTL is picked to sit inside that window rather than at random.
# Time to Live. this is the max time a cached feed is in cache 
FEED_TTL_SECONDS = 15

redis_client = redis.Redis.from_url(
    os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
)

def feed_cache_key(user_id, cursor):
    return f"feed:{user_id}:{cursor or 'first'}"
