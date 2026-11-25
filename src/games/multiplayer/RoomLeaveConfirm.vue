<script setup lang="ts">
import { inject, nextTick, onBeforeUnmount, onMounted, ref, useId, watch } from 'vue'
import { DoorOpen } from 'lucide-vue-next'
import { gameFullscreenKey } from '../fullscreen'

defineProps<{ message: string }>()
const emit = defineEmits<{ confirm: [] }>()
const id = useId()
const trigger = ref<HTMLButtonElement>()
const popover = ref<HTMLElement>()
const surface = ref<HTMLElement>()
const cancel = ref<HTMLButtonElement>()
const open = ref(false)
const fullscreen = inject(gameFullscreenKey)
let frame = 0
let observer: ResizeObserver | undefined
let disposed = false

function close(restoreFocus = true) {
  if (popover.value?.matches(':popover-open')) popover.value.hidePopover()
  if (restoreFocus) trigger.value?.focus({ preventScroll: true })
}

function position() {
  const button = trigger.value
  const panel = popover.value
  const content = surface.value
  if (!open.value || !button || !panel || !content || !panel.matches(':popover-open')) return
  const bounds = button.getBoundingClientRect()
  const viewport = window.visualViewport
  const x = viewport?.offsetLeft ?? 0
  const y = viewport?.offsetTop ?? 0
  const viewWidth = viewport?.width ?? window.innerWidth
  const viewHeight = viewport?.height ?? window.innerHeight
  if (
    bounds.bottom < y ||
    bounds.top > y + viewHeight ||
    bounds.right < x ||
    bounds.left > x + viewWidth
  ) {
    close(false)
    return
  }
  const style = getComputedStyle(panel)
  const gap = parseFloat(style.getPropertyValue('--space-sm'))
  const corner = parseFloat(style.getPropertyValue('--space-lg'))
  const width = Math.min(
    parseFloat(style.getPropertyValue('--room-leave-width')),
    viewWidth - 2 * gap,
  )
  panel.style.width = `${width}px`
  const contentStyle = getComputedStyle(content)
  const height =
    content.scrollHeight +
    parseFloat(contentStyle.borderTopWidth) +
    parseFloat(contentStyle.borderBottomWidth)
  const below = Math.max(0, y + viewHeight - bounds.bottom - 2 * gap)
  const above = Math.max(0, bounds.top - y - 2 * gap)
  const side = below >= height || below >= above ? 'below' : 'above'
  const available = side === 'below' ? below : above
  const left = Math.max(x + gap, Math.min(bounds.right - width, x + viewWidth - width - gap))
  const top =
    side === 'below' ? bounds.bottom + gap : bounds.top - gap - Math.min(height, available)
  panel.dataset.side = side
  panel.style.left = `${left}px`
  panel.style.top = `${top}px`
  panel.style.setProperty('--room-leave-max-height', `${available}px`)
  panel.style.setProperty(
    '--room-leave-arrow-left',
    `${Math.max(corner, Math.min(width - corner, bounds.left + bounds.width / 2 - left))}px`,
  )
}

function reposition() {
  if (!open.value || frame) return
  frame = requestAnimationFrame(() => {
    frame = 0
    position()
  })
}

async function show() {
  await nextTick()
  if (disposed || !trigger.value || !popover.value) return
  trigger.value.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'instant' })
  if (!open.value) trigger.value.click()
  position()
  await nextTick()
  if (!disposed && open.value) cancel.value?.focus({ preventScroll: true })
}

function beforeToggle(event: Event) {
  open.value = (event as ToggleEvent).newState === 'open'
  if (popover.value) popover.value.inert = !open.value
  if (open.value) {
    cancelAnimationFrame(frame)
    frame = requestAnimationFrame(() => {
      frame = 0
      if (disposed || !open.value) return
      position()
      cancel.value?.focus({ preventScroll: true })
    })
  } else {
    cancelAnimationFrame(frame)
    frame = 0
  }
}

function keydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  event.preventDefault()
  event.stopPropagation()
  close()
}

function confirm() {
  close(false)
  emit('confirm')
}

watch(
  () => fullscreen?.active.value,
  () => close(false),
)
watch(() => fullscreen?.scale.value, reposition)
onMounted(() => {
  observer = new ResizeObserver(reposition)
  if (trigger.value) observer.observe(trigger.value)
  const toolbar = trigger.value?.closest('.room-toolbar')
  if (toolbar) observer.observe(toolbar)
  if (surface.value) observer.observe(surface.value)
  window.addEventListener('resize', reposition)
  window.addEventListener('scroll', reposition, true)
  window.visualViewport?.addEventListener('resize', reposition)
  window.visualViewport?.addEventListener('scroll', reposition)
})
onBeforeUnmount(() => {
  disposed = true
  close(false)
  observer?.disconnect()
  cancelAnimationFrame(frame)
  window.removeEventListener('resize', reposition)
  window.removeEventListener('scroll', reposition, true)
  window.visualViewport?.removeEventListener('resize', reposition)
  window.visualViewport?.removeEventListener('scroll', reposition)
})
defineExpose({ show })
</script>

<template>
  <div class="room-leave-control">
    <button
      ref="trigger"
      class="game-button"
      type="button"
      aria-haspopup="dialog"
      :aria-expanded="open"
      :aria-controls="id"
      :popovertarget="id"
      popovertargetaction="toggle"
    >
      <DoorOpen :size="16" />离开房间
    </button>
    <div
      :id="id"
      ref="popover"
      class="room-leave-popover"
      popover="auto"
      role="dialog"
      :aria-labelledby="id + '-title'"
      :aria-describedby="id + '-message'"
      @beforetoggle="beforeToggle"
      @keydown="keydown"
    >
      <div ref="surface" class="room-leave-popover-surface">
        <h3 :id="id + '-title'">确认离开房间？</h3>
        <p :id="id + '-message'">{{ message }}</p>
        <div class="room-leave-actions">
          <button class="game-button room-leave-confirm" type="button" @click="confirm">
            确认离开
          </button>
          <button ref="cancel" class="game-button room-primary" type="button" @click="close()">
            继续留在房间
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
