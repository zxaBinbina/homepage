import { chooseGomoku } from './gomoku'
import { chooseXiangqi } from './xiangqi'

self.onmessage = (
  event: MessageEvent<{
    kind: 'gomoku' | 'xiangqi'
    board: number[]
    difficulty: number
    side: number
  }>,
) => {
  const { kind, board, difficulty, side } = event.data
  self.postMessage(
    kind === 'gomoku'
      ? chooseGomoku(board, side, difficulty)
      : chooseXiangqi(board, side, difficulty),
  )
}
