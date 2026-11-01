<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, useId, watch } from 'vue'
import { Palette } from 'lucide-vue-next'
import SegmentedControl from './SegmentedControl.vue'
import { useTheme, type ColorPalette } from '../composables/useTheme'

const { palette, setPalette } = useTheme()
const open = ref(false)
const root = ref<HTMLElement>()
const trigger = ref<HTMLButtonElement>()
const popover = ref<HTMLElement>()
const popoverRight = ref<string>()
const popoverId = useId()
const palettes = [
  { value: 'fufu-blue', label: '芙芙蓝' },
  { value: 'hutao-red', label: '胡桃红' },
] as const

function onOutsideInteraction(event: Event) {
  if (open.value && event.target instanceof Node && !root.value?.contains(event.target)) {
    open.value = false
  }
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && open.value) {
    open.value = false
    trigger.value?.focus()
  }
}

function choose(nextPalette: ColorPalette) {
  setPalette(nextPalette)
}

function alignPopover() {
  if (!open.value || !root.value || !popover.value) return
  const anchor = root.value.getBoundingClientRect()
  const width = popover.value.offsetWidth
  const left = Math.max(16, Math.min(anchor.right + 4 - width, innerWidth - width - 16))
  popoverRight.value = `${anchor.right - left - width}px`
}

watch(open, alignPopover, { flush: 'post' })
onMounted(() => {
  document.addEventListener('pointerdown', onOutsideInteraction)
  document.addEventListener('click', onOutsideInteraction)
  document.addEventListener('keydown', onKeydown)
  window.addEventListener('resize', alignPopover)
})
onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onOutsideInteraction)
  document.removeEventListener('click', onOutsideInteraction)
  document.removeEventListener('keydown', onKeydown)
  window.removeEventListener('resize', alignPopover)
})
</script>

<template>
  <div ref="root" class="palette-picker">
    <button
      ref="trigger"
      class="icon-button palette-toggle"
      type="button"
      aria-label="选择配色方案"
      title="选择配色方案"
      aria-haspopup="dialog"
      :aria-controls="open ? popoverId : undefined"
      :aria-expanded="open"
      @click="open = !open"
    >
      <Palette :size="17" aria-hidden="true" />
    </button>
    <Transition
      name="palette-popover"
      @before-leave="(el) => ((el as HTMLElement).inert = true)"
      @before-enter="(el) => ((el as HTMLElement).inert = false)"
    >
      <div
        v-if="open"
        ref="popover"
        :id="popoverId"
        class="palette-popover"
        :style="{ right: popoverRight }"
        role="dialog"
        aria-label="选择配色方案"
      >
        <p class="palette-popover-title">配色方案</p>
        <SegmentedControl
          :model-value="palette"
          :options="palettes"
          label="配色方案"
          class="palette-options"
          semantics="buttons"
          item-class="palette-option"
          @select="choose"
        >
          <template #option="{ option }">
            <span
              class="palette-swatch"
              :class="option.value === 'fufu-blue' ? 'palette-swatch--blue' : 'palette-swatch--red'"
              aria-hidden="true"
            />
            <span>{{ option.label }}</span>
          </template>
        </SegmentedControl>
      </div>
    </Transition>
  </div>
</template>
