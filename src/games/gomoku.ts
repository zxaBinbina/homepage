export const gomokuSize = 15
export type Stone = 0 | 1 | -1
export const gomokuDirections = [
  [1, 0],
  [0, 1],
  [1, 1],
  [1, -1],
] as const
function index(x: number, y: number) {
  return y * 15 + x
}
function inside(x: number, y: number) {
  return x >= 0 && y >= 0 && x < 15 && y < 15
}
export function winningLine(board: number[], at: number): number[] {
  const side = board[at]
  if (!side) return []
  const x = at % 15,
    y = Math.floor(at / 15)
  for (const [dx, dy] of gomokuDirections) {
    const line = [at]
    for (const sign of [-1, 1]) {
      let a = x + dx * sign,
        b = y + dy * sign
      while (inside(a, b) && board[index(a, b)] === side) {
        line.push(index(a, b))
        a += dx * sign
        b += dy * sign
      }
    }
    if (line.length >= 5) return line
  }
  return []
}
export function gomokuCandidates(board: number[]) {
  const cells = new Set<number>()
  board.forEach((stone, i) => {
    if (!stone) return
    for (let dy = -2; dy <= 2; dy++)
      for (let dx = -2; dx <= 2; dx++) {
        const x = (i % 15) + dx,
          y = Math.floor(i / 15) + dy
        if (inside(x, y) && !board[index(x, y)]) cells.add(index(x, y))
      }
  })
  return cells.size ? [...cells] : board.every((v) => !v) ? [112] : []
}
/** Score open and broken lines through an empty point; both colours use the same rules. */
export function pointScore(board: number[], at: number, side: number) {
  let total = 0
  const x = at % 15,
    y = Math.floor(at / 15)
  for (const [dx, dy] of gomokuDirections) {
    let line = ''
    for (let d = -5; d <= 5; d++) {
      const a = x + d * dx,
        b = y + d * dy
      line +=
        d === 0
          ? 'X'
          : !inside(a, b) || board[index(a, b)] === -side
            ? '#'
            : board[index(a, b)] === side
              ? 'X'
              : '.'
    }
    if (line.includes('XXXXX')) total += 1e7
    else if (line.includes('.XXXX.')) total += 100000
    else if (/XXXX\.|\.XXXX|XXX\.X|XX\.XX|X\.XXX/.test(line)) total += 10000
    else if (/\.XXX\.|\.XX\.X\.|\.X\.XX\./.test(line)) total += 2500
    else if (/XXX|XX\.X|X\.XX/.test(line)) total += 150
    else if (/\.XX\.|\.X\.X\./.test(line)) total += 80
    else total += 5
  }
  return total
}
export function chooseGomoku(
  board: number[],
  side = -1,
  difficulty = 1,
  budget = difficulty ? 650 : 180,
): number | null {
  const copy = [...board],
    end = performance.now() + budget
  const candidates = gomokuCandidates(copy)
  if (!candidates.length) return null
  function ordered(turn: number) {
    return gomokuCandidates(copy)
      .map((at) => ({ at, own: pointScore(copy, at, turn), opponent: pointScore(copy, at, -turn) }))
      .sort((a, b) => b.own + b.opponent * 1.05 - (a.own + a.opponent * 1.05))
  }
  const initial = ordered(side)
  const win = initial.find((m) => m.own >= 1e7)
  if (win) return win.at
  const block = initial.find((m) => m.opponent >= 1e7)
  if (block) return block.at
  let best = initial[0]!.at
  const timeout = Symbol('deadline')
  function search(depth: number, turn: number, alpha: number, beta: number): number {
    if (performance.now() > end) throw timeout
    const moves = ordered(turn)
    if (!moves.length) return 0
    if (moves.some((m) => m.own >= 1e7)) return 1e8 + depth
    if (!depth)
      return Math.max(...moves.map((m) => m.own)) - Math.max(...moves.map((m) => m.opponent)) * 1.1
    let value = -Infinity
    for (const { at } of moves.slice(0, 10)) {
      copy[at] = turn
      let score: number
      try {
        score = -search(depth - 1, -turn, -beta, -alpha)
      } finally {
        copy[at] = 0
      }
      value = Math.max(value, score)
      alpha = Math.max(alpha, score)
      if (alpha >= beta) break
    }
    return value
  }
  for (let depth = 1; depth <= (difficulty ? 3 : 1); depth++) {
    let candidate = best,
      value = -Infinity
    try {
      for (const { at } of initial.slice(0, 14)) {
        copy[at] = side
        let score: number
        try {
          score = -search(depth - 1, -side, -Infinity, -value)
        } finally {
          copy[at] = 0
        }
        if (score > value) {
          value = score
          candidate = at
        }
      }
      best = candidate
    } catch (error) {
      if (error !== timeout) throw error
      break
    }
  }
  return best
}
