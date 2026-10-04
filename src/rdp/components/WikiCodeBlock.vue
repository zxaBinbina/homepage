<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { Check, Copy, Terminal } from 'lucide-vue-next'
defineProps<{ code: string; language: string; copyLabel?: string }>()
const copied = ref(false)
const message = ref('')
let timer: ReturnType<typeof setTimeout> | undefined
async function copy(code: string) {
  clearTimeout(timer)
  try {
    await navigator.clipboard.writeText(code)
    copied.value = true
    message.value = '内容已复制'
  } catch {
    copied.value = false
    message.value = '复制失败，请选中下方命令手动复制。'
  }
  timer = setTimeout(() => {
    copied.value = false
    message.value = ''
  }, 3500)
}
onBeforeUnmount(() => clearTimeout(timer))
</script>
<template>
  <div class="wiki-code">
    <div class="wiki-code-toolbar">
      <span
        ><Terminal :size="14" aria-hidden="true" />{{
          language === 'bash' ? '终端' : language === 'ini' ? '隧道配置' : '文本'
        }}</span
      ><button @click="copy(code)" :aria-label="copied ? '内容已复制' : copyLabel || '复制代码'">
        <Check v-if="copied" :size="14" /><Copy v-else :size="14" />{{
          copied ? '内容已复制' : '复制'
        }}
      </button>
    </div>
    <pre tabindex="0" :aria-label="`${language}代码`"><code>{{ code }}</code></pre>
    <p v-if="message && !copied" class="wiki-copy-message" role="status">{{ message }}</p>
  </div>
</template>
