<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, useId } from 'vue'
import { Check, Palette } from 'lucide-vue-next'
import { useTheme, type ColorPalette } from '../composables/useTheme'

const { palette, setPalette } = useTheme()
const open = ref(false)
const root = ref<HTMLElement>()
const trigger = ref<HTMLButtonElement>()
const popoverId = useId()

function onPointerDown(event: PointerEvent) {
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
  open.value = false
  trigger.value?.focus()
}

onMounted(() => {
  document.addEventListener('pointerdown', onPointerDown)
  document.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onPointerDown)
  document.removeEventListener('keydown', onKeydown)
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
    <Transition name="palette-popover">
      <div
        v-if="open"
        :id="popoverId"
        class="palette-popover"
        role="dialog"
        aria-label="选择配色方案"
      >
        <p class="palette-popover-title">配色方案</p>
        <button
          class="palette-option"
          type="button"
          :aria-pressed="palette === 'fufu-blue'"
          @click="choose('fufu-blue')"
        >
          <span class="palette-swatch palette-swatch--blue" aria-hidden="true"></span>
          <span>芙芙蓝</span>
          <Check
            v-if="palette === 'fufu-blue'"
            class="palette-check"
            :size="15"
            aria-hidden="true"
          />
        </button>
        <button
          class="palette-option"
          type="button"
          :aria-pressed="palette === 'hutao-red'"
          @click="choose('hutao-red')"
        >
          <span class="palette-swatch palette-swatch--red" aria-hidden="true"></span>
          <span>胡桃红</span>
          <Check
            v-if="palette === 'hutao-red'"
            class="palette-check"
            :size="15"
            aria-hidden="true"
          />
        </button>
      </div>
    </Transition>
  </div>
</template>
