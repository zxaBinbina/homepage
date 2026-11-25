import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { OnlineKind, RoomSnapshot, RoomCommand } from './types'
export type RoomSession = { code: string; token: string; kind: OnlineKind }
const key = 'homepage-game-room'
export function savedRoom(): RoomSession | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(key) ?? 'null') as RoomSession | null
    return value && /^[1-9]\d{5}$/.test(value.code) && typeof value.token === 'string'
      ? value
      : null
  } catch {
    return null
  }
}
export function useGameRoom(kind: OnlineKind) {
  const router = useRouter()
  const room = ref<RoomSnapshot | null>(null),
    error = ref(''),
    status = ref<'idle' | 'connecting' | 'online' | 'retrying'>('idle'),
    pending = ref(false)
  const session = ref<RoomSession | null>(savedRoom()?.kind === kind ? savedRoom() : null)
  const self = computed(() => room.value?.players.find((p) => p.id === room.value?.selfId))
  const host = computed(() => room.value?.hostId === room.value?.selfId)
  let socket: WebSocket | undefined,
    retry: ReturnType<typeof setTimeout> | undefined,
    watch: ReturnType<typeof setTimeout> | undefined,
    generation = 0,
    leaving = false,
    disposed = false,
    failures = 0,
    controller: AbortController | undefined
  function remember(value: RoomSession | null) {
    session.value = value
    try {
      if (value) sessionStorage.setItem(key, JSON.stringify(value))
      else sessionStorage.removeItem(key)
    } catch {
      error.value = '浏览器暂时无法保存重连凭据，刷新后可能需要重新加入。'
    }
  }
  function clearTimers() {
    if (retry) clearTimeout(retry)
    if (watch) clearTimeout(watch)
    retry = undefined
    watch = undefined
  }
  function close() {
    generation++
    clearTimers()
    socket?.close()
    socket = undefined
    status.value = 'idle'
    pending.value = false
  }
  function connect() {
    if (!session.value || disposed || leaving) return
    close()
    const current = generation,
      value = session.value
    status.value = failures ? 'retrying' : 'connecting'
    const url = new URL('/api/games/rooms/' + value.code + '/connect', location.href)
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(url)
    socket = ws
    watch = setTimeout(() => {
      if (generation === current && status.value !== 'online') ws.close()
    }, 10000)
    ws.onopen = () => {
      if (generation === current) ws.send(JSON.stringify({ type: 'hello', token: value.token }))
    }
    ws.onmessage = (event) => {
      if (generation !== current) return
      try {
        const message = JSON.parse(event.data) as {
          type: string
          room?: RoomSnapshot
          message?: string
          fatal?: boolean
        }
        if (message.type === 'state' && message.room) {
          room.value = message.room
          status.value = 'online'
          pending.value = false
          failures = 0
          if (watch) clearTimeout(watch)
        } else if (message.type === 'replaced') {
          close()
          error.value = message.message ?? '席位已在其他标签页打开。'
        } else if (message.type === 'error') {
          error.value = message.message ?? '操作未能完成。'
          pending.value = false
          if (message.fatal) {
            remember(null)
            room.value = null
            close()
          }
        } else if (message.type === 'closed' || message.type === 'left') {
          remember(null)
          room.value = null
          close()
          if (message.type === 'closed') error.value = message.message ?? '房间已解散。'
        }
      } catch {
        error.value = '收到的房间信息不完整，请重新连接。'
      }
    }
    ws.onclose = () => {
      if (generation !== current || disposed || leaving || !session.value) return
      pending.value = false
      status.value = 'retrying'
      failures++
      if (failures > 8) {
        status.value = 'idle'
        error.value = '暂时无法连接房间，它可能已解散。请重试或退出房间。'
        return
      }
      retry = setTimeout(connect, Math.min(5000, 600 * failures))
    }
    ws.onerror = () => {
      if (generation === current) status.value = 'retrying'
    }
  }
  async function enter(name: string, turnstileToken: string, code?: string) {
    if (pending.value || session.value) return
    error.value = ''
    pending.value = true
    controller?.abort()
    controller = new AbortController()
    try {
      const response = await fetch(code ? '/api/games/rooms/join' : '/api/games/rooms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(
          code ? { code, name, turnstileToken } : { kind, name, turnstileToken },
        ),
        signal: controller.signal,
      })
      const value = (await response.json()) as RoomSession & { error?: string }
      if (!response.ok) throw new Error(value.error ?? '房间服务暂时不可用。')
      if (disposed) return
      remember(value)
      if (value.kind !== kind) {
        await router.push('/games/' + value.kind)
        return
      }
      connect()
    } catch (e) {
      if (!disposed && !(e instanceof DOMException && e.name === 'AbortError'))
        error.value = e instanceof Error ? e.message : '无法连接房间服务，请稍后重试。'
    } finally {
      pending.value = false
    }
  }
  function send(value: Omit<RoomCommand, 'revision'>) {
    if (
      !room.value ||
      status.value !== 'online' ||
      !socket ||
      socket.readyState !== WebSocket.OPEN
    ) {
      error.value = '正在重新连接，请稍候。'
      return false
    }
    if (pending.value && value.type !== 'chat' && value.type !== 'leave') return false
    error.value = ''
    socket.send(JSON.stringify({ ...value, revision: room.value.revision }))
    if (value.type !== 'chat' && value.type !== 'sync') {
      pending.value = true
      if (watch) clearTimeout(watch)
      watch = setTimeout(() => {
        pending.value = false
        if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'sync' }))
      }, 5000)
    }
    return true
  }
  function leave() {
    if (room.value && socket?.readyState === WebSocket.OPEN) send({ type: 'leave' })
    leaving = true
    remember(null)
    room.value = null
    close()
  }
  function reconnect() {
    failures = 0
    error.value = ''
    connect()
  }
  onBeforeUnmount(() => {
    disposed = true
    controller?.abort()
    close()
  })
  if (session.value) connect()
  return { room, self, host, error, status, session, pending, enter, send, leave, reconnect }
}
