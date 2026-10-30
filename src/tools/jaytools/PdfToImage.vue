<script setup>
// Adapted from jaywcjlove/tools packages/pdf-to-img (MIT).
import { onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import * as PDF from 'pdfjs-dist'
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { zipSync } from 'fflate'
import ToolPage from '../freemium/components/ToolPage.vue'
import { canvasBlob, saveBlob } from './files'
PDF.GlobalWorkerOptions.workerSrc = pdfWorker
const document = shallowRef(null)
const currentBlob = shallowRef(null)
const page = ref(1)
const scale = ref(1.5)
const format = ref('png')
const password = ref('')
const file = shallowRef(null)
const image = ref('')
const error = ref('')
const loading = ref(false)
const rendering = ref(false)
const exporting = ref(false)
const progress = ref('')
let generation = 0
let renderVersion = 0
let task
let renderTask
function clearImage() {
  if (image.value) URL.revokeObjectURL(image.value)
  image.value = ''
  currentBlob.value = null
}
function cancelRendering() {
  ++renderVersion
  renderTask?.cancel()
  renderTask = undefined
  rendering.value = false
}
function release() {
  ++generation
  cancelRendering()
  clearImage()
  const old = task
  task = undefined
  if (old) void old.destroy().catch(() => {})
  document.value = null
  loading.value = false
  exporting.value = false
  progress.value = ''
}
async function open() {
  release()
  error.value = ''
  if (!file.value) return
  const id = generation
  loading.value = true
  try {
    if (file.value.size > 30 * 1024 * 1024) throw new Error('PDF 请控制在 30 MB 以内。')
    const data = await file.value.arrayBuffer()
    if (id !== generation) return
    task = PDF.getDocument({
      data,
      password: password.value,
      isEvalSupported: false,
      cMapUrl: '/tool-assets/pdfjs/cmaps/',
      cMapPacked: true,
      standardFontDataUrl: '/tool-assets/pdfjs/standard_fonts/',
      wasmUrl: '/tool-assets/pdfjs/wasm/',
    })
    const pdf = await task.promise
    if (id !== generation) return
    page.value = 1
    document.value = pdf
    await preview()
  } catch (e) {
    if (id === generation)
      error.value =
        e.name === 'PasswordException'
          ? '此 PDF 需要正确密码，请填写密码后重新读取。'
          : `无法读取 PDF：${e.message}`
  } finally {
    if (id === generation) loading.value = false
  }
}
async function select(event) {
  file.value = event.target.files?.[0] || null
  await open()
}
async function render(number, id, serial) {
  if (!Number.isFinite(scale.value) || scale.value < 0.5 || scale.value > 3)
    throw new Error('清晰度应在 0.5–3 倍之间。')
  const pdfPage = await document.value.getPage(number)
  if (id !== generation || serial !== renderVersion) return null
  const viewport = pdfPage.getViewport({ scale: scale.value })
  if (
    viewport.width * viewport.height > 16000000 ||
    Math.max(viewport.width, viewport.height) > 16384
  )
    throw new Error('页面尺寸过大，请降低清晰度。')
  const canvas = window.document.createElement('canvas')
  canvas.width = Math.ceil(viewport.width)
  canvas.height = Math.ceil(viewport.height)
  renderTask = pdfPage.render({ canvas, viewport, background: 'rgb(255,255,255)' })
  try {
    await renderTask.promise
    if (id !== generation || serial !== renderVersion) return null
    return await canvasBlob(canvas, format.value === 'png' ? 'image/png' : 'image/jpeg')
  } finally {
    canvas.width = 0
    canvas.height = 0
    pdfPage.cleanup()
  }
}
async function preview() {
  cancelRendering()
  clearImage()
  error.value = ''
  if (!document.value) return
  const id = generation,
    serial = renderVersion
  rendering.value = true
  try {
    if (!Number.isInteger(page.value) || page.value < 1 || page.value > document.value.numPages)
      throw new Error('请输入有效页码。')
    const blob = await render(page.value, id, serial)
    if (blob && id === generation && serial === renderVersion) {
      currentBlob.value = blob
      image.value = URL.createObjectURL(blob)
    }
  } catch (e) {
    if (id === generation && serial === renderVersion && e.name !== 'RenderingCancelledException')
      error.value = `页面生成失败：${e.message}`
  } finally {
    if (id === generation && serial === renderVersion) rendering.value = false
  }
}
watch(
  [page, scale, format],
  () => {
    if (!exporting.value) void preview()
  },
  { flush: 'sync' },
)
const outputName = (number) =>
  `${(file.value?.name || 'document').replace(/\.pdf$/i, '')}-${number}.${format.value === 'png' ? 'png' : 'jpg'}`
async function saveAll() {
  if (!document.value) return
  cancelRendering()
  error.value = ''
  exporting.value = true
  const id = generation,
    serial = renderVersion
  try {
    if (document.value.numPages > 100)
      throw new Error('打包最多支持 100 页，请分成较小的 PDF，或逐页导出。')
    const files = {}
    let size = 0
    for (let n = 1; n <= document.value.numPages; n++) {
      progress.value = `正在生成 ${n} / ${document.value.numPages} 页…`
      const blob = await render(n, id, serial)
      if (!blob || id !== generation || serial !== renderVersion) return
      size += blob.size
      if (size > 64 * 1024 * 1024) throw new Error('图片总大小超过 64 MB，请降低清晰度或逐页导出。')
      files[outputName(n)] = new Uint8Array(await blob.arrayBuffer())
      if (id !== generation || serial !== renderVersion) return
    }
    saveBlob(
      new Blob([zipSync(files, { level: 0 })], { type: 'application/zip' }),
      `${file.value.name.replace(/\.pdf$/i, '')}-images.zip`,
    )
    progress.value = '全部页面已打包。'
  } catch (e) {
    if (id === generation && serial === renderVersion) error.value = `打包失败：${e.message}`
  } finally {
    if (id === generation && serial === renderVersion) exporting.value = false
  }
}
function cancelExport() {
  cancelRendering()
  exporting.value = false
  progress.value = '已取消打包。'
}
onBeforeUnmount(release)
</script>
<template>
  <ToolPage>
    <div class="jay-panel jay-form-grid">
      <label class="jay-field jay-file"
        >选择 PDF<input
          type="file"
          accept=".pdf,application/pdf"
          class="sr-only"
          aria-label="选择 PDF"
          @change="select"
        /><span class="jay-file-control" aria-hidden="true"
          ><span class="btn jay-file-choice">选择文件</span
          ><span>{{ file?.name || '未选择 PDF' }}</span></span
        ></label
      ><label class="jay-field"
        >文档密码（可选）<input
          v-model="password"
          class="field"
          type="password"
          autocomplete="off" /></label
      ><button class="btn" :disabled="!file || loading" @click="open">重新读取</button>
    </div>
    <div v-if="document" class="jay-actions">
      <button class="btn" :disabled="page <= 1 || rendering || exporting" @click="page--">
        上一页</button
      ><label class="jay-field"
        >页码<input
          v-model.number="page"
          class="field"
          type="number"
          min="1"
          :max="document.numPages"
          :disabled="exporting" /></label
      ><span>/ {{ document.numPages }}</span
      ><button
        class="btn"
        :disabled="page >= document.numPages || rendering || exporting"
        @click="page++"
      >
        下一页
      </button>
      <label class="jay-field"
        >清晰度<select v-model.number="scale" class="field" :disabled="exporting">
          <option :value="0.5">0.5 倍</option>
          <option :value="1">1 倍</option>
          <option :value="1.5">1.5 倍</option>
          <option :value="2">2 倍</option>
          <option :value="3">3 倍</option>
        </select></label
      ><label class="jay-field"
        >图片格式<select v-model="format" class="field" :disabled="exporting">
          <option value="png">PNG</option>
          <option value="jpeg">JPEG</option>
        </select></label
      >
    </div>
    <p v-if="loading || rendering || progress" role="status" class="jay-note">
      {{ loading ? '正在读取 PDF…' : rendering ? '正在生成预览…' : progress }}
    </p>
    <p v-if="error" role="alert" class="jay-error">{{ error }}</p>
    <Transition name="jay-panel" mode="out-in"
      ><figure v-if="image" :key="image" class="jay-pdf-preview">
        <img :src="image" :alt="`PDF 第 ${page} 页`" />
        <figcaption>{{ file?.name }} · 第 {{ page }} 页</figcaption>
      </figure></Transition
    >
    <div v-if="document" class="jay-actions">
      <button
        class="btn btn--prominent"
        :disabled="!currentBlob || rendering || exporting"
        @click="saveBlob(currentBlob, outputName(page))"
      >
        下载当前页</button
      ><button class="btn" :disabled="rendering || exporting" @click="saveAll">打包全部页面</button
      ><button v-if="exporting" class="btn" @click="cancelExport">取消打包</button>
    </div>
    <p class="jay-note">
      文件最多 30 MB，单页最多 1600 万像素；打包最多 100 页、64
      MB。文件和密码只用于当前页面，切换工具后清空。
    </p>
  </ToolPage>
</template>
