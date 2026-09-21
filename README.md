# twitter-clone

JDSG system design — a minimal Twitter-like app (Flask + Postgres backend, React/Vite frontend), built as a system-design learning exercise. See `plan/tasks.md` for the full build log and rationale.

## What's included so far (Phase 0)

**Backend** (`backend/`, Flask + Postgres via `psycopg`)
- `POST /posts` — create a post
- `POST /follow` — follow a user
- `GET /users/<id>/follows` — list who a user follows / is followed by
- `GET /feed` — fan-out-on-read feed query for a user
- Pydantic request validation (`app/validation.py`)
- Seed script (`scripts/seed.py`) — seeds alice/bob/carol plus filler users and posts for feed volume
- Test suite (`pytest`) covering validation and the feed query

**Frontend** (`frontend/`, React + Vite)
- Feed, Profile, and People pages, with a user switcher to test different logins without real auth
- Talks to the backend via `VITE_API_URL`

**Deploy**
- Backend: `https://twitter-clone-tm5q.onrender.com` (Render, free tier)
- Frontend: `https://twitter-clone-frontend-q2at.onrender.com` (Render, free tier)
- Free tier spins down after ~15 min idle — first request after that can take 30-50s to wake up

## Known gaps (intentional for Phase 0)

- No auth — user IDs are passed directly in requests
- No caching or precomputed feed table — feed is fan-out-on-read, will get slow at scale (see `architecture.md` → Future Work)
- No async fan-out worker
- No CI/CD pipeline yet
- Hosted `GET /feed` currently returns 500 — see `backend/manual_tests.md` for the open investigation

## Local development

```bash
# backend
cd backend && source venv/bin/activate && flask --app wsgi run --port 5000

# frontend
cd frontend && npm run dev
```

Manual API test commands (local + hosted) are in `backend/manual_tests.md`.
