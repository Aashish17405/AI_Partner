export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function createSessionKey(sessionId: string): string {
  return `session_${sessionId}`
}

export function createMessageCacheKey(sessionId: string): string {
  return `messages_${sessionId}`
}

export function saveSessionToLocalStorage(sessionId: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('current_session_id', sessionId)
  }
}

export function getSessionFromLocalStorage(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('current_session_id')
  }
  return null
}

export function clearSessionFromLocalStorage(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('current_session_id')
  }
}

export function createScrollInDelay(index: number): string {
  return `${index * 100}ms`
}
