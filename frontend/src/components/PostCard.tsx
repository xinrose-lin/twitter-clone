import type { Post } from '../api'
import { getUser } from '../data/users'

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h`
  const days = Math.floor(hours / 24)
  return `${days}d`
}

export default function PostCard({
  post,
  onSelectUser,
}: {
  post: Post
  onSelectUser: (userId: string) => void
}) {
  const author = getUser(post.author_id)
  const username = author?.username ?? 'unknown'

  return (
    <article className="post-card">
      <button className="avatar" onClick={() => onSelectUser(post.author_id)}>
        {username[0]?.toUpperCase()}
      </button>
      <div className="post-body">
        <div className="post-meta">
          <button className="username-link" onClick={() => onSelectUser(post.author_id)}>
            @{username}
          </button>
          <span className="post-time">· {timeAgo(post.created_at)}</span>
        </div>
        <p className="post-content">{post.content}</p>
      </div>
    </article>
  )
}
