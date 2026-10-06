import assert from 'node:assert/strict'
import { build } from 'esbuild'
async function moduleFor(name) {
  const bundle = await build({
    entryPoints: [`src/games/${name}.ts`],
    bundle: true,
    format: 'esm',
    write: false,
  })
  return import(
    `data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString('base64')}`
  )
}
function random(seed) {
  return () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0
    return seed / 2 ** 32
  }
}
const [t, s, g, x] = await Promise.all(['tetris', 'sudoku', 'gomoku', 'xiangqi'].map(moduleFor))
for (let seed = 0; seed < 30; seed++) {
  const rng = random(seed)
  assert.equal(new Set(t.bag(rng)).size, 7)
  let game = t.newTetris(rng)
  for (let i = 0; i < 120 && game.status === 'playing'; i++) {
    const old = JSON.stringify(game)
    const shifted = t.shiftBlock(game, i % 2 ? 1 : -1, 0)
    const rotated = t.rotateBlock(shifted)
    const ghost = t.ghostBlock(rotated)
    assert.ok(t.fits(game.board, ghost))
    assert.ok(!t.fits(game.board, { ...ghost, y: ghost.y + 1 }))
    const next = t.lockBlock(t.dropBlock(rotated), rng)
    assert.equal(JSON.stringify(game), old)
    assert.equal(next.game.board.length, 200)
    game = next.game
  }
}
for (let rows = 1; rows <= 4; rows++) {
  const game = t.newTetris(() => 0.3)
  for (let y = 20 - rows; y < 20; y++)
    for (let col = 0; col < 10; col++) if (col !== 4) game.board[y * 10 + col] = 1
  game.active = { x: 4, y: 16, shape: [[1], [1], [1], [1]] }
  const next = t.lockBlock(game)
  assert.equal(next.rows.length, rows)
  assert.equal(next.game.lines, rows)
  assert.equal(next.game.score, [0, 100, 300, 500, 800][rows])
  assert.equal(next.game.board.filter(Boolean).length, 4 - rows)
  game.lines = 30 - rows
  assert.equal(t.lockBlock(game).game.status, 'won')
}
const ceiling = t.newTetris()
ceiling.board = Array(200).fill(1)
ceiling.board[199] = 0
ceiling.active = { x: 0, y: -1, shape: [[1]] }
assert.equal(t.lockBlock(ceiling).game.status, 'lost')
assert.equal(t.dropInterval(25, 2), 120)
const wall = t.newTetris()
wall.active = {
  x: 0,
  y: 0,
  shape: [
    [1, 1],
    [1, 1],
  ],
}
assert.equal(t.shiftBlock(wall, -1, 0), wall)
assert.ok(t.fits(wall.board, t.rotateBlock(wall).active))

for (let level = 0; level < 3; level++) {
  for (const seed of s.sudokuSeeds[level])
    assert.equal(s.solveSudoku(seed.split('').map(Number)).length, 1)
  const variants = new Set()
  for (let seed = 0; seed < 12; seed++) {
    const game = s.newSudoku(level, random(seed))
    variants.add(game.puzzle.join(''))
    assert.equal(game.puzzle.filter(Boolean).length, [44, 36, 21][level])
    assert.ok(game.puzzle.every((value, i) => !value || value === game.solution[i]))
    assert.ok(!s.sudokuConflicts(game.solution).some(Boolean))
    assert.deepEqual(s.solveSudoku(game.puzzle), [game.solution])
  }
  assert.equal(variants.size, 12)
}
const duplicate = Array(81).fill(0)
duplicate[0] = duplicate[8] = 5
assert.ok(s.sudokuConflicts(duplicate)[0] && s.sudokuConflicts(duplicate)[8])
assert.equal(s.solveSudoku(duplicate).length, 0)
assert.equal(s.solveSudoku(Array(81).fill(0)).length, 2)

for (const [dx, dy] of g.gomokuDirections) {
  const board = Array(225).fill(0)
  for (let i = 0; i < 5; i++) board[(7 + i * dy) * 15 + 4 + i * dx] = 1
  assert.equal(g.winningLine(board, 7 * 15 + 4).length, 5)
}
const edge = Array(225).fill(0)
for (const at of [13, 14, 15, 16, 17]) edge[at] = 1
assert.equal(g.winningLine(edge, 15).length, 0, 'Lines must not wrap rows')
const six = Array(225).fill(0)
for (let i = 0; i < 6; i++) six[90 + i] = 1
assert.equal(g.winningLine(six, 92).length, 6, 'Freestyle accepts overlines')
assert.equal(g.chooseGomoku(Array(225).fill(0)), 112)
assert.equal(g.chooseGomoku(Array(225).fill(0), 1), 112)
for (const side of [-1, 1]) {
  const board = Array(225).fill(0)
  board[104] = -side
  for (const i of [105, 106, 107, 108]) board[i] = side
  assert.equal(
    g.chooseGomoku(board, -1),
    109,
    side === -1 ? 'Take an immediate win' : 'Block an immediate loss',
  )
}
assert.equal(g.chooseGomoku(Array(225).fill(1)), null)

const start = x.newXiangqi()
assert.equal(start.filter(Boolean).length, 32)
assert.equal(x.legalChessMoves(start, 1).length, 44, 'Standard starting legal moves')
assert.ok(!x.inCheck(start, 1) && !x.inCheck(start, -1))
const fixture = (...pieces) => {
  const b = Array(90).fill(0)
  b[4] = -1
  b[85] = 1
  b[49] = 7
  for (const [at, piece] of pieces) b[at] = piece
  return b
}
const targets = (b, from) =>
  x
    .legalChessMoves(b, 1)
    .filter((m) => m.from === from)
    .map((m) => m.to)
assert.ok(!targets(start, 82).includes(75), 'Horse leg blocks a knight move')
const horse = fixture([58, 4], [49, 7])
assert.ok(!targets(horse, 58).includes(39))
const elephant = fixture([65, 3], [55, 7])
assert.ok(!targets(elephant, 65).includes(45), 'Elephant eye')
assert.ok(
  targets(fixture([47, 3]), 47).every((i) => i >= 45),
  'Elephant cannot cross river',
)
const cannon = fixture([64, 6], [37, 7], [10, -5])
assert.ok(targets(cannon, 64).includes(10), 'Cannon captures over one screen')
cannon[28] = -7
assert.ok(!targets(cannon, 64).includes(10), 'Two screens prevent cannon capture')
cannon[37] = 0
cannon[28] = 0
assert.ok(!targets(cannon, 64).includes(10), 'No screen prevents cannon capture')
assert.deepEqual(targets(fixture([54, 7]), 54), [45], 'Pawn before river only moves forward')
assert.deepEqual(new Set(targets(fixture([36, 7]), 36)), new Set([27, 37]))
const facing = fixture([49, 5])
assert.ok(!targets(facing, 49).includes(48), 'Cannot expose facing kings')
assert.ok(targets(facing, 49).includes(40))
assert.ok(
  targets(fixture(), 85).every((i) => i % 9 >= 3 && i % 9 <= 5 && i >= 63),
  'King stays in palace',
)
const checked = fixture([76, -5])
assert.ok(x.inCheck(checked, 1))
assert.ok(x.legalChessMoves(checked, 1).every((m) => !x.inCheck(x.applyChessMove(checked, m), 1)))
const mate = fixture([49, 0], [76, -5], [75, -5], [77, -5])
assert.equal(x.chessOutcome(mate, 1), -1)
const stalemate = fixture([49, 0], [40, -7], [66, -5], [68, -5], [72, -5])
assert.ok(!x.inCheck(stalemate, 1))
assert.equal(x.chessOutcome(stalemate, 1), -1)
for (const side of [-1, 1])
  for (const difficulty of [0, 1]) {
    const before = JSON.stringify(start),
      move = x.chooseXiangqi(start, side, difficulty, 120)
    assert.ok(x.legalChessMoves(start, side).some((m) => m.from === move.from && m.to === move.to))
    assert.equal(JSON.stringify(start), before)
  }
console.log(
  'Classics: Tetris bags/rotation/collision/clears, Sudoku uniqueness/variants, Gomoku wins/tactics, Xiangqi legal moves/check/mate/stalemate and bounded AI passed.',
)
