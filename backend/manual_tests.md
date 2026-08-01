# Manual API tests

Seeded fixture IDs (alice/bob/carol, from `scripts/seed.py`):

```bash
alice=f6d85a30-64eb-4ee7-9398-b826d789a229
bob=48c172fe-3a2e-4779-a404-5548610ac6b6
carol=9d28730d-3522-461e-b88c-a9472985d981
```

## Local (`http://127.0.0.1:5000`)

Start the server first:
```bash
cd backend && source venv/bin/activate && flask --app wsgi run --port 5000
```

**GET /feed**
```bash
curl -s -w "\nHTTP:%{http_code}\n" "http://127.0.0.1:5000/feed?userId=$alice"
```

**POST /posts**
```bash
curl -s -w "\nHTTP:%{http_code}\n" -X POST http://127.0.0.1:5000/posts \
  -H "Content-Type: application/json" \
  -d "{\"author_id\":\"$alice\",\"content\":\"local test post\"}"
```

**POST /follow**
```bash
curl -s -w "\nHTTP:%{http_code}\n" -X POST http://127.0.0.1:5000/follow \
  -H "Content-Type: application/json" \
  -d "{\"follower_id\":\"$alice\",\"following_id\":\"$carol\"}"
```

**Validation error cases (expect 400)**
```bash
# self-follow
curl -s -w "\nHTTP:%{http_code}\n" -X POST http://127.0.0.1:5000/follow \
  -H "Content-Type: application/json" \
  -d "{\"follower_id\":\"$alice\",\"following_id\":\"$alice\"}"

# empty content
curl -s -w "\nHTTP:%{http_code}\n" -X POST http://127.0.0.1:5000/posts \
  -H "Content-Type: application/json" \
  -d "{\"author_id\":\"$alice\",\"content\":\"\"}"
```

## Hosted (`https://twitter-clone-tm5q.onrender.com`)

Same requests against the deployed backend. Note: Render free tier spins down when idle, so the first request after inactivity can take 30-50s to wake up.

**GET /feed**
```bash
curl -s -w "\nHTTP:%{http_code}\n" "https://twitter-clone-tm5q.onrender.com/feed?userId=$alice"
```

**Validation check** (bad UUID should 400, not 500):
```bash
curl -s -w "\nHTTP:%{http_code}\n" "https://twitter-clone-tm5q.onrender.com/feed?userId=not-a-uuid"
```

**POST /posts**
```bash
curl -s -w "\nHTTP:%{http_code}\n" -X POST https://twitter-clone-tm5q.onrender.com/posts \
  -H "Content-Type: application/json" \
  -d "{\"author_id\":\"$alice\",\"content\":\"hosted test post\"}"
```

**POST /follow**
```bash
curl -s -w "\nHTTP:%{http_code}\n" -X POST https://twitter-clone-tm5q.onrender.com/follow \
  -H "Content-Type: application/json" \
  -d "{\"follower_id\":\"$alice\",\"following_id\":\"$carol\"}"
```

### Known issue

`GET /feed` on the hosted deploy returned `500 Internal Server Error` on 2026-08-01 (debug mode is off, so no traceback in the response). Likely causes: `DATABASE_URL` missing/incorrect in Render's environment settings, or the DB isn't reachable from Render's network. Check Render dashboard → service → **Logs** for the traceback, and **Environment** tab to confirm `DATABASE_URL`.
