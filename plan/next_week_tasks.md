# Next Week — Task List

Carried over from Phase 0 wrap-up. These build on the seed script added in `tasks.md` step 5.

- [ ] Scale up `backend/scripts/seed.py` for Phase 1's load test — bump `EXTRA_USER_COUNT` to 200 and `POSTS_PER_EXTRA_USER` to ~20 (~4,000 posts total), and have alice follow ~100 of the extra users instead of all of them.
  - **Why:** at today's 10 users / 50 posts, the feed query's latency is too small to feel. Phase 1's load test needs a posts table large enough that query time is actually measurable before/after the fan-out-on-write optimization (see `architecture.md` → Future Work).
  - Keep alice/bob/carol as the only login-switchable profiles — the extra users are real rows (FK-required by `posts.author_id`) but exist only to pad feed volume, not to be logged into.
  - Confirmed safe against Neon's free tier (0.5 GB storage, 100 compute-hrs/month) — 4k rows is a rounding error against the storage cap.
