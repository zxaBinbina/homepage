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
const [s, p] = await Promise.all(['snake', 'popstar'].map(moduleFor))
const point = (x, y) => ({ x, y })
let snake = s.newSnake(() => 0)
assert.equal(snake.body.length, 3)
assert.deepEqual(snake.food, point(0, 0))
assert.equal(s.canTurn('right', 'left'), false)
assert.equal(s.canTurn('right', 'right'), false)
assert.equal(s.canTurn('right', 'up'), true)
assert.equal(s.canTurn('up', 'left'), true)
assert.equal(s.canTurn('up', 'down'), false)
assert.deepEqual(s.stepSnake(snake, 'left').body[0], point(6, 9), 'Reverse input is ignored')
snake.food = point(6, 9)
let next = s.stepSnake(snake, 'right', () => 0)
assert.equal(next.score, 10)
assert.equal(next.body.length, 4)
assert.equal(snake.body.length, 3, 'Rules do not mutate history')
assert.ok(!next.body.some((cell) => s.samePoint(cell, next.food)))
assert.equal(s.stepSnake({ ...snake, body: [point(17, 9), point(16, 9)] }).status, 'lost')
const loop = {
  ...snake,
  food: point(0, 0),
  direction: 'up',
  body: [point(2, 2), point(2, 3), point(3, 3), point(3, 2)],
}
assert.equal(s.stepSnake(loop, 'right').status, 'playing', 'Moving into vacating tail is legal')
assert.equal(s.stepSnake({ ...loop, body: [...loop.body, point(4, 2)] }, 'right').status, 'lost')
const full = { ...snake, size: 2, body: [point(0, 0), point(0, 1), point(1, 1)], food: point(1, 0) }
next = s.stepSnake(full)
assert.equal(next.status, 'won')
assert.equal(next.food, null)
assert.equal(next.body.length, 4)
assert.equal(s.stepSnake(next), next)
assert.equal(s.snakeInterval(50, 1), s.snakeInterval(0, 1) - 10)
assert.equal(s.snakeInterval(100000, 2), 75)

function board(entries) {
  const result = Array(100).fill(null)
  for (const [index, color] of entries) result[index] = { id: index, color }
  return result
}
const state = (b) => ({ board: b, level: 1, score: 0, bonus: 0, status: 'playing' })
assert.deepEqual(
  p.starGroup(
    board([
      [9, 0],
      [10, 0],
    ]),
    9,
  ),
  [9],
  'No row wrapping',
)
assert.deepEqual(
  p.starGroup(
    board([
      [0, 0],
      [11, 0],
    ]),
    0,
  ),
  [0],
  'No diagonal connection',
)
assert.deepEqual(
  p.starGroup(
    board([
      [0, 0],
      [1, 0],
      [11, 0],
      [12, 1],
    ]),
    0,
  ),
  [0, 1, 11],
)
assert.equal(
  p.hasStarMove(
    board([
      [0, 0],
      [11, 0],
    ]),
  ),
  false,
)
assert.equal(p.starPoints(1), 0)
assert.equal(p.starPoints(2), 20)
assert.equal(p.starPoints(10), 500)
assert.deepEqual([0, 1, 9, 10, 20].map(p.starBonus), [2000, 1980, 380, 0, 0])
assert.deepEqual([1, 2, 3, 4, 5].map(p.starTarget), [1000, 3000, 6000, 8000, 10000])
let stars = state(
  board([
    [70, 1],
    [80, 0],
    [90, 0],
    [71, 2],
    [81, 2],
    [91, 3],
    [82, 0],
    [92, 0],
  ]),
)
next = p.popStars(stars, 90)
assert.equal(next.board[90].id, 70, 'Gravity preserves survivor identity')
assert.equal(next.score, 20)
assert.equal(next.status, 'playing')
assert.equal(stars.board[90].id, 90, 'No mutation')
next = p.popStars(next, 92)
assert.equal(next.board[92], null, 'Empty columns are removed')
stars = state(
  board([
    [80, 0],
    [90, 0],
    [81, 1],
    [91, 2],
    [83, 3],
    [93, 3],
  ]),
)
next = p.popStars(stars, 90)
assert.equal(next.board[80].id, 81, 'Columns shift left preserving order')
assert.equal(next.board[90].id, 91)
assert.equal(next.board[81].id, 83)
assert.equal(next.board[91].id, 93)
assert.equal(p.popStars(next, 90), next, 'Singleton is not removable')
next = p.popStars(
  state(
    board([
      [90, 0],
      [91, 0],
    ]),
  ),
  90,
)
assert.equal(next.status, 'passed')
assert.equal(next.score, 2020)
assert.equal(next.bonus, 2000)
assert.equal(p.popStars(next, 90), next, 'Bonus applied exactly once')
stars = p.nextStarLevel(next, () => 0)
assert.equal(stars.level, 2)
assert.equal(stars.score, 2020)
assert.equal(stars.bonus, 0)
next = p.popStars(
  {
    ...state(
      board([
        [90, 0],
        [91, 0],
      ]),
    ),
    level: 2,
  },
  90,
)
assert.equal(next.status, 'lost')
assert.equal(p.nextStarLevel(next), next)
next = p.popStars(
  {
    ...state(
      board([
        [90, 0],
        [91, 0],
      ]),
    ),
    level: 2,
    score: 980,
  },
  90,
)
assert.equal(next.status, 'passed', 'Exact target passes')
// Random complete rounds conserve identities and settle every column with no gaps.
let seed = 6
const random = () => (seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 2 ** 32
for (let round = 0; round < 60; round++) {
  stars = p.newPopstar(1, 0, random)
  assert.ok(p.hasStarMove(stars.board))
  while (stars.status === 'playing') {
    const index = stars.board.findIndex(
      (tile, i) => tile && p.starGroup(stars.board, i).length >= 2,
    )
    assert.ok(index >= 0)
    const old = stars,
      count = p.starGroup(old.board, index).length
    stars = p.popStars(old, index)
    const survivors = stars.board.filter(Boolean)
    assert.equal(survivors.length, old.board.filter(Boolean).length - count)
    assert.equal(new Set(survivors.map((tile) => tile.id)).size, survivors.length)
    assert.equal(stars.score - old.score, p.starPoints(count) + stars.bonus)
    let emptyColumn = false
    for (let x = 0; x < 10; x++) {
      if (!stars.board[90 + x]) emptyColumn = true
      else assert.equal(emptyColumn, false)
      let seen = false
      for (let y = 0; y < 10; y++) {
        if (stars.board[y * 10 + x]) seen = true
        else assert.equal(seen, false, 'No holes below tiles')
      }
    }
  }
}
console.log(
  'Arcade rules passed: snake growth, collisions, tail, reverse and full board; stars connectivity, gravity, scoring, bonus, targets and 60 complete rounds.',
)
