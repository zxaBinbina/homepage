<template>
  <ToolPage fill>
    <template v-if="options.length || swap" #options>
      <OptionControls v-model="opts" :options="options" />
      <button
        v-if="swap"
        class="btn btn--sm"
        type="button"
        @click="doSwap"
        title="将结果用作输入并反转方向"
      >
        <AppIcon name="swap" :size="16" />交换
      </button>
    </template>

    <div class="split">
      <CodePane
        v-model="input"
        :label="inputLabel"
        :placeholder="placeholder"
        :sample="typeof sample === 'function' ? () => sample(opts) : sample"
        :accept="accept"
        :mono="monoInput"
      />
      <slot name="output" :output="output" :error="error" :input="input" :opts="opts">
        <CodePane
          :model-value="output"
          :label="outputLabel"
          :error="error"
          :download="downloadName"
          readonly
        />
      </slot>
    </div>
    <slot name="below" :output="output" :input="input" :opts="opts" />
  </ToolPage>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import ToolPage from './ToolPage.vue'
import CodePane from './CodePane.vue'
import OptionControls from './OptionControls.vue'
import AppIcon from './AppIcon.vue'
import { takeHandoff } from '../composables/useHandoff'
import { load, save } from '../composables/storage'

const props = defineProps({
  // (input: string, opts: object) => string | Promise<string>. Throw an Error to show it inline.
  transform: { type: Function, required: true },
  options: { type: Array, default: () => [] },
  sample: { type: [String, Function], default: null },
  inputLabel: { type: String, default: '输入' },
  outputLabel: { type: String, default: '结果' },
  placeholder: { type: String, default: '在这里输入或粘贴…' },
  accept: { type: [String, Boolean], default: '' },
  monoInput: { type: Boolean, default: true },
  // Output file name for Download; may be a function of opts.
  download: { type: [String, Function], default: 'output.txt' },
  // { key, values: [a, b] } — enables a Swap button that flips opts[key] and moves output to input.
  swap: { type: Object, default: null },
})

const route = useRoute()
const id = route.meta.tool
const defaults = Object.fromEntries(props.options.map((o) => [o.key, o.default]))
const opts = ref({ ...defaults, ...load(`freemium:opts:${id}`, {}) })
const input = ref(sessionGet(`freemium:input:${id}`) || '')
const output = ref('')
const error = ref('')

const downloadName = computed(() =>
  typeof props.download === 'function' ? props.download(opts.value) : props.download,
)

function sessionGet(k) {
  try {
    return null
  } catch {
    return null
  }
}
function sessionSet(k, v) {
  try {
    void 0
  } catch {
    /* ignore */
  }
}

let timer = null
let runId = 0
async function run() {
  const current = ++runId
  if (!input.value.trim()) {
    output.value = ''
    error.value = ''
    return
  }
  try {
    if (input.value.length > 1000000) throw new Error('输入过长，请限制在 100 万字符以内。')
    const result = await props.transform(input.value, opts.value)
    if (current !== runId) return
    output.value = result ?? ''
    error.value = ''
  } catch (e) {
    if (current !== runId) return
    output.value = ''
    error.value = `处理失败：${e?.message || String(e)}`
  }
}

watch(
  [input, opts],
  () => {
    ++runId
    output.value = ''
    error.value = ''
    clearTimeout(timer)
    timer = setTimeout(run, input.value.length > 50000 ? 300 : 90)
    sessionSet(`freemium:input:${id}`, input.value.length < 200000 ? input.value : '')
    save(`freemium:opts:${id}`, opts.value)
  },
  { deep: true },
)

onMounted(() => {
  const handed = takeHandoff()
  if (handed != null) input.value = handed
  run()
})

function doSwap() {
  const { key, values } = props.swap
  const next = opts.value[key] === values[0] ? values[1] : values[0]
  const out = output.value
  opts.value = { ...opts.value, [key]: next }
  if (out) input.value = out
}

onBeforeUnmount(() => {
  ++runId
  clearTimeout(timer)
})

defineExpose({ input, output, opts })
</script>
