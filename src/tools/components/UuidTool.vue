<script setup lang="ts">
import { ref, watch } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import OutputPanel from './OutputPanel.vue'
import { generateUuids } from '../transform'
const count = ref<number | string>(1)
const uppercase = ref(false)
const hyphens = ref(true)
const output = ref('')
const ready = ref(false)
const error = ref('')
watch(
  [count, uppercase, hyphens],
  () => {
    output.value = ''
    ready.value = false
    error.value = ''
  },
  { flush: 'sync' },
)
function generate() {
  ready.value = false
  output.value = ''
  error.value = ''
  try {
    output.value = generateUuids(Number(count.value), uppercase.value, hyphens.value)
    ready.value = true
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '生成失败，请重试。'
  }
}
</script>

<template>
  <div class="tool-workspace">
    <form class="tool-controls" @submit.prevent="generate">
      <label class="tool-field-inline"
        >数量<input v-model.number="count" type="number" min="1" max="100" step="1" required
      /></label>
      <label class="tool-checkbox"><input v-model="uppercase" type="checkbox" />大写字母</label>
      <label class="tool-checkbox"><input v-model="hyphens" type="checkbox" />保留连字符</label>
      <button type="submit" class="button primary">
        <RefreshCw :size="16" aria-hidden="true" />生成 UUID
      </button>
    </form>
    <p v-if="error" class="tool-error" role="alert">{{ error }}</p>
    <OutputPanel :value="output" :ready="ready" filename="uuids.txt" />
  </div>
</template>
