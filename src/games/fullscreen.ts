import type { InjectionKey, Ref } from 'vue'

export const gameFullscreenKey: InjectionKey<{
  active: Ref<boolean>
  toggle: () => Promise<void>
}> = Symbol('game-fullscreen')
