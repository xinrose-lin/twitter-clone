from dotenv import load_dotenv

load_dotenv()

from app.db import pool

EXTRA_USER_COUNT = 10
POSTS_PER_EXTRA_USER = 5


def seed():
    pool.open()

    with pool.connection() as conn:
        users = conn.execute(
            "INSERT INTO users (username) VALUES ('alice'), ('bob'), ('carol') "
            "RETURNING id, username"
        ).fetchall()
        alice, bob, carol = users

        extra_usernames = [f"filler_user_{i}" for i in range(EXTRA_USER_COUNT)]
        placeholders = ", ".join(["(%s)"] * len(extra_usernames))
        extra_users = conn.execute(
            f"INSERT INTO users (username) VALUES {placeholders} RETURNING id, username",
            extra_usernames,
        ).fetchall()
        extra_ids = [u["id"] for u in extra_users]

        conn.execute(
            "INSERT INTO follows (follower_id, following_id) VALUES (%s, %s), (%s, %s)",
            (alice["id"], bob["id"], alice["id"], carol["id"]),
        )
        conn.executemany(
            "INSERT INTO follows (follower_id, following_id) VALUES (%s, %s)",
            [(alice["id"], uid) for uid in extra_ids],
        )

        conn.execute(
            "INSERT INTO posts (author_id, content) VALUES "
            "(%s, 'hello from bob'), (%s, 'hello from carol')",
            (bob["id"], carol["id"]),
        )
        conn.executemany(
            "INSERT INTO posts (author_id, content) VALUES (%s, %s)",
            [
                (uid, f"filler post {j} from user {uid}")
                for uid in extra_ids
                for j in range(POSTS_PER_EXTRA_USER)
            ],
        )

    pool.close()
    print(
        f"Seeded. Alice ID: {alice['id']} | "
        f"{EXTRA_USER_COUNT} extra users, "
        f"{EXTRA_USER_COUNT * POSTS_PER_EXTRA_USER} extra posts, "
        f"alice now follows {2 + EXTRA_USER_COUNT} accounts"
    )


if __name__ == "__main__":
    seed()
