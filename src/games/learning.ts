import type { ChessState, ChessTurn } from './chess'
import type { GoState } from './go'

type LearnedMove = number | ChessTurn | { from: number; to: number }
type Entry = { key: string; move: LearnedMove; wins: number; draws: number; losses: number }
type Observation = { key: string; move: LearnedMove; side: number }
const storageKey = 'homepage-game-experience-v2'
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
export function experienceKey(kind: string, board: unknown, side = 0) {
  if (kind === 'chess') return JSON.stringify({ kind, fen: (board as ChessState).fen, side })
  if (kind === 'go') {
    const state = board as GoState
    return JSON.stringify({
      kind,
      board: state.board,
      turn: state.turn,
      passes: state.passes,
      side,
    })
  }
  return JSON.stringify({ kind, board, side })
}
const pending: Record<string, Observation[]> = {}
export function recordExperienceTurn(
  kind: string,
  board: unknown,
  side: number,
  move: LearnedMove,
) {
  ;(pending[kind] ||= []).push({ key: experienceKey(kind, board, side), move, side })
}
export function clearExperience(kind: string) {
  pending[kind] = []
}
export async function finishExperience(kind: string, winner: number) {
  const observations = pending[kind] || []
  pending[kind] = []
  const scored = observations.map(({ key, move, side }) => ({
    key,
    move,
    result: winner === 0 ? 0 : winner === side ? 1 : -1,
  }))
  const all = read(),
    entries = all[kind] || []
  for (const item of scored) {
    const entry = entries.find(
      (candidate) =>
        candidate.key === item.key && JSON.stringify(candidate.move) === JSON.stringify(item.move),
    )
    if (entry) {
      if (item.result > 0) entry.wins++
      else if (item.result < 0) entry.losses++
      else entry.draws++
    } else {
      entries.push({
        key: item.key,
        move: item.move,
        wins: +(item.result > 0),
        draws: +(item.result === 0),
        losses: +(item.result < 0),
      })
    }
  }
  all[kind] = entries.slice(-maxEntries)
  write(all)
  try {
    await fetch('/api/games/experience', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kind, observations: scored }),
      keepalive: true,
    })
  } catch {
    // Local learning remains available when the shared endpoint is offline.
  }
}

export async function sharedLearnedMove(
  kind: string,
  board: unknown,
  side: number,
): Promise<LearnedMove | null> {
  try {
    const query = new URLSearchParams({ kind, key: experienceKey(kind, board, side) })
    const response = await fetch(`/api/games/experience?${query}`)
    if (!response.ok) return null
    const data = (await response.json()) as { move?: LearnedMove | null; samples?: number }
    return (data.samples || 0) >= 20 ? data.move || null : null
  } catch {
    return null
  }
}
