<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = withDefaults(defineProps<{ open: boolean; gap?: string; lazy?: boolean }>(), {
  gap: '0px',
  lazy: false,
})
const emit = defineEmits<{ settled: [open: boolean] }>()
const panel = ref<HTMLElement>()
const rendered = ref(!props.lazy || props.open)
const settled = ref(true)
const motion = matchMedia('(prefers-reduced-motion: reduce)')
const instant = ref(motion.matches || document.hidden)
let opener: HTMLElement | null = null
let fallback: ReturnType<typeof setTimeout> | undefined

function finish() {
  clearTimeout(fallback)
  settled.value = true
  emit('settled', props.open)
}
function syncMotion() {
  instant.value = motion.matches || document.hidden
  if (instant.value) finish()
}
watch(
  () => props.open,
  (open) => {
    clearTimeout(fallback)
    if (open) {
      rendered.value = true
      if (document.activeElement instanceof HTMLElement) opener = document.activeElement
    } else if (panel.value?.contains(document.activeElement)) {
      // A programmatic close must not leave keyboard focus in an inert subtree.
      if (opener?.isConnected && !panel.value.contains(opener))
        opener.focus({ preventScroll: true })
    }
    settled.value = false
    if (instant.value) finish()
    // Also settle empty panels and browsers that do not dispatch transitionend.
    else fallback = setTimeout(finish, 350)
  },
)
function onEnd(event: TransitionEvent) {
  if (event.target === panel.value && event.propertyName === 'grid-template-rows') finish()
}
onMounted(() => {
  motion.addEventListener('change', syncMotion)
  document.addEventListener('visibilitychange', syncMotion)
})
onBeforeUnmount(() => {
  clearTimeout(fallback)
  motion.removeEventListener('change', syncMotion)
  document.removeEventListener('visibilitychange', syncMotion)
})
</script>

<template>
  <div
    ref="panel"
    class="collapse-panel"
    :class="{ 'is-open': open, 'is-settled': settled, 'is-instant': instant }"
    :style="{ '--collapse-gap': gap }"
    :inert="!open"
    :aria-hidden="!open"
    @transitionend="onEnd"
  >
    <div class="collapse-panel__clip"><slot v-if="rendered" /></div>
  </div>
</template>
