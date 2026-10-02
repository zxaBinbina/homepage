import assert from 'node:assert/strict'
import { copyFile, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { spawnSync } from 'node:child_process'

const directory = await mkdtemp(join(tmpdir(), 'homepage-music-sync-'))
try {
  await mkdir(join(directory, 'scripts'))
  await mkdir(join(directory, 'src/data'), { recursive: true })
  const script = join(directory, 'scripts/sync-music.mjs')
  const snapshot = join(directory, 'src/data/music.json')
  const mock = join(directory, 'mock.mjs')
  await copyFile(new URL('./sync-music.mjs', import.meta.url), script)
  await writeFile(
    mock,
    `
const scenario = process.env.MUSIC_SYNC_CASE
globalThis.fetch = async (url) => {
  if (scenario === 'http-error') return new Response('', { status: 503 })
  if (scenario === 'api-error') return Response.json({ code: 403 })
  if (String(url).includes('/playlist/detail')) {
    let ids = [101, 2613484729, 202]
    if (scenario === 'no-default') ids = [101, 202]
    if (scenario === 'duplicate') ids = [101, 2613484729, 101]
    if (scenario === 'empty') ids = []
    return Response.json({ code: 200, playlist: {
      name: 'Test playlist',
      trackCount: scenario === 'truncated' ? 10 : ids.length,
      trackIds: ids.map(id => ({ id })),
    } })
  }
  let ids = JSON.parse(new URL(url).searchParams.get('ids')).reverse()
  if (scenario === 'partial-details') ids = ids.filter(id => id !== 202)
  return Response.json({ code: 200, songs: ids.map(id => ({
    id, name: 'Track ' + id,
    artists: [{ name: 'Artist' }],
    album: { name: 'Album', picUrl: 'http://example.test/cover.jpg' },
    duration: 180000, fee: id === 101 ? 1 : id === 202 ? 8 : 0,
  })) })
}
`,
  )
  function run(scenario) {
    return spawnSync(process.execPath, ['--import', mock, script], {
      env: { ...process.env, MUSIC_SYNC_CASE: scenario },
      encoding: 'utf8',
      timeout: 10000,
    })
  }

  const success = run('complete')
  assert.equal(success.status, 0, success.stderr)
  const saved = await readFile(snapshot, 'utf8')
  const data = JSON.parse(saved)
  assert.deepEqual(
    data.tracks.map((track) => track.id),
    [101, 2613484729, 202],
  )
  assert.equal(data.defaultTrackId, 2613484729)
  assert.equal(data.total, 3)
  assert.deepEqual(
    data.tracks.map((track) => track.vip),
    [true, false, false],
  )
  assert.ok(data.tracks.every((track) => track.cover.startsWith('https://')))
  assert.ok(Number.isFinite(Date.parse(data.updatedAt)))

  for (const scenario of [
    'http-error',
    'api-error',
    'truncated',
    'partial-details',
    'duplicate',
    'empty',
    'no-default',
  ]) {
    const result = run(scenario)
    assert.equal(result.status, 1, `${scenario}: ${result.stderr}`)
    assert.equal(await readFile(snapshot, 'utf8'), saved, `${scenario} overwrote the snapshot`)
  }
  console.log(
    'Music sync: order, VIP, complete snapshot and preservation on upstream failures passed.',
  )
} finally {
  await rm(directory, { recursive: true, force: true })
}
