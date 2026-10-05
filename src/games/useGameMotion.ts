import { onBeforeUnmount, ref, watch, type Ref } from 'vue'

/** Decorative motion always settles, including preference changes and interrupted navigation. */
export function useGameMotion(disabled?: Ref<boolean>) {
  const preference = matchMedia('(prefers-reduced-motion: reduce)')
  const reduced = ref(preference.matches)
  const running = new Set<Animation>()
  function animate(
    element: Element | null | undefined,
    frames: Keyframe[],
    options: KeyframeAnimationOptions,
  ) {
    if (!element || reduced.value || disabled?.value || document.hidden || !element.animate)
      return null
    const animation = element.animate(frames, {
      easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
      ...options,
    })
    running.add(animation)
    return animation
  }
  async function settle(animations: (Animation | null)[]) {
    await Promise.all(
      animations.map(async (animation) => {
        if (!animation) return
        try {
          await animation.finished
        } catch {
          /* Cancellation also releases the input lock. */
        }
      }),
    )
    // Keep completed cards at their destination until the whole sequence has settled.
    animations.forEach((animation) => {
      if (!animation) return
      animation.cancel()
      running.delete(animation)
    })
  }
  function cancel() {
    running.forEach((animation) => animation.cancel())
    running.clear()
  }
  function finish() {
    running.forEach((animation) => {
      try {
        animation.finish()
      } catch {
        animation.cancel()
      }
    })
  }
  function onPreference() {
    reduced.value = preference.matches
    if (reduced.value) finish()
  }
  function onVisibility() {
    if (document.hidden) finish()
  }
  if (disabled)
    watch(disabled, (value) => {
      if (value) finish()
    })
  preference.addEventListener('change', onPreference)
  document.addEventListener('visibilitychange', onVisibility)
  onBeforeUnmount(() => {
    cancel()
    preference.removeEventListener('change', onPreference)
    document.removeEventListener('visibilitychange', onVisibility)
  })
  return { reduced, animate, settle, cancel, finish }
}
