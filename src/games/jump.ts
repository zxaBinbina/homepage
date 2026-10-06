export const JUMP_CHARGE_MS = 1200
export const JUMP_DISTANCE = 400
export const JUMP_FOOT = 8
export type JumpPlatform = { id: number; x: number; width: number }
export type JumpState = {
  current: JumpPlatform
  next: JumpPlatform
  previous: JumpPlatform | null
  x: number
  score: number
  status: 'playing' | 'lost'
}
export function jumpPower(milliseconds: number) {
  return Math.max(0, Math.min(1, milliseconds / JUMP_CHARGE_MS))
}
export function newJump(): JumpState {
  return {
    current: { id: 0, x: 140, width: 100 },
    next: { id: 1, x: 350, width: 100 },
    previous: null,
    x: 140,
    score: 0,
    status: 'playing',
  }
}
export function onJumpPlatform(x: number, platform: JumpPlatform) {
  return Math.abs(x - platform.x) <= platform.width / 2 - JUMP_FOOT
}
export function jumpLanding(game: JumpState, milliseconds: number) {
  const x = game.x + JUMP_DISTANCE * jumpPower(milliseconds)
  const target = onJumpPlatform(x, game.next)
    ? 'next'
    : onJumpPlatform(x, game.current)
      ? 'current'
      : 'gap'
  return { x, target }
}
export function landJump(game: JumpState, milliseconds: number, random = Math.random): JumpState {
  if (game.status !== 'playing') return game
  const { x, target } = jumpLanding(game, milliseconds)
  if (target === 'gap') return { ...game, x, status: 'lost' }
  if (target === 'current') return { ...game, x }
  const score = game.score + 1
  const width = Math.max(64, 100 - Math.floor(score / 4) * 4)
  const gap = 70 + random() * Math.min(110, 60 + score * 3)
  const current = game.next
  return {
    current,
    previous: game.current,
    next: { id: current.id + 1, x: current.x + current.width / 2 + gap + width / 2, width },
    x,
    score,
    status: 'playing',
  }
}
