import { useCallback, useEffect, useState } from 'react'
import './App.css'
import type { Post } from './api'
import { getFeed } from './api'
import { USERS } from './data/users'
import UserSwitcher from './components/UserSwitcher'
import FeedPage from './components/FeedPage'
import ProfilePage from './components/ProfilePage'
import PeoplePage from './components/PeoplePage'

type View = { page: 'feed' } | { page: 'profile'; userId: string } | { page: 'people' }

function App() {
  const [currentUserId, setCurrentUserId] = useState(USERS[0].id)
  const [view, setView] = useState<View>({ page: 'feed' })
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadFeed = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const feed = await getFeed(currentUserId)
      setPosts(feed.items)
    } catch {
      setError('Failed to load feed.')
    } finally {
      setLoading(false)
    }
  }, [currentUserId])

  useEffect(() => {
    loadFeed()
  }, [loadFeed])

  return (
    <>
      <header className="top-bar">
        <h1 className="logo">tweeter</h1>
        <nav className="nav-links">
          <button className="nav-link" onClick={() => setView({ page: 'feed' })}>
            Feed
          </button>
          <button className="nav-link" onClick={() => setView({ page: 'people' })}>
            People
          </button>
          <button className="nav-link" onClick={() => setView({ page: 'profile', userId: currentUserId })}>
            Profile
          </button>
        </nav>
        <UserSwitcher currentUserId={currentUserId} onChange={setCurrentUserId} />
      </header>

      <section id="center">
        {view.page === 'feed' && (
          <FeedPage
            posts={posts}
            loading={loading}
            error={error}
            currentUserId={currentUserId}
            onSelectUser={(userId) => setView({ page: 'profile', userId })}
            onPostCreated={loadFeed}
          />
        )}
        {view.page === 'profile' && (
          <ProfilePage
            profileUserId={view.userId}
            currentUserId={currentUserId}
            posts={posts}
            onSelectUser={(userId) => setView({ page: 'profile', userId })}
            onBack={() => setView({ page: 'feed' })}
          />
        )}
        {view.page === 'people' && (
          <PeoplePage currentUserId={currentUserId} onSelectUser={(userId) => setView({ page: 'profile', userId })} />
        )}
      </section>
    </>
  )
}

export default App
