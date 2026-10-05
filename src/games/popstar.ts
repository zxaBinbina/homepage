export type StarTile = { id: number; color: number }
export type StarBoard = (StarTile | null)[]
export type PopstarState = {
  board: StarBoard
  level: number
  score: number
  bonus: number
  status: 'playing' | 'passed' | 'lost'
}
export const STAR_SIZE = 10
export function starTarget(level: number) {
  return level === 1 ? 1000 : level === 2 ? 3000 : 6000 + (level - 3) * 2000
}
export function starPoints(count: number) {
  return count >= 2 ? 5 * count * count : 0
}
export function starBonus(remaining: number) {
  return Math.max(0, 2000 - 20 * remaining * remaining)
}
export function starGroup(board: StarBoard, index: number) {
  const tile = board[index]
  if (!tile) return []
  const found = new Set([index]),
    queue = [index]
  for (let i = 0; i < queue.length; i++) {
    const cell = queue[i]!,
      x = cell % STAR_SIZE
    for (const neighbor of [
      cell - STAR_SIZE,
      cell + STAR_SIZE,
      ...(x > 0 ? [cell - 1] : []),
      ...(x < STAR_SIZE - 1 ? [cell + 1] : []),
    ]) {
      if (board[neighbor]?.color === tile.color && !found.has(neighbor)) {
        found.add(neighbor)
        queue.push(neighbor)
      }
    }
  }
  return queue
}
export function hasStarMove(board: StarBoard) {
  return board.some(
    (tile, i) =>
      tile &&
      (board[i + STAR_SIZE]?.color === tile.color ||
        (i % STAR_SIZE < STAR_SIZE - 1 && board[i + 1]?.color === tile.color)),
  )
}
export function newPopstar(level = 1, score = 0, random = Math.random): PopstarState {
  const board = Array.from({ length: 100 }, (_, id) => ({ id, color: Math.floor(random() * 5) }))
  if (!hasStarMove(board)) board[0]!.color = board[1]!.color
  return { board, level, score, bonus: 0, status: 'playing' }
}
export function popStars(game: PopstarState, index: number): PopstarState {
  if (game.status !== 'playing') return game
  const group = starGroup(game.board, index)
  if (group.length < 2) return game
  const removed = new Set(group),
    board: StarBoard = Array(100).fill(null)
  let column = 0
  for (let x = 0; x < STAR_SIZE; x++) {
    const remaining: StarTile[] = []
    for (let y = 0; y < STAR_SIZE; y++) {
      const i = y * STAR_SIZE + x,
        tile = game.board[i]
      if (tile && !removed.has(i)) remaining.push(tile)
    }
    if (!remaining.length) continue
    remaining.forEach((tile, y) => {
      board[(STAR_SIZE - remaining.length + y) * STAR_SIZE + column] = tile
    })
    column++
  }
  const ended = !hasStarMove(board)
  const bonus = ended ? starBonus(board.filter(Boolean).length) : 0
  const score = game.score + starPoints(group.length) + bonus
  return {
    ...game,
    board,
    score,
    bonus,
    status: ended ? (score >= starTarget(game.level) ? 'passed' : 'lost') : 'playing',
  }
}
export function nextStarLevel(game: PopstarState, random = Math.random) {
  return game.status === 'passed' ? newPopstar(game.level + 1, game.score, random) : game
}
