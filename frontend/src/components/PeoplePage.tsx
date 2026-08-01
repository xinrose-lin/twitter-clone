import { useEffect, useState } from 'react'
import { follow as followApi, getFollows } from '../api'
import { USERS } from '../data/users'

export default function PeoplePage({
  currentUserId,
  onSelectUser,
}: {
  currentUserId: string
  onSelectUser: (userId: string) => void
}) {
  const [alreadyFollowingIds, setAlreadyFollowingIds] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [pendingId, setPendingId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getFollows(currentUserId)
      .then((data) => {
        if (cancelled) return
        setAlreadyFollowingIds(new Set(data.following.map((u) => u.id)))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [currentUserId])

  const others = USERS.filter((u) => u.id !== currentUserId && !alreadyFollowingIds.has(u.id))

  async function handleFollow(userId: string) {
    setPendingId(userId)
    try {
      await followApi(currentUserId, userId)
      setAlreadyFollowingIds((prev) => new Set(prev).add(userId))
    } finally {
      setPendingId(null)
    }
  }

  return (
    <div>
      <h2 className="page-title">People</h2>
      {loading && <p className="hint">Loading…</p>}
      {!loading && others.length === 0 && <p className="hint">You're already following everyone.</p>}
      <div className="post-list">
        {others.map((user) => {
          const isPending = pendingId === user.id
          return (
            <div key={user.id} className="person-row">
              <button className="avatar" onClick={() => onSelectUser(user.id)}>
                {user.username[0]?.toUpperCase()}
              </button>
              <button className="username-link person-name" onClick={() => onSelectUser(user.id)}>
                @{user.username}
              </button>
              <button className="follow-btn" onClick={() => handleFollow(user.id)} disabled={isPending}>
                {isPending ? 'Following…' : 'Follow'}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
