import { chooseGomoku } from './gomoku'
import { chooseXiangqi } from './xiangqi'
import { chooseChess, playChess, type ChessState, type ChessTurn } from './chess'
import { chooseGo, playGo, type GoState } from './go'
import { legalChessMoves } from './xiangqi'

self.onmessage = (
  event: MessageEvent<
    (
      | {
          kind: 'gomoku' | 'xiangqi'
          board: number[]
        }
      | { kind: 'chess'; board: ChessState }
      | { kind: 'go'; board: GoState }
    ) & {
      difficulty: number
      side: number
      learnedMove?:
        number | { from: string; to: string; promotion?: string } | { from: number; to: number }
    }
  >,
) => {
  const { difficulty, side, learnedMove } = event.data
  if (event.data.kind === 'chess') {
    const move =
      learnedMove &&
      typeof learnedMove === 'object' &&
      typeof learnedMove.from === 'string' &&
      playChess(event.data.board, learnedMove as ChessTurn)
        ? learnedMove
        : chooseChess(event.data.board, difficulty)
    self.postMessage(move)
    return
  }
  if (event.data.kind === 'go') {
    const move =
      typeof learnedMove === 'number' &&
      (learnedMove === -1 || !('error' in playGo(event.data.board, learnedMove)))
        ? learnedMove
        : chooseGo(event.data.board, difficulty)
    self.postMessage(move)
    return
  }
  const { kind, board } = event.data
  if (
    kind === 'xiangqi' &&
    learnedMove &&
    typeof learnedMove === 'object' &&
    'from' in learnedMove &&
    typeof learnedMove.from === 'number'
  ) {
    const valid = legalChessMoves(board, side).some(
      (move) => move.from === learnedMove.from && move.to === learnedMove.to,
    )
    if (valid) {
      self.postMessage(learnedMove)
      return
    }
  }
  if (typeof learnedMove === 'number') {
    const valid =
      kind === 'gomoku'
        ? Number.isInteger(learnedMove) &&
          learnedMove >= 0 &&
          learnedMove < 225 &&
          !board[learnedMove]
        : kind === 'xiangqi' && legalChessMoves(board, side).some((move) => move.to === learnedMove)
    if (valid) {
      self.postMessage(learnedMove)
      return
    }
  }
  self.postMessage(
    kind === 'gomoku'
      ? chooseGomoku(board, side, difficulty)
      : chooseXiangqi(board, side, difficulty),
  )
}
