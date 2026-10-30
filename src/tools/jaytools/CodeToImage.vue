<script setup>
// Vue adaptation of jaywcjlove/tools packages/code-to-image (MIT).
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import hljs from 'highlight.js/lib/common'
import { toBlob, toJpeg, toSvg } from 'html-to-image'
import ToolPage from '../freemium/components/ToolPage.vue'
import CodePane from '../freemium/components/CodePane.vue'
import { saveBlob } from './files'
const sample =
  '// 在代码与方块之间\nfunction hello(name) {\n  return `你好，${name}！`;\n}\n\nconsole.log(hello("悠哉世界"));'
const input = ref('')
const language = ref('javascript')
const title = ref('hello.js')
const theme = ref('site')
const background = ref('#4ea4ef')
const transparent = ref(false)
const padding = ref(32)
const fontSize = ref(16)
const width = ref(720)
const numbers = ref(true)
const windowBar = ref(true)
const format = ref('png')
const frame = ref(null)
const busy = ref(false)
const error = ref('')
const message = ref('')
let version = 0
const valid = computed(
  () =>
    input.value.length <= 20000 &&
    width.value >= 320 &&
    width.value <= 1600 &&
    padding.value >= 0 &&
    padding.value <= 80 &&
    fontSize.value >= 10 &&
    fontSize.value <= 32,
)
const highlighted = computed(() => {
  const text = input.value.slice(0, 20000)
  return language.value === 'plaintext'
    ? hljs.highlight(text, { language: 'plaintext' }).value
    : hljs.highlight(text, { language: language.value, ignoreIllegals: true }).value
})
const languages = [
  'plaintext',
  'javascript',
  'typescript',
  'json',
  'xml',
  'css',
  'bash',
  'python',
  'java',
  'c',
  'cpp',
  'go',
  'rust',
  'sql',
  'yaml',
  'markdown',
]
watch(
  [
    input,
    language,
    title,
    theme,
    background,
    transparent,
    padding,
    fontSize,
    width,
    numbers,
    windowBar,
    format,
  ],
  () => {
    version++
    error.value = ''
    message.value = ''
  },
)
async function download() {
  const id = ++version
  busy.value = true
  error.value = ''
  message.value = ''
  try {
    if (!valid.value || !input.value) throw new Error('请填写代码，并检查尺寸与字号范围。')
    await nextTick()
    const settings = {
      pixelRatio: 2,
      skipFonts: true,
      backgroundColor: format.value === 'jpeg' && transparent.value ? '#ffffff' : undefined,
    }
    let blob
    if (format.value === 'png') blob = await toBlob(frame.value, settings)
    else
      blob = await (
        await fetch(await (format.value === 'jpeg' ? toJpeg : toSvg)(frame.value, settings))
      ).blob()
    if (!blob) throw new Error('浏览器未能生成图片，请减小代码长度。')
    if (id !== version) return
    saveBlob(blob, `code.${format.value === 'jpeg' ? 'jpg' : format.value}`)
    message.value = '图片已生成。'
  } catch (e) {
    if (id === version) error.value = `导出失败：${e.message}`
  } finally {
    busy.value = false
  }
}
onBeforeUnmount(() => version++)
</script>
<template>
  <ToolPage>
    <template #options
      ><label class="jay-field"
        >代码语言<select v-model="language" class="field">
          <option v-for="lang in languages" :key="lang" :value="lang">
            {{ lang === 'plaintext' ? '纯文本' : lang === 'xml' ? 'HTML / XML' : lang }}
          </option>
        </select></label
      ><label class="jay-field"
        >图片配色<select v-model="theme" class="field">
          <option value="site">跟随站点</option>
          <option value="dark">深色</option>
          <option value="light">浅色</option>
        </select></label
      ></template
    >
    <CodePane v-model="input" label="代码" :sample="sample" />
    <div class="jay-panel jay-form-grid">
      <label class="jay-field"
        >窗口标题<input v-model="title" class="field" maxlength="100" /></label
      ><label class="jay-field"
        >图片宽度<input
          v-model.number="width"
          class="field"
          type="number"
          min="320"
          max="1600"
          step="40"
      /></label>
      <label class="jay-field"
        >字号<input
          v-model.number="fontSize"
          class="field"
          type="number"
          min="10"
          max="32" /></label
      ><label class="jay-field"
        >留白<input v-model.number="padding" class="field" type="number" min="0" max="80" /></label
      ><label class="jay-field"
        >背景颜色<input v-model="background" class="field" type="color" /></label
      ><label class="jay-field"
        >导出格式<select v-model="format" class="field">
          <option value="png">PNG</option>
          <option value="jpeg">JPEG</option>
          <option value="svg">SVG</option>
        </select></label
      >
      <label class="jay-check"><input v-model="transparent" type="checkbox" />透明背景</label
      ><label class="jay-check"><input v-model="numbers" type="checkbox" />行号</label
      ><label class="jay-check"><input v-model="windowBar" type="checkbox" />窗口栏</label>
    </div>
    <div class="jay-code-scroll" role="region" aria-label="代码图片预览" tabindex="0">
      <div
        ref="frame"
        class="jay-code-frame"
        :data-code-theme="theme"
        :style="{
          width: `${Math.min(1600, Math.max(320, width || 720))}px`,
          padding: `${Math.min(80, Math.max(0, padding || 0))}px`,
          background: transparent ? 'transparent' : background,
          fontSize: `${Math.min(32, Math.max(10, fontSize || 16))}px`,
        }"
      >
        <div class="jay-code-window">
          <div v-if="windowBar" class="jay-code-title">
            <span aria-hidden="true">● ● ●</span>{{ title }}
          </div>
          <div class="jay-code-body">
            <pre v-if="numbers" class="jay-code-numbers" aria-hidden="true">{{
              input
                .split('\n')
                .map((_, i) => i + 1)
                .join('\n')
            }}</pre>
            <pre><code v-html="highlighted"></code></pre>
          </div>
        </div>
      </div>
    </div>
    <div class="jay-actions">
      <button class="btn btn--prominent" :disabled="busy || !input || !valid" @click="download">
        {{ busy ? '正在生成…' : '下载图片' }}</button
      ><span v-if="message" role="status">{{ message }}</span>
    </div>
    <p v-if="error" role="alert" class="jay-error">{{ error }}</p>
    <p v-if="!valid" role="alert" class="jay-error">
      最多 2 万字符；宽度 320–1600、字号 10–32、留白 0–80。
    </p>
    <p class="jay-note">
      预览区域可以横向滚动。PNG / JPEG 以 2 倍清晰度导出；JPEG 的透明区域会填充为白色。SVG 使用
      foreignObject，适合现代浏览器查看。
    </p>
  </ToolPage>
</template>
