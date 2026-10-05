export type SnakeDirection = 'up' | 'down' | 'left' | 'right'
export type SnakePoint = { x: number; y: number }
export type SnakeState = {
  size: number
  body: SnakePoint[]
  direction: SnakeDirection
  food: SnakePoint | null
  score: number
  status: 'playing' | 'won' | 'lost'
}
const vectors: Record<SnakeDirection, SnakePoint> = {
  up: { x: 0, y: -1 },
  down: { x: 0, y: 1 },
  left: { x: -1, y: 0 },
  right: { x: 1, y: 0 },
}
export function samePoint(a: SnakePoint, b: SnakePoint) {
  return a.x === b.x && a.y === b.y
}
export function canTurn(from: SnakeDirection, to: SnakeDirection) {
  return vectors[from].x * vectors[to].x + vectors[from].y * vectors[to].y === 0
}
export function snakeFood(body: SnakePoint[], size: number, random = Math.random) {
  const occupied = new Set(body.map((p) => p.y * size + p.x))
  const empty = Array.from({ length: size * size }, (_, i) => i).filter((i) => !occupied.has(i))
  if (!empty.length) return null
  const cell = empty[Math.floor(random() * empty.length)]!
  return { x: cell % size, y: Math.floor(cell / size) }
}
export function newSnake(random = Math.random): SnakeState {
  const body = [
    { x: 5, y: 9 },
    { x: 4, y: 9 },
    { x: 3, y: 9 },
  ]
  return {
    size: 18,
    body,
    direction: 'right',
    food: snakeFood(body, 18, random),
    score: 0,
    status: 'playing',
  }
}
export function stepSnake(
  game: SnakeState,
  direction = game.direction,
  random = Math.random,
): SnakeState {
  if (game.status !== 'playing') return game
  if (direction !== game.direction && !canTurn(game.direction, direction))
    direction = game.direction
  const head = game.body[0]!,
    vector = vectors[direction]
  const next = { x: head.x + vector.x, y: head.y + vector.y }
  const eating = !!game.food && samePoint(next, game.food)
  // The tail vacates its square in the same tick, unless this move grows the snake.
  const occupied = eating ? game.body : game.body.slice(0, -1)
  if (
    next.x < 0 ||
    next.x >= game.size ||
    next.y < 0 ||
    next.y >= game.size ||
    occupied.some((p) => samePoint(p, next))
  )
    return { ...game, direction, status: 'lost' }
  const body = [next, ...game.body]
  if (!eating) body.pop()
  const food = eating ? snakeFood(body, game.size, random) : game.food
  return {
    ...game,
    body,
    direction,
    food,
    score: game.score + (eating ? 10 : 0),
    status: food ? 'playing' : 'won',
  }
}
export function snakeInterval(score: number, speed: number) {
  return Math.max(75, [210, 150, 105][speed]! - Math.floor(score / 50) * 10)
}
