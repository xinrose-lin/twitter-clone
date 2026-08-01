import { useState, type FormEvent } from 'react'
import './App.css'
import { createPost, follow, getFeed } from './api'

function App() {
  return (
    <section id="center">
      <h1>API test harness</h1>
      <p style={{ marginBottom: 24 }}>
        Seed the backend first (<code>python -m scripts.seed</code>) and
        paste alice/bob/carol's UUIDs below.
      </p>

      <div className="panels">
        <CreatePostPanel />
        <FollowPanel />
        <FeedPanel />
      </div>
    </section>
  )
}

function CreatePostPanel() {
  const [authorId, setAuthorId] = useState('')
  const [content, setContent] = useState('')
  const [result, setResult] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setResult('loading...')
    try {
      const post = await createPost(authorId, content)
      setResult(JSON.stringify(post, null, 2))
    } catch (err) {
      setResult(String(err))
    }
  }

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <h2>POST /posts</h2>
      <label>
        author_id
        <input value={authorId} onChange={(e) => setAuthorId(e.target.value)} placeholder="uuid" required />
      </label>
      <label>
        content
        <textarea value={content} onChange={(e) => setContent(e.target.value)} required />
      </label>
      <button type="submit">Create post</button>
      {result && <pre>{result}</pre>}
    </form>
  )
}

function FollowPanel() {
  const [followerId, setFollowerId] = useState('')
  const [followingId, setFollowingId] = useState('')
  const [result, setResult] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setResult('loading...')
    try {
      const res = await follow(followerId, followingId)
      setResult(JSON.stringify(res, null, 2))
    } catch (err) {
      setResult(String(err))
    }
  }

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <h2>POST /follow</h2>
      <label>
        follower_id
        <input value={followerId} onChange={(e) => setFollowerId(e.target.value)} placeholder="uuid" required />
      </label>
      <label>
        following_id
        <input value={followingId} onChange={(e) => setFollowingId(e.target.value)} placeholder="uuid" required />
      </label>
      <button type="submit">Follow</button>
      {result && <pre>{result}</pre>}
    </form>
  )
}

function FeedPanel() {
  const [userId, setUserId] = useState('')
  const [cursor, setCursor] = useState('')
  const [result, setResult] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setResult('loading...')
    try {
      const feed = await getFeed(userId, cursor || undefined)
      setResult(JSON.stringify(feed, null, 2))
    } catch (err) {
      setResult(String(err))
    }
  }

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <h2>GET /feed</h2>
      <label>
        userId
        <input value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="uuid" required />
      </label>
      <label>
        cursor (optional)
        <input value={cursor} onChange={(e) => setCursor(e.target.value)} placeholder="ISO timestamp" />
      </label>
      <button type="submit">Load feed</button>
      {result && <pre>{result}</pre>}
    </form>
  )
}

export default App
