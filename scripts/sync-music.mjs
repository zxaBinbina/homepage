// Refresh public playlist metadata only. Audio stays on NetEase's servers.
import { mkdir, writeFile, rename } from 'node:fs/promises'

const playlistId = 8410450907
const defaultTrackId = 2613484729
const endpoint = 'https://music.163.com'
async function get(path) {
  const response = await fetch(`${endpoint}${path}`, {
    headers: { Referer: `${endpoint}/`, 'User-Agent': 'Mozilla/5.0' },
    signal: AbortSignal.timeout(20000),
  })
  if (!response.ok) throw new Error(`NetEase HTTP ${response.status}`)
  const data = await response.json()
  if (data.code !== 200) throw new Error(`NetEase API code ${data.code}`)
  return data
}

try {
  const { playlist } = await get(`/api/v6/playlist/detail?id=${playlistId}&n=1000`)
  if (!playlist?.trackIds?.length) throw new Error('Playlist is empty or unavailable')
  const ids = playlist.trackIds.map((track) => track.id)
  if (
    ids.some((id) => !Number.isSafeInteger(id) || id <= 0) ||
    new Set(ids).size !== ids.length ||
    playlist.trackCount !== ids.length
  ) {
    throw new Error('The playlist track list is incomplete or invalid')
  }
  const details = new Map()
  for (let start = 0; start < ids.length; start += 100) {
    const batch = encodeURIComponent(JSON.stringify(ids.slice(start, start + 100)))
    const { songs } = await get(`/api/song/detail/?ids=${batch}`)
    for (const song of songs) {
      if (!song.id || !song.name) continue
      details.set(song.id, {
        id: song.id,
        title: song.name,
        artist: song.artists.map((artist) => artist.name).join(' / '),
        album: song.album.name,
        cover: song.album.picUrl.replace(/^http:/, 'https:'),
        duration: Math.round(song.duration / 1000),
        // NetEase fee=1 is VIP; fee=4 (paid album) and fee=8 (paid download) are distinct.
        vip: song.fee === 1,
      })
    }
  }
  if (ids.some((id) => !details.has(id))) {
    throw new Error('Some song details are missing; refusing to save a partial playlist')
  }
  if (!ids.includes(defaultTrackId) || !details.has(defaultTrackId)) {
    throw new Error('The default song is missing from the public playlist')
  }
  const data = {
    playlistId,
    name: playlist.name,
    url: `${endpoint}/#/playlist?id=${playlistId}`,
    defaultTrackId,
    updatedAt: new Date().toISOString(),
    total: ids.length,
    tracks: ids.map((id) => details.get(id)),
  }
  const directory = new URL('../src/data/', import.meta.url)
  const temporary = new URL('music.json.tmp', directory)
  await mkdir(directory, { recursive: true })
  await writeFile(temporary, `${JSON.stringify(data, null, 2)}\n`)
  await rename(temporary, new URL('music.json', directory))
  console.log(
    `Synced ${data.tracks.length}/${ids.length} songs in NetEase order. Default: ${details.get(defaultTrackId).title}`,
  )
} catch (error) {
  console.error(`Music sync failed; existing metadata was preserved. ${error.message}`)
  process.exitCode = 1
}
