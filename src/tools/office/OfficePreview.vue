<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { Maximize, Minimize } from 'lucide-vue-next'
import { useTheme } from '../../composables/useTheme'
import { OfficeViewer } from './office-viewer.mjs'

const props = defineProps<{ name: string; bytes: Uint8Array }>()
const { light } = useTheme()
const box = ref<HTMLElement>()
const container = ref<HTMLElement>()
const fullButton = ref<HTMLButtonElement>()
const status = ref('正在加载 Office 预览…')
const error = ref('')
const ready = ref(false)
const fullscreen = ref(false)
const sourceHref = ref('')
let viewer: OfficeViewer | undefined
let timer: ReturnType<typeof setTimeout> | undefined
let generation = 0

function viewerUrl() {
  const configured = import.meta.env.VITE_OFFICE_VIEWER_ORIGIN as string | undefined
  const origin = new URL(configured || 'https://homepage-r2n.pages.dev')
  if (!configured && ['127.0.0.1', 'localhost'].includes(location.hostname)) {
    origin.protocol = location.protocol
    origin.hostname = location.hostname === 'localhost' ? '127.0.0.1' : 'localhost'
    origin.port = location.port
  }
  if (!configured && origin.origin === location.origin) origin.href = 'https://zxabinbina.cc.cd'
  if (origin.origin === location.origin) throw new Error('预览来源需要与主页使用不同地址。')
  if (origin.protocol !== 'https:' && !['127.0.0.1', 'localhost'].includes(origin.hostname))
    throw new Error('预览来源需要使用 HTTPS。')
  return new URL('/office-viewer/v0.2.0/index.html', origin).href
}
function dispose() {
  ++generation
  clearTimeout(timer)
  timer = undefined
  viewer?.destroy()
  viewer = undefined
}
async function open() {
  dispose()
  if (!container.value) return
  const version = generation
  const current = () => version === generation
  ready.value = false
  error.value = ''
  status.value = '正在加载 Office 预览…'
  try {
    const url = viewerUrl()
    sourceHref.value = new URL('source/index.html', url).href
    const active = new OfficeViewer(container.value, {
      url,
      title: `${props.name} · Office 文件预览`,
      timeoutMs: 90000,
      params: { x2t: 'prebuilt', theme: light.value ? 'light' : 'dark' },
    })
    viewer = active
    timer = setTimeout(() => {
      if (!current()) return
      dispose()
      error.value = '预览加载超时，请重试。下载的文件仍可正常打开。'
    }, 180000)
    active.on('phase', (data) => {
      if (!current()) return
      status.value = data.phase === 'converting' ? '正在打开办公文件…' : '正在加载文档画面…'
    })
    active.on('editorError', () => {
      if (!current()) return
      dispose()
      ready.value = false
      error.value = 'Office 预览未能打开，请重试或下载文件查看。'
    })
    await active.ready
    if (!current()) return
    await active.open({ name: props.name, data: props.bytes, mode: 'desktop', timeoutMs: 150000 })
    if (!current()) return
    await active.call('theme', { light: light.value })
    clearTimeout(timer)
    timer = undefined
    ready.value = true
  } catch {
    if (!current()) return
    dispose()
    error.value = 'Office 预览未能打开，请重试或下载文件查看。'
  }
}
async function toggleFullscreen() {
  try {
    if (ready.value) error.value = ''
    if (document.fullscreenElement === box.value) await document.exitFullscreen()
    else await box.value?.requestFullscreen()
  } catch {
    error.value = '浏览器暂不支持全屏，可直接在预览区域查看。'
  }
}
function updateFullscreen() {
  const wasFull = fullscreen.value
  fullscreen.value = document.fullscreenElement === box.value
  if (wasFull && !fullscreen.value) fullButton.value?.focus({ preventScroll: true })
}
document.addEventListener('fullscreenchange', updateFullscreen)
watch([container, () => props.bytes, () => props.name], () => void open(), { flush: 'post' })
watch(light, () => {
  if (viewer && ready.value) void viewer.call('theme', { light: light.value }).catch(() => {})
})
onBeforeUnmount(() => {
  dispose()
  document.removeEventListener('fullscreenchange', updateFullscreen)
})
</script>

<template>
  <div ref="box" class="office-preview" :data-ready="ready">
    <div class="office-preview-toolbar">
      <span class="jay-note">{{ name }}</span>
      <button
        ref="fullButton"
        class="btn"
        type="button"
        :aria-pressed="fullscreen"
        @click="toggleFullscreen"
      >
        <Minimize v-if="fullscreen" :size="16" aria-hidden="true" />
        <Maximize v-else :size="16" aria-hidden="true" />
        {{ fullscreen ? '退出全屏' : '全屏预览' }}
      </button>
    </div>
    <div class="office-preview-stage" :aria-busy="!ready && !error">
      <div ref="container" class="office-preview-frame" :class="{ 'is-loading': !ready }"></div>
      <div v-if="!ready" class="office-preview-status">
        <template v-if="error">
          <p class="jay-error" role="alert">{{ error }}</p>
          <button class="btn" type="button" @click="open">重新加载预览</button>
        </template>
        <p v-else role="status" aria-live="polite">{{ status }}</p>
      </div>
    </div>
    <p v-if="error && ready" class="jay-error" role="alert">{{ error }}</p>
    <p class="jay-note office-preview-mobile-note">可在预览内横向滚动，也可以全屏查看。</p>
    <p class="jay-note office-preview-source">
      ONLYOFFICE · 只读预览
      <a href="https://github.com/unestgroup/office-wasm-viewer" target="_blank" rel="noopener"
        >GitHub 项目</a
      >
      <a :href="sourceHref || undefined" target="_blank" rel="noopener">源码与许可</a>
    </p>
  </div>
</template>
