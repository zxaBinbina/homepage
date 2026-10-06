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
const [c, g] = await Promise.all(['chess', 'go'].map(moduleFor))
const initial = c.newChess()
assert.equal(new c.Chess(initial.fen).moves().length, 20)
assert.equal(c.playChess(initial, { from: 'e2', to: 'e5' }), null)
assert.equal(c.squareAt(0), 'a8')
assert.equal(c.squareIndex('h1'), 63)
let chess = initial
for (const [from, to] of [
  ['f2', 'f3'],
  ['e7', 'e5'],
  ['g2', 'g4'],
  ['d8', 'h4'],
])
  chess = c.playChess(chess, { from, to })
assert.equal(c.chessResult(chess).winner, -1)
assert.equal(initial.ply, 0)
assert.equal(c.chessResult(c.newChess('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')).reason, '无子可动，逼和')
assert.equal(c.chessResult(c.newChess('7k/8/6K1/8/8/8/8/8 w - - 0 1')).winner, 0)
assert.equal(c.chessResult(c.newChess('7k/8/6K1/8/8/8/8/R7 w - - 100 51')).winner, 0)
const castle = c.newChess('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1')
for (const to of ['c1', 'g1']) assert.ok(c.playChess(castle, { from: 'e1', to }))
const castled = new c.Chess(c.playChess(castle, { from: 'e1', to: 'g1' }).fen)
assert.equal(castled.get('f1').type, 'r')
assert.equal(castled.get('g1').type, 'k')
assert.equal(
  c.playChess(c.newChess('r3kr1r/8/8/8/8/8/8/R3K2R w KQ - 0 1'), { from: 'e1', to: 'g1' }),
  null,
  'Cannot castle through check',
)
assert.equal(
  c.playChess(c.newChess('4r2k/8/8/8/8/8/4R3/4K3 w - - 0 1'), { from: 'e2', to: 'd2' }),
  null,
  'Pinned piece must shield the king',
)
chess = initial
for (const [from, to] of [
  ['e2', 'e4'],
  ['a7', 'a6'],
  ['e4', 'e5'],
  ['d7', 'd5'],
])
  chess = c.playChess(chess, { from, to })
const ep = c.playChess(chess, { from: 'e5', to: 'd6' })
assert.ok(ep)
assert.equal(new c.Chess(ep.fen).get('d5'), undefined)
let expired = c.playChess(chess, { from: 'h2', to: 'h3' })
expired = c.playChess(expired, { from: 'h7', to: 'h6' })
assert.equal(c.playChess(expired, { from: 'e5', to: 'd6' }), null)
for (const promotion of ['q', 'r', 'b', 'n']) {
  const promoted = c.playChess(c.newChess('7k/P7/8/8/8/8/8/7K w - - 0 1'), {
    from: 'a7',
    to: 'a8',
    promotion,
  })
  assert.equal(new c.Chess(promoted.fen).get('a8').type, promotion)
}
chess = initial
for (let i = 0; i < 2; i++)
  for (const [from, to] of [
    ['g1', 'f3'],
    ['g8', 'f6'],
    ['f3', 'g1'],
    ['f6', 'g8'],
  ])
    chess = c.playChess(chess, { from, to })
assert.equal(c.chessResult(chess).reason, '同一局面出现三次')
for (const difficulty of [0, 1]) {
  const mate = c.newChess('7k/5Q2/6K1/8/8/8/8/8 w - - 0 1')
  assert.equal(c.chessResult(c.playChess(mate, c.chooseChess(mate, difficulty))).winner, 1)
  chess = initial
  for (let i = 0; i < 8; i++) {
    const next = c.playChess(chess, c.chooseChess(chess, difficulty))
    assert.ok(next)
    chess = next
  }
}

function position(entries, turn = 1) {
  const state = g.newGo()
  for (const [at, side] of entries) state.board[at] = side
  state.turn = turn
  state.positions = [state.board.join(',')]
  return state
}
let go = position([
  [40, -1],
  [31, 1],
  [39, 1],
  [41, 1],
])
const before = JSON.stringify(go)
let moved = g.playGo(go, 49)
assert.deepEqual(moved.captured, [40])
assert.equal(moved.state.board[40], 0)
assert.equal(moved.state.captures[0], 1)
assert.equal(JSON.stringify(go), before)
assert.match(
  g.playGo(
    position([
      [31, -1],
      [39, -1],
      [41, -1],
      [49, -1],
    ]),
    40,
  ).error,
  /自杀/,
)
assert.ok(g.playGo(go, 40).error)
for (const invalid of [-2, 81, NaN, 1.5]) assert.ok(g.playGo(go, invalid).error)
// One placement takes two disconnected enemy groups; each is counted once.
moved = g.playGo(
  position([
    [39, -1],
    [41, -1],
    [30, 1],
    [38, 1],
    [48, 1],
    [32, 1],
    [42, 1],
    [50, 1],
  ]),
  40,
)
assert.deepEqual(
  moved.captured.sort((a, b) => a - b),
  [39, 41],
)
// Ko: Black captures at 41; White may not recreate the board at 40.
go = position([
  [40, -1],
  [31, 1],
  [39, 1],
  [49, 1],
  [32, -1],
  [42, -1],
  [50, -1],
])
moved = g.playGo(go, 41)
assert.deepEqual(moved.captured, [40])
assert.match(g.playGo(moved.state, 40).error, /劫争/)
// The ban includes older boards, even when it is not an immediate recapture.
const historical = g.newGo(),
  future = g.playGo(historical, 40).state.board.join(',')
historical.positions = [future, ...historical.positions]
assert.match(g.playGo(historical, 40).error, /劫争/)
go = g.passGo(g.passGo(g.newGo()))
assert.equal(go.passes, 2)
assert.equal(go.turn, 1)
assert.ok(g.playGo(go, 40).error)
assert.equal(g.passGo(go), go)
go = g.playGo(g.passGo(g.newGo()), 40).state
assert.equal(go.passes, 0)
assert.equal(go.board[40], -1)
assert.equal(g.scoreGo(Array(81).fill(0)).black, 0)
assert.equal(g.scoreGo(Array(81).fill(0)).white, 6.5)
const mixed = Array(81).fill(0)
mixed[0] = 1
mixed[80] = -1
assert.equal(g.scoreGo(mixed).black, 1)
assert.equal(g.scoreGo(mixed).white, 7.5)
const territory = Array(81).fill(1)
territory[40] = 0
territory[41] = -1
assert.equal(g.scoreGo(territory, [41]).black, 81)
assert.equal(territory[41], -1, 'Scoring must not mutate the board')
for (const difficulty of [0, 1]) {
  go = position([
    [40, -1],
    [31, 1],
    [39, 1],
    [41, 1],
  ])
  assert.equal(g.chooseGo(go, difficulty), 49, 'Take a free capture')
  assert.equal(g.chooseGo(g.passGo(g.newGo()), difficulty), -1, 'Accept an uncontested ending')
  go = g.newGo()
  for (let i = 0; i < 60 && go.passes < 2; i++) {
    const at = g.chooseGo(go, difficulty)
    if (at === -1) go = g.passGo(go)
    else {
      moved = g.playGo(go, at)
      assert.ok(!('error' in moved))
      go = moved.state
    }
    for (let n = 0; n < 81; n++) if (go.board[n]) assert.ok(g.goGroup(go.board, n).liberties.length)
  }
}
console.log(
  'Chess / Go rules passed: legal moves, checkmate/draws, castling, en passant, promotions, repetition, AI legality; liberties, multi-capture, suicide, superko, passes, area/dead-stone scoring, bounded local opponents.',
)
