import type { InjectionKey, Ref } from 'vue'

export const gameFullscreenKey: InjectionKey<{
  active: Ref<boolean>
  scale: Ref<number>
  overlay: Ref<HTMLDialogElement | undefined>
  fit: () => void
  toggle: () => Promise<void>
}> = Symbol('game-fullscreen')
