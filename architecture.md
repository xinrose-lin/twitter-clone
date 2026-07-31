# Architecture

A minimal Twitter clone. Design follows the fan-out pattern described in
[hellointerview's Facebook News Feed breakdown](https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-news-feed),
scoped down to a simple, single-user-scale base version (no viral hot-key handling, no precompute tiering — those are noted as future work).

## Functional Requirements

- A user can create a post (text only, for v1).
- A user can follow / unfollow another user.
- A user can view their feed: posts from everyone they follow, newest first.
- The feed supports pagination (infinite scroll).

**Out of scope (v1):** likes, replies/retweets, media attachments, DMs, notifications, search, private accounts.

## Non-Functional Requirements

- Feed reads should be fast (sub-second) — reads happen far more often than writes.
- Some staleness is fine — a new post doesn't need to appear in followers' feeds instantly (seconds-to-a-minute delay is acceptable).
- Correctness of chronological order matters more than perfect real-time delivery.
- Design for a small/medium scale to start (thousands–millions of users), but keep the fan-out pattern so it doesn't need a rewrite to grow.

## Core Entities

| Entity | Description |
|---|---|
| **User** | An account. |
| **Follow** | Directional edge: `follower` → `followee`. |
| **Post** | Text content authored by a user, timestamped. |

## API Design

```
POST   /posts                              create a post
PUT    /users/:id/follow                   follow a user (idempotent)
DELETE /users/:id/follow                   unfollow a user
GET    /feed?pageSize=20&cursor=<ts>       paginated feed, cursor = timestamp of last seen post
```

## High-Level Architecture

```
Client
  │
  ▼
API Gateway / Backend (single service for v1)
  │
  ├── Post Service   → writes to Posts table
  ├── Follow Service  → writes to Follows table
  └── Feed Service    → reads Follows + Posts, assembles feed
```

For a base version, Post/Follow/Feed can live in one backend service — the
split above is logical, not necessarily physical processes.

## Data Model

**Users**
```
id (PK), username, created_at
```

**Follows**
```
follower_id (PK), followee_id (SK)         -- "who do I follow"
followee_id (GSI PK), follower_id (GSI SK) -- "who follows me" (reverse index)
```

**Posts**
```
id (PK), author_id, content, created_at
GSI: author_id (PK), created_at (SK)       -- fetch a user's posts, newest first
```

## Feed Generation: Fan-out on Read (v1 approach)

For a simple base implementation, generate feeds **at read time**:

1. `GET /feed` → look up the list of users the requester follows.
2. Query each followee's recent posts (via the `author_id` GSI).
3. Merge the results and sort by `created_at` descending.
4. Return a page, with the cursor being the timestamp of the last post shown.

This is simple and always consistent, but does `O(followees)` queries per
feed load — fine at small scale, and matches the "start simple, optimize
when you hit a real bottleneck" principle from the reference article.

## Future Work (not in v1, noted for later)

- **Fan-out on write**: precompute a `PrecomputedFeed` table per user when a
  followee posts, so reads become a single lookup. Needed once fan-out-on-read
  gets too slow (users following many accounts).
- **Hybrid fan-out**: for accounts with very large follower counts, skip
  precompute (write fan-out becomes too expensive) and merge their posts in
  at read time instead — same hybrid idea as the reference design.
- **Hot key / caching**: replicated cache for viral posts once traffic
  justifies it.
- Likes, replies, media, notifications.

## Why This Scope

Everything above "Feed Generation" is the full base functionality (post,
follow, view feed, paginate). Everything under "Future Work" is scaling
machinery that only matters once the simple version hits a concrete
bottleneck — deliberately deferred rather than built up front.
