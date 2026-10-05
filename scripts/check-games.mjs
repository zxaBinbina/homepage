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
const number = await moduleFor('twenty48')
const mines = await moduleFor('minesweeper')
const cards = await moduleFor('solitaire')
function random(seed) {
  return () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0
    return seed / 2 ** 32
  }
}
const rowBoard = (row) => [...row, ...Array(12).fill(0)]
assert.deepEqual(number.slide(rowBoard([2, 2, 2, 2]), 'left'), {
  board: rowBoard([4, 4, 0, 0]),
  gained: 8,
  changed: true,
})
assert.deepEqual(number.slide(rowBoard([2, 2, 4, 0]), 'left').board, rowBoard([4, 4, 0, 0]))
assert.deepEqual(number.slide(rowBoard([2, 0, 2, 2]), 'right').board, rowBoard([0, 0, 2, 4]))
assert.deepEqual(
  number.slide([2, 0, 0, 0, 2, 0, 0, 0, 4, 0, 0, 0, 4, 0, 0, 0], 'up').board,
  [4, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
)
assert.deepEqual(
  number.slide([2, 0, 0, 0, 2, 0, 0, 0, 4, 0, 0, 0, 4, 0, 0, 0], 'down').board,
  [0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 8, 0, 0, 0],
)
const trace = number.traceSlide(rowBoard([2, 2, 2, 2]), 'right')
assert.deepEqual(trace.merges, [3, 2])
assert.deepEqual(trace.movements, [
  { from: 3, to: 3, value: 2 },
  { from: 2, to: 3, value: 2 },
  { from: 1, to: 2, value: 2 },
  { from: 0, to: 2, value: 2 },
])
assert.deepEqual(
  number.traceSlide([2, 0, 0, 0, 2, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0], 'down').movements,
  [
    { from: 8, to: 12, value: 4 },
    { from: 4, to: 8, value: 2 },
    { from: 0, to: 8, value: 2 },
  ],
)
const fixed = { board: rowBoard([2, 0, 0, 0]), score: 0 }
assert.equal(number.moveNumbers(fixed, 'left'), fixed, 'Invalid move must not spawn')
assert.deepEqual(number.moveNumbers(fixed, 'right', () => 0).board, rowBoard([2, 0, 0, 2]))
assert.equal(number.numbersOver([2, 4, 2, 4, 4, 2, 4, 2, 2, 4, 2, 4, 4, 2, 4, 2]), true)
assert.equal(number.numbersOver([2, 2, 4, 8, 4, 8, 16, 32, 8, 16, 32, 64, 16, 32, 64, 128]), false)
assert.equal(number.numbersOver(rowBoard([2, 4, 8, 16])), false)
assert.equal(Math.max(...number.slide(rowBoard([1024, 1024, 0, 0]), 'left').board), 2048)
for (let seed = 0; seed < 30; seed++) {
  const rng = random(seed)
  let game = number.newNumberGame(rng)
  assert.equal(game.board.filter(Boolean).length, 2)
  for (let i = 0; i < 100; i++) {
    const before = [...game.board]
    const next = number.moveNumbers(game, ['up', 'right', 'down', 'left'][i % 4], rng)
    const increase = next.board.reduce((a, b) => a + b, 0) - game.board.reduce((a, b) => a + b, 0)
    assert.ok(next === game ? increase === 0 : increase === 2 || increase === 4)
    assert.deepEqual(game.board, before, 'Moves must not mutate undo snapshots')
    game = next
  }
}
for (const [size, count] of [
  [4, 1],
  [129, 1],
  [5.5, 1],
  [NaN, 1],
  [Infinity, 1],
  [9, 0],
  [9, -1],
  [9, 73],
  [9, 1.5],
  [9, NaN],
  [9, Infinity],
])
  assert.throws(() => mines.newMineGame(size, count), RangeError)
assert.equal(mines.maxMineCount(128), 16375)
for (const [size, count] of [
  [5, 1],
  [5, 16],
  [17, 53],
  [128, 1],
  [128, 16375],
]) {
  for (const first of [
    0,
    size - 1,
    size * (size - 1),
    size * size - 1,
    Math.floor(size / 2) * size + Math.floor(size / 2),
  ]) {
    let game = mines.revealMine(mines.newMineGame(size, count), first, random(42))
    assert.equal(game.cells.length, size * size)
    assert.equal(game.cells.filter((cell) => cell.mine).length, count)
    assert.ok([first, ...mines.neighbors(first, size)].every((i) => !game.cells[i].mine))
    for (let i = 0; i < game.cells.length; i++) {
      if (!game.cells[i].mine && !game.cells[i].open) game = mines.revealMine(game, i)
    }
    assert.equal(game.status, 'won', `Custom ${size} × ${size}, ${count} mines, start ${first}`)
  }
}
for (const { size, mines: count } of mines.mineLevels) {
  for (let seed = 0; seed < 20; seed++) {
    for (const first of [0, size - 1, size * size - 1, Math.floor((size * size) / 2)]) {
      const empty = mines.newMineGame(size, count)
      let game = mines.revealMine(empty, first, random(seed))
      assert.equal(game.cells.filter((c) => c.mine).length, count)
      assert.ok([first, ...mines.neighbors(first, size)].every((i) => !game.cells[i].mine))
      assert.ok(game.cells[first].open && game.cells[first].adjacent === 0)
      assert.ok(empty.cells.every((c) => !c.mine && !c.open))
      for (let i = 0; i < game.cells.length; i++) {
        assert.equal(
          game.cells[i].adjacent,
          mines.neighbors(i, size).filter((n) => game.cells[n].mine).length,
        )
        if (!game.cells[i].mine && !game.cells[i].open) game = mines.revealMine(game, i)
      }
      assert.equal(game.status, 'won')
      assert.equal(mines.flagMine(game, 0), game)
    }
  }
}
const unflaggedGame = mines.newMineGame()
let mineGame = mines.flagMine(unflaggedGame, 0)
assert.equal(unflaggedGame.cells[0].flag, false, 'Flags must not mutate the previous board')
assert.equal(mineGame.cells[0].flag, true)
assert.equal(mines.revealMine(mineGame, 0), mineGame)
mineGame = mines.flagMine(mineGame, 0)
assert.equal(mineGame.cells[0].flag, false)
mineGame = mines.revealMine(mineGame, 40, random(42))
const bomb = mineGame.cells.findIndex((c) => c.mine)
const lost = mines.revealMine(mineGame, bomb)
assert.equal(lost.status, 'lost')
assert.equal(lost.exploded, bomb)
assert.equal(mines.revealMine(lost, 0), lost)
assert.equal(mines.flagMine(lost, 0), lost)
const chord = mines.newMineGame(5, 1)
chord.status = 'playing'
chord.cells[0].mine = true
chord.cells.forEach(
  (c, i) => (c.adjacent = mines.neighbors(i, 5).filter((n) => chord.cells[n].mine).length),
)
chord.cells[6].open = true
assert.equal(mines.revealMine(chord, 6), chord)
assert.equal(mines.revealMine(mines.flagMine(chord, 0), 6).status, 'won')
assert.equal(mines.revealMine(mines.flagMine(chord, 1), 6).status, 'lost')
let flags = mines.newMineGame()
for (let i = 0; i < 10; i++) flags = mines.flagMine(flags, i)
assert.equal(mines.flagMine(flags, 11), flags)
const face = (suit, rank, faceUp = true) => ({ suit, rank, faceUp })
const emptyCards = () => ({
  stock: [],
  waste: [],
  foundations: [[], [], [], []],
  tableau: [[], [], [], [], [], [], []],
  moves: 0,
})
function deckIntact(game) {
  const deck = [...game.stock, ...game.waste, ...game.foundations.flat(), ...game.tableau.flat()]
  assert.equal(deck.length, 52)
  assert.equal(new Set(deck.map((c) => `${c.suit}-${c.rank}`)).size, 52)
}
for (let seed = 0; seed < 40; seed++) {
  const game = cards.newSolitaire(random(seed))
  deckIntact(game)
  assert.equal(game.stock.length, 24)
  game.tableau.forEach((pile, i) => {
    assert.equal(pile.length, i + 1)
    assert.equal(pile.filter((c) => c.faceUp).length, 1)
    assert.ok(pile.at(-1).faceUp)
  })
  const original = JSON.stringify(game)
  let next = game
  const firstRound = []
  for (let i = 0; i < 24; i++) {
    next = cards.drawCard(next)
    firstRound.push(cards.cardName(next.waste.at(-1)))
    deckIntact(next)
  }
  next = cards.drawCard(next)
  assert.equal(next.waste.length, 0)
  assert.equal(next.stock.length, 24)
  for (const name of firstRound) {
    next = cards.drawCard(next)
    assert.equal(cards.cardName(next.waste.at(-1)), name)
  }
  assert.equal(JSON.stringify(game), original)
}
let game = emptyCards()
game.tableau[0] = [face(0, 4, false), face(1, 12), face(0, 11)]
game.tableau[1] = [face(2, 13)]
const original = JSON.stringify(game)
const moved = cards.moveCard(
  game,
  { kind: 'tableau', pile: 0, index: 1 },
  { kind: 'tableau', pile: 1 },
)
assert.ok(moved)
assert.equal(moved.tableau[1].length, 3)
assert.equal(moved.tableau[0][0].faceUp, true)
assert.equal(JSON.stringify(game), original)
assert.equal(
  cards.moveCard(game, { kind: 'tableau', pile: 0, index: 0 }, { kind: 'tableau', pile: 2 }),
  null,
)
assert.equal(
  cards.moveCard(game, { kind: 'tableau', pile: 0, index: 1 }, { kind: 'tableau', pile: 2 }),
  null,
)
assert.equal(
  cards.moveCard(game, { kind: 'tableau', pile: 0, index: 1 }, { kind: 'tableau', pile: 0 }),
  null,
)
game.tableau[1] = [face(1, 13)]
assert.equal(
  cards.moveCard(game, { kind: 'tableau', pile: 0, index: 1 }, { kind: 'tableau', pile: 1 }),
  null,
)
assert.ok(
  cards.moveCard(game, { kind: 'tableau', pile: 1, index: 0 }, { kind: 'tableau', pile: 2 }),
)
game = emptyCards()
game.waste = [face(0, 1)]
assert.equal(cards.moveCard(game, { kind: 'waste' }, { kind: 'foundation', pile: 1 }), null)
let next = cards.moveCard(game, { kind: 'waste' }, { kind: 'foundation', pile: 0 })
assert.ok(next)
next.tableau[0] = [face(1, 2)]
assert.ok(cards.moveCard(next, { kind: 'foundation', pile: 0 }, { kind: 'tableau', pile: 0 }))
next.waste = [face(0, 3)]
assert.equal(cards.moveCard(next, { kind: 'waste' }, { kind: 'foundation', pile: 0 }), null)
next.waste = [face(0, 2)]
assert.ok(cards.moveCard(next, { kind: 'waste' }, { kind: 'foundation', pile: 0 }))
game = emptyCards()
for (let suit = 0; suit < 4; suit++)
  game.foundations[suit] = Array.from({ length: 12 }, (_, i) => face(suit, i + 1))
for (let suit = 0; suit < 4; suit++) game.tableau[suit] = [face(suit, 13)]
assert.equal(cards.canFinish(game), true)
next = cards.finishSolitaire(game)
assert.equal(cards.solitaireWon(next), true)
assert.equal(next.moves, 4)
assert.equal(game.foundations[0].length, 12)
deckIntact(next)
game.tableau[0][0].faceUp = false
assert.equal(cards.canFinish(game), false)
assert.equal(cards.finishSolitaire(game), game)
console.log(
  'Games passed: 2048 rules and terminal boards; mines safe starts, flood/chord and win/loss; solitaire deals, legal moves, immutable undo and completion.',
)

await import('./check-games-classics.mjs')

await import('./check-games-arcade.mjs')
