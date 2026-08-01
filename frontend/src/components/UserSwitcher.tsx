import { USERS } from '../data/users'

export default function UserSwitcher({
  currentUserId,
  onChange,
}: {
  currentUserId: string
  onChange: (userId: string) => void
}) {
  return (
    <div className="user-switcher">
      <span>Viewing as</span>
      <select value={currentUserId} onChange={(e) => onChange(e.target.value)}>
        {USERS.map((u) => (
          <option key={u.id} value={u.id}>
            @{u.username}
          </option>
        ))}
      </select>
    </div>
  )
}
