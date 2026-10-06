export type SlidingSize = 3 | 4 | 5
export type SlidingState = { size: SlidingSize; board: number[]; moves: number }

export function slidingSolved(board: number[]) {
  return board.every((tile, i) => tile === (i + 1) % board.length)
}
export function slidingNeighbors(blank: number, size: number) {
  return [
    blank - size,
    blank + size,
    ...(blank % size ? [blank - 1] : []),
    ...(blank % size < size - 1 ? [blank + 1] : []),
  ].filter((i) => i >= 0 && i < size * size)
}
export function slidingSolvable(board: number[], size: number) {
  let inversions = 0
  for (let i = 0; i < board.length; i++)
    for (let j = i + 1; j < board.length; j++)
      if (board[i] && board[j] && board[i]! > board[j]!) inversions++
  return size % 2 === 1
    ? inversions % 2 === 0
    : (inversions + size - Math.floor(board.indexOf(0) / size)) % 2 === 1
}
export function newSliding(size: SlidingSize = 4, random = Math.random): SlidingState {
  const board = Array.from({ length: size * size }, (_, i) => (i + 1) % (size * size))
  for (let i = board.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1))
    ;[board[i], board[j]] = [board[j]!, board[i]!]
  }
  if (!slidingSolvable(board, size)) {
    const [a, b] = board.map((tile, i) => (tile ? i : -1)).filter((i) => i >= 0)
    ;[board[a!], board[b!]] = [board[b!]!, board[a!]!]
  }
  if (slidingSolved(board))
    [board[board.length - 2], board[board.length - 1]] = [0, board.length - 1]
  return { size, board, moves: 0 }
}
export function moveSliding(game: SlidingState, tile: number): SlidingState {
  const blank = game.board.indexOf(0),
    index = game.board.indexOf(tile)
  if (!tile || slidingSolved(game.board) || !slidingNeighbors(blank, game.size).includes(index))
    return game
  const board = [...game.board]
  ;[board[index], board[blank]] = [0, tile]
  return { ...game, board, moves: game.moves + 1 }
}
