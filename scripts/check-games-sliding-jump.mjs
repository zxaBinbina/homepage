import assert from 'node:assert/strict'
import { build } from 'esbuild'

async function moduleFor(name) {
  const result = await build({
    entryPoints: [`src/games/${name}.ts`],
    bundle: true,
    format: 'esm',
    write: false,
  })
  return import(
    `data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString('base64')}`
  )
}
const [s, j] = await Promise.all(['huarongdao', 'jump'].map(moduleFor))
let seed = 28
const random = () => (seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 2 ** 32
for (const size of [3, 4, 5]) {
  const goal = Array.from({ length: size * size }, (_, i) => (i + 1) % (size * size))
  assert.equal(s.slidingSolved(goal), true)
  assert.equal(s.slidingSolvable(goal, size), true)
  const bad = [...goal]
  ;[bad[0], bad[1]] = [bad[1], bad[0]]
  assert.equal(s.slidingSolvable(bad, size), false)
  for (const rng of [() => 0, () => 0.999999, ...Array(120).fill(random)]) {
    let game = s.newSliding(size, rng)
    assert.equal(s.slidingSolved(game.board), false)
    assert.equal(s.slidingSolvable(game.board, size), true)
    assert.deepEqual(
      [...game.board].sort((a, b) => a - b),
      Array.from({ length: size * size }, (_, i) => i),
    )
    for (let move = 0; move < 30 && !s.slidingSolved(game.board); move++) {
      const before = game,
        blank = game.board.indexOf(0)
      const adjacent = s.slidingNeighbors(blank, size)
      const index = adjacent[Math.floor(random() * adjacent.length)]
      game = s.moveSliding(game, game.board[index])
      assert.equal(game.moves, before.moves + 1)
      assert.equal(game.board.indexOf(0), index)
      assert.equal(before.board[blank], 0, 'Do not mutate undo history')
      assert.equal(s.slidingSolvable(game.board, size), true)
    }
  }
  const almost = s.newSliding(size, () => 0.999999)
  assert.equal(s.moveSliding(almost, 1), almost, 'Nonadjacent tile cannot move')
  assert.equal(s.moveSliding(almost, 0), almost)
  assert.equal(s.moveSliding(almost, 999), almost)
  const win = s.moveSliding(almost, size * size - 1)
  assert.equal(s.slidingSolved(win.board), true)
  assert.equal(win.moves, 1)
  assert.equal(s.moveSliding(win, size * size - 1), win, 'Win locks moves')
}
assert.deepEqual(s.slidingNeighbors(3, 3).sort(), [0, 4, 6], 'No row wrap')

let game = j.newJump()
const durationFor = (x) => ((x - game.x) / j.JUMP_DISTANCE) * j.JUMP_CHARGE_MS
assert.equal(j.jumpPower(-1), 0)
assert.equal(j.jumpPower(600), 0.5)
assert.equal(j.jumpPower(12000), 1)
assert.equal(j.jumpLanding(game, 0).target, 'current')
assert.equal(j.landJump(game, 90).score, 0, 'Short hop does not earn points')
assert.equal(j.landJump(game, 90).status, 'playing')
assert.equal(j.landJump(game, 300).status, 'lost', 'Landing in gap loses')
assert.equal(j.landJump(game, 1200).status, 'lost', 'Overshoot loses')
const edge = game.next.x - game.next.width / 2 + j.JUMP_FOOT
assert.equal(j.onJumpPlatform(edge, game.next), true)
assert.equal(j.onJumpPlatform(edge - 0.01, game.next), false)
assert.equal(j.onJumpPlatform(game.next.x + game.next.width / 2 - j.JUMP_FOOT, game.next), true)
const first = j.landJump(game, durationFor(game.next.x), random)
assert.equal(first.score, 1)
assert.equal(first.current.id, 1)
assert.equal(game.score, 0, 'Immutable state')
const lost = j.landJump(game, 1200)
assert.equal(j.landJump(lost, 630), lost)
for (let i = 0; i < 500; i++) {
  const old = game
  game = j.landJump(game, durationFor(game.next.x), random)
  assert.equal(game.score, i + 1)
  assert.equal(game.status, 'playing')
  assert.equal(game.previous.id, old.current.id)
  assert.equal(game.current.id, old.next.id)
  assert.ok(game.next.width >= 64 && game.next.width <= 100)
  assert.ok(game.next.x - game.next.width / 2 > game.current.x + game.current.width / 2)
  const farthestStart = game.current.x - game.current.width / 2 + j.JUMP_FOOT
  assert.ok(game.next.x - farthestStart < j.JUMP_DISTANCE, 'Every target remains reachable')
  assert.ok(
    game.next.x - game.current.x + 140 + game.next.width / 2 + 12 < 600,
    'Next platform fits scene',
  )
}
console.log(
  'Sliding / jump rules passed: 366 solvable shuffles, legal moves, immutable undo, sorted finish; charge limits, safe edges, gap/overshoot, scores and 500 reachable platforms.',
)
