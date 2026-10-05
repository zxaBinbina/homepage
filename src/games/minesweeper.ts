export type MineCell = { mine: boolean; adjacent: number; open: boolean; flag: boolean }
export type MineGame = {
  size: number
  mines: number
  cells: MineCell[]
  status: 'ready' | 'playing' | 'won' | 'lost'
  exploded: number | null
}
export const mineLevels = [
  { name: '轻松 · 9 × 9', size: 9, mines: 10 },
  { name: '挑战 · 12 × 12', size: 12, mines: 24 },
] as const

export function newMineGame(size = 9, mines = 10): MineGame {
  return {
    size,
    mines,
    cells: Array.from({ length: size * size }, () => ({
      mine: false,
      adjacent: 0,
      open: false,
      flag: false,
    })),
    status: 'ready',
    exploded: null,
  }
}

export function neighbors(index: number, size: number): number[] {
  const row = Math.floor(index / size),
    column = index % size
  const result: number[] = []
  for (let y = Math.max(0, row - 1); y <= Math.min(size - 1, row + 1); y++)
    for (let x = Math.max(0, column - 1); x <= Math.min(size - 1, column + 1); x++)
      if (y * size + x !== index) result.push(y * size + x)
  return result
}

export function flagMine(game: MineGame, index: number): MineGame {
  const cell = game.cells[index]
  if (!cell || cell.open || game.status === 'won' || game.status === 'lost') return game
  if (!cell.flag && game.cells.filter((item) => item.flag).length >= game.mines) return game
  const cells = game.cells.map((item) => ({ ...item }))
  cells[index]!.flag = !cell.flag
  return { ...game, cells }
}

export function revealMine(game: MineGame, index: number, random = Math.random): MineGame {
  const cell = game.cells[index]
  if (!cell || cell.flag || game.status === 'won' || game.status === 'lost') return game
  const next: MineGame = { ...game, cells: game.cells.map((item) => ({ ...item })) }
  if (next.status === 'ready') {
    const safe = new Set([index, ...neighbors(index, next.size)])
    const available = next.cells.flatMap((_, i) => (safe.has(i) ? [] : [i]))
    for (let i = 0; i < next.mines; i++) {
      const pick = i + Math.floor(random() * (available.length - i))
      ;[available[i], available[pick]] = [available[pick]!, available[i]!]
      next.cells[available[i]!]!.mine = true
    }
    next.cells.forEach((item, i) => {
      item.adjacent = neighbors(i, next.size).filter((n) => next.cells[n]!.mine).length
    })
    next.status = 'playing'
  }
  // Clicking an open number clears its neighbors only when enough flags surround it.
  const adjacent = neighbors(index, next.size)
  if (cell.open && adjacent.filter((i) => next.cells[i]!.flag).length !== cell.adjacent) return game
  const queue = cell.open ? [...adjacent] : [index]
  while (queue.length) {
    const i = queue.pop()!
    const item = next.cells[i]!
    if (item.open || item.flag) continue
    item.open = true
    if (item.mine) {
      next.status = 'lost'
      next.exploded = i
      return next
    }
    if (!item.adjacent) queue.push(...neighbors(i, next.size))
  }
  if (next.cells.every((item) => item.mine || item.open)) next.status = 'won'
  return next
}
