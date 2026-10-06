import { chooseGomoku } from './gomoku'
import { chooseXiangqi } from './xiangqi'
import { chooseChess, type ChessState } from './chess'
import { chooseGo, type GoState } from './go'

self.onmessage = (
  event: MessageEvent<
    (
      | {
          kind: 'gomoku' | 'xiangqi'
          board: number[]
        }
      | { kind: 'chess'; board: ChessState }
      | { kind: 'go'; board: GoState }
    ) & { difficulty: number; side: number }
  >,
) => {
  const { difficulty, side } = event.data
  if (event.data.kind === 'chess') {
    self.postMessage(chooseChess(event.data.board, difficulty))
    return
  }
  if (event.data.kind === 'go') {
    self.postMessage(chooseGo(event.data.board, difficulty))
    return
  }
  const { kind, board } = event.data
  self.postMessage(
    kind === 'gomoku'
      ? chooseGomoku(board, side, difficulty)
      : chooseXiangqi(board, side, difficulty),
  )
}
