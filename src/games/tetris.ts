export type Block = { x: number; y: number; shape: number[][] }
export type TetrisState = {
  board: number[]
  active: Block
  queue: number[]
  score: number
  lines: number
  status: 'playing' | 'won' | 'lost'
}
export const shapes = [
  [
    [0, 0, 0, 0],
    [1, 1, 1, 1],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ],
  [
    [1, 1],
    [1, 1],
  ],
  [
    [0, 1, 0],
    [1, 1, 1],
    [0, 0, 0],
  ],
  [
    [0, 1, 1],
    [1, 1, 0],
    [0, 0, 0],
  ],
  [
    [1, 1, 0],
    [0, 1, 1],
    [0, 0, 0],
  ],
  [
    [1, 0, 0],
    [1, 1, 1],
    [0, 0, 0],
  ],
  [
    [0, 0, 1],
    [1, 1, 1],
    [0, 0, 0],
  ],
]
export function bag(random = Math.random) {
  const result = [0, 1, 2, 3, 4, 5, 6]
  for (let i = 6; i > 0; i--) {
    const j = Math.floor(random() * (i + 1))
    ;[result[i], result[j]] = [result[j]!, result[i]!]
  }
  return result
}
function spawn(id: number): Block {
  const shape = shapes[id]!.map((row) => [...row])
  return { x: Math.floor((10 - shape.length) / 2), y: 0, shape }
}
export function blocks(piece: Block) {
  return piece.shape.flatMap((row, y) =>
    row.flatMap((value, x) => (value ? [{ x: x + piece.x, y: y + piece.y }] : [])),
  )
}
export function fits(board: number[], piece: Block) {
  return blocks(piece).every(
    ({ x, y }) => x >= 0 && x < 10 && y < 20 && (y < 0 || !board[y * 10 + x]),
  )
}
export function newTetris(random = Math.random): TetrisState {
  const queue = bag(random)
  return {
    board: Array(200).fill(0),
    active: spawn(queue.shift()!),
    queue,
    score: 0,
    lines: 0,
    status: 'playing',
  }
}
export function shiftBlock(game: TetrisState, dx: number, dy: number): TetrisState {
  if (game.status !== 'playing') return game
  const active = { ...game.active, x: game.active.x + dx, y: game.active.y + dy }
  return fits(game.board, active) ? { ...game, active } : game
}
export function rotateBlock(game: TetrisState): TetrisState {
  if (game.status !== 'playing') return game
  const old = game.active.shape
  const shape = old.map((row, y) => row.map((_, x) => old[old.length - 1 - x]![y]!))
  // Modest wall/floor kicks keep rotation usable at the edges without costly physics.
  for (const [dx, dy] of [
    [0, 0],
    [-1, 0],
    [1, 0],
    [-2, 0],
    [2, 0],
    [0, -1],
    [0, -2],
  ] as const) {
    const active = { x: game.active.x + dx, y: game.active.y + dy, shape }
    if (fits(game.board, active)) return { ...game, active }
  }
  return game
}
export function ghostBlock(game: TetrisState) {
  let piece = game.active
  while (fits(game.board, { ...piece, y: piece.y + 1 })) piece = { ...piece, y: piece.y + 1 }
  return piece
}
export function lockBlock(game: TetrisState, random = Math.random) {
  if (game.status !== 'playing') return { game, rows: [] as number[], locked: game.board }
  const locked = [...game.board]
  if (blocks(game.active).some(({ y }) => y < 0))
    return { game: { ...game, status: 'lost' as const }, rows: [], locked }
  for (const { x, y } of blocks(game.active)) locked[y * 10 + x] = 1
  const rows = Array.from({ length: 20 }, (_, y) => y).filter((y) =>
    locked.slice(y * 10, y * 10 + 10).every(Boolean),
  )
  const board = [
    ...Array(rows.length * 10).fill(0),
    ...locked.filter((_, i) => !rows.includes(Math.floor(i / 10))),
  ]
  const queue = [...game.queue]
  if (queue.length < 7) queue.push(...bag(random))
  const active = spawn(queue.shift()!)
  const lines = game.lines + rows.length
  const score =
    game.score + [0, 100, 300, 500, 800][rows.length]! * (1 + Math.floor(game.lines / 5))
  const status = lines >= 30 ? 'won' : fits(board, active) ? 'playing' : 'lost'
  return { game: { board, active, queue, lines, score, status } as TetrisState, rows, locked }
}
export function dropBlock(game: TetrisState): TetrisState {
  if (game.status !== 'playing') return game
  const active = ghostBlock(game)
  return { ...game, active, score: game.score + (active.y - game.active.y) * 2 }
}
export function dropInterval(lines: number, level: number) {
  return Math.max(120, [950, 720, 480][level]! - Math.floor(lines / 5) * 120)
}
