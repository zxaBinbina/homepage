import { chooseGomoku } from './gomoku'
import { chooseXiangqi } from './xiangqi'

self.onmessage = (
  event: MessageEvent<{ kind: 'gomoku' | 'xiangqi'; board: number[]; difficulty: number }>,
) => {
  const { kind, board, difficulty } = event.data
  self.postMessage(
    kind === 'gomoku' ? chooseGomoku(board, -1, difficulty) : chooseXiangqi(board, -1, difficulty),
  )
}
