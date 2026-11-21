import {
  battle,
  canMove,
  canPlaceJunqi,
  headquarters,
  legalJunqiMoves,
  rankNames,
  type JPiece,
  type JSide,
  type JState,
} from './junqi'

export type JBelief = { side: JSide; candidates: number[]; moved: boolean }
export type JPublicMove = { id: number; side: JSide; from: number; to: number }
export type JKnowledge = {
  views: Record<JSide, Record<number, JBelief>>
  revealedSides: JSide[]
  moves: JPublicMove[]
}
export type JObservedPiece = {
  id: number
  side: JSide
  rank: number | null
  candidates: readonly number[]
}
export type JObservation = {
  observer: JSide
  board: (JObservedPiece | null)[]
  remainingRanks: number[]
  moves: readonly JPublicMove[]
  finished: boolean
}
export type JSharedMarks = Readonly<Record<number, number>>
const counts = [3, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 2]
const values = [5, 9, 4, 5, 6, 7, 8, 10, 13, 18, 120, 10]
function pieceFor(rank: number, side: JSide, id: number): JPiece {
  return { rank, side, id, flag: rank === 10, mine: rank === 0, bomb: rank === 11 }
}

/** Initial beliefs use occupied stations and legal setup constraints, never enemy ranks. */
export function createJunqiKnowledge(state: JState): JKnowledge {
  const views: JKnowledge['views'] = { 1: {}, '-1': {} }
  state.board.forEach((piece, at) => {
    if (!piece) return
    const observer = -piece.side as JSide
    views[observer][piece.id] = {
      side: piece.side,
      moved: false,
      candidates: rankNames
        .map((_, rank) => rank)
        .filter((rank) => canPlaceJunqi(pieceFor(rank, piece.side, piece.id), at)),
    }
  })
  return { views, revealedSides: [], moves: [] }
}
function cloneKnowledge(knowledge: JKnowledge): JKnowledge {
  const copy = (side: JSide) =>
    Object.fromEntries(
      Object.entries(knowledge.views[side]).map(([id, belief]) => [
        id,
        { ...belief, candidates: [...belief.candidates] },
      ]),
    )
  return {
    views: { 1: copy(1), '-1': copy(-1) },
    revealedSides: [...knowledge.revealedSides],
    moves: [...knowledge.moves],
  }
}
function remainingRanks(view: Record<number, JBelief>) {
  const remaining = [...counts]
  // Keep captured pieces in the deduction ledger; their known ranks consume inventory too.
  Object.values(view).forEach((belief) => {
    if (belief.candidates.length === 1) remaining[belief.candidates[0]!]!--
  })
  return remaining.map((count) => Math.max(0, count))
}
function propagate(view: Record<number, JBelief>) {
  for (let pass = 0; pass < 25; pass++) {
    const remaining = remainingRanks(view)
    let changed = false
    for (const belief of Object.values(view)) {
      if (belief.candidates.length < 2) continue
      const possible = belief.candidates.filter((rank) => remaining[rank]! > 0)
      if (possible.length && possible.length < belief.candidates.length) {
        belief.candidates = possible
        changed = true
      }
    }
    if (!changed) break
  }
}
function constrain(belief: JBelief | undefined, matches: (rank: number) => boolean) {
  if (!belief) return
  const possible = belief.candidates.filter(matches)
  if (possible.length) belief.candidates = possible
}

/** The referee may inspect the combatants; it publishes verdicts and commander-loss events. */
export function advanceJunqiKnowledge(
  knowledge: JKnowledge,
  before: JState,
  after: JState,
  from: number,
  to: number,
): JKnowledge {
  const next = cloneKnowledge(knowledge)
  const attacker = before.board[from]!,
    defender = before.board[to]
  const opponent = -attacker.side as JSide
  const mover = next.views[opponent][attacker.id]
  if (mover) {
    mover.moved = true
    constrain(mover, (rank) => rank !== 0 && rank !== 10)
    const publicBoard = before.board.map((piece) =>
      piece ? pieceFor(5, piece.side, piece.id) : null,
    )
    if (
      !canMove({ board: publicBoard, turn: attacker.side, selected: null, finished: 0 }, from, to)
    )
      constrain(mover, (rank) => rank === 1)
  }
  if (defender) {
    const verdict = battle(attacker, defender)
    // Each observer combines only their own combatant's rank with the referee's verdict.
    constrain(
      next.views[attacker.side][defender.id],
      (rank) => battle(attacker, pieceFor(rank, defender.side, defender.id)) === verdict,
    )
    constrain(
      next.views[defender.side][attacker.id],
      (rank) => battle(pieceFor(rank, attacker.side, attacker.id), defender) === verdict,
    )
  }
  for (const piece of [attacker, defender]) {
    if (!piece || piece.rank !== 9 || after.board.some((alive) => alive?.id === piece.id)) continue
    if (!next.revealedSides.includes(piece.side)) next.revealedSides.push(piece.side)
    const view = next.views[-piece.side as JSide]
    if (view[piece.id]) view[piece.id]!.candidates = [9]
    const flag = after.board.find((alive) => alive?.side === piece.side && alive.flag)
    if (flag && view[flag.id]) view[flag.id]!.candidates = [10]
  }
  next.moves = [...next.moves.slice(-11), { id: attacker.id, side: attacker.side, from, to }]
  propagate(next.views[1])
  propagate(next.views[-1])
  return next
}

/** This is the entire input boundary for the challenge opponent. Unknown ranks stay null. */
export function observeJunqi(state: JState, observer: JSide, knowledge: JKnowledge): JObservation {
  const view = knowledge.views[observer]
  return {
    observer,
    finished: !!state.finished,
    moves: knowledge.moves.map((move) => ({ ...move })),
    remainingRanks: remainingRanks(view),
    board: state.board.map((piece) => {
      if (!piece) return null
      if (piece.side === observer || state.finished)
        return { id: piece.id, side: piece.side, rank: piece.rank, candidates: [piece.rank] }
      const candidates = [...(view[piece.id]?.candidates ?? rankNames.map((_, rank) => rank))]
      return {
        id: piece.id,
        side: piece.side,
        rank: candidates.length === 1 ? candidates[0]! : null,
        candidates,
      }
    }),
  }
}
export function guessJunqiPiece(observation: JObservation, id: number) {
  const piece = observation.board.find((piece) => piece?.id === id)
  if (!piece)
    return {
      rank: null,
      certain: false,
      candidates: [] as number[],
      distribution: [] as { rank: number; weight: number }[],
    }
  const weights = piece.candidates.map((rank) => ({
    rank,
    weight: piece.candidates.length === 1 ? 1 : (observation.remainingRanks[rank] ?? 1),
  }))
  const sum = weights.reduce((sum, candidate) => sum + candidate.weight, 0)
  const total = sum || weights.length
  const distribution = weights
    .map((candidate) => ({
      rank: candidate.rank,
      weight: (sum ? candidate.weight : 1) / total,
    }))
    .sort((a, b) => b.weight - a.weight || a.rank - b.rank)
  const tied =
    distribution.length > 1 && Math.abs(distribution[0]!.weight - distribution[1]!.weight) < 0.001
  return {
    rank: tied ? null : (distribution[0]?.rank ?? null),
    certain: piece.candidates.length === 1,
    candidates: [...piece.candidates],
    distribution,
  }
}
function distanceToFlag(at: number, enemy: JSide) {
  return Math.min(
    ...[...headquarters]
      .filter((hq) => (enemy === 1 ? hq >= 30 : hq < 30))
      .map(
        (hq) => Math.abs(Math.floor(at / 5) - Math.floor(hq / 5)) + Math.abs((at % 5) - (hq % 5)),
      ),
  )
}

/** Moves and scores come from the observation and explicitly shared guesses, not JState. */
export function chooseJunqiChallenge(
  observation: JObservation,
  sharedMarks: JSharedMarks = {},
): [number, number] | null {
  if (observation.finished) return null
  const publicState: JState = {
    board: observation.board.map((piece) =>
      piece ? pieceFor(piece.rank ?? 5, piece.side, piece.id) : null,
    ),
    turn: observation.observer,
    selected: null,
    finished: 0,
  }
  const moves = legalJunqiMoves(publicState)
  let best: [number, number] | null = null,
    bestScore = -Infinity
  const enemy = -observation.observer as JSide
  for (const move of moves) {
    const [from, to] = move,
      own = publicState.board[from]!,
      target = observation.board[to]
    const progress = distanceToFlag(from, enemy) - distanceToFlag(to, enemy)
    let score = progress * 1.4 - distanceToFlag(to, enemy) * 0.08
    const recent = observation.moves.filter(
      (record) => record.side === own.side && record.id === own.id,
    )
    const last = recent.at(-1)
    if (last && last.from === to && last.to === from) score -= 5
    score -= recent.filter((record) => record.from === from && record.to === to).length * 2
    if (target) {
      score += guessJunqiPiece(observation, target.id).distribution.reduce((expected, guess) => {
        const result = battle(own, pieceFor(guess.rank, target.side, target.id))
        const value = values[guess.rank]!
        return (
          expected +
          guess.weight *
            (result === 'win'
              ? value + 3
              : result === 'both'
                ? value - values[own.rank]!
                : -values[own.rank]! - 3)
        )
      }, 0)
    }
    // Shared notes reveal what the human thinks of this computer piece, never human ranks.
    const claimed = sharedMarks[own.id]
    if (claimed !== undefined && claimed >= 0 && claimed < rankNames.length) {
      if ((claimed === 0 || claimed === 10) && claimed !== own.rank) score -= 4
      else {
        const bluff = Math.max(-2, Math.min(3, (values[claimed]! - values[own.rank]!) / 8))
        score += target ? -Math.max(0, bluff) * 0.8 : bluff * 0.7
      }
    }
    if (score > bestScore) {
      bestScore = score
      best = move
    }
  }
  return best
}
