import { onBeforeUnmount, onMounted, type Ref } from 'vue'

const easing = 'cubic-bezier(0.22, 1, 0.36, 1)'
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches

/** Native dialogs keep their focus trap until the closing animation finishes. */
export function useBookDialog(element: Ref<HTMLDialogElement | undefined>, drawer = false) {
  let serial = 0
  let animation: Animation | undefined
  const media = matchMedia('(prefers-reduced-motion: reduce)')
  function finishMotion() {
    animation?.finish()
  }
  async function change(open: boolean, immediate = false) {
    const dialog = element.value
    if (!dialog || (!open && !dialog.open)) return
    const token = ++serial
    const wasOpen = dialog.open
    const current = getComputedStyle(dialog)
    const initial = { opacity: current.opacity, transform: current.transform }
    animation?.cancel()
    if (open && !wasOpen) dialog.showModal()
    if (!immediate && !reduced()) {
      const hidden = {
        opacity: 0,
        transform: drawer
          ? `translateX(${dialog.classList.contains('is-settings') ? 28 : -28}px)`
          : 'translateY(12px) scale(0.98)',
      }
      const target = open ? { opacity: 1, transform: 'none' } : hidden
      const active = dialog.animate([wasOpen ? initial : hidden, target], {
        duration: open ? 220 : 160,
        easing,
        fill: 'both',
      })
      animation = active
      await active.finished.catch(() => {})
      if (token !== serial) return
      active.cancel()
      animation = undefined
    }
    if (!open && token === serial) dialog.close()
  }
  onMounted(() => media.addEventListener('change', finishMotion))
  onBeforeUnmount(() => {
    ++serial
    animation?.cancel()
    element.value?.close()
    media.removeEventListener('change', finishMotion)
  })
  return { open: () => change(true), close: (immediate = false) => change(false, immediate) }
}

/** Opacity changes leave paragraph geometry stable while saving and restoring progress. */
export function useBookFade() {
  let animation: Animation | undefined
  const media = matchMedia('(prefers-reduced-motion: reduce)')
  function finish() {
    if (media.matches && animation?.playState === 'running') animation.finish()
  }
  function fade(element?: HTMLElement) {
    animation?.cancel()
    if (!element || reduced()) return
    const active = element.animate([{ opacity: 0.55 }, { opacity: 1 }], { duration: 180, easing })
    animation = active
    void active.finished.catch(() => {})
  }
  onMounted(() => media.addEventListener('change', finish))
  onBeforeUnmount(() => {
    animation?.cancel()
    media.removeEventListener('change', finish)
  })
  return fade
}
