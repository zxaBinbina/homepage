export const onlineKinds = ['xiangqi', 'gomoku', 'chess', 'go', 'doudizhu', 'junqi'] as const
export type OnlineKind = (typeof onlineKinds)[number]
export const isOnlineKind = (value: unknown): value is OnlineKind =>
  typeof value === 'string' && (onlineKinds as readonly string[]).includes(value)
export type RoomSettings = {
  turnSeconds: 0 | 30 | 60 | 120
  undo: 'enabled' | 'ask' | 'disabled'
  junqi: 'open' | 'hidden'
}
export type RoomPlayer = {
  id: string
  name: string
  seat: number
  ready: boolean
  connected: boolean
  bot: boolean
  auto: boolean
}
export type BoardPiece = {
  side: number
  label: string
  piece?: 'p' | 'r' | 'n' | 'b' | 'q' | 'k'
  hidden?: boolean
}
export type GameView = {
  board: (BoardPiece | null)[]
  columns: number
  turn: number
  status: 'setup' | 'playing' | 'scoring' | 'finished'
  last: { from: number; to: number } | null
  targets: Record<number, number[]>
  promotions: Record<string, string[]>
  ply: number
  result: { winners: number[]; message: string } | null
  setupReady: number[]
  dead: number[]
  scoreReady: number[]
  score: { black: number; white: number; ownership: number[] } | null
  hand: { id: number; rank: number }[]
  counts: number[]
  bottom: { id: number; rank: number }[]
  lastCards: { id: number; rank: number }[]
  lastPlayer: number
  landlord: number
  bids: number[]
  multiplier: number
  canPass: boolean
  canUndo: boolean
  hint: number[]
}
export type RoomSnapshot = {
  code: string
  kind: OnlineKind
  selfId: string
  hostId: string
  phase: 'lobby' | 'playing' | 'finished'
  revision: number
  serverTime: number
  settings: RoomSettings
  players: RoomPlayer[]
  game: GameView | null
  chat: { id: string; name: string; text: string }[]
  proposal: {
    id: string
    type: 'undo' | 'restart'
    requester: string
    accepted: string[]
    expiresAt: number
  } | null
  deadline: number | null
  pauseUntil: number | null
  notice: string
}
export type RoomCommand = {
  type:
    | 'ready'
    | 'start'
    | 'settings'
    | 'move'
    | 'setup-ready'
    | 'dead'
    | 'score'
    | 'resume-play'
    | 'undo'
    | 'restart'
    | 'answer'
    | 'chat'
    | 'leave'
    | 'sync'
  revision: number
  from?: number
  to?: number
  promotion?: string
  cards?: number[]
  bid?: number
  ready?: boolean
  settings?: RoomSettings
  proposalId?: string
  accept?: boolean
  text?: string
}
