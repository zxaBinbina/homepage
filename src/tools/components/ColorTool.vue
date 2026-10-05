<script setup lang="ts">
import { ref, watch } from 'vue'
import OutputPanel from './OutputPanel.vue'
import { convertColor } from '../transform'

const input = ref('')
const color = ref<ReturnType<typeof convertColor> | null>(null)
const output = ref('')
const error = ref('')
watch(
  input,
  () => {
    color.value = null
    output.value = ''
    error.value = ''
  },
  { flush: 'sync' },
)
function convert() {
  color.value = null
  output.value = ''
  error.value = ''
  try {
    color.value = convertColor(input.value)
    output.value = `HEX: ${color.value.hex}\nRGB: ${color.value.rgb}\nHSL: ${color.value.hsl}`
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '请输入有效颜色。'
  }
}
function pick(event: Event) {
  input.value = (event.target as HTMLInputElement).value
  convert()
}
function sample() {
  input.value = '#4EA4EF'
  convert()
}
</script>

<template>
  <div class="tool-workspace">
    <div class="tool-editor-grid">
      <form class="tool-form-panel" @submit.prevent="convert">
        <label class="tool-field"
          >输入颜色<input
            v-model="input"
            placeholder="#4EA4EF / rgb(78, 164, 239)"
            autocomplete="off"
            spellcheck="false"
            :aria-invalid="!!error"
            :aria-describedby="error ? 'color-error' : undefined"
        /></label>
        <div class="tool-controls tool-color-controls">
          <label class="tool-field-inline"
            >取色器<input type="color" :value="color?.hex || '#4ea4ef'" @input="pick"
          /></label>
          <button class="button secondary" type="button" @click="sample">示例</button>
          <button class="button primary" type="submit">转换颜色</button>
        </div>
        <div
          class="tool-color-preview"
          :style="color ? { backgroundColor: color.hex } : undefined"
          role="img"
          :aria-label="color ? `颜色预览：${color.hex}` : '等待输入颜色'"
        ></div>
        <p v-if="error" id="color-error" class="tool-error" role="alert">{{ error }}</p>
      </form>
      <OutputPanel
        class="tool-compact-output tool-color-output"
        :value="output"
        :ready="!!color"
        filename="color.txt"
      />
    </div>
  </div>
</template>
