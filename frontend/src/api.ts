const BASE = import.meta.env.VITE_API_URL;

export type Post = {
  id: string;
  content: string;
  author_id: string;
  created_at: string;
};

export async function getFeed(userId: string, cursor?: string): Promise<{ items: Post[] }> {
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

export type FollowedUser = {
  id: string;
  username: string;
};

export async function getFollows(userId: string): Promise<{ following: FollowedUser[]; followers: FollowedUser[] }> {
  const res = await fetch(`${BASE}/users/${userId}/follows`);
  if (!res.ok) throw new Error("Failed to load follows");
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
