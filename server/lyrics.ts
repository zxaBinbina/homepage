import music from '../src/data/music.json'

const allowedIds = new Set(music.tracks.map((track) => String(track.id)))

export async function lyricsResponse(url: URL): Promise<Response> {
  const id = url.searchParams.get('id') || ''
  if (!allowedIds.has(id)) return Response.json({ error: '歌曲不在歌单中' }, { status: 404 })
  try {
    const upstream = await fetch(
      `https://music.163.com/api/song/lyric?id=${id}&lv=-1&kv=-1&tv=-1`,
      {
        headers: { Referer: 'https://music.163.com/', 'User-Agent': 'Mozilla/5.0' },
        signal: AbortSignal.timeout(8000),
      },
    )
    if (!upstream.ok) throw new Error('Lyrics upstream unavailable')
    const data = (await upstream.json()) as {
      code: number
      pureMusic?: boolean
      nolyric?: boolean
      lrc?: { lyric?: string }
      tlyric?: { lyric?: string }
    }
    if (data.code !== 200) throw new Error('Lyrics API error')
    return Response.json(
      {
        instrumental: Boolean(data.pureMusic || data.nolyric),
        lyric: data.lrc?.lyric || '',
        translation: data.tlyric?.lyric || '',
      },
      { headers: { 'Cache-Control': 'public, max-age=3600', 'X-Content-Type-Options': 'nosniff' } },
    )
  } catch {
    return Response.json(
      { error: '歌词暂时无法加载' },
      { status: 503, headers: { 'Cache-Control': 'no-store' } },
    )
  }
}
