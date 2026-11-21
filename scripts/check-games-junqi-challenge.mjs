import assert from 'node:assert/strict'
import { build } from 'esbuild'
async function moduleFor(file) {
  const bundle = await build({ entryPoints: [file], bundle: true, format: 'esm', write: false })
  return import(
    `data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString('base64')}`
  )
}
const [j, k] = await Promise.all([
  moduleFor('src/games/junqi.ts'),
  moduleFor('src/games/junqiKnowledge.ts'),
])
const unit = (rank, side, id) => ({
  rank,
  side,
  id,
  flag: rank === 10,
  mine: rank === 0,
  bomb: rank === 11,
})
function state(pieces, turn = 1) {
  const board = Array(60).fill(null)
  for (const [at, piece] of pieces) board[at] = piece
  return { board, turn, selected: null, finished: 0 }
}
function random(seed) {
  return () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0
    return seed / 2 ** 32
  }
}
for (let seed = 0; seed < 100; seed++) {
  const game = { ...j.newJunqi(random(seed)), turn: -1 }
  const knowledge = k.createJunqiKnowledge(game)
  const observation = k.observeJunqi(game, -1, knowledge)
  assert.equal(observation.board.filter((p) => p?.side === 1 && p.rank === null).length, 25)
  assert.equal(observation.board.filter((p) => p?.side === -1 && p.rank !== null).length, 25)
  const guarded = {
    ...game,
    board: game.board.map((p) =>
      p?.side === 1
        ? new Proxy(p, {
            get(target, key) {
              if (['rank', 'mine', 'bomb', 'flag'].includes(key)) throw Error(`Read hidden ${key}`)
              return target[key]
            },
          })
        : p,
    ),
  }
  const safe = k.observeJunqi(guarded, -1, k.createJunqiKnowledge(guarded))
  assert.deepEqual(safe, observation)
  const choice = k.chooseJunqiChallenge(safe)
  assert(choice && j.canMove(game, ...choice), 'Challenge must choose a legal own move')
  const swapped = { ...game, board: game.board.map((p) => (p ? { ...p } : null)) }
  const places = swapped.board.flatMap((p, at) =>
    p?.side === 1 && p.rank >= 1 && p.rank <= 9 ? [at] : [],
  )
  const a = places[0],
    b = places[1]
  ;[swapped.board[a].rank, swapped.board[b].rank] = [swapped.board[b].rank, swapped.board[a].rank]
  const alternate = k.observeJunqi(swapped, -1, k.createJunqiKnowledge(swapped))
  assert.deepEqual(
    alternate,
    observation,
    'Changing unrevealed ranks cannot change the observation',
  )
  assert.deepEqual(
    k.chooseJunqiChallenge(alternate),
    choice,
    'AI cannot use unrevealed enemy ranks',
  )
  assert.deepEqual(k.createJunqiKnowledge(game), knowledge, 'Inference and scoring are immutable')
}
const turning = state(
  [
    [1, unit(10, -1, 100)],
    [58, unit(10, 1, 101)],
    [10, unit(1, -1, 102)],
    [55, unit(5, 1, 103)],
  ],
  -1,
)
const start = k.createJunqiKnowledge(turning)
const turned = j.moveJunqi(turning, 10, 9)
const learned = k.advanceJunqiKnowledge(start, turning, turned, 10, 9)
assert.equal(
  k.observeJunqi(turned, 1, learned).board[9].rank,
  1,
  'A railway turn identifies the engineer',
)
assert.equal(start.views[1][102].moved, false, 'Earlier snapshots must remain unchanged')
assert(k.guessJunqiPiece(k.observeJunqi(turned, 1, learned), 102).certain)
const attack = state([
  [1, unit(10, -1, 100)],
  [58, unit(10, 1, 101)],
  [30, unit(9, 1, 102)],
  [25, unit(1, -1, 103)],
  [10, unit(5, -1, 104)],
])
const initial = k.createJunqiKnowledge(attack),
  after = j.moveJunqi(attack, 30, 25)
const inferred = k.advanceJunqiKnowledge(initial, attack, after, 30, 25)
const belief = k.observeJunqi(after, -1, inferred).board[25]
assert.equal(belief.rank, null)
assert(
  belief.candidates.includes(9) && !belief.candidates.includes(1),
  'A battle narrows ranks without exposing the winner',
)
const alternate = { ...attack, board: attack.board.map((p) => (p ? { ...p } : null)) }
alternate.board[30].rank = 8
const altAfter = j.moveJunqi(alternate, 30, 25)
assert.deepEqual(
  k.observeJunqi(
    altAfter,
    -1,
    k.advanceJunqiKnowledge(k.createJunqiKnowledge(alternate), alternate, altAfter, 30, 25),
  ),
  k.observeJunqi(after, -1, inferred),
  'Same public verdict gives the same computer knowledge',
)
const commander = state(
  [
    [1, unit(10, -1, 100)],
    [58, unit(10, 1, 101)],
    [35, unit(9, 1, 102)],
    [20, unit(11, -1, 103)],
    [10, unit(5, -1, 104)],
  ],
  -1,
)
const before = k.createJunqiKnowledge(commander)
const bombMove = j.moveJunqi(commander, 20, 30)
const withMove = k.advanceJunqiKnowledge(before, commander, bombMove, 20, 30)
const lost = j.moveJunqi(bombMove, 35, 30)
const revealed = k.advanceJunqiKnowledge(withMove, bombMove, lost, 35, 30)
assert(revealed.revealedSides.includes(1))
assert.equal(
  k.observeJunqi(lost, -1, revealed).board[58].rank,
  10,
  'Commander loss publicly reveals the flag',
)
assert.equal(
  k.observeJunqi(commander, -1, before).board[58].rank,
  null,
  'Undo snapshots keep the former flag hidden',
)
const signals = state(
  [
    [1, unit(10, -1, 100)],
    [58, unit(10, 1, 101)],
    [5, unit(7, -1, 102)],
    [9, unit(7, -1, 103)],
    [50, unit(1, 1, 104)],
    [54, unit(1, 1, 105)],
  ],
  -1,
)
const observed = k.observeJunqi(signals, -1, k.createJunqiKnowledge(signals))
const baseline = k.chooseJunqiChallenge(observed)
const marked = k.chooseJunqiChallenge(observed, { [signals.board[baseline[0]].id]: 10 })
assert.notEqual(marked[0], baseline[0], 'Explicitly shared guesses must affect computer decisions')
for (const piece of observed.board.filter((p) => p?.side === 1)) {
  const guess = k.guessJunqiPiece(observed, piece.id)
  assert(Math.abs(guess.distribution.reduce((sum, p) => sum + p.weight, 0) - 1) < 1e-9)
}
assert.equal(k.chooseJunqiChallenge({ ...observed, finished: true }), null)
const publicEnding = k.observeJunqi(
  { ...signals, finished: 1 },
  -1,
  k.createJunqiKnowledge(signals),
)
assert(
  publicEnding.board.filter(Boolean).every((piece) => piece.rank !== null),
  'Remaining ranks are public after the result',
)
console.log(
  'Junqi challenge: 100 masked observations, no hidden-rank reads, fair moves, battle/rail deductions, flag revelation, immutable undo and shared signals passed.',
)
