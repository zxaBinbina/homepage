import { onBeforeUnmount, onMounted, ref, type Ref } from 'vue'

/** Fullscreen belongs to this reader only; rejected requests still allow quiet reading. */
export function useReaderFocus<T>(options: {
  exitButton: Ref<HTMLButtonElement | undefined>
  enterButton: Ref<HTMLButtonElement | undefined>
  capture: () => T
  restore: (anchor: T) => Promise<void>
  notice: (text: string) => void
}) {
  const focused = ref(false)
  const exitVisible = ref(false)
  let ownsFullscreen = false
  let serial = 0
  let near = false
  let lastPointer: Pick<PointerEvent, 'pointerType' | 'clientX' | 'clientY'> | undefined
  let disposed = false
  let timer: ReturnType<typeof setTimeout> | undefined
  function scheduleHide(delay = 650) {
    clearTimeout(timer)
    timer = setTimeout(() => {
      timer = undefined
      if (!near) exitVisible.value = false
    }, delay)
  }
  function reveal() {
    exitVisible.value = true
    scheduleHide(1800)
  }
  function pointerMove(event: Pick<PointerEvent, 'pointerType' | 'clientX' | 'clientY'>) {
    if (event.pointerType !== 'mouse') return
    lastPointer = { pointerType: 'mouse', clientX: event.clientX, clientY: event.clientY }
    if (!focused.value) return
    const rect = options.exitButton.value?.getBoundingClientRect()
    if (!rect) return
    near =
      event.clientX >= rect.left - 48 &&
      event.clientX <= rect.right + 48 &&
      event.clientY >= rect.top - 36 &&
      event.clientY <= rect.bottom + 36
    if (near) {
      clearTimeout(timer)
      timer = undefined
      exitVisible.value = true
    } else if (!timer) scheduleHide()
  }
  function pointerLeave() {
    lastPointer = undefined
    near = false
    scheduleHide()
  }
  function pointerUp(event: PointerEvent) {
    if (focused.value && event.pointerType !== 'mouse') reveal()
  }
  async function setFocus(active: boolean) {
    if (focused.value === active || disposed) return
    const token = ++serial
    const anchor = options.capture()
    focused.value = active
    clearTimeout(timer)
    near = false
    if (active) {
      reveal()
      if (!document.fullscreenElement) {
        try {
          if (!document.documentElement.requestFullscreen) throw new Error('Unsupported')
          ownsFullscreen = true
          // Called before any await so the browser sees the original user activation.
          await document.documentElement.requestFullscreen()
        } catch {
          ownsFullscreen = false
          if (focused.value && !disposed) options.notice('浏览器未能进入全屏，已开启专注阅读。')
        }
      }
    } else {
      exitVisible.value = false
      if (ownsFullscreen && document.fullscreenElement === document.documentElement) {
        ownsFullscreen = false
        await document.exitFullscreen().catch(() => {})
      }
    }
    if (token !== serial || disposed) {
      if (
        !focused.value &&
        ownsFullscreen &&
        document.fullscreenElement === document.documentElement
      ) {
        ownsFullscreen = false
        await document.exitFullscreen().catch(() => {})
      }
      return
    }
    await options.restore(anchor)
    if (token !== serial || disposed) return
    if (active) {
      options.exitButton.value?.focus({ preventScroll: true })
      if (lastPointer) pointerMove(lastPointer)
    } else options.enterButton.value?.focus({ preventScroll: true })
  }
  function fullscreenChanged() {
    if (ownsFullscreen && !document.fullscreenElement) {
      ownsFullscreen = false
      void setFocus(false)
    }
  }
  function escape(event: KeyboardEvent) {
    if (event.key === 'Escape' && focused.value) {
      event.preventDefault()
      void setFocus(false)
    }
  }
  function release() {
    ++serial
    focused.value = false
    clearTimeout(timer)
    if (ownsFullscreen && document.fullscreenElement === document.documentElement) {
      ownsFullscreen = false
      void document.exitFullscreen().catch(() => {})
    }
  }
  onMounted(() => {
    document.addEventListener('fullscreenchange', fullscreenChanged)
    document.addEventListener('keydown', escape)
  })
  onBeforeUnmount(() => {
    disposed = true
    release()
    document.removeEventListener('fullscreenchange', fullscreenChanged)
    document.removeEventListener('keydown', escape)
  })
  return {
    focused,
    exitVisible,
    toggleFocus: () => setFocus(!focused.value),
    pointerMove,
    pointerLeave,
    pointerUp,
    reveal,
    release,
  }
}
