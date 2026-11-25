const allowedGames = new Set(['chess', 'go', 'gomoku', 'xiangqi'])
const cors = { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }

type Env = { GAME_EXPERIENCE?: KVNamespace }
type Context = { request: Request; env: Env }
type RecordBody = {
  kind: string
  observations: { key: string; move: unknown; result: -1 | 0 | 1 }[]
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
    !Array.isArray(body.observations) ||
    body.observations.length > 500 ||
    body.observations.some(
      (item) =>
        !item ||
        typeof item.key !== 'string' ||
        item.key.length < 2 ||
        item.key.length > 1200 ||
        ![-1, 0, 1].includes(item.result) ||
        !validMove(body.kind, item.move),
    )
  )
    return new Response(JSON.stringify({ error: 'invalid experience' }), {
      status: 400,
      headers: cors,
    })
  const aggregate = new Map<
    string,
    Record<string, { wins: number; draws: number; losses: number }>
  >()
  for (const item of body.observations) {
    const key = `v2:${body.kind}:${await digest(item.key)}`
    let moves = aggregate.get(key)
    if (!moves) {
      moves = {}
      const raw = await env.GAME_EXPERIENCE.get(key)
      try {
        if (raw) Object.assign(moves, JSON.parse(raw))
      } catch {
        /* Ignore damaged aggregate rows. */
      }
      aggregate.set(key, moves)
    }
    const moveKey = JSON.stringify(item.move)
    const stats = moves[moveKey] || (moves[moveKey] = { wins: 0, draws: 0, losses: 0 })
    const field = item.result > 0 ? 'wins' : item.result < 0 ? 'losses' : 'draws'
    stats[field] = Math.min(stats[field] + 1, 10000)
  }
  for (const [key, moves] of aggregate) {
    const top = Object.entries(moves)
      .sort((a, b) => total(b[1]) - total(a[1]))
      .slice(0, 8)
    await env.GAME_EXPERIENCE.put(key, JSON.stringify(Object.fromEntries(top)))
  }
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
  const raw = await env.GAME_EXPERIENCE.get(`v2:${kind}:${await digest(keyValue)}`)
  let moves: Record<string, { wins: number; draws: number; losses: number }> = {}
  try {
    moves = raw
      ? (JSON.parse(raw) as Record<string, { wins: number; draws: number; losses: number }>)
      : {}
  } catch {
    moves = {}
  }
  const move = Object.entries(moves)
    .filter(([, stats]) => total(stats) >= 20 && wilsonLowerBound(stats) > 0.5)
    .sort((a, b) => wilsonLowerBound(b[1]) - wilsonLowerBound(a[1]))[0]
  const samples = move ? total(move[1]) : 0
  const winRate = move && samples ? (move[1].wins + move[1].draws * 0.5) / samples : 0
  return new Response(
    JSON.stringify({ move: move ? JSON.parse(move[0]) : null, samples, winRate }),
    { headers: cors },
  )
}

function total(value: { wins: number; draws: number; losses: number }) {
  return value.wins + value.draws + value.losses
}
function wilsonLowerBound(value: { wins: number; draws: number; losses: number }) {
  const samples = total(value)
  if (!samples) return 0
  const rate = (value.wins + value.draws * 0.5) / samples
  const z = 1.96
  const denominator = 1 + (z * z) / samples
  const center = rate + (z * z) / (2 * samples)
  const margin = z * Math.sqrt((rate * (1 - rate) + (z * z) / (4 * samples)) / samples)
  return (center - margin) / denominator
}

interface KVNamespace {
  get(key: string): Promise<string | null>
  put(key: string, value: string): Promise<void>
}

async function digest(value: string) {
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))
  return [...new Uint8Array(bytes)].map((byte) => byte.toString(16).padStart(2, '0')).join('')
}
