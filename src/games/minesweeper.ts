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
  { name: '高级 · 16 × 16', size: 16, mines: 40 },
  { name: '专家 · 20 × 20', size: 20, mines: 80 },
  { name: '极限 · 30 × 30', size: 30, mines: 200 },
] as const
export const mineLimits = { minSize: 5, maxSize: 128 } as const

// Reserve the first cell and all eight neighbors, even for a central first move.
export function maxMineCount(size: number): number {
  return size * size - 9
}

export function mineConfigErrors(size: number, mines: number): { size?: string; mines?: string } {
  if (!Number.isInteger(size) || size < mineLimits.minSize || size > mineLimits.maxSize)
    return { size: `边长请输入 ${mineLimits.minSize}–${mineLimits.maxSize} 之间的整数。` }
  if (!Number.isInteger(mines) || mines < 1 || mines > maxMineCount(size))
    return { mines: `地雷数量请输入 1–${maxMineCount(size)} 之间的整数。` }
  return {}
}

export function newMineGame(size = 9, mines = 10): MineGame {
  const errors = mineConfigErrors(size, mines)
  if (errors.size || errors.mines) throw new RangeError(errors.size || errors.mines)
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
  const cells = [...game.cells]
  cells[index] = { ...cell, flag: !cell.flag }
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
