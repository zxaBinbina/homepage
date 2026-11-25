import assert from 'node:assert/strict'
import { build } from 'esbuild'
import { Miniflare, Log, LogLevel, convertV4MiniflareOptions } from 'miniflare'
import { gzipSync } from 'node:zlib'
import { mkdtemp, rm, readdir, stat } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const engineBundle = await build({
  entryPoints: ['src/games/multiplayer/engine.ts'],
  bundle: true,
  format: 'esm',
  write: false,
})
const engine = await import(
  'data:text/javascript;base64,' + Buffer.from(engineBundle.outputFiles[0].text).toString('base64')
)
const settings = { turnSeconds: 0, undo: 'ask', junqi: 'open' }
for (const kind of ['xiangqi', 'gomoku', 'chess', 'go', 'doudizhu', 'junqi']) {
  const game = engine.newOnlineGame(kind)
  if (kind === 'junqi')
    for (const seat of [0, 1]) engine.actOnlineGame(game, settings, seat, { type: 'setup-ready' })
  for (let step = 0; step < 4; step++) {
    const before = JSON.stringify(game)
    assert.throws(
      () =>
        engine.actOnlineGame(
          game,
          settings,
          (engine.gameTurn(game) + 1) % (kind === 'doudizhu' ? 3 : 2),
          { type: 'move', to: 0 },
        ),
      /轮到你/,
    )
    assert.equal(JSON.stringify(game), before, 'Rejected commands must not mutate the game')
    engine.actOnlineGame(
      game,
      settings,
      engine.gameTurn(game),
      engine.automaticAction(game, settings),
    )
    assert.equal(game.ply, step + 1)
  }
}
const undo = engine.newOnlineGame('gomoku')
for (const [seat, to] of [
  [0, 112],
  [1, 113],
  [0, 114],
  [1, 115],
])
  engine.actOnlineGame(undo, settings, seat, { type: 'move', to })
engine.undoOnlineGame(undo, 0)
assert.equal(undo.ply, 2)
assert.equal(undo.position.board[114], 0)
assert.equal(undo.position.board[115], 0)
assert.equal(engine.undoAllowed(undo, { ...settings, undo: 'disabled' }, 0), false)
const hidden = engine.newOnlineGame('junqi'),
  hiddenSettings = { ...settings, junqi: 'hidden' }
for (const seat of [0, 1]) {
  const view = engine.projectGame(hidden, hiddenSettings, seat)
  assert.equal(
    view.board.filter((p) => p?.side === (seat === 0 ? 1 : -1)).every((p) => !p.hidden),
    true,
  )
  assert.equal(
    view.board.some((p) => p?.side !== (seat === 0 ? 1 : -1) && p?.hidden),
    true,
  )
  assert.equal(JSON.stringify(view).includes('knowledge'), false)
  engine.actOnlineGame(hidden, hiddenSettings, seat, { type: 'setup-ready' })
}
engine.actOnlineGame(hidden, hiddenSettings, 0, engine.automaticAction(hidden, hiddenSettings))
assert.equal(hidden.history.length, 0)
assert.equal(engine.undoAllowed(hidden, hiddenSettings, 0), false)
const cards = engine.newOnlineGame('doudizhu')
assert.equal(engine.projectGame(cards, settings, 0).hand.length, 17)
assert.equal(engine.projectGame(cards, settings, 0).bottom.length, 0)
assert.deepEqual(engine.projectGame(cards, settings, 0).counts, [17, 17, 17])
engine.actOnlineGame(cards, settings, 0, { type: 'move', bid: 3 })
const foreign = cards.position.hands[1][0].id
assert.throws(
  () => engine.actOnlineGame(cards, settings, 0, { type: 'move', cards: [foreign] }),
  /自己的手牌/,
)
assert.equal(engine.projectGame(cards, settings, 1).hand.length, 17)
const go = engine.newOnlineGame('go')
engine.actOnlineGame(go, settings, 0, { type: 'move', to: 40 })
engine.actOnlineGame(go, settings, 1, { type: 'move', to: 41 })
engine.actOnlineGame(go, settings, 0, { type: 'move', to: -1 })
engine.actOnlineGame(go, settings, 1, { type: 'move', to: -1 })
engine.actOnlineGame(go, settings, 0, { type: 'score' })
assert.equal(go.result, null)
engine.actOnlineGame(go, settings, 1, { type: 'dead', to: 40 })
assert.deepEqual(go.scoreReady, [])
for (const seat of [0, 1]) engine.actOnlineGame(go, settings, seat, { type: 'score' })
assert.equal(engine.gameStatus(go), 'finished')
console.log(
  'Six rule adapters, bounded computer moves, undo, hidden information and bilateral Go scoring: passed.',
)

const bundle = await build({
  entryPoints: ['worker/index.ts'],
  bundle: true,
  format: 'esm',
  platform: 'browser',
  external: ['cloudflare:workers'],
  write: false,
})
assert.ok(
  gzipSync(bundle.outputFiles[0].contents).length < 3 * 1024 * 1024,
  'Free Workers bundle limit',
)
async function checkAssets(path) {
  let count = 0
  for (const entry of await readdir(path, { withFileTypes: true })) {
    const file = join(path, entry.name)
    if (entry.isDirectory()) count += await checkAssets(file)
    else {
      assert.ok(
        (await stat(file)).size <= 25 * 1024 * 1024,
        'Free Workers single-file limit: ' + file,
      )
      count++
    }
  }
  return count
}
assert.ok((await checkAssets('dist')) <= 20000)
const persistence = await mkdtemp(join(tmpdir(), 'homepage-rooms-'))
let verificationCount = 0
const spent = new Set()
const runtimeOptions = {
  name: 'homepage-test',
  modules: true,
  script: bundle.outputFiles[0].text,
  compatibilityDate: '2026-11-25',
  log: new Log(LogLevel.ERROR),
  host: '127.0.0.1',
  port: process.argv.includes('--serve') ? 8796 : 0,
  durableObjects: {
    ROOMS: { className: 'GameRoom', useSQLite: true },
    ROOM_DIRECTORY: { className: 'RoomDirectory', useSQLite: true },
  },
  resourcePersistencePath: persistence,
  kvNamespaces: ['GAME_EXPERIENCE'],
  bindings: {
    SITE_ORIGIN: 'https://zxabinbina.cc.cd',
    TURNSTILE_SITE_KEY: '1x00000000000000000000AA',
    TURNSTILE_SECRET_KEY: 'test-secret',
    ...(process.argv.includes('--serve') ? {} : { LOCAL_TEST_TIMERS: 'true' }),
  },
  assets: {
    directory: 'dist',
    binding: 'ASSETS',
    run_worker_first: ['/api/*', '/office-viewer/v0.2.0/wasm/prebuilt/x2t.wasm.br'],
    routerConfig: { has_user_worker: true },
    assetConfig: { html_handling: 'auto-trailing-slash', not_found_handling: '404-page' },
  },
  outboundService: async (request) => {
    const url = new URL(request.url)
    if (url.hostname === 'challenges.cloudflare.com') {
      assert.equal(url.pathname, '/turnstile/v0/siteverify')
      const body = await request.json()
      assert.equal(body.secret, 'test-secret')
      verificationCount++
      const success = body.response !== 'invalid' && !spent.has(body.response)
      if (!process.argv.includes('--serve')) spent.add(body.response)
      return Response.json({
        success,
        hostname: 'zxabinbina.cc.cd',
        action: body.response?.startsWith('join-') ? 'room_join' : 'room_create',
      })
    }
    if (url.hostname === 'music.163.com') return Response.json({ code: 200, pureMusic: true })
    return new Response('', { status: 404 })
  },
}
let mf = new Miniflare(convertV4MiniflareOptions(runtimeOptions))
await mf.ready
if (process.argv.includes('--serve')) {
  console.log(
    'Local browser fixture at http://127.0.0.1:8796; only this fixture mocks Siteverify. Production never bypasses verification.',
  )
  await new Promise((resolve) => {
    process.once('SIGINT', resolve)
    process.once('SIGTERM', resolve)
  })
  await mf.dispose()
  await rm(persistence, { recursive: true, force: true })
  process.exit(0)
}
const root = 'https://zxabinbina.cc.cd'
let sequence = 0
async function post(path, body, origin = root) {
  const response = await mf.dispatchFetch(root + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: origin },
    body: JSON.stringify(body),
  })
  return { status: response.status, data: await response.json() }
}
const proof = (join) => (join ? 'join-' : 'create-') + ++sequence
async function create(kind, name = '房主') {
  const result = await post('/api/games/rooms', { kind, name, turnstileToken: proof(false) })
  assert.equal(result.status, 200, JSON.stringify(result))
  assert.match(result.data.code, /^[1-9]\d{5}$/)
  return result.data
}
async function joinRoom(session, name) {
  const result = await post('/api/games/rooms/join', {
    code: session.code,
    name,
    turnstileToken: proof(true),
  })
  assert.equal(result.status, 200, JSON.stringify(result))
  return result.data
}
function until(predicate, message = 'state update', timeout = 8000) {
  return new Promise((resolve, reject) => {
    const started = Date.now()
    const interval = setInterval(() => {
      if (predicate()) {
        clearInterval(interval)
        resolve()
      } else if (Date.now() - started > timeout) {
        clearInterval(interval)
        reject(new Error('Timed out: ' + message))
      }
    }, 10)
  })
}
async function connect(session) {
  const response = await mf.dispatchFetch(root + '/api/games/rooms/' + session.code + '/connect', {
    headers: { Upgrade: 'websocket', Origin: root },
  })
  assert.equal(response.status, 101)
  const ws = response.webSocket,
    client = { ws, room: null, errors: [], closed: false }
  ws.accept()
  ws.addEventListener('message', (event) => {
    const value = JSON.parse(event.data)
    if (value.type === 'state') client.room = value.room
    if (value.type === 'error') client.errors.push(value.message)
    if (value.type === 'closed' || value.type === 'left') client.closed = true
  })
  ws.send(JSON.stringify({ type: 'hello', token: session.token }))
  await until(() => client.room, 'authenticated connection')
  client.send = async (command) => {
    const revision = client.room.revision,
      errors = client.errors.length,
      lastChat = client.room.chat.at(-1)?.id
    ws.send(JSON.stringify({ ...command, revision }))
    await until(
      () =>
        client.room.revision > revision ||
        (command.type === 'chat' && client.room.chat.at(-1)?.id !== lastChat) ||
        client.errors.length > errors ||
        client.closed,
      command.type,
    )
    assert.equal(client.errors.length, errors, client.errors.at(-1))
  }
  return client
}
async function start(a, b) {
  await until(() => a.room.players.length >= 2 && b.room.players.length >= 2)
  await a.send({ type: 'ready', ready: true })
  await until(() => b.room.players.find((p) => p.id === a.room.selfId)?.ready)
  await b.send({ type: 'ready', ready: true })
  await until(() => a.room.players.every((p) => p.ready))
  await a.send({ type: 'start' })
  await until(() => b.room.phase === 'playing')
}
try {
  const wasm = await fetch(
    new URL('/office-viewer/v0.2.0/wasm/prebuilt/x2t.wasm.br', await mf.ready),
    {
      headers: { 'Accept-Encoding': 'gzip, br' },
    },
  )
  assert.equal(wasm.status, 200)
  assert.deepEqual(
    [...new Uint8Array(await wasm.arrayBuffer()).slice(0, 8)],
    [0, 97, 115, 109, 1, 0, 0, 0],
    'Precompressed Office WASM must decode to a real module',
  )
  assert.equal(
    (
      await post(
        '/api/games/rooms',
        { kind: 'go', name: '访客', turnstileToken: proof(false) },
        'https://untrusted.test',
      )
    ).status,
    403,
  )
  assert.equal((await post('/api/games/rooms', { kind: 'go', name: '访客' })).status, 400)
  assert.equal(
    (await post('/api/games/rooms', { kind: 'go', name: '访客', turnstileToken: 'invalid' }))
      .status,
    400,
  )
  const replayToken = proof(false)
  await post('/api/games/rooms', { kind: 'gomoku', name: '访客', turnstileToken: replayToken })
  assert.equal(
    (await post('/api/games/rooms', { kind: 'gomoku', name: '访客', turnstileToken: replayToken }))
      .status,
    400,
  )
  const sessions = await Promise.all(Array.from({ length: 8 }, () => create('gomoku')))
  assert.equal(
    new Set(sessions.map((s) => s.code)).size,
    sessions.length,
    'Concurrent room numbers must be unique',
  )
  for (const kind of ['gomoku', 'xiangqi', 'chess', 'go', 'junqi']) {
    const s = await create(kind),
      a = await connect(s),
      b = await connect(await joinRoom(s, '朋友'))
    await start(a, b)
    const late = await post('/api/games/rooms/join', {
      code: s.code,
      name: '新玩家',
      turnstileToken: proof(true),
    })
    assert.equal(late.status, 409)
    if (kind === 'junqi') {
      await a.send({ type: 'setup-ready' })
      await until(() => b.room.game.setupReady.includes(0))
      await b.send({ type: 'setup-ready' })
      await until(() => a.room.game.status === 'playing')
    }
    const move =
      kind === 'gomoku' || kind === 'go'
        ? { to: 40 }
        : kind === 'chess'
          ? { from: 52, to: 36 }
          : (() => {
              const from = Number(Object.keys(a.room.game.targets)[0])
              return { from, to: a.room.game.targets[from][0] }
            })()
    await a.send({ type: 'move', ...move })
    await until(() => b.room.game.ply === 1)
    assert.deepEqual(a.room.game.board, b.room.game.board)
    await a.send({ type: 'undo' })
    await until(() => b.room.proposal)
    await b.send({ type: 'answer', proposalId: b.room.proposal.id, accept: true })
    await until(() => a.room.game.ply === 0)
    await a.send({ type: 'chat', text: '<script>只是文字</script>' })
    await until(() => b.room.chat.some((m) => m.text.includes('<script>')))
    a.ws.close()
    await until(() => b.room.pauseUntil)
    const restored = await connect(s)
    await until(() => !b.room.pauseUntil)
    assert.equal(restored.room.selfId, a.room.selfId)
    await restored.send({ type: 'restart' })
    await until(() => b.room.proposal)
    await b.send({ type: 'answer', proposalId: b.room.proposal.id, accept: true })
    await until(() => restored.room.phase === 'lobby')
    await restored.send({ type: 'leave' })
    await until(() => b.room.hostId === b.room.selfId)
    await b.send({ type: 'leave' })
    await until(() => b.closed)
    assert.equal(
      (
        await post('/api/games/rooms/join', {
          code: s.code,
          name: '新朋友',
          turnstileToken: proof(true),
        })
      ).status,
      404,
    )
  }
  const ddSession = await create('doudizhu'),
    dd = await connect(ddSession)
  await dd.send({ type: 'ready', ready: true })
  await dd.send({ type: 'start' })
  assert.equal(dd.room.players.filter((p) => p.bot).length, 2)
  assert.equal(dd.room.game.hand.length, 17)
  assert.equal(dd.room.game.bottom.length, 0)
  await dd.send({ type: 'move', bid: 3 })
  await until(() => dd.room.game.landlord === 0)
  assert.equal(dd.room.game.hand.length, 20)
  await dd.send({ type: 'leave' })
  await until(() => dd.closed)
  const trio = await create('doudizhu'),
    trioClients = [await connect(trio)]
  trioClients.push(
    await connect(await joinRoom(trio, '朋友甲')),
    await connect(await joinRoom(trio, '朋友乙')),
  )
  for (const client of trioClients) {
    await client.send({ type: 'ready', ready: true })
    await until(() =>
      trioClients.every((c) => c.room.players.find((p) => p.id === client.room.selfId)?.ready),
    )
  }
  await trioClients[0].send({ type: 'start' })
  await until(() => trioClients.every((c) => c.room.phase === 'playing'))
  assert.equal(trioClients[0].room.players.filter((p) => p.bot).length, 0)
  assert.equal(
    new Set(trioClients.flatMap((c) => c.room.game.hand.map((card) => card.id))).size,
    51,
  )
  await trioClients[0].send({ type: 'move', bid: 3 })
  await until(() => trioClients.every((c) => c.room.game.landlord === 0))
  assert.deepEqual(
    trioClients.map((c) => c.room.game.hand.length),
    [20, 17, 17],
  )
  assert.equal(
    (
      await post('/api/games/rooms/join', {
        code: trio.code,
        name: '第四人',
        turnstileToken: proof(true),
      })
    ).status,
    409,
  )
  for (const client of trioClients) await client.send({ type: 'leave' })
  for (const kind of ['xiangqi', 'gomoku', 'chess', 'go', 'doudizhu', 'junqi']) {
    const session = await create(kind),
      a = await connect(session),
      b = await connect(await joinRoom(session, '朋友'))
    await a.send({ type: 'settings', settings: { ...settings, turnSeconds: 30 } })
    await until(() => b.room.settings.turnSeconds === 30)
    await start(a, b)
    if (kind === 'junqi') {
      await a.send({ type: 'setup-ready' })
      await until(() => b.room.game.setupReady.includes(0))
      await b.send({ type: 'setup-ready' })
    }
    await until(() => a.room.game.ply >= 1, kind + ' timed computer move')
    assert.equal(
      a.room.players.filter((p) => !p.bot).every((p) => !p.auto),
      true,
      'Timeout must return control to humans',
    )
    await a.send({ type: 'leave' })
    await b.send({ type: 'leave' })
  }
  const lostSession = await create('chess'),
    lostHost = await connect(lostSession),
    survivor = await connect(await joinRoom(lostSession, '朋友'))
  await start(lostHost, survivor)
  lostHost.ws.close()
  await until(() => survivor.room.phase === 'finished', 'disconnect forfeit')
  assert.equal(survivor.room.hostId, survivor.room.selfId)
  const nextPlayer = await connect(await joinRoom(lostSession, '下一位朋友'))
  assert.equal(nextPlayer.room.game, null, 'A new member must not inherit an old match or undo it')
  await survivor.send({ type: 'leave' })
  await nextPlayer.send({ type: 'leave' })
  const allGone = await create('gomoku'),
    idle = await connect(allGone)
  idle.ws.close()
  await new Promise((resolve) => setTimeout(resolve, 1800))
  assert.equal(
    (
      await post('/api/games/rooms/join', {
        code: allGone.code,
        name: '新朋友',
        turnstileToken: proof(true),
      })
    ).status,
    404,
  )
  assert.ok(verificationCount > 20)
  runtimeOptions.bindings.LOCAL_TEST_TIMERS = 'false'
  await mf.setOptions(convertV4MiniflareOptions(runtimeOptions))
  const persistentSession = await create('gomoku'),
    persistentGuest = await joinRoom(persistentSession, '持久化朋友')
  const beforeRestartA = await connect(persistentSession),
    beforeRestartB = await connect(persistentGuest)
  await start(beforeRestartA, beforeRestartB)
  await beforeRestartA.send({ type: 'move', to: 112 })
  await beforeRestartA.send({ type: 'chat', text: '重启后仍应保留' })
  await mf.dispose()
  mf = new Miniflare(convertV4MiniflareOptions(runtimeOptions))
  await mf.ready
  const afterRestartA = await connect(persistentSession),
    afterRestartB = await connect(persistentGuest)
  assert.equal(afterRestartA.room.selfId, beforeRestartA.room.selfId)
  assert.equal(afterRestartA.room.game.ply, 1)
  assert.equal(afterRestartA.room.game.board[112].side, 1)
  assert.ok(afterRestartA.room.chat.some((m) => m.text === '重启后仍应保留'))
  await afterRestartA.send({ type: 'leave' })
  await afterRestartB.send({ type: 'leave' })
  assert.equal((await mf.dispatchFetch(root + '/api/music/lyrics?id=2613484729')).status, 200)
  assert.equal((await mf.dispatchFetch(root + '/games/gomoku')).status, 200)
  assert.equal((await mf.dispatchFetch(root + '/not-a-page/deep')).status, 404)
  console.log(
    'Turnstile enforcement, concurrent rooms, five two-player games, bots, consent, chat, reconnection, host transfer, cleanup and Workers assets: passed.',
  )
} finally {
  await mf.dispose()
  await rm(persistence, { recursive: true, force: true })
}
