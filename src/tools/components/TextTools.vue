<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { ArrowLeftRight, Eraser, FlaskConical } from 'lucide-vue-next'
import OutputPanel from './OutputPanel.vue'
import {
  checkInput,
  convertRadix,
  decodeBase64,
  encodeBase64,
  formatJson,
  escapeHtml,
  hashAlgorithms,
  hashText,
  parseJwt,
  textStats,
  transformText,
  transformUrl,
  unescapeHtml,
  type HashAlgorithm,
  type TextAction,
} from '../transform'

const props = defineProps<{
  id: 'json' | 'base64' | 'url' | 'text' | 'radix' | 'hash' | 'jwt' | 'html'
}>()
const input = ref('')
const output = ref('')
const ready = ref(false)
const error = ref('')
const indent = ref('  ')
const urlSafe = ref(false)
const urlMode = ref<'component' | 'uri'>('component')
const plusAsSpace = ref(false)
const sourceBase = ref(10)
const targetBase = ref(16)
const bases = Array.from({ length: 35 }, (_, index) => index + 2)
const algorithm = ref<HashAlgorithm>('SHA-256')
const uppercaseHash = ref(false)
const busy = ref(false)
let generation = 0
const stats = computed(() => textStats(input.value))
const samples = {
  json: '{"name":"悠哉世界","online":true,"players":["a彬彬a","Steve"],"id":1234567890123456789}',
  base64: '你好，方块世界！🌍',
  url: '你好 世界 & Minecraft /?name=a彬彬a',
  text: '  悠哉世界  \nMinecraft\n\nMinecraft\n用代码与热爱构筑',
  radix: '12345678901234567890',
  hash: 'abc',
  jwt: [
    encodeBase64('{"alg":"HS256","typ":"JWT"}', true),
    encodeBase64('{"sub":"zxabinbina","name":"a彬彬a","iat":1704067200,"exp":1893456000}', true),
    'c2FtcGxl',
  ].join('.'),
  html: '<p title="你好">Minecraft & 方块世界</p>',
}
function invalidate() {
  generation++
  busy.value = false
  output.value = ''
  ready.value = false
  error.value = ''
}
watch(
  [input, indent, urlSafe, urlMode, plusAsSpace, sourceBase, targetBase, algorithm, uppercaseHash],
  invalidate,
  { flush: 'sync' },
)
onBeforeUnmount(invalidate)
async function run(action: string) {
  invalidate()
  const current = generation
  try {
    checkInput(input.value)
    if (!input.value && props.id !== 'hash') throw new Error('请先输入需要处理的内容。')
    let result: string
    if (props.id === 'json')
      result = formatJson(input.value, action === 'minify' ? '' : indent.value)
    else if (props.id === 'base64')
      result =
        action === 'decode'
          ? decodeBase64(input.value, urlSafe.value)
          : encodeBase64(input.value, urlSafe.value)
    else if (props.id === 'url')
      result = transformUrl(input.value, action === 'decode', urlMode.value, plusAsSpace.value)
    else if (props.id === 'radix')
      result = convertRadix(input.value, sourceBase.value, targetBase.value)
    else if (props.id === 'html')
      result = action === 'decode' ? unescapeHtml(input.value) : escapeHtml(input.value)
    else if (props.id === 'jwt') result = parseJwt(input.value)
    else if (props.id === 'hash') {
      busy.value = true
      const digest = await hashText(input.value, algorithm.value)
      result = uppercaseHash.value ? digest.toUpperCase() : digest
    } else result = transformText(input.value, action as TextAction)
    if (current !== generation) return
    output.value = result
    ready.value = true
  } catch (reason) {
    if (current !== generation) return
    error.value = reason instanceof Error ? reason.message : '处理失败，请检查输入内容。'
  } finally {
    if (current === generation) busy.value = false
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
      <template v-else-if="id === 'radix'">
        <label class="tool-field-inline"
          >输入进制<select v-model.number="sourceBase" aria-label="输入进制">
            <option v-for="base in bases" :key="base" :value="base">{{ base }} 进制</option>
          </select></label
        >
        <label class="tool-field-inline"
          >输出进制<select v-model.number="targetBase" aria-label="输出进制">
            <option v-for="base in bases" :key="base" :value="base">{{ base }} 进制</option>
          </select></label
        >
        <button class="button primary" type="button" @click="run('convert')">转换进制</button>
      </template>
      <template v-else-if="id === 'hash'">
        <label class="tool-field-inline"
          >算法<select v-model="algorithm" aria-label="哈希算法">
            <option v-for="item in hashAlgorithms" :key="item" :value="item">{{ item }}</option>
          </select></label
        >
        <label class="tool-checkbox"
          ><input v-model="uppercaseHash" type="checkbox" />输出大写</label
        >
        <button class="button primary" type="button" :disabled="busy" @click="run('hash')">
          {{ busy ? '计算中…' : '计算哈希' }}
        </button>
      </template>
      <template v-else-if="id === 'jwt'">
        <button class="button primary" type="button" @click="run('parse')">解析 JWT</button>
      </template>
      <template v-else-if="id === 'html'">
        <button class="button primary" type="button" @click="run('encode')">转义</button>
        <button class="button secondary" type="button" @click="run('decode')">还原</button>
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
        :busy="busy"
        :filename="id === 'json' ? 'formatted.json' : `${id}-result.txt`"
      />
    </div>
    <div v-if="id !== 'hash' && id !== 'jwt'" class="tool-after-actions">
      <button type="button" class="button secondary" :disabled="!ready" @click="reuse">
        <ArrowLeftRight :size="16" aria-hidden="true" />将结果用作输入
      </button>
    </div>
  </div>
</template>
