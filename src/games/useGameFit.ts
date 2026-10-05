import { onBeforeUnmount, onMounted, ref, watch, type Ref } from 'vue'

/** Fit the natural game layout into the fullscreen frame, preserving its proportions. */
export function useGameFit(
  active: Ref<boolean>,
  frame: Ref<HTMLElement | undefined>,
  content: Ref<HTMLElement | undefined>,
) {
  const scale = ref(1)
  let observer: ResizeObserver | undefined
  function fit() {
    const area = frame.value
    const game = content.value
    if (!area || !game) return
    if (!active.value) {
      scale.value = 1
      game.style.removeProperty('--game-fit-scale')
      game.style.removeProperty('--game-fit-left')
      game.style.removeProperty('--game-fit-top')
      return
    }
    const style = getComputedStyle(area)
    const width = area.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight)
    const height =
      area.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom)
    scale.value = Math.min(1, width / game.offsetWidth, height / game.offsetHeight)
    game.style.setProperty('--game-fit-scale', String(scale.value))
    game.style.setProperty('--game-fit-left', `${parseFloat(style.paddingLeft) + width / 2}px`)
    game.style.setProperty('--game-fit-top', `${parseFloat(style.paddingTop) + height / 2}px`)
  }
  watch(active, fit, { flush: 'post' })
  onMounted(() => {
    observer = new ResizeObserver(fit)
    if (frame.value) observer.observe(frame.value)
    if (content.value) observer.observe(content.value)
  })
  onBeforeUnmount(() => observer?.disconnect())
  return { scale, fit }
}
