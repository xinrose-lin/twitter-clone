from dotenv import load_dotenv

load_dotenv()

from app.db import pool


def seed():
    pool.open()

    with pool.connection() as conn:
        users = conn.execute(
            "INSERT INTO users (username) VALUES ('alice'), ('bob'), ('carol') "
            "RETURNING id, username"
        ).fetchall()
        alice, bob, carol = users

        conn.execute(
            "INSERT INTO follows (follower_id, following_id) VALUES (%s, %s), (%s, %s)",
            (alice["id"], bob["id"], alice["id"], carol["id"]),
        )

        conn.execute(
            "INSERT INTO posts (author_id, content) VALUES "
            "(%s, 'hello from bob'), (%s, 'hello from carol')",
            (bob["id"], carol["id"]),
        )

    pool.close()
    print("Seeded. Alice ID:", alice["id"])


if __name__ == "__main__":
    seed()
