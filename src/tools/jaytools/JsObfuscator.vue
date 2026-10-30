<script setup>
// Adapted from jaywcjlove/tools packages/js-obfuscator (MIT).
import { computed, ref, watch } from 'vue'
import ToolPage from '../freemium/components/ToolPage.vue'
import CodePane from '../freemium/components/CodePane.vue'
import {
  defaultOption,
  lowOption,
  mediumOption,
  highOption,
  allOptions,
} from './obfuscator-options'
import { useToolWorker } from './useToolWorker'
const worker = useToolWorker(
  () => new Worker(new URL('./obfuscate.worker.js', import.meta.url), { type: 'module' }),
  20000,
)
const presets = {
  default: defaultOption,
  low: lowOption,
  medium: mediumOption,
  high: highOption,
  all: allOptions,
}
const preset = ref('default')
const input = ref('')
const output = ref('')
const sourceMap = ref('')
const error = ref('')
const busy = ref(false)
const custom = ref('{}')
const advanced = ref(false)
let version = 0
const options = computed(() => ({ ...presets[preset.value], ...JSON.parse(custom.value) }))
function invalidate() {
  version++
  worker.cancel()
  busy.value = false
  output.value = ''
  sourceMap.value = ''
  error.value = ''
}
watch([input, preset, custom], invalidate, { flush: 'sync' })
async function run() {
  invalidate()
  const id = version
  busy.value = true
  try {
    if (!input.value.trim()) throw new Error('请先输入 JavaScript 代码。')
    if (input.value.length > 100000) throw new Error('代码请控制在 10 万字符以内。')
    const extra = JSON.parse(custom.value)
    if (!extra || typeof extra !== 'object' || Array.isArray(extra))
      throw new Error('自定义选项必须是 JSON 对象。')
    const result = await worker.run(input.value, options.value)
    if (version !== id) return
    output.value = result.result
    sourceMap.value = result.map
  } catch (e) {
    if (version === id) error.value = `处理失败：${e.message}`
  } finally {
    if (version === id) busy.value = false
  }
}
</script>
<template>
  <ToolPage>
    <template #options>
      <label class="jay-field"
        >混淆预设<select v-model="preset" class="field">
          <option value="default">默认</option>
          <option value="low">轻度</option>
          <option value="medium">中度</option>
          <option value="high">高度</option>
          <option value="all">完整默认选项</option>
        </select></label
      >
      <button class="btn" :aria-expanded="advanced" @click="advanced = !advanced">
        自定义选项
      </button>
      <button class="btn btn--prominent" :disabled="busy || !input.trim()" @click="run">
        {{ busy ? '正在混淆…' : '开始混淆' }}
      </button>
      <button v-if="busy" class="btn" @click="invalidate">取消</button>
    </template>
    <Transition
      name="jay-panel"
      @before-leave="(el) => (el.inert = true)"
      @before-enter="(el) => (el.inert = false)"
    >
      <div v-if="advanced" class="jay-panel">
        <label class="jay-field"
          >自定义选项（JSON，覆盖当前预设）<textarea
            v-model="custom"
            class="field"
            rows="5"
            spellcheck="false"
          />
        </label>
        <p class="jay-note">
          例如 {"compact":false,"seed":42,"sourceMap":true}。支持 javascript-obfuscator 的全部选项。
        </p>
      </div>
    </Transition>
    <div class="split">
      <CodePane
        v-model="input"
        label="JavaScript 源码"
        sample="function greet(name) { return '你好，' + name; }"
      /><CodePane
        :model-value="output"
        label="混淆结果"
        :error="error"
        readonly
        download="obfuscated.js"
      />
    </div>
    <CodePane
      v-if="sourceMap"
      :model-value="sourceMap"
      label="Source Map"
      readonly
      download="obfuscated.js.map"
    />
    <p class="jay-note">
      高强度混淆会增大代码并影响运行速度。这里只转换源码，不执行输入或输出；使用前请在自己的项目中测试。
    </p>
  </ToolPage>
</template>
