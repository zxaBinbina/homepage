// Positive pieces are red (the player), negative pieces are black (the computer).
export type ChessMove = { from: number; to: number }
export const chessNames = ['空位', '帅', '仕', '相', '马', '车', '炮', '兵']
export const blackNames = ['空位', '将', '士', '象', '马', '车', '炮', '卒']
export function chessName(piece: number) {
  return (piece > 0 ? '红' : '黑') + (piece > 0 ? chessNames : blackNames)[Math.abs(piece)]
}
export function newXiangqi() {
  const board = Array<number>(90).fill(0)
  const back = [5, 4, 3, 2, 1, 2, 3, 4, 5]
  back.forEach((piece, x) => {
    board[x] = -piece
    board[81 + x] = piece
  })
  for (const x of [1, 7]) {
    board[18 + x] = -6
    board[63 + x] = 6
  }
  for (const x of [0, 2, 4, 6, 8]) {
    board[27 + x] = -7
    board[54 + x] = 7
  }
  return board
}
export function applyChessMove(board: number[], move: ChessMove) {
  const next = [...board]
  next[move.to] = next[move.from]!
  next[move.from] = 0
  return next
}
function pseudoMoves(board: number[], from: number) {
  const piece = board[from]!,
    side = Math.sign(piece),
    kind = Math.abs(piece)
  const x = from % 9,
    y = Math.floor(from / 9),
    targets: number[] = []
  const add = (a: number, b: number) => {
    if (a >= 0 && a < 9 && b >= 0 && b < 10 && Math.sign(board[b * 9 + a]!) !== side)
      targets.push(b * 9 + a)
  }
  const palace = (a: number, b: number) =>
    a >= 3 && a <= 5 && (side > 0 ? b >= 7 && b <= 9 : b >= 0 && b <= 2)
  if (kind === 1 || kind === 2) {
    const steps =
      kind === 1
        ? [
            [0, 1],
            [0, -1],
            [1, 0],
            [-1, 0],
          ]
        : [
            [1, 1],
            [1, -1],
            [-1, 1],
            [-1, -1],
          ]
    for (const [dx, dy] of steps) if (palace(x + dx!, y + dy!)) add(x + dx!, y + dy!)
    if (kind === 1)
      for (const sign of [-1, 1]) {
        for (let b = y + sign; b >= 0 && b < 10; b += sign) {
          const target = board[b * 9 + x]
          if (target) {
            if (target === -side) add(x, b)
            break
          }
        }
      }
  } else if (kind === 3) {
    for (const dx of [-2, 2])
      for (const dy of [-2, 2]) {
        const a = x + dx,
          b = y + dy
        if ((side > 0 ? b >= 5 : b <= 4) && !board[(y + dy / 2) * 9 + x + dx / 2]) add(a, b)
      }
  } else if (kind === 4) {
    for (const [dx, dy] of [
      [1, 2],
      [-1, 2],
      [1, -2],
      [-1, -2],
      [2, 1],
      [2, -1],
      [-2, 1],
      [-2, -1],
    ] as const) {
      const legX = x + (Math.abs(dx) === 2 ? Math.sign(dx) : 0)
      const legY = y + (Math.abs(dy) === 2 ? Math.sign(dy) : 0)
      if (!board[legY * 9 + legX]) add(x + dx, y + dy)
    }
  } else if (kind === 5 || kind === 6) {
    for (const [dx, dy] of [
      [0, 1],
      [0, -1],
      [1, 0],
      [-1, 0],
    ] as const) {
      let screen = false
      for (let a = x + dx, b = y + dy; a >= 0 && a < 9 && b >= 0 && b < 10; a += dx, b += dy) {
        const target = board[b * 9 + a]
        if (kind === 5) {
          add(a, b)
          if (target) break
        } else if (!screen) {
          if (!target) add(a, b)
          else screen = true
        } else if (target) {
          add(a, b)
          break
        }
      }
    }
  } else if (kind === 7) {
    add(x, y - side)
    if (side > 0 ? y <= 4 : y >= 5) {
      add(x - 1, y)
      add(x + 1, y)
    }
  }
  return targets
}
export function inCheck(board: number[], side: number) {
  const king = board.indexOf(side)
  return (
    king < 0 ||
    board.some((piece, i) => Math.sign(piece) === -side && pseudoMoves(board, i).includes(king))
  )
}
export function legalChessMoves(board: number[], side: number): ChessMove[] {
  if (!board.includes(side) || !board.includes(-side)) return []
  return board.flatMap((piece, from) =>
    Math.sign(piece) !== side
      ? []
      : pseudoMoves(board, from)
          .map((to) => ({ from, to }))
          .filter((move) => !inCheck(applyChessMove(board, move), side)),
  )
}
export function chessOutcome(board: number[], turn: number): number {
  if (!board.includes(1)) return -1
  if (!board.includes(-1)) return 1
  return legalChessMoves(board, turn).length ? 0 : -turn
}
const values = [0, 100000, 120, 120, 310, 650, 350, 80]
function evaluate(board: number[], side: number) {
  return (
    board.reduce((score, piece, i) => {
      const kind = Math.abs(piece),
        s = Math.sign(piece),
        y = Math.floor(i / 9)
      const advanced = s > 0 ? 9 - y : y
      return (
        score +
        s *
          (values[kind]! +
            (kind === 7
              ? advanced * 12 + (advanced >= 5 ? 45 : 0)
              : kind === 4 || kind === 6
                ? (4 - Math.abs((i % 9) - 4)) * 5
                : 0))
      )
    }, 0) * side
  )
}
export function chooseXiangqi(
  board: number[],
  side = -1,
  difficulty = 1,
  budget = difficulty ? 850 : 200,
): ChessMove | null {
  const end = performance.now() + budget,
    timeout = Symbol('deadline')
  const ordered = (position: number[], turn: number) =>
    legalChessMoves(position, turn).sort(
      (a, b) =>
        values[Math.abs(position[b.to]!)]! * 10 -
        values[Math.abs(position[b.from]!)]! -
        (values[Math.abs(position[a.to]!)]! * 10 - values[Math.abs(position[a.from]!)]!),
    )
  const initial = ordered(board, side)
  if (!initial.length) return null
  let best = initial[0]!
  function search(
    position: number[],
    turn: number,
    depth: number,
    alpha: number,
    beta: number,
  ): number {
    if (performance.now() > end) throw timeout
    if (!position.includes(turn)) return -1e7 - depth
    if (!position.includes(-turn)) return 1e7 + depth
    const moves = ordered(position, turn)
    if (!moves.length) return -1e7 - depth
    if (!depth) return evaluate(position, turn)
    let score = -Infinity
    for (const move of moves) {
      score = Math.max(
        score,
        -search(applyChessMove(position, move), -turn, depth - 1, -beta, -alpha),
      )
      alpha = Math.max(alpha, score)
      if (alpha >= beta) break
    }
    return score
  }
  for (let depth = 1; depth <= (difficulty ? 4 : 2); depth++) {
    let candidate = best,
      score = -Infinity
    const moves = [best, ...initial.filter((m) => m.from !== best.from || m.to !== best.to)]
    try {
      for (const move of moves) {
        const value = -search(applyChessMove(board, move), -side, depth - 1, -Infinity, -score)
        if (value > score) {
          score = value
          candidate = move
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
