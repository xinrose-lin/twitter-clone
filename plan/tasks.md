# Twitter Baseline (v2) — Build Guide — Phase 0 (MVP v0)

Stack: **Python + Flask + `psycopg` (no ORM) + Postgres backend, React (Vite) frontend**
Same architecture as `architecture.md` — this is a language/framework swap, not a redesign. If you already ran the schema in the first (Next.js) spike, you can reuse that same Postgres database; the tables don't change.

Goal: same naive, working feed (create post → follow → view feed) as the first spike, but this time also used as a vehicle to practice a real branch → PR → CI workflow, and a test-driven-development loop for anything that's pure logic. This is **Phase 0** of `roadmap.md`'s phased plan — fan-out-on-read, no cache, no Docker, no auth hardening. Those are deliberately deferred to later phases; see "What NOT to do in Phase 0" below.

---

## Definition of done for Phase 0

- [ ] `GET /feed`, `POST /posts`, `PUT/DELETE /users/:id/follow` all work against a real Postgres, via fan-out-on-read
- [ ] `pytest` passes locally and in CI, with real coverage on the feed query and validation (not just happy-path)
- [ ] React frontend can create a post, follow a user, and render a feed against the real deployed API
- [ ] Every PR since `chore/repo-setup` went through CI, not a direct push to `main`
- [ ] Backend deployed (Fly.io or Render) and frontend deployed (Vercel), reachable over the public internet
- [ ] `README.md` states the Phase 0 scope and explicitly lists what's deferred (cache, fan-out-on-write, auth hardening, Docker) as forward-looking, not forgotten

If any of these is missing, Phase 1's load test won't be measuring the thing you actually intend to improve later — don't skip ahead.

## What NOT to do in Phase 0

Resist adding these even if they'd be easy right now — each has a later phase where it's the actual point, and building it early means that phase's load test has nothing naive left to measure:

- Redis / caching of any kind
- Fan-out-on-write / precomputed feeds
- Docker or Docker Compose
- JWT auth, rate limiting, password hashing (Phase 3 buffer work)
- Prometheus/Grafana (Phase 4)

---

## Progress — execution order

The sections below are ordered to match this list exactly — read top to bottom, build top to bottom.

- [ ] 10. CI: `.github/workflows/ci.yml` (lint + test both apps on every PR) — do this first, expect it to fail until step 6 exists, then merge and turn on branch protection — **in progress**: workflow pushed on `chore/ci-pipeline`, fixing `ruff check` failures before merge
- [x] 0. Repo setup — `.gitignore`, folder structure
- [ ] 1. Schema — reuse or re-run `users` / `follows` / `posts` in Postgres
- [x] 2. Backend: DB connection pool — `backend/app/db.py`
- [ ] 3. Backend: Validation + Feed query builder, **TDD** — `backend/app/validation.py`, `backend/app/feed.py`, `backend/tests/test_validation.py`, `backend/tests/test_feed.py` — **stop for a design check-in before merging**; the feed query is what Phase 1's load test measures
- [ ] 4. Backend: Routes — `backend/app/routes/{posts,follow,feed}.py` - tested with - "curl "http://127.0.0.1:5000/feed?userId=f6d85a30-64eb-4ee7-9398-b826d789a229"
- [ ] 5. Backend: Seed script — `backend/scripts/seed.py`
- [ ] 6. Frontend: Vite + React scaffold — `frontend/`
- [ ] 7. Frontend: wire up fetch calls to the three endpoints
- [ ] 8. Deploy — backend to Fly.io/Render, frontend to Vercel (do this as soon as the steps above are mergeable, don't save it for the end)
- [ ] 9. Manual end-to-end verification (seed → curl → browser, against the deployed app, not just localhost)

**Suggested branch-per-checklist-item mapping:**

```
main                              ← protected, always green
 ├─ chore/ci-pipeline             (step 10 — build this first)
 ├─ chore/repo-setup              (step 0)
 ├─ feat/flask-db-connection      (steps 1–2)
 ├─ feat/flask-validation-feed    (step 3 — TDD, written + tested together)
 ├─ feat/flask-routes             (step 4)
 ├─ chore/seed-script             (step 5)
 ├─ feat/react-scaffold           (step 6)
 ├─ feat/react-api-integration    (step 7)
 └─ chore/deploy                  (step 8)
```

Commit checkpoint, as a rule of thumb: commit at every point `pytest` (or the equivalent frontend check) is green, not mid-red and not "whenever I remember." One passing behavior → one commit. See the TDD loop in step 3 and the git workflow in the appendix for the mechanics.

---

## 10. CI pipeline

Runs on every push and PR, spins up a real Postgres for the backend tests (not mocked), lints and tests both apps.

`.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: twitter_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
          cache-dependency-path: backend/requirements.txt
      - run: pip install -r requirements.txt
      - run: ruff check .
      - run: pytest
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/twitter_test

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run lint
      - run: npm run build
```

**Why a real Postgres service container, not a mock:** the whole point of the feed query is SQL correctness (the join, the index, the ordering). Mocking the DB would test that you *called* a mock correctly, not that the query works.

**Why `concurrency` + `cancel-in-progress`:** if you push twice to the same PR quickly (common when fixing a lint error), this cancels the stale run instead of wasting CI minutes on code you've already superseded.

Push this on `chore/ci-pipeline`, open the PR, watch both jobs go green (backend will fail until step 4's routes exist — that's expected), then merge and turn on branch protection:

`github.com/xinrose-lin/twitter-clone` → **Settings → Branches → Add branch protection rule**, pattern `main`:

- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging → select the CI job(s) once they've run once
- ✅ Require branches to be up to date before merging
- ✅ Do not allow bypassing the above settings (applies the rule to you too — good, that's the point)
- ❌ Skip "require approvals" — GitHub won't let you approve your own PR anyway, and there's no one else on this repo yet

---

## 0. Repo setup

```bash
git checkout -b chore/repo-setup
mkdir -p backend/app/routes backend/scripts backend/tests
```

`.gitignore` (repo root):
```
# python
backend/venv/
backend/__pycache__/
backend/**/__pycache__/
backend/.env

# node
frontend/node_modules/
frontend/dist/

# both
.env
.DS_Store
```

Commit `architecture.md`, `roadmap.md`, this file, and `.gitignore` together as your first commit, then open the first PR — good warm-up rep for the branch → PR → merge loop before any real logic is on the line.

```bash
git add plan/ .gitignore
git commit -m "Add v2 architecture doc, tasks.md, and .gitignore for Flask/React stack"
```

---

## 1. Schema

Same three tables as the first spike — if you already have them in your Neon/Supabase Postgres, skip straight to step 2. Otherwise, run in the SQL editor:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT UNIQUE NOT NULL
);

CREATE TABLE follows (
  follower_id UUID REFERENCES users(id),
  following_id UUID REFERENCES users(id),
  PRIMARY KEY (follower_id, following_id)
);

CREATE TABLE posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  author_id UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON posts (author_id, created_at DESC);
```

The architecture doesn't change just because the language did — same reasoning as before applies: the index on `(author_id, created_at DESC)` is what keeps the feed query a sorted index scan instead of a full table scan.

---

## 2. Backend: DB connection pool — `backend/app/db.py`

```python
import os
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

pool = ConnectionPool(
    conninfo=os.environ["DATABASE_URL"],
    kwargs={"row_factory": dict_row},
    open=True,
)
```

**Why `psycopg` (v3) over `psycopg2`:** it's the actively developed successor, ships a built-in pool (`psycopg_pool`) instead of needing a separate package, and has a nicer connection context manager. Same "no ORM" philosophy as the first spike — every query you write here is the real SQL that runs, which is the point of this exercise.

**Why `row_factory=dict_row`:** by default psycopg returns rows as plain tuples (`(id, content, ...)`), which is unreadable and error-prone once you `jsonify()` it. `dict_row` gets you `{"id": ..., "content": ...}` instead — matches what `pg`'s `result.rows` gave you for free in the JS version.

**Not TDD material:** this module has no branching logic of its own — it's wiring around a real Postgres connection. A unit test here would mean mocking `psycopg_pool`, which only proves you called the mock correctly, not that the pool works (same reasoning as the CI section's "why a real Postgres, not a mock"). It gets exercised for real once the routes and manual e2e verification (step 9) run against it.

`backend/.env.example`:
```
DATABASE_URL=postgresql://user:password@host/dbname
```

Commit once this file exists and the pool imports cleanly (`python -c "from app.db import pool"` doesn't error):
```bash
git add backend/app/db.py backend/.env.example
git commit -m "Add psycopg connection pool"
```

---

## 3. Backend: Validation + Feed query builder — TDD

`backend/app/validation.py` and `backend/app/feed.py` are pure functions — no Flask, no HTTP, no database. That makes them the right place to actually run a red → green → refactor loop, unlike step 2's `db.py`.

**The loop, one behavior at a time:**

1. **Red.** Write one test for one behavior. Run `pytest` — confirm it fails (import error or assertion failure, not a typo-error).
2. **Green.** Write the smallest amount of implementation code that makes it pass. Don't add fields, branches, or validators nothing is testing yet.
3. **Refactor.** With the test green, clean up the implementation if it needs it. Re-run `pytest` after every change — it must stay green.
4. **Commit.** Only at a green state — never mid-red. One passing behavior → one commit.
5. Repeat for the next behavior.

### 3a. Validation — start here

`backend/tests/test_validation.py`, one behavior first:
```python
import uuid
import pytest
from pydantic import ValidationError

from app.validation import CreatePostRequest


def test_rejects_empty_content():
    with pytest.raises(ValidationError):
        CreatePostRequest(author_id=uuid.uuid4(), content="")
```

Run `pytest` → red (`app.validation` doesn't exist yet).

`backend/app/validation.py`, just enough to go green:
```python
from uuid import UUID
from pydantic import BaseModel, Field


class CreatePostRequest(BaseModel):
    author_id: UUID
    content: str = Field(min_length=1, max_length=500)
```

Run `pytest` → green. Commit:
```bash
git add backend/app/validation.py backend/tests/test_validation.py
git commit -m "Add CreatePostRequest validation with TDD (reject empty content)"
```

Next behavior — self-follow rejection. Add the test first:
```python
from app.validation import FollowRequest


def test_rejects_self_follow():
    same_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        FollowRequest(follower_id=same_id, following_id=same_id)
```

Red, then implement:
```python
from typing import Optional
from datetime import datetime
from pydantic import model_validator


class FollowRequest(BaseModel):
    follower_id: UUID
    following_id: UUID

    @model_validator(mode="after")
    def no_self_follow(self):
        if self.follower_id == self.following_id:
            raise ValueError("Cannot follow yourself")
        return self


class FeedQuery(BaseModel):
    user_id: UUID
    cursor: Optional[datetime] = None
```

**Why `pydantic`, same reasoning as `zod` before:** shape validation (`min_length`, `UUID` parsing) is declarative; `model_validator` is pydantic's equivalent of zod's `.refine()` — for rules that depend on *more than one field at once*, which a per-field check can't express.

Green, then commit:
```bash
git add backend/app/validation.py backend/tests/test_validation.py
git commit -m "Add FollowRequest self-follow rejection with TDD"
```

(`FeedQuery` has no behavior of its own to test yet — it's exercised once `feed.py` and the routes use it. Adding a test for a model with no validation logic would just be testing pydantic itself.)

### 3b. Feed query builder

`backend/tests/test_feed.py`, first behavior:
```python
def test_build_feed_query_no_cursor():
    from app.feed import build_feed_query
    text, params = build_feed_query("user-1")
    assert params == ["user-1"]
    assert "created_at < %s" not in text
```

Red, then the smallest implementation:
```python
def build_feed_query(user_id, cursor=None):
    params = [str(user_id)]
    text = """
        SELECT p.id, p.content, p.author_id, p.created_at
        FROM posts p
        WHERE p.author_id = ANY(
            SELECT following_id FROM follows WHERE follower_id = %s
        )
        ORDER BY p.created_at DESC
        LIMIT 20
    """
    return text, params
```

Green. Next behavior — the cursor branch:
```python
def test_build_feed_query_with_cursor():
    from app.feed import build_feed_query
    text, params = build_feed_query("user-1", "2026-01-01T00:00:00Z")
    assert params == ["user-1", "2026-01-01T00:00:00Z"]
    assert "created_at < %s" in text
```

Red, then extend the implementation to go green:
```python
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
```

**Why `%s` instead of `$1`/`$2`:** different driver, different placeholder syntax (psycopg always uses positional `%s`, filled in order) — but the underlying guarantee is identical: values are sent separately from the SQL text, so this is still fully parameterized and still immune to SQL injection. Never f-string a value into `text` directly.

**Same known limitation as before, carried over on purpose:** fan-out-on-read. Not a bug, a deliberately deferred optimization — see `architecture.md`'s Future Work section.

Green, then commit:
```bash
git add backend/app/feed.py backend/tests/test_feed.py
git commit -m "Add feed query builder with TDD (cursor and no-cursor cases)"
```

Run: `pytest` from `backend/` — everything above should pass with **no database running**. Push the branch, open the PR, and **stop for a design check-in before merging** — this is the query Phase 1's load test measures.

```bash
git push -u origin feat/flask-validation-feed
```

---

## 4. Backend: Routes

`backend/app/__init__.py` (the app factory):
```python
from flask import Flask
from flask_cors import CORS

from app.routes.posts import posts_bp
from app.routes.follow import follow_bp
from app.routes.feed import feed_bp


def create_app():
    app = Flask(__name__)
    CORS(app)  # React dev server runs on a different origin/port
    app.register_blueprint(posts_bp)
    app.register_blueprint(follow_bp)
    app.register_blueprint(feed_bp)
    return app
```

**Why an app factory + blueprints, not one big `app.py`:** a function that *builds* an app (rather than a module-level `app = Flask(...)`) is what lets tests spin up a fresh app instance per test without shared state, and blueprints let each resource's routes live in their own file instead of one growing file — the Flask-idiomatic equivalent of Next.js's one-route-per-file convention you had before.

`backend/wsgi.py`:
```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

`backend/app/routes/posts.py`:
```python
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
```

`backend/app/routes/follow.py`:
```python
from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from app.db import pool
from app.validation import FollowRequest

follow_bp = Blueprint("follow", __name__)


@follow_bp.post("/follow")
def follow():
    try:
        data = FollowRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    with pool.connection() as conn:
        conn.execute(
            "INSERT INTO follows (follower_id, following_id) VALUES (%s, %s) "
            "ON CONFLICT DO NOTHING",
            (str(data.follower_id), str(data.following_id)),
        )

    return jsonify({"success": True})
```

`backend/app/routes/feed.py`:
```python
from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from app.db import pool
from app.validation import FeedQuery
from app.feed import build_feed_query

feed_bp = Blueprint("feed", __name__)


@feed_bp.get("/feed")
def feed():
    try:
        query = FeedQuery(
            user_id=request.args.get("userId"),
            cursor=request.args.get("cursor"),
        )
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    text, params = build_feed_query(str(query.user_id), query.cursor)

    with pool.connection() as conn:
        rows = conn.execute(text, params).fetchall()

    return jsonify({"items": rows})
```

Deliberately thin, same as before — all real logic already lives in (and is tested via) `build_feed_query`.

*(Watch for this gotcha: Flask's JSON encoder handles `UUID`/`datetime` conversion automatically in modern versions, but if `jsonify` ever throws "not JSON serializable," that's the first thing to check.)*

*(No auth yet — IDs passed directly, same intentional gap as the first spike.)*

`backend/requirements.txt`:
```
flask
flask-cors
psycopg[binary,pool]
pydantic
python-dotenv
pytest
ruff
```

Commit once the app boots (`flask --app wsgi run` starts without error) — this is wiring, not TDD, so there's no red/green loop, just a working state to commit:
```bash
git add backend/app/__init__.py backend/wsgi.py backend/app/routes/ backend/requirements.txt
git commit -m "Wire up Flask routes for posts, follow, and feed"
```

---

## 5. Backend: Seed script — `backend/scripts/seed.py`

```python
from app.db import pool


def seed():
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

    print("Seeded. Alice ID:", alice["id"])


if __name__ == "__main__":
    seed()
```

Run: `python -m scripts.seed` from `backend/`. Same deliberately small, specific seed data as before — easy to eyeball correctness.

Commit once it runs cleanly against a real Postgres:
```bash
git add backend/scripts/seed.py
git commit -m "Add seed script for alice/bob/carol fixture data"
```

---

## 6–7. Frontend: React scaffold + API wiring

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
```

`frontend/.env`:
```
VITE_API_URL=http://localhost:5000
```

`frontend/src/api.ts`:
```ts
const BASE = import.meta.env.VITE_API_URL;

export async function getFeed(userId: string, cursor?: string) {
  const params = new URLSearchParams({ userId, ...(cursor && { cursor }) });
  const res = await fetch(`${BASE}/feed?${params}`);
  if (!res.ok) throw new Error("Failed to load feed");
  return res.json();
}

export async function createPost(authorId: string, content: string) {
  const res = await fetch(`${BASE}/posts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ author_id: authorId, content }),
  });
  if (!res.ok) throw new Error("Failed to create post");
  return res.json();
}

export async function follow(followerId: string, followingId: string) {
  const res = await fetch(`${BASE}/follow`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ follower_id: followerId, following_id: followingId }),
  });
  if (!res.ok) throw new Error("Failed to follow");
  return res.json();
}
```

A single `Feed` component calling `getFeed` on mount is enough to prove the wiring end to end — this doc isn't trying to spec the UI, just get the three endpoints reachable from a real browser.

**Why `flask-cors` was needed back in step 4:** Vite's dev server runs on `localhost:5173`, Flask on `localhost:5000` — different origin, so without CORS headers the browser blocks the fetch outright regardless of whether the backend logic is correct.

Commit once the scaffold builds and the Feed component renders against local Flask:
```bash
git add frontend/
git commit -m "Scaffold React frontend and wire up API calls"
```

---

## 8. Deploy

Backend → **Fly.io or Render** (Docker not required — both platforms build a Python app from a `Procfile`/buildpack without you writing a Dockerfile at this stage). Frontend → **Vercel**.

- Set `DATABASE_URL` as an environment variable/secret on the backend host, not in a committed file
- Set `VITE_API_URL` on Vercel to the deployed backend's URL
- Update `flask-cors`'s allowed origins (or the deployed frontend's config) so the deployed frontend can actually call the deployed backend — this is the most common thing to trip on, since it only surfaces once both sides are live, not in local dev
- Do this as soon as the steps above are mergeable, even if the deployed app is barely functional — deploy pain (env vars, CORS, build config) is cheaper to hit now than at the end
- A `deploy.yml` triggered on merge-to-`main` is optional here; manual deploy is fine for Phase 0 — automate it later if it becomes friction

---

## 9. Manual end-to-end verification

```bash
# terminal 1
cd backend && python -m scripts.seed   # note Alice's printed ID
flask --app wsgi run

# terminal 2
cd frontend && npm run dev
```

```bash
curl "http://localhost:5000/feed?userId=<alice-id-from-seed-output>"
```

Expect Carol's post first (posted later), then Bob's. Confirm the same thing renders in the browser at `localhost:5173` — then repeat the check against the deployed URLs from step 8. Local-only verification doesn't count as done; the deploy is where CORS/env-var mistakes actually show up.

---

## Known gaps (intentional, carried over from v1)

- No auth — IDs passed directly in requests.
- No caching / precomputed feed table.
- No async fan-out worker.
- Fan-out-on-read — will get slow for users following many accounts, or accounts with many followers. See `architecture.md` → Future Work.
- No deploy pipeline yet — CI (test-on-PR) is step 10; CD (auto-deploy-on-merge) is deliberately deferred until there's something worth shipping.

---

## Appendix: Git & DevOps concepts

Background and workflow reference — not steps to execute, just the mental model behind steps 0–9 above.

### Understanding Git — core concepts

You asked to actually understand this, not just copy commands, so here's the mental model. Everything else in this doc (branches, PRs, CI) is built on these five ideas:

| Concept | What it actually is |
|---|---|
| **Commit** | An immutable snapshot of the whole repo at a point in time, plus a pointer to its parent commit(s). History is a chain of these. |
| **Branch** | Just a movable label pointing at one commit. `main` is not special to git — it's a branch by convention. Creating a branch is instant and cheap (it's not a copy of files). |
| **HEAD** | A pointer to "where you are right now" — normally it points at a branch, which points at a commit. |
| **Staging area (the index)** | `git add` doesn't commit — it moves changes into a holding area. `git commit` snapshots *what's staged*, not everything you've changed. This is what lets you commit half your changes and leave the rest for later. |
| **Remote (`origin`)** | A copy of the repo's history living elsewhere (GitHub, in your case). Your local repo and GitHub only sync when you tell them to: `git push` (local → remote), `git pull` (remote → local, = fetch + merge), `git fetch` (remote → local, but don't merge yet — just look). |

Two more that matter once you're branching:

- **Merge**: combine two branches' histories into one, creating a new commit with two parents. Nothing is rewritten — safe on shared branches.
- **Rebase**: replay your branch's commits one-by-one on top of another branch's tip, as if you'd started there. Produces a straight line, no merge commit — but it *rewrites* commit hashes. Rule of thumb: rebase your own not-yet-pushed or not-yet-shared branch to keep it current with `main`; never rebase a branch someone else is also working on.
- **Pull Request (PR)**: not a git concept at all — it's a GitHub feature. It's a UI wrapper around "merge branch A into branch B" that adds a diff view, comments, and (critically) a gate: required CI checks and/or reviews before the merge button unlocks.

The commands you'll actually type, in order, every single feature:

```bash
git checkout main && git pull          # start from the latest main
git checkout -b feat/some-small-thing  # branch, cheap and instant
# ...edit files...
git status                             # see what changed
git diff                               # see the actual line changes
git add backend/app/validation.py      # stage specific files (not -A — be deliberate)
git commit -m "Add pydantic validation schemas"
git push -u origin feat/some-small-thing   # -u sets the upstream, only needed the first push
```

Then open a PR (`gh pr create --fill` or the GitHub UI), let CI run, review your own diff, merge, then:

```bash
git checkout main && git pull
git branch -d feat/some-small-thing    # delete the now-merged local branch
```

### Should you be using PRs? Yes — even solo

A PR gate isn't about needing someone else's approval. Solo, it buys you three things:

1. **A forced second look.** Reading your own diff in GitHub's UI, outside your editor, catches things a self-review inside VS Code doesn't — leftover `print()`s, a variable you meant to rename, an accidental file.
2. **CI runs automatically before anything touches `main`.** Once step 10 is wired up, every PR gets tested before it's mergeable — `main` stays in a state you could deploy at any moment.
3. **A real history.** `git log --oneline main` becomes a changelog of actual features, not "wip", "fix", "asdf".

#### Can you build features "in parallel"?

Two different things people mean by this:

**1. Sequenced-but-independent branches (the one you'll actually use).** Nothing stops you from cutting `feat/flask-routes` off `main` while `feat/react-scaffold`'s PR is still open waiting on CI or your own review. Branches are cheap — cut one per checklist item above, each becomes a small, easy-to-review PR (rule of thumb: keep diffs under ~300–400 lines; if a branch is ballooning, that's a sign to land part of it and split the rest).

**2. Literally simultaneous, on disk — `git worktree`.** Normally a folder can only have one branch checked out at a time. `git worktree add ../twitter-clone-feed feat/flask-feed-query` checks out a *second* branch into a *second* folder, both sharing the same `.git` history underneath. That means two editor windows, two branches, no stashing to switch context — genuinely useful once you have, say, a long test suite running against one branch while you write code on another. For this project's size, #1 is where the real value is; worktrees are worth knowing about, not necessary yet.

### Other DevOps practices worth adopting here

- **Secrets never in git.** `backend/.env` (holds `DATABASE_URL`) goes in `.gitignore`; commit a `backend/.env.example` with the shape but no real value instead. The *test* `DATABASE_URL` in step 10's CI workflow is thrown away every CI run (fresh container), so it's fine to keep the dummy `postgres:postgres` credentials in plaintext in the workflow file — anything real (a production deploy key, later) goes in **Settings → Secrets and variables → Actions**, referenced as `${{ secrets.NAME }}`.
- **Dependabot** (`.github/dependabot.yml`) — opens automatic PRs bumping `requirements.txt`/`package.json` versions, gated by the same CI job. Cheap to add, catches drift before it becomes a big-bang upgrade.
- **Conventional commit messages** (`feat: add feed route`, `fix: off-by-one in cursor`, `chore: bump ruff`) — not enforced by anything here, just a habit that makes `git log` skimmable later.
- **Deploy pipeline is a deliberately separate, later step.** Once there's something worth shipping, a `deploy.yml` triggered on merge-to-`main` (Render/Fly.io/Railway for Flask, Vercel/Netlify for the Vite build) is the natural next piece — not needed to start building.
</content>
