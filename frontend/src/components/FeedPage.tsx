import { useState, type FormEvent } from 'react'
import type { Post } from '../api'
import { createPost } from '../api'
import PostCard from './PostCard'

export default function FeedPage({
  posts,
  loading,
  error,
  currentUserId,
  onSelectUser,
  onPostCreated,
}: {
  posts: Post[]
  loading: boolean
  error: string | null
  currentUserId: string
  onSelectUser: (userId: string) => void
  onPostCreated: () => void
}) {
  const [content, setContent] = useState('')
  const [posting, setPosting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!content.trim()) return
    setPosting(true)
    try {
      await createPost(currentUserId, content.trim())
      setContent('')
      onPostCreated()
    } finally {
      setPosting(false)
    }
  }

  return (
    <div>
      <form className="composer" onSubmit={handleSubmit}>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="What's happening?"
          maxLength={500}
        />
        <button type="submit" disabled={posting || !content.trim()}>
          {posting ? 'Posting…' : 'Post'}
        </button>
      </form>

      {loading && <p className="hint">Loading feed…</p>}
      {error && <p className="hint error">{error}</p>}
      {!loading && !error && posts.length === 0 && (
        <p className="hint">No posts yet — follow someone or post something.</p>
      )}

      <div className="post-list">
        {posts.map((post) => (
          <PostCard key={post.id} post={post} onSelectUser={onSelectUser} />
        ))}
      </div>
    </div>
  )
}
