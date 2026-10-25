<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useTheme } from '../composables/useTheme'

const { palette } = useTheme()
const cursorDirectory = computed(() => `/cursors/${palette.value}`)
const position = ref({ x: 0, y: 0 })
const visible = ref(false)
const animated = ref(true)
const cursorReady = ref(false)
let media: MediaQueryList | undefined
let observer: MutationObserver | undefined
let pointerPosition = { x: 0, y: 0 }

function syncBusyCursor(target: EventTarget | null) {
  const overBusyArea =
    target instanceof Element && Boolean(target.closest('[aria-busy="true"], .is-loading'))
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

function preloadBusyCursor() {
  const directory = cursorDirectory.value
  const gif = new Image()
  const png = new Image()
  gif.src = `${directory}/busy.gif`
  png.src = `${directory}/busy.png`
  Promise.allSettled([gif.decode(), png.decode()]).then((results) => {
    if (directory !== cursorDirectory.value) return
    animated.value = !media?.matches && results[0]?.status !== 'rejected'
    cursorReady.value = results.some((result) => result.status === 'fulfilled')
    if (cursorReady.value)
      syncBusyCursor(document.elementFromPoint(pointerPosition.x, pointerPosition.y))
  })
}

watch(cursorDirectory, () => {
  cursorReady.value = false
  syncBusyCursor(document.elementFromPoint(pointerPosition.x, pointerPosition.y))
  if (media) preloadBusyCursor()
})

onMounted(() => {
  media = window.matchMedia('(prefers-reduced-motion: reduce)')
  animated.value = !media.matches
  media.addEventListener('change', onMotionChange)
  preloadBusyCursor()
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
    :src="`${cursorDirectory}/${animated ? 'busy.gif' : 'busy.png'}`"
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
