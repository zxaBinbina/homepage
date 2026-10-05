<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowLeftRight, Eraser, FlaskConical } from 'lucide-vue-next'
import OutputPanel from './OutputPanel.vue'
import {
  checkInput,
  decodeBase64,
  encodeBase64,
  formatJson,
  textStats,
  transformText,
  transformUrl,
  type TextAction,
} from '../transform'

const props = defineProps<{ id: 'json' | 'base64' | 'url' | 'text' }>()
const input = ref('')
const output = ref('')
const ready = ref(false)
const error = ref('')
const indent = ref('  ')
const urlSafe = ref(false)
const urlMode = ref<'component' | 'uri'>('component')
const plusAsSpace = ref(false)
const stats = computed(() => textStats(input.value))
const samples = {
  json: '{"name":"悠哉世界","online":true,"players":["a彬彬a","Steve"],"id":1234567890123456789}',
  base64: '你好，方块世界！🌍',
  url: '你好 世界 & Minecraft /?name=a彬彬a',
  text: '  悠哉世界  \nMinecraft\n\nMinecraft\n用代码与热爱构筑',
}
function invalidate() {
  output.value = ''
  ready.value = false
  error.value = ''
}
watch([input, indent, urlSafe, urlMode, plusAsSpace], invalidate, { flush: 'sync' })
function run(action: string) {
  invalidate()
  try {
    checkInput(input.value)
    if (!input.value) throw new Error('请先输入需要处理的内容。')
    if (props.id === 'json')
      output.value = formatJson(input.value, action === 'minify' ? '' : indent.value)
    else if (props.id === 'base64')
      output.value =
        action === 'decode'
          ? decodeBase64(input.value, urlSafe.value)
          : encodeBase64(input.value, urlSafe.value)
    else if (props.id === 'url')
      output.value = transformUrl(
        input.value,
        action === 'decode',
        urlMode.value,
        plusAsSpace.value,
      )
    else output.value = transformText(input.value, action as TextAction)
    ready.value = true
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '处理失败，请检查输入内容。'
  }
}
function reuse() {
  const result = output.value
  input.value = result
  invalidate()
}
function clear() {
  input.value = ''
  invalidate()
}
</script>

<template>
  <div class="tool-workspace">
    <div class="tool-controls">
      <template v-if="id === 'json'">
        <label class="tool-field-inline"
          >缩进<select v-model="indent" aria-label="缩进">
            <option value="  ">2 个空格</option>
            <option value="    ">4 个空格</option>
            <option :value="'\t'">Tab</option>
          </select></label
        >
        <button class="button primary" type="button" @click="run('format')">格式化 / 校验</button>
        <button class="button secondary" type="button" @click="run('minify')">压缩 JSON</button>
      </template>
      <template v-else-if="id === 'base64' || id === 'url'">
        <label v-if="id === 'base64'" class="tool-field-inline"
          >格式<select v-model="urlSafe" aria-label="Base64 格式">
            <option :value="false">标准 Base64</option>
            <option :value="true">URL 安全 Base64</option>
          </select></label
        >
        <template v-else>
          <label class="tool-field-inline"
            >模式<select v-model="urlMode" aria-label="URL 模式">
              <option value="component">参数值</option>
              <option value="uri">完整网址</option>
            </select></label
          >
          <label v-if="urlMode === 'component'" class="tool-checkbox"
            ><input v-model="plusAsSpace" type="checkbox" />解码时将 + 视为空格</label
          >
        </template>
        <button class="button primary" type="button" @click="run('encode')">编码</button>
        <button class="button secondary" type="button" @click="run('decode')">解码</button>
      </template>
      <template v-else>
        <button class="button primary" type="button" @click="run('deduplicate')">按行去重</button>
        <button class="button secondary" type="button" @click="run('empty')">移除空行</button>
        <button class="button secondary" type="button" @click="run('trim')">清理行首尾空格</button>
        <button class="button secondary" type="button" @click="run('upper')">转大写</button>
        <button class="button secondary" type="button" @click="run('lower')">转小写</button>
      </template>
    </div>
    <p v-if="error" id="tool-input-error" class="tool-error" role="alert">{{ error }}</p>
    <div class="tool-editor-grid">
      <section class="tool-editor" aria-label="输入内容">
        <div class="tool-editor-header">
          <label for="tool-input">输入内容</label>
          <div class="tool-inline-actions">
            <button type="button" @click="input = samples[id]">
              <FlaskConical :size="15" aria-hidden="true" />示例
            </button>
            <button type="button" @click="clear">
              <Eraser :size="15" aria-hidden="true" />清空
            </button>
          </div>
        </div>
        <textarea
          id="tool-input"
          v-model="input"
          spellcheck="false"
          autocomplete="off"
          autocapitalize="off"
          :aria-invalid="!!error"
          :aria-describedby="error ? 'tool-input-error' : undefined"
          :placeholder="id === 'json' ? '输入 JSON，或点击「示例」' : '输入或粘贴内容'"
        />
        <p class="tool-editor-meta">
          {{ stats.characters.toLocaleString() }} 个字符 · {{ stats.lines.toLocaleString() }} 行
        </p>
      </section>
      <OutputPanel
        :value="output"
        :ready="ready"
        :filename="id === 'json' ? 'formatted.json' : `${id}-result.txt`"
      />
    </div>
    <div class="tool-after-actions">
      <button type="button" class="button secondary" :disabled="!ready" @click="reuse">
        <ArrowLeftRight :size="16" aria-hidden="true" />将结果用作输入
      </button>
    </div>
  </div>
</template>
