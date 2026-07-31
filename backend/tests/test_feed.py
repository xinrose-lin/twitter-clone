from app.feed import build_feed_query


def test_build_feed_query_no_cursor():
    text, params = build_feed_query("user-1")
    assert params == ["user-1"]
    assert "created_at < %s" not in text

def test_build_feed_query_with_cursor():
    text, params = build_feed_query("user-1", "2026-01-01T00:00:00Z")
    assert params == ["user-1", "2026-01-01T00:00:00Z"]
    assert "created_at < %s" in text