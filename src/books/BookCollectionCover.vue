<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import BookCover from './BookCover.vue'
import type { BookCollection } from './catalog'

const props = defineProps<{ collection: BookCollection }>()
const element = ref<HTMLElement>()
const current = ref(0)
const media = matchMedia('(prefers-reduced-motion: reduce)')
let host: HTMLElement | null = null
let dialog: HTMLDialogElement | null = null
let cycleTimer: ReturnType<typeof setInterval> | undefined
let holdTimer: ReturnType<typeof setTimeout> | undefined
let gesture: { id: number; x: number; y: number; activated: boolean } | undefined
let blockClick = false

function position(index: number) {
  return (index - current.value + props.collection.volumes.length) % props.collection.volumes.length
}
function inside(event: MouseEvent) {
  const bounds = element.value?.getBoundingClientRect()
  return (
    !!bounds &&
    event.clientX >= bounds.left &&
    event.clientX <= bounds.right &&
    event.clientY >= bounds.top &&
    event.clientY <= bounds.bottom
  )
}
function stop() {
  clearInterval(cycleTimer)
  cycleTimer = undefined
  current.value = 0
}
function start() {
  if (cycleTimer || media.matches || document.hidden) return
  cycleTimer = setInterval(() => {
    current.value = (current.value + 1) % props.collection.volumes.length
  }, 1200)
}
function hover(event: PointerEvent) {
  if (event.pointerType !== 'mouse') return
  if (inside(event) && !event.buttons) start()
  else stop()
}
function leave(event: PointerEvent) {
  if (event.pointerType === 'mouse') stop()
}
function beginHold(event: PointerEvent) {
  blockClick = false
  if (event.pointerType === 'mouse' || !event.isPrimary || !inside(event)) return
  stop()
  clearTimeout(holdTimer)
  gesture = { id: event.pointerId, x: event.clientX, y: event.clientY, activated: false }
  holdTimer = setTimeout(() => {
    if (!gesture) return
    gesture.activated = true
    start()
  }, 350)
}
function moveHold(event: PointerEvent) {
  if (!gesture || gesture.id !== event.pointerId) return
  if (Math.hypot(event.clientX - gesture.x, event.clientY - gesture.y) > 12 || !inside(event)) {
    clearTimeout(holdTimer)
    stop()
  }
}
function endHold(event: PointerEvent) {
  if (!gesture || gesture.id !== event.pointerId) return
  blockClick = event.type === 'pointerup' && gesture.activated
  reset()
}
function reset() {
  clearTimeout(holdTimer)
  holdTimer = undefined
  gesture = undefined
  stop()
}
function click(event: MouseEvent) {
  if (blockClick) {
    event.preventDefault()
    event.stopImmediatePropagation()
    blockClick = false
  }
  reset()
}
function contextMenu(event: MouseEvent) {
  if (gesture && inside(event)) event.preventDefault()
}
function visibility() {
  if (document.hidden) reset()
}
watch(() => props.collection, reset)
onMounted(() => {
  // The card's native details button covers the artwork, so listen on its container.
  host = element.value?.closest('.book-card, .book-details-heading') || null
  dialog = element.value?.closest('dialog') || null
  host?.addEventListener('pointerenter', hover)
  host?.addEventListener('pointermove', hover)
  host?.addEventListener('pointerleave', leave)
  host?.addEventListener('pointerdown', beginHold, { passive: true })
  host?.addEventListener('click', click, true)
  host?.addEventListener('contextmenu', contextMenu)
  dialog?.addEventListener('close', reset)
  window.addEventListener('pointermove', moveHold, { passive: true })
  window.addEventListener('pointerup', endHold)
  window.addEventListener('pointercancel', endHold)
  window.addEventListener('blur', reset)
  window.addEventListener('scroll', reset, { passive: true, capture: true })
  document.addEventListener('visibilitychange', visibility)
  media.addEventListener('change', reset)
})
onBeforeUnmount(() => {
  reset()
  host?.removeEventListener('pointerenter', hover)
  host?.removeEventListener('pointermove', hover)
  host?.removeEventListener('pointerleave', leave)
  host?.removeEventListener('pointerdown', beginHold)
  host?.removeEventListener('click', click, true)
  host?.removeEventListener('contextmenu', contextMenu)
  dialog?.removeEventListener('close', reset)
  window.removeEventListener('pointermove', moveHold)
  window.removeEventListener('pointerup', endHold)
  window.removeEventListener('pointercancel', endHold)
  window.removeEventListener('blur', reset)
  window.removeEventListener('scroll', reset, true)
  document.removeEventListener('visibilitychange', visibility)
  media.removeEventListener('change', reset)
})
</script>

<template>
  <div ref="element" class="book-collection-cover" aria-hidden="true">
    <BookCover
      v-for="(book, index) in collection.volumes"
      :key="book.id"
      :book="book"
      :number="index + 1"
      :style="{
        '--cover-offset': position(index) / Math.max(collection.volumes.length - 1, 1),
        zIndex: collection.volumes.length - position(index),
      }"
    />
  </div>
</template>
