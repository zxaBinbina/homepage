import assert from 'node:assert/strict'
import { build } from 'esbuild'

async function load(path) {
  const result = await build({
    entryPoints: [path],
    bundle: true,
    format: 'esm',
    platform: 'browser',
    write: false,
  })
  return import(
    `data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString('base64')}`
  )
}
const { parseLrc, mergeLyrics } = await load('src/utils/lyrics.ts')
assert.deepEqual(
  parseLrc(
    '[ar:Test]\n[offset:500]\n[00:01.50][00:03.50]First test line\n[00:02.00]Second test line',
  ),
  [
    { time: 1, text: 'First test line' },
    { time: 1.5, text: 'Second test line' },
    { time: 3, text: 'First test line' },
  ],
)
assert.equal(parseLrc('plain text').length, 0)
assert.deepEqual(mergeLyrics('[00:01.0]Test line', '[00:01.00]测试行'), [
  { time: 1, text: 'Test line', translation: '测试行' },
])

const { onRequestGet } = await load('functions/api/music/lyrics.ts')
const request = (id) => ({ request: new Request(`https://example.test/api/music/lyrics?id=${id}`) })
const originalFetch = globalThis.fetch
let calls = 0
try {
  globalThis.fetch = async (url) => {
    calls++
    assert.equal(new URL(url).hostname, 'music.163.com')
    return Response.json({
      code: 200,
      pureMusic: true,
      lrc: { lyric: '[00:00.00]Test' },
      tlyric: { lyric: '' },
    })
  }
  const valid = await onRequestGet(request('2613484729'))
  assert.equal(valid.status, 200)
  assert.equal((await valid.json()).instrumental, true)
  assert.equal(valid.headers.get('cache-control'), 'public, max-age=3600')
  const invalid = await onRequestGet(request('https://elsewhere.test'))
  assert.equal(invalid.status, 404)
  assert.equal(calls, 1)
  globalThis.fetch = async () => new Response('', { status: 503 })
  const failed = await onRequestGet(request('2613484729'))
  assert.equal(failed.status, 503)
  assert.equal(failed.headers.get('cache-control'), 'no-store')
  console.log(
    'LRC timestamps, repeated lines, offset, translation, Pages worker bundle, allowlist and upstream failure: passed.',
  )
} finally {
  globalThis.fetch = originalFetch
}
