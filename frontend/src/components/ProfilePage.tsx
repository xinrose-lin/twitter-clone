import { useEffect, useState } from 'react'
import type { FollowedUser, Post } from '../api'
import { follow as followApi, getFollows } from '../api'
import { getUser } from '../data/users'
import PostCard from './PostCard'

export default function ProfilePage({
  profileUserId,
  currentUserId,
  posts,
  onSelectUser,
  onBack,
}: {
  profileUserId: string
  currentUserId: string
  posts: Post[]
  onSelectUser: (userId: string) => void
  onBack: () => void
}) {
  const [following, setFollowing] = useState<FollowedUser[]>([])
  const [followers, setFollowers] = useState<FollowedUser[]>([])
  const [followsLoading, setFollowsLoading] = useState(true)
  const [followPending, setFollowPending] = useState(false)

  const user = getUser(profileUserId)
  const username = user?.username ?? 'unknown'
  const isSelf = profileUserId === currentUserId
  const authoredPosts = posts.filter((p) => p.author_id === profileUserId)
  const currentUserFollowsProfile = followers.some((u) => u.id === currentUserId)

  useEffect(() => {
    let cancelled = false
    setFollowsLoading(true)
    getFollows(profileUserId)
      .then((data) => {
        if (cancelled) return
        setFollowing(data.following)
        setFollowers(data.followers)
      })
      .finally(() => {
        if (!cancelled) setFollowsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [profileUserId])

  async function handleFollow() {
    setFollowPending(true)
    try {
      await followApi(currentUserId, profileUserId)
      setFollowers((prev) => [...prev, { id: currentUserId, username: getUser(currentUserId)?.username ?? '' }])
    } finally {
      setFollowPending(false)
    }
  }

  return (
    <div>
      <button className="back-link" onClick={onBack}>
        ← Back to feed
      </button>

      <div className="profile-header">
        <div className="avatar large">{username[0]?.toUpperCase()}</div>
        <div>
          <h2>@{username}</h2>
          {!isSelf && (
            <button
              className="follow-btn"
              onClick={handleFollow}
              disabled={currentUserFollowsProfile || followPending || followsLoading}
            >
              {currentUserFollowsProfile ? 'Following' : followPending ? 'Following…' : 'Follow'}
            </button>
          )}
        </div>
      </div>

      <div className="follow-lists">
        <div className="follow-list">
          <h3>Following ({following.length})</h3>
          {following.length === 0 ? (
            <p className="hint">Not following anyone.</p>
          ) : (
            following.map((u) => (
              <button key={u.id} className="username-link" onClick={() => onSelectUser(u.id)}>
                @{u.username}
              </button>
            ))
          )}
        </div>
        <div className="follow-list">
          <h3>Followers ({followers.length})</h3>
          {followers.length === 0 ? (
            <p className="hint">No followers yet.</p>
          ) : (
            followers.map((u) => (
              <button key={u.id} className="username-link" onClick={() => onSelectUser(u.id)}>
                @{u.username}
              </button>
            ))
          )}
        </div>
      </div>

      <div className="post-list">
        {authoredPosts.length === 0 ? (
          <p className="hint">
            No posts visible from @{username}
            {!isSelf && ` — you (viewing as the current user) may not follow them yet, so their posts don't show up in your feed.`}
          </p>
        ) : (
          authoredPosts.map((post) => (
            <PostCard key={post.id} post={post} onSelectUser={onSelectUser} />
          ))
        )}
      </div>
    </div>
  )
}
