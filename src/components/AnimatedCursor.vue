<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const position = ref({ x: 0, y: 0 })
const visible = ref(false)
const animated = ref(true)
const cursorReady = ref(false)
let media: MediaQueryList | undefined
let observer: MutationObserver | undefined
let pointerPosition = { x: 0, y: 0 }

function syncBusyCursor(target: EventTarget | null) {
  const overBusyArea =
    target instanceof Element &&
    Boolean(target.closest('[aria-busy="true"], .is-loading'))
  visible.value = overBusyArea && cursorReady.value
  document.body.classList.toggle('has-animated-busy-cursor', visible.value)
}

function onPointerMove(event: PointerEvent) {
  if (event.pointerType !== 'mouse') return
  pointerPosition = { x: event.clientX, y: event.clientY }
  position.value = pointerPosition
  syncBusyCursor(document.elementFromPoint(event.clientX, event.clientY))
}

function onMotionChange(event: MediaQueryListEvent) {
  animated.value = !event.matches
}

onMounted(() => {
  media = window.matchMedia('(prefers-reduced-motion: reduce)')
  animated.value = !media.matches
  media.addEventListener('change', onMotionChange)
  const gif = new Image()
  const png = new Image()
  gif.src = '/cursors/busy.gif'
  png.src = '/cursors/busy.png'
  Promise.allSettled([gif.decode(), png.decode()]).then((results) => {
    if (results[0]?.status === 'rejected') animated.value = false
    cursorReady.value = results.some((result) => result.status === 'fulfilled')
    if (cursorReady.value)
      syncBusyCursor(document.elementFromPoint(pointerPosition.x, pointerPosition.y))
  })
  document.addEventListener('pointermove', onPointerMove, { passive: true })
  observer = new MutationObserver((records) => {
    const busyStateChanged = records.some((record) => {
      if (record.attributeName === 'aria-busy') return true
      const target = record.target
      return (
        target instanceof Element &&
        (target.classList.contains('is-loading') ||
          (record.oldValue || '').split(/\s+/).includes('is-loading'))
      )
    })
    if (busyStateChanged)
      syncBusyCursor(document.elementFromPoint(pointerPosition.x, pointerPosition.y))
  })
  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ['aria-busy', 'class'],
    attributeOldValue: true,
    subtree: true,
  })
})

onBeforeUnmount(() => {
  observer?.disconnect()
  media?.removeEventListener('change', onMotionChange)
  document.removeEventListener('pointermove', onPointerMove)
  document.body.classList.remove('has-animated-busy-cursor')
})
</script>

<template>
  <img
    v-if="visible"
    class="animated-busy-cursor"
    :src="animated ? '/cursors/busy.gif' : '/cursors/busy.png'"
    alt=""
    aria-hidden="true"
    :style="{ left: `${position.x - 16}px`, top: `${position.y - 16}px` }"
  />
</template>

<style scoped>
.animated-busy-cursor {
  position: fixed;
  z-index: 2147483647;
  width: 32px;
  height: 32px;
  max-width: none;
  pointer-events: none;
}
</style>
