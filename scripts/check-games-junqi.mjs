import assert from 'node:assert/strict'
import { build } from 'esbuild'
const bundle = await build({
  entryPoints: ['src/games/junqi.ts'],
  bundle: true,
  format: 'esm',
  write: false,
})
const j = await import(
  `data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString('base64')}`
)
const piece = (rank, side = 1, id = rank) => ({
  rank,
  side,
  id,
  flag: rank === 10,
  mine: rank === 0,
  bomb: rank === 11,
})
function state(placements, turn = 1) {
  const board = Array(60).fill(null)
  board[1] = piece(10, -1, 100)
  board[58] = piece(10, 1, 101)
  for (const [at, unit] of placements) board[at] = unit
  return { board, turn, selected: null, finished: 0 }
}
function random(seed) {
  return () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0
    return seed / 2 ** 32
  }
}
const expected = [3, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 2]
for (let seed = 0; seed < 100; seed++) {
  const game = j.newJunqi(random(seed))
  assert.equal(game.board.filter(Boolean).length, 50)
  assert.equal(new Set(game.board.filter(Boolean).map((p) => p.id)).size, 50)
  for (const side of [1, -1]) {
    const army = game.board.filter((p) => p?.side === side)
    assert.equal(army.length, 25)
    assert.deepEqual(
      expected,
      j.rankNames.map((_, rank) => army.filter((p) => p.rank === rank).length),
    )
    assert.equal(
      army.filter((p) => p.rank === 1 && p.bomb).length,
      0,
      'Engineers must not be bombs',
    )
    game.board.forEach((p, at) => {
      if (p?.side === side) assert(j.canPlaceJunqi(p, at), `Invalid initial placement at ${at}`)
    })
  }
  for (const at of j.camps) assert.equal(game.board[at], null)
}
assert.deepEqual(
  [...j.camps].sort((a, b) => a - b),
  [11, 13, 17, 21, 23, 36, 38, 42, 46, 48],
)
assert(!j.canPlaceJunqi(piece(10), 30))
assert(j.canPlaceJunqi(piece(10), 56))
assert(!j.canPlaceJunqi(piece(0), 45))
assert(!j.canPlaceJunqi(piece(11), 30))
const formation = j.newJunqi(() => 0)
assert(j.swapJunqiSetup(formation, 30, 31))
const flag = formation.board.findIndex((p) => p?.side === 1 && p.flag)
assert.equal(j.swapJunqiSetup(formation, flag, 30), null)
assert.equal(j.swapJunqiSetup(formation, 30, 0), null)
assert.equal(j.swapJunqiSetup(formation, 30, 36), null)
const straight = state([
  [5, piece(7)],
  [55, piece(1, -1, 50)],
])
assert(j.canMove(straight, 5, 9))
straight.board[7] = piece(2, -1)
assert(!j.canMove(straight, 5, 9), 'Rail paths cannot jump occupied stations')
const turn = state([
  [10, piece(1)],
  [55, piece(1, -1, 50)],
])
assert(j.canMove(turn, 10, 9), 'Engineer can turn along a clear railroad')
turn.board[10] = piece(7)
assert(!j.canMove(turn, 10, 9), 'Ordinary officers cannot turn on railroads')
assert(!j.rail(17), 'Center camps are not a long central railroad')
for (const from of [25, 27, 29])
  assert(
    j.canMove(
      state([
        [from, piece(7)],
        [55, piece(1, -1, 50)],
      ]),
      from,
      from + 5,
    ),
  )
for (const from of [26, 28])
  assert(
    !j.canMove(
      state([
        [from, piece(7)],
        [55, piece(1, -1, 50)],
      ]),
      from,
      from + 5,
    ),
    'Only three mountain crossings',
  )
assert(
  !j.canMove(
    state([
      [12, piece(7)],
      [17, piece(2, -1)],
    ]),
    12,
    17,
  ),
  'Occupied camps cannot be attacked',
)
assert(
  j.canMove(
    state([
      [17, piece(7)],
      [12, piece(2, -1)],
    ]),
    17,
    12,
  ),
  'A unit can leave camp to attack',
)
assert(!j.canMove(state([[56, piece(7)]]), 56, 51), 'Units in headquarters stay there')
const fight = (a, b) =>
  j.moveJunqi(
    state([
      [25, a],
      [30, b],
      [55, piece(1, -1, 50)],
    ]),
    25,
    30,
  )
const both = fight(piece(7), piece(7, -1, 20))
assert.equal(both.board[25], null)
assert.equal(both.board[30], null, 'Equal ranks must remove both units')
const bomb = fight(piece(11), piece(9, -1, 20))
assert.equal(bomb.board[25], null)
assert.equal(bomb.board[30], null, 'Bombs must remove both units')
assert.equal(fight(piece(1), piece(0, -1, 20)).board[30].rank, 1, 'Engineer safely removes a mine')
assert.equal(fight(piece(7), piece(0, -1, 20)).board[30].mine, true, 'Officers lose to mines')
const lost = fight(piece(2), piece(9, -1, 20))
assert.equal(lost.board[25], null)
assert.equal(lost.board[30].id, 20, 'The defender stays in place after a failed attack')
const flagCapture = j.moveJunqi(
  state([
    [6, piece(1)],
    [55, piece(1, -1, 50)],
  ]),
  6,
  1,
)
assert.equal(flagCapture.finished, 1)
const bombFlagCapture = j.moveJunqi(
  state([
    [6, piece(11)],
    [55, piece(1, -1, 50)],
  ]),
  6,
  1,
)
assert.equal(bombFlagCapture.finished, 1)
assert.equal(bombFlagCapture.board[6], null)
assert.equal(bombFlagCapture.board[1], null, 'A bomb removes the flag and itself, and still wins')
const blocked = j.moveJunqi(state([[25, piece(9)]]), 25, 30)
assert.equal(blocked.finished, 1, 'A side with only an immobile flag has no moves')
assert.equal(j.chooseJunqi(blocked), null)
assert.equal(j.moveJunqi(blocked, 30, 35), null, 'No moves after a result')
console.log(
  'Junqi: 100 formations, swaps, railroads, camps/headquarters, captures and terminal states passed.',
)

await import('./check-games-junqi-challenge.mjs')
