export const goSize = 9
export const goKomi = 6.5
export type GoState = {
  board: number[]
  turn: number
  positions: string[]
  passes: number
  captures: [number, number]
  ply: number
  last: number | null
}
export function newGo(): GoState {
  const board = Array<number>(goSize * goSize).fill(0)
  return {
    board,
    turn: 1,
    positions: [board.join(',')],
    passes: 0,
    captures: [0, 0],
    ply: 0,
    last: null,
  }
}
export function goNeighbors(at: number) {
  const x = at % goSize,
    y = Math.floor(at / goSize)
  return [
    x > 0 ? at - 1 : -1,
    x < goSize - 1 ? at + 1 : -1,
    y > 0 ? at - goSize : -1,
    y < goSize - 1 ? at + goSize : -1,
  ].filter((n) => n >= 0)
}
export function goGroup(board: number[], at: number) {
  const stones = new Set<number>(),
    liberties = new Set<number>()
  if (!board[at]) return { stones: [], liberties: [] }
  const stack = [at]
  while (stack.length) {
    const n = stack.pop()!
    if (stones.has(n)) continue
    stones.add(n)
    for (const neighbor of goNeighbors(n)) {
      if (!board[neighbor]) liberties.add(neighbor)
      else if (board[neighbor] === board[at] && !stones.has(neighbor)) stack.push(neighbor)
    }
  }
  return { stones: [...stones], liberties: [...liberties] }
}
/** Positional superko: a placement may never repeat any earlier board, passes are exempt. */
export function playGo(
  state: GoState,
  at: number,
): { state: GoState; captured: number[] } | { error: string } {
  if (state.passes >= 2) return { error: '双方已停一手，请先完成数子或继续对局。' }
  if (!Number.isInteger(at) || at < 0 || at >= state.board.length || state.board[at])
    return { error: '请在空交点落子。' }
  const board = [...state.board],
    captured: number[] = []
  board[at] = state.turn
  for (const neighbor of goNeighbors(at)) {
    if (board[neighbor] !== -state.turn) continue
    const group = goGroup(board, neighbor)
    if (!group.liberties.length) {
      captured.push(...group.stones)
      group.stones.forEach((n) => {
        board[n] = 0
      })
    }
  }
  if (!goGroup(board, at).liberties.length)
    return { error: '这里是自杀着：落下后没有气，也不能提子。' }
  const key = board.join(',')
  if (state.positions.includes(key))
    return { error: '这里会重复先前的局面，请先在别处落子（劫争）。' }
  const captures: [number, number] = [...state.captures]
  captures[state.turn === 1 ? 0 : 1] += captured.length
  return {
    state: {
      board,
      turn: -state.turn,
      positions: [...state.positions, key],
      passes: 0,
      captures,
      ply: state.ply + 1,
      last: at,
    },
    captured,
  }
}
export function passGo(state: GoState): GoState {
  return state.passes >= 2
    ? state
    : { ...state, turn: -state.turn, passes: state.passes + 1, ply: state.ply + 1, last: null }
}
/** Chinese-style area: living stones + exclusively surrounded empties; neutral regions count for neither. */
export function scoreGo(board: number[], dead: number[] = []) {
  const clean = [...board]
  dead.forEach((n) => {
    clean[n] = 0
  })
  const ownership = [...clean],
    seen = new Set<number>()
  for (let at = 0; at < clean.length; at++) {
    if (clean[at] || seen.has(at)) continue
    const region: number[] = [],
      borders = new Set<number>(),
      stack = [at]
    while (stack.length) {
      const n = stack.pop()!
      if (seen.has(n)) continue
      seen.add(n)
      region.push(n)
      for (const neighbor of goNeighbors(n)) {
        if (clean[neighbor]) borders.add(clean[neighbor]!)
        else if (!seen.has(neighbor)) stack.push(neighbor)
      }
    }
    const owner = borders.size === 1 ? [...borders][0]! : 0
    region.forEach((n) => {
      ownership[n] = owner
    })
  }
  const black = ownership.filter((n) => n === 1).length
  const white = ownership.filter((n) => n === -1).length + goKomi
  return {
    black,
    white,
    ownership,
    winner: black > white ? 1 : -1,
    margin: Math.abs(black - white),
  }
}
function isEye(board: number[], at: number, side: number) {
  if (!goNeighbors(at).every((n) => board[n] === side)) return false
  const x = at % goSize,
    y = Math.floor(at / goSize)
  const diagonals = [-1, 1]
    .flatMap((dx) => [-1, 1].map((dy) => [x + dx, y + dy]))
    .filter(([a, b]) => a! >= 0 && a! < goSize && b! >= 0 && b! < goSize)
  const opponents = diagonals.filter(([a, b]) => board[b! * goSize + a!] === -side).length
  return opponents <= (diagonals.length === 4 ? 1 : 0)
}
function candidates(state: GoState) {
  const result: { at: number; state: GoState; value: number; tactical: boolean }[] = []
  const ownAtari = new Set<number>(),
    enemyAtari = new Set<number>(),
    seen = new Set<number>()
  state.board.forEach((stone, at) => {
    if (!stone || seen.has(at)) return
    const group = goGroup(state.board, at)
    group.stones.forEach((n) => seen.add(n))
    if (group.liberties.length === 1)
      (stone === state.turn ? ownAtari : enemyAtari).add(group.liberties[0]!)
  })
  for (let at = 0; at < state.board.length; at++) {
    if (state.board[at] || isEye(state.board, at, state.turn)) continue
    const move = playGo(state, at)
    if ('error' in move) continue
    const group = goGroup(move.state.board, at)
    const capture = move.captured.length
    if (group.liberties.length === 1 && !capture) continue
    const x = at % goSize,
      y = Math.floor(at / goSize)
    const edge = Math.min(x, y, goSize - 1 - x, goSize - 1 - y)
    const nearby = state.board.reduce(
      (sum, stone, n) =>
        sum +
        (stone && Math.abs((n % goSize) - x) + Math.abs(Math.floor(n / goSize) - y) <= 2 ? 1 : 0),
      0,
    )
    const saving = ownAtari.has(at) && group.liberties.length > 1
    const value =
      capture * 45 +
      (saving ? 38 : 0) +
      (enemyAtari.has(at) ? 12 : 0) +
      Math.min(group.liberties.length, 5) * 2 +
      (edge === 2 ? 6 : edge === 0 ? -5 : 2) +
      (nearby ? 4 : 0) -
      Math.abs(x - 4) * 0.12 -
      Math.abs(y - 4) * 0.1
    result.push({ at, state: move.state, value, tactical: capture > 0 || saving })
  }
  return result.sort((a, b) => b.value - a.value)
}
/** Small local tactical search, deliberately bounded; no remote engine or model. -1 means pass. */
export function chooseGo(state: GoState, difficulty = 0): number {
  if (state.passes >= 2) return -1
  const moves = candidates(state)
  if (!moves.length) return -1
  // Accept a proposed ending unless there is still an immediate capture or rescue.
  if (state.passes && !moves.some((m) => m.tactical)) return -1
  if (!difficulty) return moves[0]!.at
  const deadline = Date.now() + 650
  let best = moves[0]!,
    value = -Infinity
  for (const move of moves.slice(0, 12)) {
    if (Date.now() > deadline) break
    const reply = candidates(move.state)[0]
    const score = move.value - (reply?.value ?? 0) * 0.65
    if (score > value) {
      value = score
      best = move
    }
  }
  return best.at
}
