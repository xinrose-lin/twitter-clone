import argparse
import random
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

from app.db import pool

NUM_USERS = 2000
ALICE_FOLLOWS = 120
FOLLOWS_PER_USER = (50, 100)
POSTS_PER_USER = (10, 50)
POST_DAYS_SPREAD = 60

FIRST_NAMES = [
    "james", "mary", "john", "patricia", "robert", "jennifer", "michael", "linda",
    "william", "elizabeth", "david", "barbara", "richard", "susan", "joseph", "jessica",
    "thomas", "sarah", "charles", "karen", "daniel", "nancy", "matthew", "lisa",
    "anthony", "betty", "mark", "margaret", "donald", "sandra", "steven", "ashley",
    "andrew", "kimberly", "paul", "emily", "joshua", "donna", "kenneth", "michelle",
    "kevin", "carol", "brian", "amanda", "george", "melissa", "edward", "deborah",
    "ronald", "stephanie",
]
LAST_NAMES = [
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis",
    "rodriguez", "martinez", "hernandez", "lopez", "gonzalez", "wilson", "anderson",
    "thomas", "taylor", "moore", "jackson", "martin", "lee", "perez", "thompson",
    "white", "harris", "sanchez", "clark", "ramirez", "lewis", "robinson", "walker",
    "young", "allen", "king", "wright", "scott", "torres", "nguyen", "hill", "flores",
]

TOPICS = [
    "coffee", "the new office chair", "my sourdough starter", "the weekend hike",
    "this bug in production", "the client call", "my running shoes", "the farmers market",
    "that new coffee shop", "my backlog", "the standup meeting", "this podcast episode",
    "the weather", "my houseplants", "the gym", "this recipe", "the traffic",
    "my inbox", "the new album", "this book", "my sleep schedule", "the game last night",
    "my bike", "the conference talk", "this rabbit hole", "the group chat",
    "my desk setup", "the deploy", "this playlist", "the road trip",
]
OPINIONS = [
    "is somehow still going strong",
    "finally clicked for me",
    "is not worth the hype",
    "made my whole week",
    "is a bigger problem than I thought",
    "turned out better than expected",
    "is still unresolved, send help",
    "was exactly what I needed",
    "is starting to grow on me",
    "needs a complete rethink",
    "surprised me in a good way",
    "is officially a lost cause",
    "paid off after all",
    "is on the list for tomorrow",
    "went sideways fast",
]

USERNAMES = ["alice", "bob", "carol"]


def make_usernames(n):
    seen = set(USERNAMES)
    out = []
    while len(out) < n:
        candidate = f"{random.choice(FIRST_NAMES)}_{random.choice(LAST_NAMES)}{random.randint(1, 999)}"
        if candidate not in seen:
            seen.add(candidate)
            out.append(candidate)
    return out


def make_post_content():
    return f"{random.choice(TOPICS)} {random.choice(OPINIONS)}".capitalize()


def random_timestamp():
    delta = timedelta(
        days=random.uniform(0, POST_DAYS_SPREAD),
        seconds=random.uniform(0, 86400),
    )
    return datetime.now(timezone.utc) - delta


def seed(num_users, reset):
    pool.open()

    with pool.connection() as conn:
        if reset:
            conn.execute("TRUNCATE posts, follows, users CASCADE")

        existing_count = conn.execute("SELECT count(*) AS c FROM users").fetchone()["c"]
        if existing_count >= num_users and not reset:
            print(
                f"Already have {existing_count} users (>= requested {num_users}). "
                "Pass --reset to wipe and reseed at the new size."
            )
            pool.close()
            return

        conn.execute(
            "INSERT INTO users (username) VALUES ('alice'), ('bob'), ('carol') "
            "ON CONFLICT (username) DO NOTHING"
        )
        core = {
            u["username"]: u["id"]
            for u in conn.execute(
                "SELECT id, username FROM users WHERE username IN ('alice', 'bob', 'carol')"
            ).fetchall()
        }
        alice_id, bob_id, carol_id = core["alice"], core["bob"], core["carol"]

        extra_usernames = make_usernames(num_users - 3)
        with conn.cursor().copy("COPY users (username) FROM STDIN") as copy:
            for username in extra_usernames:
                copy.write_row((username,))

        all_users = conn.execute("SELECT id FROM users").fetchall()
        all_ids = [u["id"] for u in all_users]

        follow_pairs = set()

        alice_targets = random.sample(
            [uid for uid in all_ids if uid != alice_id],
            min(ALICE_FOLLOWS, len(all_ids) - 1),
        )
        for uid in alice_targets:
            follow_pairs.add((alice_id, uid))

        for uid in all_ids:
            if uid == alice_id:
                continue
            k = random.randint(*FOLLOWS_PER_USER)
            candidates = [other for other in all_ids if other != uid]
            targets = random.sample(candidates, min(k, len(candidates)))
            for target in targets:
                follow_pairs.add((uid, target))

        with conn.cursor().copy(
            "COPY follows (follower_id, following_id) FROM STDIN"
        ) as copy:
            for follower_id, following_id in follow_pairs:
                copy.write_row((follower_id, following_id))

        post_count = 0
        with conn.cursor().copy(
            "COPY posts (author_id, content, created_at) FROM STDIN"
        ) as copy:
            for uid in all_ids:
                n_posts = random.randint(*POSTS_PER_USER)
                for _ in range(n_posts):
                    copy.write_row((uid, make_post_content(), random_timestamp()))
                    post_count += 1

    pool.close()
    print(
        f"Seeded {len(all_ids)} users, {len(follow_pairs)} follows, {post_count} posts. "
        f"Alice ID: {alice_id} | Bob ID: {bob_id} | Carol ID: {carol_id}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=NUM_USERS, help="total users to seed")
    parser.add_argument(
        "--reset", action="store_true", help="TRUNCATE posts/follows/users before reseeding"
    )
    args = parser.parse_args()
    seed(args.users, args.reset)
