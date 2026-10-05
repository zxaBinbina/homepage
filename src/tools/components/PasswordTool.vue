<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import OutputPanel from './OutputPanel.vue'
import { generatePasswords } from '../transform'

const options = reactive({
  length: 20,
  count: 1,
  lowercase: true,
  uppercase: true,
  numbers: true,
  symbols: true,
  excludeSimilar: true,
})
const output = ref('')
const ready = ref(false)
const error = ref('')
watch(
  options,
  () => {
    output.value = ''
    ready.value = false
    error.value = ''
  },
  { flush: 'sync' },
)
function generate() {
  output.value = ''
  ready.value = false
  error.value = ''
  try {
    output.value = generatePasswords({
      ...options,
      length: Number(options.length),
      count: Number(options.count),
    })
    ready.value = true
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '生成失败，请重试。'
  }
}
</script>

<template>
  <div class="tool-workspace">
    <form @submit.prevent="generate">
      <div class="tool-controls">
        <label class="tool-field-inline"
          >密码长度<input
            v-model.number="options.length"
            type="number"
            min="8"
            max="128"
            step="1"
            required
        /></label>
        <label class="tool-field-inline"
          >生成数量<input
            v-model.number="options.count"
            type="number"
            min="1"
            max="50"
            step="1"
            required
        /></label>
        <label class="tool-checkbox"
          ><input v-model="options.excludeSimilar" type="checkbox" />排除易混字符（0 O o 1 I l
          |）</label
        >
      </div>
      <div class="tool-controls" role="group" aria-label="密码字符类型">
        <label class="tool-checkbox"
          ><input v-model="options.lowercase" type="checkbox" />小写字母</label
        >
        <label class="tool-checkbox"
          ><input v-model="options.uppercase" type="checkbox" />大写字母</label
        >
        <label class="tool-checkbox"><input v-model="options.numbers" type="checkbox" />数字</label>
        <label class="tool-checkbox"><input v-model="options.symbols" type="checkbox" />符号</label>
        <button type="submit" class="button primary">
          <RefreshCw :size="16" aria-hidden="true" />生成密码
        </button>
      </div>
    </form>
    <p v-if="error" class="tool-error" role="alert">{{ error }}</p>
    <OutputPanel :value="output" :ready="ready" filename="passwords.txt" />
  </div>
</template>
