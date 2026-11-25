import type { Env } from './env'
import { RoomDirectory, GameRoom, json } from './rooms'
import { lyricsResponse } from '../server/lyrics'
import { onRequestGet, onRequestPost } from '../server/gameExperience'
import { turnstileSiteKey, verifyTurnstile } from './turnstile'
export { RoomDirectory, GameRoom }
function validOrigin(request: Request, env: Env) {
  const origin = request.headers.get('Origin')
  if (!origin) return false
  const target = new URL(request.url)
  if (origin === target.origin || origin === env.SITE_ORIGIN) return true
  try {
    return (
      ['127.0.0.1', 'localhost', '[::1]'].includes(target.hostname) &&
      ['127.0.0.1', 'localhost', '[::1]'].includes(new URL(origin).hostname)
    )
  } catch {
    return false
  }
}
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url)
    if (url.pathname === '/office-viewer/v0.2.0/wasm/prebuilt/x2t.wasm.br') {
      // Assets' automatic compression must not re-encode an already Brotli-compressed module.
      const headers = new Headers(request.headers)
      headers.set('Accept-Encoding', 'identity')
      const asset = await env.ASSETS.fetch(new Request(request, { headers }))
      const responseHeaders = new Headers(asset.headers)
      if (asset.status === 200) {
        responseHeaders.set('Content-Type', 'application/wasm')
        responseHeaders.set('Content-Encoding', 'br')
      }
      return new Response(asset.body, {
        status: asset.status,
        headers: responseHeaders,
        encodeBody: 'manual',
      })
    }
    if (!url.pathname.startsWith('/api/')) return env.ASSETS.fetch(request)
    if (url.pathname === '/api/music/lyrics')
      return request.method === 'GET'
        ? lyricsResponse(url)
        : json({ error: 'method not allowed' }, 405)
    if (url.pathname === '/api/games/experience') {
      if (request.method === 'GET') return onRequestGet({ request, env })
      if (request.method === 'POST') return onRequestPost({ request, env })
      return json({ error: 'method not allowed' }, 405)
    }
    if (url.pathname.startsWith('/api/games/rooms')) {
      if (url.pathname === '/api/games/rooms/config' && request.method === 'GET')
        return json({ siteKey: turnstileSiteKey(request, env) })
      if (!validOrigin(request, env)) return json({ error: '请从本站游戏页面进入房间。' }, 403)
      try {
        const directory = env.ROOM_DIRECTORY.getByName('directory')
        const match = /^\/api\/games\/rooms\/([1-9]\d{5})\/connect$/.exec(url.pathname)
        if (
          match &&
          request.method === 'GET' &&
          request.headers.get('Upgrade')?.toLowerCase() === 'websocket'
        ) {
          const roomId = await directory.locate(match[1]!)
          if (!roomId) return json({ error: '房间不存在或已解散。' }, 404)
          return env.ROOMS.getByName(roomId).fetch(request)
        }
        if (
          request.method !== 'POST' ||
          !['/api/games/rooms', '/api/games/rooms/join'].includes(url.pathname)
        )
          return json({ error: '接口不存在。' }, 404)
        const ip = request.headers.get('CF-Connecting-IP') ?? 'local'
        if (env.ROOM_LIMIT && !(await env.ROOM_LIMIT.limit({ key: ip })).success)
          return json({ error: '创建或加入房间太频繁，请稍后再试。' }, 429)
        const body = await request.text()
        if (body.length > 4096) return json({ error: '请求内容过长。' }, 413)
        const data = JSON.parse(body) as { turnstileToken?: unknown }
        await verifyTurnstile(
          request,
          env,
          data.turnstileToken,
          url.pathname.endsWith('/join') ? 'room_join' : 'room_create',
        )
        return await directory.fetch(
          new Request('https://directory/' + (url.pathname.endsWith('/join') ? 'join' : 'new'), {
            method: 'POST',
            body,
          }),
        )
      } catch (error) {
        return json(
          { error: error instanceof Error ? error.message : '房间服务暂时不可用，请稍后重试。' },
          400,
        )
      }
    }
    return json({ error: '接口不存在。' }, 404)
  },
} satisfies ExportedHandler<Env>
