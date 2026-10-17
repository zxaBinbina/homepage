import type { ChessState, ChessTurn } from './chess'
import type { GoState } from './go'

type LearnedMove = number | ChessTurn | { from: number; to: number }
type Entry = { key: string; move: LearnedMove; count: number }
const storageKey = 'homepage-game-experience-v1'
const maxEntries = 600

function read(): Record<string, Entry[]> {
  if (typeof localStorage === 'undefined') return {}
  try {
    const value = JSON.parse(localStorage.getItem(storageKey) || '{}')
    return value && typeof value === 'object' ? value : {}
  } catch {
    return {}
  }
}
function write(value: Record<string, Entry[]>) {
  try {
    localStorage.setItem(storageKey, JSON.stringify(value))
  } catch {
    /* Storage is optional. */
  }
}
export function experienceKey(kind: string, board: unknown) {
  if (kind === 'chess') return JSON.stringify({ kind, fen: (board as ChessState).fen })
  if (kind === 'go') {
    const state = board as GoState
    return JSON.stringify({ kind, board: state.board, turn: state.turn, passes: state.passes })
  }
  return JSON.stringify({ kind, board })
}
export function rememberMove(kind: string, board: unknown, move: LearnedMove) {
  const all = read(),
    key = experienceKey(kind, board),
    entries = all[kind] || []
  const encoded = JSON.stringify(move)
  const existing = entries.find(
    (entry) => entry.key === key && JSON.stringify(entry.move) === encoded,
  )
  if (existing) existing.count = Math.min(existing.count + 1, 99)
  else entries.push({ key, move, count: 1 })
  all[kind] = entries.sort((a, b) => b.count - a.count).slice(0, maxEntries)
  write(all)
}
export function learnedMove(kind: string, board: unknown): LearnedMove | null {
  const key = experienceKey(kind, board)
  const match = (read()[kind] || [])
    .filter((entry) => entry.key === key)
    .sort((a, b) => b.count - a.count)[0]
  return match && match.count >= 2 ? match.move : null
}

export async function syncExperience(kind: string, board: unknown, move: LearnedMove) {
  try {
    await fetch('/api/games/experience', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kind, key: experienceKey(kind, board), move }),
      keepalive: true,
    })
  } catch {
    // Local learning remains available when the shared endpoint is offline.
  }
}

export async function sharedLearnedMove(kind: string, board: unknown): Promise<LearnedMove | null> {
  try {
    const query = new URLSearchParams({ kind, key: experienceKey(kind, board) })
    const response = await fetch(`/api/games/experience?${query}`)
    if (!response.ok) return null
    const data = (await response.json()) as { move?: LearnedMove | null; count?: number }
    return (data.count || 0) >= 2 ? data.move || null : null
  } catch {
    return null
  }
}
