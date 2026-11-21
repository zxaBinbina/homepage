export type JSide = 1 | -1
export type JPiece = {
  side: JSide
  rank: number
  id: number
  flag?: boolean
  mine?: boolean
  bomb?: boolean
}
export type JState = {
  board: (JPiece | null)[]
  turn: JSide
  selected: number | null
  finished: 0 | JSide
}
export const rows = 12
export const cols = 5
export const rankNames = [
  '地雷',
  '工兵',
  '排长',
  '连长',
  '营长',
  '团长',
  '旅长',
  '师长',
  '军长',
  '司令',
  '军旗',
  '炸弹',
]
export const camps = new Set([11, 13, 17, 21, 23, 36, 38, 42, 46, 48])
export const headquarters = new Set([1, 3, 56, 58])
const pieces = [9, 8, 7, 7, 6, 6, 5, 5, 4, 4, 3, 3, 3, 2, 2, 2, 1, 1, 1, 0, 0, 0, 10, 11, 11]
const inside = (at: number) => Number.isInteger(at) && at >= 0 && at < rows * cols
export const rail = (at: number) => {
  if (!inside(at)) return false
  const r = Math.floor(at / cols),
    c = at % cols
  return r >= 1 && r <= 10 && (c === 0 || c === 4 || [1, 5, 6, 10].includes(r))
}
export function canPlaceJunqi(piece: JPiece, at: number) {
  if (!inside(at) || camps.has(at)) return false
  const r = Math.floor(at / cols)
  if (piece.side === 1 ? r < 6 : r > 5) return false
  if (piece.flag) return headquarters.has(at)
  if (piece.mine) return piece.side === 1 ? r >= 10 : r <= 1
  if (piece.bomb) return r !== (piece.side === 1 ? 6 : 5)
  return true
}
export function newJunqi(random = Math.random): JState {
  const board: (JPiece | null)[] = Array(rows * cols).fill(null)
  function shuffle<T>(values: T[]) {
    const result = [...values]
    for (let i = result.length - 1; i > 0; i--) {
      const j = Math.floor(random() * (i + 1))
      ;[result[i], result[j]] = [result[j]!, result[i]!]
    }
    return result
  }
  for (const side of [1, -1] as JSide[]) {
    const available = Array.from({ length: 30 }, (_, i) => i + (side === 1 ? 30 : 0)).filter(
      (at) => !camps.has(at),
    )
    const flagAt = shuffle([...headquarters].filter((at) => (side === 1 ? at >= 30 : at < 30)))[0]!
    const mines = shuffle(
      available.filter(
        (at) => at !== flagAt && canPlaceJunqi({ side, rank: 0, id: -1, mine: true }, at),
      ),
    ).slice(0, 3)
    const bombs = shuffle(
      available.filter(
        (at) =>
          at !== flagAt &&
          !mines.includes(at) &&
          canPlaceJunqi({ side, rank: 11, id: -1, bomb: true }, at),
      ),
    ).slice(0, 2)
    const reserved = new Map<number, number>([
      [flagAt, 10],
      ...mines.map((at) => [at, 0] as [number, number]),
      ...bombs.map((at) => [at, 11] as [number, number]),
    ])
    const rest = shuffle(pieces.filter((rank) => rank !== 0 && rank !== 10 && rank !== 11))
    shuffle(available.filter((at) => !reserved.has(at))).forEach((at, i) =>
      reserved.set(at, rest[i]!),
    )
    available.forEach((at, i) => {
      const rank = reserved.get(at)!
      board[at] = {
        side,
        rank,
        id: i + (side === 1 ? 0 : 25),
        flag: rank === 10,
        mine: rank === 0,
        bomb: rank === 11,
      }
    })
  }
  return { board, turn: 1, selected: null, finished: 0 }
}
export function swapJunqiSetup(state: JState, from: number, to: number): JState | null {
  const a = state.board[from],
    b = state.board[to]
  if (
    state.finished ||
    from === to ||
    !a ||
    !b ||
    a.side !== 1 ||
    b.side !== 1 ||
    !canPlaceJunqi(a, to) ||
    !canPlaceJunqi(b, from)
  )
    return null
  const board = [...state.board]
  ;[board[from], board[to]] = [b, a]
  return { ...state, board, selected: null }
}
export function location(at: number) {
  return `第 ${Math.floor(at / cols) + 1} 行，第 ${(at % cols) + 1} 列`
}
export function neighbors(at: number) {
  return [at - cols, at + cols, at - 1, at + 1].filter((next) => {
    if (!inside(next)) return false
    const r = Math.floor(at / cols),
      nr = Math.floor(next / cols)
    if (Math.abs((next % cols) - (at % cols)) + Math.abs(nr - r) !== 1) return false
    // Only the two outer bridges and the middle bridge cross the mountain boundary.
    return !(
      [r, nr].includes(5) &&
      [r, nr].includes(6) &&
      at % cols !== 0 &&
      at % cols !== 2 &&
      at % cols !== 4
    )
  })
}
function clearRail(board: (JPiece | null)[], from: number, to: number) {
  const sameRow = Math.floor(from / cols) === Math.floor(to / cols),
    sameCol = from % cols === to % cols
  if (!sameRow && !sameCol) return false
  const step = (from < to ? 1 : -1) * (sameRow ? 1 : cols)
  for (let at = from + step; at !== to + step; at += step)
    if (!rail(at) || !neighbors(at - step).includes(at) || (at !== to && board[at])) return false
  return true
}
function engineerPath(board: (JPiece | null)[], from: number, to: number) {
  const queue = [from],
    seen = new Set([from])
  for (let index = 0; index < queue.length; index++) {
    const at = queue[index]!
    if (at === to) return true
    for (const next of neighbors(at))
      if (rail(next) && !seen.has(next) && (!board[next] || next === to)) {
        seen.add(next)
        queue.push(next)
      }
  }
  return false
}
export function canMove(state: JState, from: number, to: number) {
  if (state.finished || !inside(from) || !inside(to)) return false
  const piece = state.board[from],
    target = state.board[to]
  if (
    !piece ||
    piece.side !== state.turn ||
    piece.flag ||
    piece.mine ||
    headquarters.has(from) ||
    target?.side === piece.side ||
    (target && camps.has(to))
  )
    return false
  const dr = Math.abs(Math.floor(from / cols) - Math.floor(to / cols)),
    dc = Math.abs((from % cols) - (to % cols))
  if (dr === 1 && dc === 1 && (camps.has(from) || camps.has(to))) return true
  if (rail(from) && rail(to))
    return (
      clearRail(state.board, from, to) ||
      (!piece.bomb && piece.rank === 1 && engineerPath(state.board, from, to))
    )
  return neighbors(from).includes(to)
}
export function battle(attacker: JPiece, defender: JPiece) {
  if (attacker.bomb || defender.bomb) return 'both'
  if (defender.flag) return 'win'
  if (defender.mine) return attacker.rank === 1 ? 'win' : 'lose'
  if (attacker.rank === defender.rank) return 'both'
  return attacker.rank > defender.rank ? 'win' : 'lose'
}
export function legalJunqiMoves(state: JState): [number, number][] {
  const moves: [number, number][] = []
  state.board.forEach((piece, from) => {
    if (piece?.side !== state.turn) return
    for (let to = 0; to < state.board.length; to++)
      if (canMove(state, from, to)) moves.push([from, to])
  })
  return moves
}
export function moveJunqi(state: JState, from: number, to: number): JState | null {
  if (!canMove(state, from, to)) return null
  const board = [...state.board],
    attacker = board[from]!,
    defender = board[to]
  board[from] = null
  const result = defender ? battle(attacker, defender) : 'win'
  board[to] = result === 'win' ? attacker : result === 'both' ? null : defender!
  const next: JState = { board, turn: state.turn === 1 ? -1 : 1, selected: null, finished: 0 }
  if (defender?.flag || !legalJunqiMoves(next).length) next.finished = state.turn
  return next
}
export function chooseJunqi(state: JState) {
  const moves = legalJunqiMoves(state)
  return (
    moves.find(([, to]) => state.board[to]?.flag) ??
    moves.find(
      ([from, to]) => state.board[to] && battle(state.board[from]!, state.board[to]!) === 'win',
    ) ??
    moves.find(
      ([from, to]) => state.board[to] && battle(state.board[from]!, state.board[to]!) === 'both',
    ) ??
    moves.find(([, to]) => !state.board[to]) ??
    moves[0] ??
    null
  )
}
