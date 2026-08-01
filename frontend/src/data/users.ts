export type User = {
  id: string
  username: string
}

export const USERS: User[] = [
  { id: 'f6d85a30-64eb-4ee7-9398-b826d789a229', username: 'alice' },
  { id: '48c172fe-3a2e-4779-a404-5548610ac6b6', username: 'bob' },
  { id: '9d28730d-3522-461e-b88c-a9472985d981', username: 'carol' },
]

export function getUser(id: string): User | undefined {
  return USERS.find((u) => u.id === id)
}
