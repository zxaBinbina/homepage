import assert from 'node:assert/strict'
import { build } from 'esbuild'
import { Miniflare, Log, LogLevel, convertV4MiniflareOptions } from 'miniflare'

const bundled = await build({
  entryPoints: ['functions/api/projects/SPTL/release.ts'],
  bundle: true,
  write: false,
  format: 'esm',
  platform: 'browser',
})
const { onRequest } = await import(
  `data:text/javascript;base64,${Buffer.from(bundled.outputFiles[0].text).toString('base64')}`
)
const repo = 'https://github.com/zxaBinbina/SplayerPlasmaTaskbarLyrics'
const request = (method = 'GET') => ({
  request: new Request('https://example.test/api/projects/SPTL/release', { method }),
})
const payload = {
  tag_name: 'v1.3.0',
  html_url: `${repo}/releases/tag/v1.3.0`,
  published_at: '2026-12-01T00:00:00Z',
  body: 'A new release',
  draft: false,
  prerelease: false,
  assets: [
    {
      name: 'sptl-source-1.3.0.tar.gz',
      browser_download_url: `${repo}/releases/download/v1.3.0/sptl-source-1.3.0.tar.gz`,
      size: 123,
    },
  ],
}
const fetchOriginal = globalThis.fetch
try {
  let calls = 0
  globalThis.fetch = async (url) => {
    calls++
    assert.equal(new URL(url).hostname, 'api.github.com')
    return Response.json(payload)
  }
  const response = await onRequest(request())
  assert.equal(response.status, 200)
  const release = await response.json()
  assert.equal(release.version, '1.3.0')
  assert.equal(release.body, payload.body)
  assert.equal(release.assets[0].url, payload.assets[0].browser_download_url)
  assert.match(response.headers.get('cache-control'), /s-maxage=300/)
  assert.equal((await onRequest(request('POST'))).status, 405)
  assert.equal(calls, 1)

  globalThis.fetch = async (url) => {
    if (url.includes('api.github.com')) return new Response('', { status: 403 })
    if (url.endsWith('/releases/latest')) {
      const page = new Response('latest page')
      Object.defineProperty(page, 'url', { value: `${repo}/releases/tag/v1.4.0` })
      return page
    }
    assert.equal(url, `${repo}/releases/expanded_assets/v1.4.0`)
    return new Response(
      '<a href="/zxaBinbina/SplayerPlasmaTaskbarLyrics/releases/download/v1.4.0/sptl-source-1.4.0.tar.gz">Source</a>',
    )
  }
  const fallback = await onRequest(request())
  assert.equal(fallback.status, 200)
  assert.equal((await fallback.json()).version, '1.4.0')

  globalThis.fetch = async () => new Response('', { status: 503 })
  const failed = await onRequest(request())
  assert.equal(failed.status, 503)
  assert.equal(failed.headers.get('cache-control'), 'no-store')

  globalThis.fetch = async (url) => {
    if (url.includes('api.github.com'))
      return Response.json({
        ...payload,
        assets: [
          { ...payload.assets[0], browser_download_url: 'https://example.com/malicious.tar.gz' },
        ],
      })
    return new Response('', { status: 404 })
  }
  assert.equal((await onRequest(request())).status, 503)
  const previousCaches = globalThis.caches
  const cache = new Map()
  let upstreamCalls = 0
  globalThis.caches = {
    default: {
      match: async (key) => cache.get(key.url)?.clone(),
      put: async (key, response) => {
        cache.set(key.url, response.clone())
      },
    },
  }
  try {
    globalThis.fetch = async () => {
      upstreamCalls++
      return Response.json(payload)
    }
    assert.equal((await onRequest(request())).status, 200)
    assert.equal((await onRequest(request())).status, 200)
    assert.equal(upstreamCalls, 1, 'The edge cache must reuse a successful release response')
  } finally {
    if (previousCaches === undefined) delete globalThis.caches
    else globalThis.caches = previousCaches
  }
  console.log(
    'SPTL latest version, cache, API rate limit fallback, upstream failures and asset origin checks passed',
  )
} finally {
  globalThis.fetch = fetchOriginal
}

// Exercise the production dispatcher so an unregistered API fails this regression check.
const workerBundle = await build({
  entryPoints: ['worker/index.ts'],
  bundle: true,
  write: false,
  format: 'esm',
  platform: 'browser',
  external: ['cloudflare:workers'],
})
let workerUpstreamCalls = 0
const runtime = new Miniflare(
  convertV4MiniflareOptions({
    modules: true,
    script: workerBundle.outputFiles[0].text,
    compatibilityDate: '2026-11-25',
    log: new Log(LogLevel.ERROR),
    host: '127.0.0.1',
    port: 0,
    durableObjects: {
      ROOMS: { className: 'GameRoom', useSQLite: true },
      ROOM_DIRECTORY: { className: 'RoomDirectory', useSQLite: true },
    },
    outboundService: async (request) => {
      workerUpstreamCalls++
      assert.equal(new URL(request.url).hostname, 'api.github.com')
      return Response.json(payload)
    },
  }),
)
try {
  const url = 'https://example.test/api/projects/SPTL/release'
  const response = await runtime.dispatchFetch(url)
  assert.equal(response.status, 200)
  assert.equal((await response.json()).version, '1.3.0')
  assert.equal((await runtime.dispatchFetch(url)).status, 200)
  assert.equal(workerUpstreamCalls, 1, 'The production Worker must cache release responses')
  const rejected = await runtime.dispatchFetch(url, { method: 'POST' })
  assert.equal(rejected.status, 405)
  assert.equal(rejected.headers.get('allow'), 'GET')
  assert.equal(workerUpstreamCalls, 1)
  console.log('SPTL production Worker routing, edge cache and method handling passed')
} finally {
  await runtime.dispose()
}
