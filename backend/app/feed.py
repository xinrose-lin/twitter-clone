
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