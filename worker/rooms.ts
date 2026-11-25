import { DurableObject } from 'cloudflare:workers'
import type { Env } from './env'
import {
  isOnlineKind,
  type OnlineKind,
  type RoomSettings,
  type RoomPlayer,
  type RoomSnapshot,
  type RoomCommand,
} from '../src/games/multiplayer/types'
import {
  newOnlineGame,
  gameStatus,
  gameTurn,
  actOnlineGame,
  projectGame,
  automaticAction,
  undoAllowed,
  undoOnlineGame,
  resignOnlineGame,
  type OnlineGame,
} from '../src/games/multiplayer/engine'
export const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
  })
type Player = RoomPlayer & { token: string; disconnectedAt: number | null; left: boolean }
type StoredRoom = {
  code: string
  roomId: string
  kind: OnlineKind
  players: Player[]
  hostId: string
  settings: RoomSettings
  phase: RoomSnapshot['phase']
  revision: number
  game: OnlineGame | null
  gamePlayers: string[]
  chat: RoomSnapshot['chat']
  proposal: RoomSnapshot['proposal']
  deadline: number | null
  pausedRemaining: number | null
  notice: string
}
type Attachment = { playerId: string | null; openedAt: number; lastMessage: number; burst: number }
const defaults: RoomSettings = { turnSeconds: 0, undo: 'ask', junqi: 'open' }
const token = () => crypto.randomUUID() + crypto.randomUUID()
export function validName(value: unknown) {
  if (typeof value !== 'string') throw new Error('请填写昵称。')
  const name = value.trim()
  if (!name || [...name].length > 16 || /[\p{Cc}\p{Cf}]/u.test(name))
    throw new Error('昵称需要 1～16 个可见字符。')
  return name
}
export function validSettings(value: unknown): RoomSettings {
  if (!value || typeof value !== 'object') throw new Error('房间设置不完整。')
  const v = value as RoomSettings
  if (
    ![0, 30, 60, 120].includes(v.turnSeconds) ||
    !['enabled', 'ask', 'disabled'].includes(v.undo) ||
    !['open', 'hidden'].includes(v.junqi)
  )
    throw new Error('请选择有效的房间设置。')
  return { turnSeconds: v.turnSeconds, undo: v.undo, junqi: v.junqi }
}
export class RoomDirectory extends DurableObject<Env> {
  async fetch(request: Request) {
    const body = (await request.json()) as {
      kind?: unknown
      name?: unknown
      code?: unknown
      token?: unknown
    }
    if (new URL(request.url).pathname === '/new') {
      if (!isOnlineKind(body.kind)) return json({ error: '这款游戏暂不支持联机。' }, 400)
      const name = validName(body.name),
        roomId = crypto.randomUUID()
      const code = await this.ctx.storage.transaction(async (storage) => {
        for (let attempt = 0; attempt < 50; attempt++) {
          const bytes = crypto.getRandomValues(new Uint32Array(1))[0]!
          const candidate = String(100000 + (bytes % 900000))
          if (await storage.get(candidate)) continue
          await storage.put(candidate, { roomId })
          return candidate
        }
        throw new Error('暂时没有可用房间号，请稍后重试。')
      })
      try {
        const response = await this.env.ROOMS.getByName(roomId).fetch(
          new Request('https://room/initialize', {
            method: 'POST',
            body: JSON.stringify({ code, roomId, kind: body.kind, name }),
          }),
        )
        if (!(await this.ctx.storage.getAlarm()))
          await this.ctx.storage.setAlarm(Date.now() + 3600000)
        return response
      } catch (error) {
        await this.release(code, roomId)
        throw error
      }
    }
    if (typeof body.code !== 'string' || !/^[1-9]\d{5}$/.test(body.code))
      return json({ error: '请输入 6 位数字房间号。' }, 400)
    const record = await this.ctx.storage.get<{ roomId: string }>(body.code)
    if (!record) return json({ error: '房间不存在或已解散。' }, 404)
    return this.env.ROOMS.getByName(record.roomId).fetch(
      new Request('https://room/join', {
        method: 'POST',
        body: JSON.stringify({ name: body.name, token: body.token }),
      }),
    )
  }
  async locate(code: string) {
    return (await this.ctx.storage.get<{ roomId: string }>(code))?.roomId ?? null
  }
  async release(code: string, roomId: string) {
    await this.ctx.storage.transaction(async (storage) => {
      if ((await storage.get<{ roomId: string }>(code))?.roomId === roomId)
        await storage.delete(code)
    })
  }
  async alarm() {
    const records = await this.ctx.storage.list<{ roomId: string }>()
    for (const [code, record] of records)
      if (!(await this.env.ROOMS.getByName(record.roomId).isAlive()))
        await this.release(code, record.roomId)
    if ((await this.ctx.storage.list({ limit: 1 })).size)
      await this.ctx.storage.setAlarm(Date.now() + 3600000)
  }
}
export class GameRoom extends DurableObject<Env> {
  private room: StoredRoom | null = null
  private chain: Promise<unknown> = Promise.resolve()
  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env)
    ctx.blockConcurrencyWhile(async () => {
      ctx.storage.sql.exec(
        'CREATE TABLE IF NOT EXISTS room_state (id INTEGER PRIMARY KEY CHECK (id = 1), payload TEXT NOT NULL)',
      )
      const stored = ctx.storage.sql
        .exec<{ payload: string }>('SELECT payload FROM room_state WHERE id = 1')
        .toArray()[0]
      this.room = stored
        ? (JSON.parse(stored.payload) as StoredRoom)
        : ((await ctx.storage.get<StoredRoom>('room')) ?? null)
      if (!this.room) return
      let changed = false
      const live = new Set(
        ctx.getWebSockets().map((ws) => (ws.deserializeAttachment() as Attachment)?.playerId),
      )
      for (const p of this.room.players) {
        if (!p.bot && !p.left && p.connected && !live.has(p.id)) {
          p.connected = false
          p.disconnectedAt = Date.now()
          p.ready = false
          changed = true
        }
      }
      if (changed || !stored) {
        this.room.revision++
        this.adjustClock()
        await this.save()
        await ctx.storage.delete('room')
      }
    })
  }
  isAlive() {
    return this.room !== null
  }
  private serial<T>(work: () => Promise<T>): Promise<T> {
    const next = this.chain.then(work, work)
    this.chain = next.catch(() => {})
    return next
  }
  private get grace() {
    return this.env.LOCAL_TEST_TIMERS === 'true' ? 1200 : 180000
  }
  private addPlayer(name: string, seat: number): Player {
    return {
      id: crypto.randomUUID(),
      token: token(),
      name,
      seat,
      ready: false,
      connected: false,
      bot: false,
      auto: false,
      disconnectedAt: Date.now(),
      left: false,
    }
  }
  private humans() {
    return this.room!.players.filter((p) => !p.bot && !p.left)
  }
  private visiblePlayers(): RoomPlayer[] {
    const room = this.room!
    return room.players.flatMap((p) => {
      if (p.left)
        return room.kind === 'doudizhu' && room.phase === 'playing'
          ? [
              {
                id: 'bot-' + p.seat,
                name: '电脑 ' + (p.seat + 1),
                seat: p.seat,
                ready: true,
                connected: true,
                bot: true,
                auto: true,
              },
            ]
          : []
      const { id, name, seat, ready, connected, bot, auto } = p
      return [{ id, name, seat, ready, connected, bot, auto }]
    })
  }
  private sameParticipants() {
    return this.room!.gamePlayers.every((id, seat) =>
      this.room!.players.some((p) => p.id === id && p.seat === seat && !p.left),
    )
  }
  private pauseUntil() {
    const waiting = this.humans().filter(
      (p) => !p.connected && !p.auto && p.disconnectedAt !== null,
    )
    return waiting.length ? Math.min(...waiting.map((p) => p.disconnectedAt! + this.grace)) : null
  }
  private transferHost() {
    const room = this.room!,
      host = room.players.find((p) => p.id === room.hostId)
    if (
      !host ||
      host.left ||
      host.auto ||
      (!host.connected &&
        host.disconnectedAt !== null &&
        host.disconnectedAt + this.grace <= Date.now())
    )
      room.hostId = this.humans().find((p) => p.connected)?.id ?? this.humans()[0]?.id ?? ''
  }
  private snapshot(player: Player): RoomSnapshot {
    const room = this.room!
    const game = room.game
      ? projectGame(
          room.game,
          room.settings,
          player.seat,
          room.gamePlayers[player.seat] === player.id,
        )
      : null
    if (game && !this.sameParticipants()) game.canUndo = false
    return {
      code: room.code,
      kind: room.kind,
      selfId: player.id,
      hostId: room.hostId,
      phase: room.phase,
      revision: room.revision,
      serverTime: Date.now(),
      settings: room.settings,
      players: this.visiblePlayers(),
      game,
      chat: room.chat,
      proposal: room.proposal,
      deadline: room.deadline,
      pauseUntil: this.pauseUntil(),
      notice: room.notice,
    }
  }
  private send(ws: WebSocket, payload: unknown) {
    try {
      ws.send(JSON.stringify(payload))
    } catch {
      /* close event handles disconnects */
    }
  }
  private broadcast() {
    if (!this.room) return
    for (const ws of this.ctx.getWebSockets()) {
      const attachment = ws.deserializeAttachment() as Attachment
      const player = this.room.players.find(
        (p) => p.id === attachment.playerId && !p.left && !p.bot,
      )
      if (player) this.send(ws, { type: 'state', room: this.snapshot(player) })
    }
  }
  private async save() {
    if (this.room) {
      this.ctx.storage.sql.exec(
        'INSERT INTO room_state (id, payload) VALUES (1, ?) ON CONFLICT(id) DO UPDATE SET payload = excluded.payload',
        JSON.stringify(this.room),
      )
      this.broadcast()
      await this.schedule()
    }
  }
  private async schedule() {
    if (!this.room) return
    const room = this.room,
      times: number[] = [],
      waiting = this.pauseUntil()
    if (waiting) times.push(waiting)
    if (room.deadline) times.push(room.deadline)
    if (room.proposal) times.push(room.proposal.expiresAt)
    if (!this.humans().some((p) => p.connected))
      times.push(Math.max(...this.humans().map((p) => p.disconnectedAt ?? Date.now())) + this.grace)
    for (const ws of this.ctx.getWebSockets()) {
      const a = ws.deserializeAttachment() as Attachment
      if (!a.playerId) times.push(a.openedAt + 10000)
    }
    if (room.game && room.phase === 'playing' && gameStatus(room.game) === 'playing' && !waiting) {
      const player = room.players.find((p) => p.seat === gameTurn(room.game!))
      if (player?.bot || player?.auto || player?.left)
        times.push(Date.now() + (this.env.LOCAL_TEST_TIMERS === 'true' ? 30 : 650))
    }
    if (times.length) await this.ctx.storage.setAlarm(Math.max(Date.now() + 20, Math.min(...times)))
    else await this.ctx.storage.deleteAlarm()
  }
  private adjustClock(reset = false) {
    const room = this.room!,
      pause = this.pauseUntil()
    const duration = room.settings.turnSeconds * (this.env.LOCAL_TEST_TIMERS === 'true' ? 10 : 1000)
    if (!room.game || room.phase !== 'playing' || gameStatus(room.game) !== 'playing') {
      room.deadline = null
      room.pausedRemaining = null
      return
    }
    if (pause) {
      if (room.deadline !== null) room.pausedRemaining = Math.max(0, room.deadline - Date.now())
      else if (reset) room.pausedRemaining = duration
      room.deadline = null
    } else if (room.settings.turnSeconds) {
      room.deadline =
        Date.now() +
        (reset
          ? duration
          : (room.pausedRemaining ??
            Math.max(0, (room.deadline ?? Date.now() + duration) - Date.now())))
      room.pausedRemaining = null
    } else room.deadline = null
  }
  private finishIfNeeded() {
    if (this.room!.game?.result && this.room!.phase === 'playing') {
      this.room!.phase = 'finished'
      this.room!.proposal = null
      this.room!.players.forEach((p) => {
        p.ready = p.bot
        if (
          !p.bot &&
          !p.connected &&
          p.disconnectedAt !== null &&
          p.disconnectedAt + this.grace <= Date.now()
        ) {
          p.left = true
          p.token = ''
        }
      })
      this.transferHost()
      this.adjustClock()
    }
  }
  private async destroy() {
    const room = this.room
    if (!room) return
    this.room = null
    for (const ws of this.ctx.getWebSockets()) {
      this.send(ws, { type: 'closed', message: '房间已解散，聊天与对局已清空。' })
      ws.close(1000, 'room closed')
    }
    await this.ctx.storage.deleteAll()
    await this.ctx.storage.deleteAlarm()
    await this.env.ROOM_DIRECTORY.getByName('directory').release(room.code, room.roomId)
  }
  async fetch(request: Request) {
    return this.serial(async () => {
      const path = new URL(request.url).pathname
      if (path === '/initialize') {
        if (this.room) return json({ error: '房间已创建。' }, 409)
        const body = (await request.json()) as {
            code: string
            roomId: string
            kind: OnlineKind
            name: string
          },
          player = this.addPlayer(validName(body.name), 0)
        this.room = {
          code: body.code,
          roomId: body.roomId,
          kind: body.kind,
          players: [player],
          hostId: player.id,
          settings: { ...defaults },
          phase: 'lobby',
          revision: 1,
          game: null,
          gamePlayers: [],
          chat: [],
          proposal: null,
          deadline: null,
          pausedRemaining: null,
          notice: '分享房间号，等朋友一起准备。',
        }
        await this.save()
        return json({ code: body.code, kind: body.kind, token: player.token })
      }
      if (!this.room) return json({ error: '房间不存在或已解散。' }, 404)
      if (path === '/join') {
        const body = (await request.json()) as { name?: unknown; token?: unknown }
        let player =
          typeof body.token === 'string'
            ? this.humans().find((p) => p.token === body.token)
            : undefined
        if (body.token && !player) return json({ error: '原席位已失效，请重新加入房间。' }, 403)
        if (!player) {
          if (this.room.phase === 'playing')
            return json({ error: '本局正在进行，请在对局结束后加入。' }, 409)
          const name = validName(body.name)
          if (this.humans().some((p) => p.name === name))
            return json({ error: '房间内已有这个昵称，请换一个。' }, 409)
          const capacity = this.room.kind === 'doudizhu' ? 3 : 2
          const seat = Array.from({ length: capacity }, (_, s) => s).find(
            (s) => !this.room!.players.some((p) => p.seat === s && !p.left && !p.bot),
          )
          if (seat === undefined) return json({ error: '房间席位已满。' }, 409)
          player = this.addPlayer(name, seat)
          if (this.room.phase === 'finished') {
            this.room.game = null
            this.room.gamePlayers = []
            this.room.phase = 'lobby'
            this.room.proposal = null
            this.room.notice = '有新朋友加入，请准备开始下一局。'
          }
          this.room.players = this.room.players.filter((p) => p.seat !== seat)
          this.room.players.push(player)
          this.room.players.forEach((p) => {
            p.ready = p.bot
          })
          this.room.revision++
          await this.save()
        }
        return json({ code: this.room.code, kind: this.room.kind, token: player.token })
      }
      if (request.headers.get('Upgrade')?.toLowerCase() !== 'websocket')
        return json({ error: '需要实时连接。' }, 400)
      if (this.ctx.getWebSockets().length >= 10)
        return json({ error: '房间连接较多，请稍后重试。' }, 429)
      const pair = new WebSocketPair(),
        [client, server] = Object.values(pair)
      server!.serializeAttachment({
        playerId: null,
        openedAt: Date.now(),
        lastMessage: 0,
        burst: 0,
      } satisfies Attachment)
      this.ctx.acceptWebSocket(server!)
      await this.schedule()
      return new Response(null, { status: 101, webSocket: client! })
    })
  }
  async webSocketMessage(ws: WebSocket, message: string | ArrayBuffer) {
    return this.serial(async () => {
      if (!this.room) {
        ws.close(1000, 'room closed')
        return
      }
      try {
        if (typeof message !== 'string' || message.length > 4096)
          throw new Error('消息过长或格式不正确。')
        const a = ws.deserializeAttachment() as Attachment,
          now = Date.now()
        a.burst = now - a.lastMessage < 1000 ? a.burst + 1 : 1
        a.lastMessage = now
        if (a.burst > 20) throw new Error('操作太快，请稍后再试。')
        const command = JSON.parse(message) as RoomCommand & { token?: string }
        if (!a.playerId) {
          const player = this.humans().find((p) => p.token === command.token)
          if (!player) {
            this.send(ws, { type: 'error', message: '席位凭据已失效，请重新加入。', fatal: true })
            ws.close(1008, 'invalid credential')
            return
          }
          for (const other of this.ctx.getWebSockets()) {
            if (other === ws) continue
            const old = other.deserializeAttachment() as Attachment
            if (old.playerId === player.id) {
              old.playerId = null
              other.serializeAttachment(old)
              this.send(other, {
                type: 'replaced',
                message: '席位已在其他标签页打开，请从一个标签页继续。',
              })
              other.close(1000, 'reconnected')
            }
          }
          a.playerId = player.id
          ws.serializeAttachment(a)
          player.connected = true
          player.disconnectedAt = null
          player.auto = false
          this.transferHost()
          this.room.revision++
          this.adjustClock()
          await this.save()
          return
        }
        ws.serializeAttachment(a)
        const player = this.humans().find((p) => p.id === a.playerId)
        if (!player) throw new Error('你已离开房间。')
        await this.command(player, command)
      } catch (error) {
        this.send(ws, {
          type: 'error',
          message: error instanceof Error ? error.message : '操作未能完成，请重试。',
        })
        if (this.room) this.broadcast()
      }
    })
  }
  private async command(player: Player, command: RoomCommand) {
    const room = this.room!
    if (!command || typeof command.type !== 'string') throw new Error('操作格式不正确。')
    if (command.type === 'sync') {
      this.broadcast()
      return
    }
    if (command.type === 'leave') {
      room.proposal = null
      player.left = true
      player.token = ''
      player.connected = false
      player.ready = false
      if (room.game && room.phase === 'playing') {
        resignOnlineGame(room.game, player.seat)
        player.auto = room.kind === 'doudizhu'
        this.finishIfNeeded()
      }
      this.transferHost()
      for (const ws of this.ctx.getWebSockets())
        if ((ws.deserializeAttachment() as Attachment).playerId === player.id) {
          this.send(ws, { type: 'left' })
          ws.close(1000, 'left room')
        }
      if (!this.humans().length) {
        await this.destroy()
        return
      }
      room.revision++
      this.adjustClock()
      await this.save()
      return
    }
    if (command.type === 'chat') {
      const text = typeof command.text === 'string' ? command.text.trim() : ''
      if (!text || [...text].length > 200 || /[\p{Cc}\p{Cf}]/u.test(text))
        throw new Error('消息需要 1～200 个可见字符。')
      room.chat.push({ id: crypto.randomUUID(), name: player.name, text })
      room.chat = room.chat.slice(-30)
      await this.save()
      return
    }
    if (command.revision !== room.revision) throw new Error('局面刚刚更新，请再试一次。')
    if (command.type === 'ready') {
      room.proposal = null
      if (room.phase === 'playing') throw new Error('本局正在进行。')
      player.ready = command.ready === true
    } else if (command.type === 'settings') {
      if (room.hostId !== player.id || room.phase === 'playing')
        throw new Error('只有房主可在开局前修改设置。')
      room.settings = validSettings(command.settings)
      room.proposal = null
      room.players.forEach((p) => {
        p.ready = p.bot
      })
    } else if (command.type === 'start') {
      if (room.hostId !== player.id || room.phase === 'playing')
        throw new Error('请由房主在准备完成后开局。')
      const humans = this.humans()
      if (
        humans.some((p) => !p.connected || !p.ready) ||
        (room.kind !== 'doudizhu' && humans.length !== 2)
      )
        throw new Error('请等所有真人加入并准备。')
      if (room.kind === 'doudizhu')
        for (let seat = 0; seat < 3; seat++) {
          if (humans.some((p) => p.seat === seat)) continue
          room.players = room.players.filter((p) => p.seat !== seat)
          room.players.push({
            id: 'bot-' + seat,
            token: '',
            name: '电脑 ' + (seat + 1),
            seat,
            ready: true,
            connected: true,
            auto: true,
            bot: true,
            disconnectedAt: null,
            left: false,
          })
        }
      room.game = newOnlineGame(room.kind)
      room.gamePlayers = Array.from(
        { length: room.kind === 'doudizhu' ? 3 : 2 },
        (_, seat) => room.players.find((p) => p.seat === seat)!.id,
      )
      room.phase = 'playing'
      room.proposal = null
      room.notice = room.kind === 'junqi' ? '双方布阵确认后开始对局。' : '开局啦，祝你们玩得开心。'
      this.adjustClock(true)
    } else if (command.type === 'undo' || command.type === 'restart') {
      if (!room.game || (command.type === 'restart' && room.phase !== 'playing'))
        throw new Error('请先开始对局。')
      if (room.proposal) throw new Error('请先处理当前申请。')
      if (
        command.type === 'undo' &&
        (!this.sameParticipants() || !undoAllowed(room.game, room.settings, player.seat))
      )
        throw new Error('当前不能悔棋。')
      if (command.type === 'undo' && room.settings.undo === 'enabled') {
        undoOnlineGame(room.game, player.seat)
        room.phase = 'playing'
        this.adjustClock(true)
      } else {
        room.proposal = {
          id: crypto.randomUUID(),
          type: command.type,
          requester: player.id,
          accepted: [player.id],
          expiresAt: Date.now() + 60000,
        }
        this.resolveProposal()
      }
    } else if (command.type === 'answer') {
      if (
        !room.proposal ||
        room.proposal.id !== command.proposalId ||
        room.proposal.accepted.includes(player.id)
      )
        throw new Error('这份申请已结束或已经答复。')
      if (!command.accept) {
        room.proposal = null
        room.notice = '申请未通过，继续当前对局。'
      } else {
        room.proposal.accepted.push(player.id)
        this.resolveProposal()
      }
    } else {
      if (!room.game || room.phase !== 'playing') throw new Error('请先完成准备并开局。')
      if (this.pauseUntil()) throw new Error('有玩家掉线，正在等待重连。')
      actOnlineGame(room.game, room.settings, player.seat, command)
      room.proposal = null
      room.notice = ''
      this.finishIfNeeded()
      this.adjustClock(true)
    }
    room.revision++
    await this.save()
  }
  private resolveProposal() {
    const room = this.room!,
      proposal = room.proposal
    if (!proposal || !this.humans().every((p) => proposal.accepted.includes(p.id))) return
    if (proposal.type === 'restart') {
      room.phase = 'lobby'
      room.game = null
      room.proposal = null
      room.players.forEach((p) => {
        p.ready = p.bot
      })
      room.notice = '大家已同意重开，请重新准备。'
      this.adjustClock()
    } else {
      const requester = room.players.find((p) => p.id === proposal.requester)!
      undoOnlineGame(room.game!, requester.seat)
      room.phase = 'playing'
      room.proposal = null
      room.notice = '悔棋申请已通过。'
      this.adjustClock(true)
    }
  }
  async webSocketClose(ws: WebSocket) {
    return this.disconnected(ws)
  }
  async webSocketError(ws: WebSocket) {
    return this.disconnected(ws)
  }
  private disconnected(ws: WebSocket) {
    return this.serial(async () => {
      if (!this.room) return
      const a = ws.deserializeAttachment() as Attachment
      if (!a?.playerId) return
      const id = a.playerId
      a.playerId = null
      ws.serializeAttachment(a)
      if (
        this.ctx
          .getWebSockets()
          .some((socket) => (socket.deserializeAttachment() as Attachment)?.playerId === id)
      )
        return
      const lost = this.humans().find((p) => p.id === id)
      if (!lost) {
        await this.schedule()
        return
      }
      lost.connected = false
      lost.disconnectedAt = Date.now()
      lost.ready = false
      this.room.revision++
      this.adjustClock()
      await this.save()
    })
  }
  async alarm() {
    return this.serial(async () => {
      if (!this.room) return
      const now = Date.now(),
        room = this.room
      for (const ws of this.ctx.getWebSockets()) {
        const a = ws.deserializeAttachment() as Attachment
        if (!a.playerId && a.openedAt + 10000 <= now) ws.close(1008, 'authentication timeout')
      }
      if (
        !this.humans().some((p) => p.connected) &&
        this.humans().every((p) => (p.disconnectedAt ?? now) + this.grace <= now)
      ) {
        await this.destroy()
        return
      }
      for (const p of this.humans()) {
        if (
          p.connected ||
          p.auto ||
          p.disconnectedAt === null ||
          p.disconnectedAt + this.grace > now
        )
          continue
        p.auto = true
        p.ready = false
        if (room.game && room.phase === 'playing') {
          resignOnlineGame(room.game, p.seat)
          room.notice =
            room.kind === 'doudizhu'
              ? p.name + '暂未回来，电脑接管席位。'
              : '有玩家未能及时重连，本局结束。'
        } else {
          p.left = true
          p.token = ''
        }
      }
      this.transferHost()
      this.finishIfNeeded()
      this.adjustClock()
      if (room.proposal && room.proposal.expiresAt <= now) {
        room.proposal = null
        room.notice = '申请已过期，继续当前对局。'
      }
      if (
        room.game &&
        room.phase === 'playing' &&
        gameStatus(room.game) === 'playing' &&
        !this.pauseUntil()
      ) {
        const seat = gameTurn(room.game),
          player = room.players.find((p) => p.seat === seat)
        if (
          player?.bot ||
          player?.auto ||
          player?.left ||
          (room.deadline !== null && room.deadline <= now)
        ) {
          try {
            actOnlineGame(room.game, room.settings, seat, automaticAction(room.game, room.settings))
            room.proposal = null
            room.notice =
              player?.bot || player?.auto ? '' : player!.name + '本步超时，电脑已代操作一步。'
            this.finishIfNeeded()
            this.adjustClock(true)
          } catch {
            room.notice = '电脑暂时未能完成操作，稍后会重试。'
            room.deadline = Date.now() + 1500
          }
        }
      }
      room.revision++
      await this.save()
    })
  }
}
