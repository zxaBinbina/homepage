import { nextTick, onBeforeUnmount, watch } from 'vue'

// Shared by the editor and HTML preview. Keep the same component instance while expanding.
export function useToolModal(open, surface) {
  let previous = null
  let overflow = ''
  let inert = false
  let active = false
  const focusable =
    'button:not(:disabled), input:not(:disabled), textarea, select, a[href], [tabindex="0"]'
  function keydown(event) {
    if (!active || !surface.value) return
    if (event.key === 'Escape') {
      event.preventDefault()
      open.value = false
    }
    if (event.key !== 'Tab') return
    const nodes = [...surface.value.querySelectorAll(focusable)].filter(
      (el) => el.getClientRects().length && !el.closest('[inert]'),
    )
    const first = nodes[0],
      last = nodes.at(-1)
    if (!first) {
      event.preventDefault()
      return
    }
    if (
      event.shiftKey &&
      (document.activeElement === first || !surface.value.contains(document.activeElement))
    ) {
      event.preventDefault()
      last.focus()
    } else if (
      !event.shiftKey &&
      (document.activeElement === last || !surface.value.contains(document.activeElement))
    ) {
      event.preventDefault()
      first.focus()
    }
  }
  function cleanup() {
    if (!active) return
    active = false
    document.removeEventListener('keydown', keydown)
    const app = document.getElementById('app')
    if (app) app.inert = inert
    document.body.style.overflow = overflow
    if (previous?.isConnected) previous.focus({ preventScroll: true })
  }
  watch(open, async (value) => {
    if (!value) {
      await nextTick()
      cleanup()
      return
    }
    previous = document.activeElement
    overflow = document.body.style.overflow
    const app = document.getElementById('app')
    inert = app?.inert || false
    active = true
    await nextTick()
    if (!open.value || !active) return
    if (app) app.inert = true
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', keydown)
    surface.value?.querySelector(focusable)?.focus()
  })
  onBeforeUnmount(cleanup)
}
