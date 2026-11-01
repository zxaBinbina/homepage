<script setup lang="ts">
import { computed, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { Download, FileUp, ShieldCheck } from 'lucide-vue-next'
import ToolPage from '../freemium/components/ToolPage.vue'
import CleanerWorker from './cleaner.worker?worker&inline'
import { MAX_INPUT_BYTES, type CleaningMode, type CleaningResult } from './cleaner'

const input = ref('')
const mode = ref<CleaningMode>('precise')
const previewLines = ref(10)
const filename = ref('')
const phase = ref<'reading' | 'cleaning' | ''>('')
const message = ref('')
const error = ref('')
const result = shallowRef<CleaningResult | null>(null)
const downloadUrl = ref('')
const busy = computed(() => phase.value !== '')
const downloadName = computed(
  () => `${filename.value.replace(/\.[^.]+$/, '') || 'codex-conversation'}.cleaned.jsonl`,
)
const preview = computed(() =>
  previewLines.value && result.value?.output
    ? result.value.output.split('\n', previewLines.value).join('\n')
    : '',
)
const descriptions: Record<CleaningMode, string> = {
  precise:
    '删除含 encrypted_content 字段或 type 为 reasoning / Reasoning 对象的整行，包括嵌套对象。保留 reasoning_effort、reasoning_output_tokens 等元数据。',
  broad:
    '删除原始文本中任意含 encrypted_content 或 reasoning 字样的整行，不区分大小写。参数、用量元数据和正文里提及这些词的行也会删除。',
  fields:
    '逐行递归删除 encrypted_content、reasoning 键及 type 为 reasoning / Reasoning 的对象，保留参数与用量元数据。顶层推理对象写为 {}，嵌套推理对象从属性或数组中移除，行数保持不变。',
}
const sample = [
  { type: 'session_meta', payload: { title: '一次代码讨论' } },
  { type: 'turn_context', reasoning_effort: 'medium' },
  { type: 'response_item', payload: { type: 'reasoning', encrypted_content: '示例加密内容' } },
  { type: 'response_item', payload: { type: 'message', content: '你好，这是可以分享的正文。' } },
  { type: 'event_msg', usage: { reasoning_output_tokens: 128 } },
]
  .map((event) => JSON.stringify(event))
  .join('\n')

let worker: Worker | undefined
let reader: FileReader | undefined
let timer: ReturnType<typeof setTimeout> | undefined
let version = 0

function stopTask() {
  worker?.terminate()
  worker = undefined
  reader?.abort()
  reader = undefined
  clearTimeout(timer)
  phase.value = ''
}
function invalidate() {
  version++
  stopTask()
  if (downloadUrl.value) URL.revokeObjectURL(downloadUrl.value)
  downloadUrl.value = ''
  result.value = null
  message.value = ''
  error.value = ''
}
watch(
  input,
  () => {
    invalidate()
    filename.value = ''
  },
  { flush: 'sync' },
)
watch(mode, invalidate, { flush: 'sync' })
onBeforeUnmount(invalidate)

function cancel() {
  invalidate()
  message.value = '已取消，可调整内容后重新清理。'
}
function loadSample() {
  invalidate()
  input.value = sample
  filename.value = ''
}
function clearInput() {
  invalidate()
  input.value = ''
  filename.value = ''
}
function loadFile(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''
  if (!file) return
  invalidate()
  if (file.size > MAX_INPUT_BYTES) {
    error.value = '文件请控制在 20 MB 以内。'
    return
  }
  const id = version
  phase.value = 'reading'
  reader = new FileReader()
  reader.onload = (loaded) => {
    if (id !== version) return
    reader = undefined
    input.value = String(loaded.target?.result ?? '')
    filename.value = file.name
    phase.value = ''
    message.value = '文件已读取，选择模式后开始清理。'
  }
  reader.onerror = () => {
    if (id !== version) return
    stopTask()
    error.value = '文件读取失败，请重新选择文件。'
  }
  reader.readAsText(file, 'UTF-8')
}
function run() {
  invalidate()
  if (!input.value) return
  const id = version
  phase.value = 'cleaning'
  const fail = (text: string) => {
    if (id !== version) return
    stopTask()
    error.value = text
  }
  try {
    worker = new CleanerWorker()
    timer = setTimeout(() => fail('处理超过 30 秒，请拆分文件后重试。'), 30000)
    worker.onmessage = ({ data }: MessageEvent<{ result?: CleaningResult; error?: string }>) => {
      if (id !== version) return
      stopTask()
      if (data.error || !data.result) {
        error.value = data.error || '未能生成结果，请重试。'
        return
      }
      result.value = data.result
      if (!data.result.invalidLines) {
        downloadUrl.value = URL.createObjectURL(
          new Blob([data.result.output], { type: 'application/x-ndjson;charset=utf-8' }),
        )
      }
    }
    worker.onerror = () => fail('清理程序未能运行，请重新加载后重试。')
    worker.postMessage({ input: input.value, mode: mode.value })
  } catch {
    fail('清理程序未能启动，请重新加载后重试。')
  }
}
</script>

<template>
  <ToolPage class="codex-cleaner">
    <template #options>
      <label class="codex-cleaner-field">
        清理模式
        <select v-model="mode" class="field" aria-describedby="codex-mode-help">
          <option value="precise">精确模式（默认）</option>
          <option value="broad">宽泛模式</option>
          <option value="fields">只删字段不删行</option>
        </select>
      </label>
      <button class="btn btn--prominent" :disabled="busy || !input" @click="run">
        {{ phase === 'cleaning' ? '正在清理…' : '开始清理' }}
      </button>
      <button v-if="busy" class="btn" @click="cancel">取消</button>
    </template>

    <p id="codex-mode-help" class="codex-cleaner-note">{{ descriptions[mode] }}</p>
    <section class="codex-cleaner-panel" aria-labelledby="codex-input-heading">
      <div class="codex-cleaner-toolbar">
        <h2 id="codex-input-heading">原始 JSONL</h2>
        <div class="codex-cleaner-actions">
          <label class="codex-cleaner-file">
            <span class="btn"><FileUp :size="16" aria-hidden="true" />选择文件</span>
            <input
              class="sr-only"
              type="file"
              accept=".jsonl,.ndjson,.json,.txt"
              aria-label="选择 JSONL 文件"
              @change="loadFile"
            />
          </label>
          <button class="btn" @click="loadSample">载入示例</button>
          <button class="btn" :disabled="!input && !busy" @click="clearInput">清空</button>
        </div>
      </div>
      <textarea
        v-model="input"
        class="field codex-cleaner-editor"
        aria-labelledby="codex-input-heading"
        aria-describedby="codex-input-help"
        :aria-invalid="!!result?.invalidLines"
        placeholder='粘贴对话记录，每行一个 JSON 事件对象。例如：{"type":"message","content":"你好"}'
        rows="10"
        spellcheck="false"
        autocapitalize="off"
        autocomplete="off"
      />
      <p id="codex-input-help" class="codex-cleaner-note">
        {{ filename ? `已读取：${filename} · ` : '' }}支持 UTF-8 JSONL，最多 20
        MB。空行会报错；文件末尾的单个换行不计为额外一行。
      </p>
    </section>

    <p v-if="busy || message" class="codex-cleaner-note" role="status">
      {{
        phase === 'reading'
          ? '正在读取文件…'
          : phase === 'cleaning'
            ? '正在逐行校验并清理…'
            : message
      }}
    </p>
    <p v-if="error" class="codex-cleaner-error" role="alert">{{ error }}</p>

    <section v-if="result" class="codex-cleaner-panel" aria-labelledby="codex-result-heading">
      <div class="codex-cleaner-toolbar">
        <h2 id="codex-result-heading">清理结果</h2>
        <a
          v-if="downloadUrl"
          class="btn btn--prominent"
          :href="downloadUrl"
          :download="downloadName"
        >
          <Download :size="16" aria-hidden="true" />下载 .jsonl
        </a>
      </div>
      <dl class="codex-cleaner-stats">
        <div>
          <dt>处理前</dt>
          <dd>{{ result.inputLines }} 行</dd>
        </div>
        <div>
          <dt>处理后</dt>
          <dd>{{ result.outputLines === null ? '未生成' : `${result.outputLines} 行` }}</dd>
        </div>
        <div>
          <dt>删除行数</dt>
          <dd>{{ result.removedLines === null ? '未生成' : `${result.removedLines} 行` }}</dd>
        </div>
      </dl>
      <div v-if="result.invalidLines" class="codex-cleaner-error" role="alert">
        <p>
          校验未通过：{{ result.invalidLines }} 行无效或无法处理，未生成下载文件。请修正后重试。
        </p>
        <ul>
          <li v-for="issue in result.issues" :key="issue.line">
            第 {{ issue.line }} 行：{{ issue.message }}
          </li>
        </ul>
        <p v-if="result.invalidLines > result.issues.length">
          仅显示前 {{ result.issues.length }} 处错误。
        </p>
      </div>
      <template v-else>
        <p class="codex-cleaner-success" role="status">
          <ShieldCheck :size="18" aria-hidden="true" />
          <span
            >{{
              result.outputLines
                ? `校验通过：输出 ${result.outputLines} 行，每行都是合法 JSON 对象。`
                : '校验通过：所有行均已清除，下载文件为空。'
            }}
            <template v-if="mode === 'fields'"
              >已清理 {{ result.modifiedLines }} 行的字段，保留全部行。</template
            ></span
          >
        </p>
        <label class="codex-cleaner-field">
          结果预览
          <select v-model.number="previewLines" class="field">
            <option :value="0">不预览</option>
            <option :value="10">前 10 行</option>
            <option :value="30">前 30 行</option>
            <option :value="100">前 100 行</option>
          </select>
        </label>
        <textarea
          v-if="previewLines && result.outputLines"
          :value="preview"
          class="field codex-cleaner-editor"
          aria-label="清理后 JSONL 预览"
          readonly
          rows="8"
          spellcheck="false"
        />
        <p class="codex-cleaner-note">
          下载包含全部清理结果，不受预览行数影响。仅按所选规则清理，正文与其他字段仍会保留。
        </p>
      </template>
    </section>
  </ToolPage>
</template>
