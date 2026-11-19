<script setup lang="ts">
import { computed, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import * as PDF from 'pdfjs-dist'
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import ToolPage from '../freemium/components/ToolPage.vue'
import { saveBlob } from '../jaytools/files'
import { normalizeText } from './analyze'
import type { ConvertId, ConvertOptions, ConvertOutput, PdfPageData, Target } from './types'

PDF.GlobalWorkerOptions.workerSrc = pdfWorker
const props = defineProps<{ toolId: ConvertId }>()
const target = computed(
  () =>
    ({
      'pdf-to-word': 'word',
      'pdf-to-excel': 'excel',
      'pdf-to-powerpoint': 'powerpoint',
      'pdf-to-markdown': 'markdown',
    })[props.toolId] as Target,
)
const file = shallowRef<File | null>(null)
const fileInput = ref<HTMLInputElement>()
const password = ref('')
const mode = ref<'text' | 'image'>('text')
const first = ref(1)
const last = ref<number | string>('')
const resolution = ref('1200')
const pageBreaks = ref(true)
const excelScope = ref<'tables' | 'all'>('tables')
const excelSheets = ref<'pages' | 'single'>('pages')
const numbers = ref(false)
const busy = ref(false)
const progress = ref('')
const error = ref('')
const result = shallowRef<ConvertOutput | null>(null)
const copied = ref(false)
let generation = 0
let task: PDF.PDFDocumentLoadingTask | undefined
let renderTask: PDF.RenderTask | undefined
let worker: Worker | undefined
let rejectWorker: ((reason: Error) => void) | undefined
let timer: ReturnType<typeof setTimeout> | undefined
const imageMode = computed(
  () => ['word', 'powerpoint'].includes(target.value) && mode.value === 'image',
)
const imageNote = computed(() =>
  imageMode.value
    ? '每页作为一张图片，保留版面；文字不可编辑，支持扫描件。'
    : target.value === 'powerpoint'
      ? '仅保留可编辑文字与大致位置，使用替代字体，不保留图片、背景和原文字颜色。'
      : '读取已有文字层，不含 OCR；图片不导出，复杂多栏、合并单元格与换行表格需核对。',
)

function release() {
  ++generation
  renderTask?.cancel()
  renderTask = undefined
  worker?.terminate()
  worker = undefined
  rejectWorker?.(new Error('已取消'))
  rejectWorker = undefined
  const oldTask = task
  task = undefined
  if (oldTask) void oldTask.destroy().catch(() => {})
  clearTimeout(timer)
  timer = undefined
  busy.value = false
  progress.value = ''
  result.value = null
  copied.value = false
}
function clear() {
  release()
  file.value = null
  password.value = ''
  error.value = ''
  if (fileInput.value) fileInput.value.value = ''
}
function choose(event: Event) {
  release()
  password.value = ''
  const selected = (event.target as HTMLInputElement).files?.[0] || null
  file.value = selected
  error.value =
    selected && selected.size > 30 * 1024 * 1024 ? '文件超过 30 MB，请先拆分或压缩 PDF。' : ''
  if (error.value) file.value = null
}
watch(
  [password, mode, first, last, resolution, pageBreaks, excelScope, excelSheets, numbers],
  () => {
    release()
    error.value = ''
  },
  { flush: 'sync' },
)
watch(
  () => props.toolId,
  () => {
    clear()
    mode.value = target.value === 'powerpoint' ? 'image' : 'text'
  },
  { immediate: true },
)
onBeforeUnmount(release)

async function convert() {
  release()
  error.value = ''
  const selected = file.value
  if (!selected) return
  const endInput = last.value === '' ? null : Number(last.value)
  if (
    !Number.isInteger(first.value) ||
    first.value < 1 ||
    (endInput != null && (!Number.isInteger(endInput) || endInput < first.value))
  ) {
    error.value = '请输入有效页码，结束页不能小于开始页。'
    return
  }
  const version = generation
  const options: ConvertOptions = {
    target: target.value,
    mode: imageMode.value ? 'image' : 'text',
    pageBreaks: pageBreaks.value,
    excelScope: excelScope.value,
    excelSheets: excelSheets.value,
    numbers: numbers.value,
  }
  busy.value = true
  progress.value = '正在读取 PDF…'
  const active = () => {
    if (version !== generation) throw new Error('已取消')
  }
  timer = setTimeout(() => {
    if (version === generation) {
      release()
      error.value = '转换超时，请减少页数后重试。'
    }
  }, 120000)
  try {
    const data = new Uint8Array(await selected.arrayBuffer())
    active()
    const localTask = PDF.getDocument({
      data,
      password: password.value,
      verbosity: 0,
      fontExtraProperties: true,
      cMapUrl: '/tool-assets/pdfjs/cmaps/',
      cMapPacked: true,
      standardFontDataUrl: '/tool-assets/pdfjs/standard_fonts/',
      wasmUrl: '/tool-assets/pdfjs/wasm/',
    })
    task = localTask
    const document = await localTask.promise
    active()
    const end = endInput ?? document.numPages
    if (first.value > document.numPages || end > document.numPages)
      throw new Error(`这份 PDF 共 ${document.numPages} 页，请调整页码范围。`)
    const count = end - first.value + 1,
      limit = options.mode === 'image' ? 100 : 300
    if (count > limit) throw new Error(`本模式一次最多转换 ${limit} 页，请缩小页码范围。`)
    const pages: PdfPageData[] = []
    let imageBytes = 0
    for (let number = first.value; number <= end; number++) {
      active()
      progress.value = `正在处理第 ${number} 页（${number - first.value + 1} / ${count}）…`
      const page = await document.getPage(number)
      const viewport = page.getViewport({ scale: 1 })
      if (
        viewport.width / 72 > 40 ||
        viewport.height / 72 > 40 ||
        viewport.width < 24 ||
        viewport.height < 24
      )
        throw new Error('页面尺寸超出办公文档支持范围，请先调整 PDF 页面大小。')
      const content = await page.getTextContent()
      await page.getOperatorList()
      active()
      const fonts: PdfPageData['fonts'] = {}
      const items = content.items.flatMap((item) => {
        if (!('str' in item)) return []
        const tx = PDF.Util.transform(viewport.transform, item.transform)
        const height = Math.hypot(tx[2]!, tx[3]!)
        let fontName = content.styles[item.fontName]?.fontFamily || ''
        try {
          if (page.commonObjs.has(item.fontName))
            fontName = page.commonObjs.get(item.fontName)?.name || fontName
        } catch {
          /* Use the style fallback. */
        }
        fonts[item.fontName] = { name: fontName }
        return [
          {
            x: Math.max(0, tx[4]!),
            y: Math.max(0, tx[5]! - height * 0.8),
            width: item.width,
            height,
            text: normalizeText(item.str),
            font: item.fontName,
          },
        ]
      })
      const pageData: PdfPageData = {
        index: number - 1,
        width: viewport.width,
        height: viewport.height,
        items,
        fonts,
      }
      if (options.mode === 'image') {
        const scale = Math.min(
          Number(resolution.value) / viewport.width,
          Math.sqrt(6000000 / (viewport.width * viewport.height)),
        )
        const imageViewport = page.getViewport({ scale })
        const canvas = window.document.createElement('canvas')
        canvas.width = Math.ceil(imageViewport.width)
        canvas.height = Math.ceil(imageViewport.height)
        const context = canvas.getContext('2d')
        if (!context) throw new Error('浏览器无法创建图片画布。')
        let currentRender: PDF.RenderTask | undefined
        try {
          currentRender = page.render({
            canvas,
            canvasContext: context,
            viewport: imageViewport,
            background: 'rgb(255,255,255)',
          })
          renderTask = currentRender
          await currentRender.promise
          active()
          pageData.image = canvas.toDataURL('image/jpeg', 0.9)
          imageBytes += pageData.image.length * 0.75
          if (imageBytes > 60 * 1024 * 1024)
            throw new Error('图片总量超过 60 MB，请减少页数或降低清晰度。')
        } finally {
          canvas.width = 0
          canvas.height = 0
          if (renderTask === currentRender) renderTask = undefined
        }
      }
      pages.push(pageData)
      page.cleanup()
      await new Promise((resolve) => setTimeout(resolve, 0))
    }
    active()
    progress.value = '正在整理内容并生成文件…'
    worker = new Worker(new URL('./convert.worker.ts', import.meta.url), { type: 'module' })
    const output = await new Promise<ConvertOutput>((resolve, reject) => {
      rejectWorker = reject
      worker!.onmessage = (event: MessageEvent<{ result?: ConvertOutput; error?: string }>) => {
        if (event.data.error) reject(new Error(event.data.error))
        else if (event.data.result) resolve(event.data.result)
      }
      worker!.onerror = () => reject(new Error('转换模块未能加载，请重新加载页面后重试。'))
      worker!.postMessage({ pages, options })
    })
    active()
    result.value = output
    progress.value = '转换完成'
  } catch (reason) {
    if (version !== generation) return
    const name = reason instanceof Error ? reason.name : ''
    error.value =
      name === 'PasswordException'
        ? 'PDF 已加密，请输入正确的打开密码后重试。'
        : name === 'InvalidPDFException'
          ? '无法读取这份 PDF，请确认文件完整且格式正确。'
          : reason instanceof Error
            ? reason.message
            : '转换失败，请检查 PDF 后重试。'
    progress.value = ''
  } finally {
    if (version === generation) {
      busy.value = false
      worker?.terminate()
      worker = undefined
      rejectWorker = undefined
      clearTimeout(timer)
      timer = undefined
      const oldTask = task
      task = undefined
      if (oldTask) void oldTask.destroy().catch(() => {})
    }
  }
}
function download() {
  const output = result.value
  if (output && file.value)
    saveBlob(
      new Blob([new Uint8Array(output.bytes)], { type: output.mime }),
      `${file.value.name.replace(/\.pdf$/i, '')}.${output.extension}`,
    )
}
async function copy() {
  const current = result.value
  if (!current) return
  const version = generation
  try {
    await navigator.clipboard.writeText(new TextDecoder().decode(current.bytes))
    if (version === generation) copied.value = true
  } catch {
    if (version === generation) error.value = '复制未成功，可下载 Markdown 文件。'
  }
}
</script>

<template>
  <ToolPage>
    <template #actions>
      <button class="btn btn--prominent" type="button" :disabled="!file || busy" @click="convert">
        开始转换
      </button>
      <button class="btn" type="button" :disabled="!file && !busy && !error" @click="clear">
        取消并清空
      </button>
    </template>
    <template #options>
      <label v-if="target === 'word' || target === 'powerpoint'" class="jay-field"
        >转换模式
        <select v-model="mode" class="field">
          <option value="text">可编辑文字</option>
          <option value="image">整页图片</option>
        </select>
      </label>
      <label class="jay-field"
        >开始页<input v-model.number="first" class="field" type="number" min="1" step="1"
      /></label>
      <label class="jay-field"
        >结束页（留空为末页）<input
          v-model.number="last"
          class="field"
          type="number"
          min="1"
          step="1"
      /></label>
      <label v-if="imageMode" class="jay-field"
        >图片清晰度<select v-model="resolution" class="field">
          <option value="1200">标准 · 1200 像素宽</option>
          <option value="1800">清晰 · 1800 像素宽</option>
        </select></label
      >
      <template v-if="target === 'excel'">
        <label class="jay-field"
          >导出内容<select v-model="excelScope" class="field">
            <option value="tables">仅表格</option>
            <option value="all">全部文字</option>
          </select></label
        >
        <label class="jay-field"
          >工作表布局<select v-model="excelSheets" class="field">
            <option value="pages">每页一个工作表</option>
            <option value="single">合并为一个工作表</option>
          </select></label
        >
        <label class="jay-check"
          ><input v-model="numbers" type="checkbox" />识别普通数字（编号保持为文字）</label
        >
      </template>
      <label v-if="!imageMode && (target === 'word' || target === 'markdown')" class="jay-check"
        ><input v-model="pageBreaks" type="checkbox" />保留页间分隔</label
      >
    </template>
    <div class="jay-panel pdfconv-panel">
      <div class="jay-form-grid">
        <label class="jay-field jay-file"
          >选择 PDF（最多 30 MB）<input
            ref="fileInput"
            class="sr-only"
            type="file"
            aria-label="选择 PDF"
            accept=".pdf,application/pdf"
            @change="choose"
          /><span class="jay-file-control" aria-hidden="true"
            ><span class="btn jay-file-choice">选择文件</span
            ><span>{{ file?.name || '未选择 PDF' }}</span></span
          ></label
        >
        <label class="jay-field"
          >打开密码（仅加密文件需要）<input
            v-model="password"
            class="field"
            type="password"
            autocomplete="off"
            placeholder="不会保存密码"
        /></label>
      </div>
      <p class="jay-note">
        {{ imageNote }}一次最多转换 {{ imageMode ? '100' : '300' }} 页，可用页码分批处理。
      </p>
      <p v-if="progress" class="pdfconv-status" role="status" aria-live="polite">{{ progress }}</p>
      <p v-if="error" class="jay-error" role="alert">{{ error }}</p>
      <div v-if="result" class="pdfconv-result">
        <p>
          {{ result.stats.pages }} 页已转换<span v-if="!imageMode">
            · {{ result.stats.tables }} 个表格</span
          >
          · {{ (result.bytes.byteLength / 1024).toFixed(1) }} KB
        </p>
        <p v-if="!imageMode && result.stats.textPages < result.stats.pages" class="jay-note">
          {{ result.stats.pages - result.stats.textPages }}
          页没有文字层，文字模式未能提取这些页面的内容。
        </p>
        <div class="jay-actions">
          <button class="btn btn--prominent" type="button" @click="download">
            下载 .{{ result.extension }}
          </button>
          <button v-if="target === 'markdown'" class="btn" type="button" @click="copy">
            {{ copied ? '已复制' : '复制 Markdown' }}
          </button>
        </div>
        <label v-if="target === 'markdown'" class="jay-field"
          >Markdown 预览（最多 5 万字符，下载与复制包含完整内容）
          <textarea
            class="field pdfconv-preview"
            readonly
            :value="result.preview"
            spellcheck="false"
          ></textarea>
        </label>
      </div>
      <p class="jay-note">
        请核对转换后的内容与排版。<a href="/licenses/pdf-convert.txt" target="_blank" rel="noopener"
          >开源来源与许可</a
        >
      </p>
    </div>
  </ToolPage>
</template>
