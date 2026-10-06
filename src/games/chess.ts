import { Chess, type Move, type PieceSymbol, type Square } from 'chess.js'

export { Chess }
export type ChessTurn = { from: Square; to: Square; promotion?: string }
export type ChessState = { fen: string; positions: string[]; ply: number; last: ChessTurn | null }
export const pieceNames: Record<PieceSymbol, string> = {
  k: '王',
  q: '后',
  r: '车',
  b: '象',
  n: '马',
  p: '兵',
}
export function squareAt(index: number): Square {
  return `${'abcdefgh'[index % 8]}${8 - Math.floor(index / 8)}` as Square
}
export function squareIndex(square: string) {
  return (8 - Number(square[1])) * 8 + 'abcdefgh'.indexOf(square[0]!)
}
export function chessPosition(fen: string) {
  return fen.split(' ').slice(0, 4).join(' ')
}
export function newChess(fen = new Chess().fen()): ChessState {
  return { fen, positions: [chessPosition(fen)], ply: 0, last: null }
}
export function playChess(state: ChessState, move: ChessTurn): ChessState | null {
  const game = new Chess(state.fen)
  try {
    game.move(move)
    return {
      fen: game.fen(),
      positions: [...state.positions, chessPosition(game.fen())],
      ply: state.ply + 1,
      last: move,
    }
  } catch {
    return null
  }
}
export function chessResult(state: ChessState) {
  const game = new Chess(state.fen)
  if (game.isCheckmate()) return { winner: game.turn() === 'w' ? -1 : 1, reason: '将死' }
  if (game.isStalemate()) return { winner: 0, reason: '无子可动，逼和' }
  if (game.isInsufficientMaterial()) return { winner: 0, reason: '双方子力不足以将死' }
  if (Number(state.fen.split(' ')[4]) >= 100)
    return { winner: 0, reason: '连续 50 回合未动兵或吃子' }
  if (state.positions.filter((p) => p === chessPosition(state.fen)).length >= 3)
    return { winner: 0, reason: '同一局面出现三次' }
  return null
}
const values: Record<PieceSymbol, number> = { p: 100, n: 320, b: 330, r: 500, q: 900, k: 0 }
function evaluate(game: Chess) {
  let score = 0
  for (const [row, rank] of game.board().entries())
    for (const [column, piece] of rank.entries()) {
      if (!piece) continue
      const advance = piece.color === 'w' ? 6 - row : row - 1
      const center = 7 - Math.abs(column - 3.5) - Math.abs(row - 3.5)
      const position =
        piece.type === 'p'
          ? advance * 9 + center * 2
          : piece.type === 'n' || piece.type === 'b'
            ? center * 10
            : piece.type === 'k'
              ? -center * 4
              : center * 2
      score += (values[piece.type] + position) * (piece.color === 'w' ? 1 : -1)
    }
  return score * (game.turn() === 'w' ? 1 : -1)
}
function priority(move: Move) {
  return (
    (move.captured ? values[move.captured] * 10 - values[move.piece] : 0) +
    (move.promotion ? values[move.promotion] : 0) +
    (move.san.includes('+') ? 35 : 0)
  )
}
/** Iterative alpha-beta keeps a completed legal fallback when the per-turn budget expires. */
export function chooseChess(state: ChessState, difficulty = 0): ChessTurn | null {
  if (chessResult(state)) return null
  const game = new Chess(state.fen),
    deadline = Date.now() + (difficulty ? 1100 : 350)
  const initial = game.moves({ verbose: true }).sort((a, b) => priority(b) - priority(a))
  let best = initial[0]
  if (!best) return null
  const timeout = Symbol('search budget')
  function search(depth: number, alpha: number, beta: number, ply: number): number {
    if (Date.now() >= deadline) throw timeout
    if (game.isCheckmate()) return -100000 + ply
    if (game.isDraw()) return 0
    if (!depth) return evaluate(game)
    let value = -Infinity
    for (const move of game.moves({ verbose: true }).sort((a, b) => priority(b) - priority(a))) {
      game.move(move)
      let score: number
      try {
        score = -search(depth - 1, -beta, -alpha, ply + 1)
      } finally {
        game.undo()
      }
      value = Math.max(value, score)
      alpha = Math.max(alpha, score)
      if (alpha >= beta) break
    }
    return value
  }
  for (let depth = 1; depth <= (difficulty ? 3 : 2); depth++) {
    let candidate = best,
      value = -Infinity
    try {
      for (const move of initial) {
        game.move(move)
        let score: number
        try {
          score = -search(depth - 1, -Infinity, -value, 1)
        } finally {
          game.undo()
        }
        if (score > value) {
          value = score
          candidate = move
        }
      }
      best = candidate
      initial.sort((a, b) => Number(b === best) - Number(a === best))
    } catch (error) {
      if (error !== timeout) throw error
      break
    }
  }
  return { from: best.from, to: best.to, ...(best.promotion ? { promotion: best.promotion } : {}) }
}
