<script setup lang="ts">
import { ref, watch } from 'vue'
import { Copy, Download } from 'lucide-vue-next'
const props = withDefaults(
  defineProps<{ value: string; ready: boolean; busy?: boolean; filename?: string }>(),
  {
    filename: 'result.txt',
  },
)
const message = ref('')
const output = ref<HTMLTextAreaElement>()
watch(
  () => props.value,
  () => {
    message.value = ''
  },
)
watch(
  () => props.ready,
  () => {
    message.value = ''
  },
)
async function copy() {
  const value = props.value
  try {
    await navigator.clipboard.writeText(value)
    if (props.value === value && props.ready) message.value = '结果已复制'
  } catch {
    if (props.value !== value || !props.ready) return
    output.value?.focus()
    output.value?.select()
    message.value = '无法自动复制，已选中结果，请手动复制。'
  }
}
function download() {
  const url = URL.createObjectURL(
    new Blob([props.value], {
      type: props.filename.endsWith('.json')
        ? 'application/json;charset=utf-8'
        : 'text/plain;charset=utf-8',
    }),
  )
  const link = document.createElement('a')
  link.href = url
  link.download = props.filename
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
  message.value = '已创建下载文件'
}
</script>

<template>
  <section class="tool-editor tool-output" aria-label="处理结果" :aria-busy="busy">
    <div class="tool-editor-header">
      <label for="tool-output">处理结果</label>
      <div class="tool-inline-actions">
        <button type="button" :disabled="!ready" @click="copy">
          <Copy :size="15" aria-hidden="true" />复制
        </button>
        <button type="button" :disabled="!ready" @click="download">
          <Download :size="15" aria-hidden="true" />下载
        </button>
      </div>
    </div>
    <textarea
      id="tool-output"
      ref="output"
      :value="value"
      readonly
      spellcheck="false"
      placeholder="处理结果显示在这里"
    />
    <p class="tool-editor-meta" role="status">
      {{
        message || (busy ? '计算中…' : ready ? (value ? '处理完成' : '结果为空文本') : '等待处理')
      }}
    </p>
  </section>
</template>
