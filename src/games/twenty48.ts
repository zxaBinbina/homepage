export type Direction = 'left' | 'right' | 'up' | 'down'
export type NumberGame = { board: number[]; score: number }

export function addTile(board: number[], random = Math.random): number[] {
  const empty = board.flatMap((value, index) => (value === 0 ? [index] : []))
  if (!empty.length) return board
  const next = [...board]
  next[empty[Math.floor(random() * empty.length)]!] = random() < 0.9 ? 2 : 4
  return next
}

export function newNumberGame(random = Math.random): NumberGame {
  return { board: addTile(addTile(Array(16).fill(0), random), random), score: 0 }
}

/** Slide first, then spawn only when a move actually changes the board. */
export function slide(board: number[], direction: Direction) {
  const next = Array<number>(16).fill(0)
  let gained = 0
  for (let line = 0; line < 4; line++) {
    const indices = Array.from({ length: 4 }, (_, offset) => {
      const step = direction === 'right' || direction === 'down' ? 3 - offset : offset
      return direction === 'left' || direction === 'right' ? line * 4 + step : step * 4 + line
    })
    const values = indices.map((index) => board[index]!).filter(Boolean)
    const merged: number[] = []
    for (let i = 0; i < values.length; i++) {
      if (values[i] === values[i + 1]) {
        const value = values[i]! * 2
        merged.push(value)
        gained += value
        i++
      } else merged.push(values[i]!)
    }
    indices.forEach((index, offset) => (next[index] = merged[offset] ?? 0))
  }
  return { board: next, gained, changed: next.some((value, index) => value !== board[index]) }
}

export function moveNumbers(game: NumberGame, direction: Direction, random = Math.random) {
  const moved = slide(game.board, direction)
  return moved.changed
    ? { board: addTile(moved.board, random), score: game.score + moved.gained }
    : game
}

export function numbersOver(board: number[]) {
  return (['left', 'right', 'up', 'down'] as const).every(
    (direction) => !slide(board, direction).changed,
  )
}
