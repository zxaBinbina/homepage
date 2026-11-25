<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, useId, watch } from 'vue'
import { Palette, Moon, Sun, Monitor } from 'lucide-vue-next'
import SegmentedControl from './SegmentedControl.vue'
import { useTheme, type ColorPalette, type ThemeMode } from '../composables/useTheme'

/* 明暗模式与配色方案合并为一个入口：点击打开统一面板，面板内两组分段控件分别选择。
   配色组在前沿用原配色弹窗的视觉位置，明暗组作为新增分组置于其下并以细线分隔。 */
const { mode, palette, setThemeMode, setPalette } = useTheme()
const open = ref(false)
const root = ref<HTMLElement>()
const trigger = ref<HTMLButtonElement>()
const popover = ref<HTMLElement>()
const popoverRight = ref<string>()
let alignmentFrame = 0
let alignmentObserver: ResizeObserver | undefined
const panelId = useId()

const modes = [
  { value: 'dark', label: '深色', id: 'theme-mode-dark' },
  { value: 'light', label: '浅色', id: 'theme-mode-light' },
  { value: 'auto', label: '自动', id: 'theme-mode-auto' },
] as const
const palettes = [
  { value: 'fufu-blue', label: '芙芙蓝' },
  { value: 'hutao-red', label: '胡桃红' },
] as const

function chooseMode(next: ThemeMode) {
  setThemeMode(next)
}
function choosePalette(next: ColorPalette) {
  setPalette(next)
}

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
function alignPopover() {
  if (!open.value || !root.value || !popover.value) return
  const anchor = root.value.getBoundingClientRect()
  const width = popover.value.offsetWidth
  const left = Math.max(16, Math.min(anchor.right + 4 - width, innerWidth - width - 16))
  popoverRight.value = `${anchor.right - left - width}px`
}
function scheduleAlignment() {
  if (!open.value) return
  cancelAnimationFrame(alignmentFrame)
  alignmentFrame = requestAnimationFrame(alignPopover)
}

watch(
  open,
  () => {
    alignPopover()
    scheduleAlignment()
  },
  { flush: 'post' },
)
onMounted(() => {
  // Header width may settle after resize when the document scrollbar changes.
  alignmentObserver = new ResizeObserver(scheduleAlignment)
  alignmentObserver.observe(document.documentElement)
  const header = root.value?.closest('header')
  if (header) alignmentObserver.observe(header)
  document.addEventListener('pointerdown', onOutsideInteraction)
  document.addEventListener('click', onOutsideInteraction)
  document.addEventListener('keydown', onKeydown)
  window.addEventListener('resize', scheduleAlignment)
})
onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onOutsideInteraction)
  document.removeEventListener('click', onOutsideInteraction)
  document.removeEventListener('keydown', onKeydown)
  window.removeEventListener('resize', scheduleAlignment)
  alignmentObserver?.disconnect()
  cancelAnimationFrame(alignmentFrame)
})
</script>

<template>
  <div ref="root" class="palette-picker theme-panel">
    <button
      ref="trigger"
      class="icon-button palette-toggle theme-toggle"
      type="button"
      :data-mode="mode"
      :data-palette="palette"
      aria-label="主题设置"
      title="主题设置"
      aria-haspopup="dialog"
      :aria-controls="open ? panelId : undefined"
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
        :id="panelId"
        class="palette-popover theme-panel-popover"
        :style="{ right: popoverRight }"
        role="dialog"
        aria-label="主题设置"
      >
        <p class="palette-popover-title">配色方案</p>
        <SegmentedControl
          :model-value="palette"
          :options="palettes"
          label="配色方案"
          class="palette-options"
          item-class="palette-option"
          semantics="buttons"
          @select="choosePalette"
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
        <p class="palette-popover-title theme-panel-title">明暗模式</p>
        <SegmentedControl
          :model-value="mode"
          :options="modes"
          label="明暗模式"
          class="theme-mode-options"
          item-class="theme-mode-option"
          semantics="buttons"
          @select="chooseMode"
        >
          <template #option="{ option }">
            <Moon v-if="option.value === 'dark'" :size="13" aria-hidden="true" />
            <Sun v-else-if="option.value === 'light'" :size="13" aria-hidden="true" />
            <Monitor v-else :size="13" aria-hidden="true" />
            <span>{{ option.label }}</span>
          </template>
        </SegmentedControl>
      </div>
    </Transition>
  </div>
</template>
