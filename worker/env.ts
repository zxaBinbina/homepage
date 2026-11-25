import type { GameRoom, RoomDirectory } from './rooms'
export type Env = {
  ASSETS: Fetcher
  GAME_EXPERIENCE?: KVNamespace
  ROOMS: DurableObjectNamespace<GameRoom>
  ROOM_DIRECTORY: DurableObjectNamespace<RoomDirectory>
  ROOM_LIMIT: RateLimit
  SITE_ORIGIN?: string
  LOCAL_TEST_TIMERS?: string
  TURNSTILE_SITE_KEY?: string
  TURNSTILE_SECRET_KEY?: string
}
