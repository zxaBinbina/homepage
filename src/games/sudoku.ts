export function peers(a: number, b: number) {
  return (
    Math.floor(a / 9) === Math.floor(b / 9) ||
    a % 9 === b % 9 ||
    (Math.floor(a / 27) === Math.floor(b / 27) &&
      Math.floor((a % 9) / 3) === Math.floor((b % 9) / 3))
  )
}
export function sudokuConflicts(board: number[]) {
  return board.map(
    (value, i) => !!value && board.some((other, j) => i !== j && value === other && peers(i, j)),
  )
}
export function candidates(board: number[], at: number) {
  const used = new Set(board.filter((_, i) => i !== at && peers(i, at)))
  return [1, 2, 3, 4, 5, 6, 7, 8, 9].filter((v) => !used.has(v))
}
/** Stop at two solutions: uniqueness is sufficient, full enumeration is unnecessary. */
export function solveSudoku(input: number[], limit = 2) {
  const board = [...input],
    solutions: number[][] = []
  if (
    board.length !== 81 ||
    board.some((n) => !Number.isInteger(n) || n < 0 || n > 9) ||
    sudokuConflicts(board).some(Boolean)
  )
    return solutions
  function visit() {
    let at = -1,
      choices: number[] = []
    for (let i = 0; i < 81; i++)
      if (!board[i]) {
        const next = candidates(board, i)
        if (!next.length) return
        if (at < 0 || next.length < choices.length) {
          at = i
          choices = next
        }
        if (next.length === 1) break
      }
    if (at < 0) {
      solutions.push([...board])
      return
    }
    for (const value of choices) {
      board[at] = value
      visit()
      board[at] = 0
      if (solutions.length >= limit) break
    }
  }
  visit()
  return solutions
}
function shuffle<T>(items: T[], random: () => number) {
  const next = [...items]
  for (let i = next.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1))
    ;[next[i], next[j]] = [next[j]!, next[i]!]
  }
  return next
}
// Local seed puzzles have unique solutions. Permuting digits, bands, stacks and
// rows/columns within each group preserves the solution and logical difficulty.
export const sudokuSeeds = [
  ['530070000600195000098000060800060003400803001700020006060000280000419005000080079'],
  ['000260701680070090190004500820100040004602900050003028009300074040050036703018000'],
  ['800000000003600000070090200050007000000045700000100030001000068008500010090000400'],
]
const sudokuAnswers = [
  ['534678912672195348198342567859761423426853791713924856961537284287419635345286179'],
  ['435269781682571493197834562826195347374682915951743628519326874248957136763418259'],
  ['812753649943682175675491283154237896369845721287169534521974368438526917796318452'],
]
export function newSudoku(level = 0, random = Math.random) {
  // Preverified answers avoid running the advanced solver on the UI thread.
  const choice = Math.floor(random() * sudokuSeeds[level]!.length)
  const seed = sudokuSeeds[level]![choice]!.split('').map(Number)
  const answer = sudokuAnswers[level]![choice]!.split('').map(Number)
  const target = [44, 36, 21][level]!
  const holes = shuffle(
    seed.map((v, i) => (!v ? i : -1)).filter((i) => i >= 0),
    random,
  )
  while (seed.filter(Boolean).length < target) {
    const i = holes.pop()!
    seed[i] = answer[i]!
  }
  const order = () =>
    shuffle([0, 1, 2], random).flatMap((group) =>
      shuffle([0, 1, 2], random).map((i) => group * 3 + i),
    )
  const rows = order(),
    cols = order(),
    digits = shuffle([1, 2, 3, 4, 5, 6, 7, 8, 9], random)
  const transpose = random() < 0.5
  const transform = (source: number[]) =>
    Array.from({ length: 81 }, (_, i) => {
      const r = rows[transpose ? i % 9 : Math.floor(i / 9)]!,
        c = cols[transpose ? Math.floor(i / 9) : i % 9]!
      const value = source[r * 9 + c]!
      return value ? digits[value - 1]! : 0
    })
  return { puzzle: transform(seed), solution: transform(answer) }
}
