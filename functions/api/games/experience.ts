const allowedGames = new Set(['chess', 'go', 'gomoku', 'xiangqi'])
const cors = { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }

type Env = { GAME_EXPERIENCE?: KVNamespace }
type Context = { request: Request; env: Env }
type RecordBody = {
  kind: string
  key: string
  move: number | { from: string; to: string; promotion?: string }
}

function validMove(kind: string, move: unknown) {
  if (kind === 'chess') {
    if (!move || typeof move !== 'object') return false
    const value = move as Record<string, unknown>
    return (
      typeof value.from === 'string' &&
      /^[a-h][1-8]$/.test(value.from) &&
      typeof value.to === 'string' &&
      /^[a-h][1-8]$/.test(value.to)
    )
  }
  if (kind === 'xiangqi') {
    if (!move || typeof move !== 'object') return false
    const value = move as Record<string, unknown>
    return (
      Number.isInteger(value.from) &&
      Number(value.from) >= 0 &&
      Number(value.from) < 90 &&
      Number.isInteger(value.to) &&
      Number(value.to) >= 0 &&
      Number(value.to) < 90
    )
  }
  return (
    Number.isInteger(move) &&
    (move as number) >= (kind === 'go' ? -1 : 0) &&
    (move as number) < (kind === 'go' ? 81 : kind === 'gomoku' ? 225 : 90)
  )
}

export async function onRequestPost({ request, env }: Context) {
  if (!env.GAME_EXPERIENCE)
    return new Response(JSON.stringify({ error: 'experience storage unavailable' }), {
      status: 503,
      headers: cors,
    })
  let body: RecordBody
  try {
    body = (await request.json()) as RecordBody
  } catch {
    return new Response(JSON.stringify({ error: 'invalid json' }), { status: 400, headers: cors })
  }
  if (
    !allowedGames.has(body.kind) ||
    typeof body.key !== 'string' ||
    body.key.length < 2 ||
    body.key.length > 1200 ||
    !validMove(body.kind, body.move)
  )
    return new Response(JSON.stringify({ error: 'invalid experience' }), {
      status: 400,
      headers: cors,
    })
  const key = `v1:${body.kind}:${await digest(body.key)}`
  const raw = await env.GAME_EXPERIENCE.get(key)
  let moves: Record<string, number> = {}
  try {
    moves = raw ? (JSON.parse(raw) as Record<string, number>) : {}
  } catch {
    moves = {}
  }
  const moveKey = JSON.stringify(body.move)
  moves[moveKey] = Math.min((moves[moveKey] || 0) + 1, 10000)
  const top = Object.entries(moves)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
  await env.GAME_EXPERIENCE.put(key, JSON.stringify(Object.fromEntries(top)))
  return new Response(JSON.stringify({ saved: true }), { status: 202, headers: cors })
}

export async function onRequestGet({ request, env }: Context) {
  const url = new URL(request.url)
  const kind = url.searchParams.get('kind') || ''
  const keyValue = url.searchParams.get('key') || ''
  if (!env.GAME_EXPERIENCE)
    return new Response(JSON.stringify({ error: 'experience storage unavailable' }), {
      status: 503,
      headers: cors,
    })
  if (!allowedGames.has(kind) || keyValue.length < 2 || keyValue.length > 1200)
    return new Response(JSON.stringify({ error: 'invalid experience' }), {
      status: 400,
      headers: cors,
    })
  const raw = await env.GAME_EXPERIENCE.get(`v1:${kind}:${await digest(keyValue)}`)
  let moves: Record<string, number> = {}
  try {
    moves = raw ? (JSON.parse(raw) as Record<string, number>) : {}
  } catch {
    moves = {}
  }
  const move = Object.entries(moves).sort((a, b) => b[1] - a[1])[0]
  return new Response(
    JSON.stringify({ move: move ? JSON.parse(move[0]) : null, count: move?.[1] || 0 }),
    { headers: cors },
  )
}

interface KVNamespace {
  get(key: string): Promise<string | null>
  put(key: string, value: string): Promise<void>
}

async function digest(value: string) {
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))
  return [...new Uint8Array(bytes)].map((byte) => byte.toString(16).padStart(2, '0')).join('')
}
