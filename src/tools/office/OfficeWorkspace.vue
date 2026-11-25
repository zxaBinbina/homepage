<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { Maximize, Minimize } from 'lucide-vue-next'
import { useTheme } from '../../composables/useTheme'
import { OfficeViewer } from './office-viewer.mjs'

const props = defineProps<{ name: string; bytes: Uint8Array; editable?: boolean }>()
const emit = defineEmits<{
  ready: [value: boolean]
  modified: [value: boolean]
  saveRequested: []
  saving: [value: boolean]
  warning: [message: string]
}>()
const saving = ref(false)
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
const resizeObserver = new ResizeObserver(() => {
  if (viewer && ready.value) void viewer.call('resize').catch(() => {})
})

function viewerUrl() {
  const configured = import.meta.env.VITE_OFFICE_VIEWER_ORIGIN as string | undefined
  const origin = new URL(configured || 'https://homepage.zxabinbina.workers.dev')
  if (!configured && ['127.0.0.1', 'localhost'].includes(location.hostname)) {
    origin.protocol = location.protocol
    origin.hostname = location.hostname === 'localhost' ? '127.0.0.1' : 'localhost'
    origin.port = location.port
  }
  if (!configured && origin.origin === location.origin) origin.href = 'https://zxabinbina.cc.cd'
  if (origin.origin === location.origin) throw new Error('预览来源需要与主页使用不同地址。')
  if (origin.protocol !== 'https:' && !['127.0.0.1', 'localhost'].includes(origin.hostname))
    throw new Error('预览来源需要使用 HTTPS。')
  return new URL('/office-viewer/v0.2.0/', origin).href
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
  emit('ready', false)
  error.value = ''
  status.value = '正在加载 Office 预览…'
  try {
    const url = viewerUrl()
    sourceHref.value = new URL('source/index.html', url).href
    const active = new OfficeViewer(container.value, {
      url,
      title: `${props.name} · Office ${props.editable ? '文档编辑' : '文件预览'}`,
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
    active.on('modified', (data) => {
      if (current()) emit('modified', !!data.modified)
    })
    active.on('saveRequested', () => {
      if (current() && ready.value && !saving.value) emit('saveRequested')
    })
    active.on('editorWarning', () => {
      if (current() && props.editable) emit('warning', '这项操作未能完成，可继续编辑并下载文档。')
    })
    active.on('editorError', () => {
      if (!current()) return
      if (props.editable && ready.value) {
        emit('warning', '这项操作未能完成，可继续编辑并下载文档。')
        return
      }
      dispose()
      ready.value = false
      emit('ready', false)
      error.value = 'Office 预览未能打开，请重试或下载文件查看。'
    })
    await active.ready
    if (!current()) return
    await active.open({
      name: props.name,
      data: props.bytes,
      mode: props.editable ? 'edit' : 'desktop',
      timeoutMs: 150000,
    })
    if (!current()) return
    await active.call('theme', { light: light.value })
    clearTimeout(timer)
    timer = undefined
    ready.value = true
    emit('ready', true)
    await nextTick()
    if (current()) void active.call('resize').catch(() => {})
  } catch {
    if (!current()) return
    dispose()
    error.value = 'Office 预览未能打开，请重试或下载文件查看。'
  }
}
async function save() {
  const active = viewer
  if (!props.editable || !ready.value || !active || saving.value)
    throw new Error('编辑器尚未就绪。')
  const version = generation
  saving.value = true
  emit('saving', true)
  let timeout: ReturnType<typeof setTimeout> | undefined
  try {
    const result = await Promise.race([
      active.save(),
      new Promise<never>((_, reject) => {
        timeout = setTimeout(() => reject(new Error('下载生成超时，请重试。')), 120000)
      }),
    ])
    if (version !== generation) throw new Error('文档已关闭。')
    return result
  } finally {
    clearTimeout(timeout)
    saving.value = false
    emit('saving', false)
  }
}
defineExpose({ save })
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
watch(
  container,
  (next, previous) => {
    if (previous) resizeObserver.unobserve(previous)
    if (next) resizeObserver.observe(next)
  },
  { flush: 'post' },
)
watch([container, () => props.bytes, () => props.name, () => props.editable], () => void open(), {
  flush: 'post',
})
watch(light, () => {
  if (viewer && ready.value) void viewer.call('theme', { light: light.value }).catch(() => {})
})
onBeforeUnmount(() => {
  resizeObserver.disconnect()
  dispose()
  document.removeEventListener('fullscreenchange', updateFullscreen)
})
</script>

<template>
  <div
    ref="box"
    class="office-preview"
    :class="{ 'office-editor-workspace': editable }"
    :data-ready="ready"
    :data-editable="!!editable"
  >
    <div class="office-preview-toolbar">
      <span class="jay-note">{{ name }}</span>
      <slot name="actions" />
      <button
        ref="fullButton"
        class="btn"
        type="button"
        :aria-pressed="fullscreen"
        :disabled="saving"
        @click="toggleFullscreen"
      >
        <Minimize v-if="fullscreen" :size="16" aria-hidden="true" />
        <Maximize v-else :size="16" aria-hidden="true" />
        {{ fullscreen ? '退出全屏' : editable ? '全屏编辑' : '全屏预览' }}
      </button>
    </div>
    <div
      class="office-preview-stage"
      :aria-busy="saving || (!ready && !error)"
      tabindex="0"
      aria-label="Office 文档区域，可滚动查看"
    >
      <div
        ref="container"
        class="office-preview-frame"
        :class="{ 'is-loading': !ready }"
        :inert="saving"
      ></div>
      <div v-if="!ready" class="office-preview-status">
        <template v-if="error">
          <p class="jay-error" role="alert">{{ error }}</p>
          <button class="btn" type="button" @click="open">重新加载预览</button>
        </template>
        <p v-else role="status" aria-live="polite">{{ status }}</p>
      </div>
    </div>
    <p v-if="saving" class="jay-note" role="status">正在生成编辑后的文件…</p>
    <p v-if="error && ready" class="jay-error" role="alert">{{ error }}</p>
    <p class="jay-note office-preview-mobile-note">可在预览内横向滚动，也可以全屏查看。</p>
    <p class="jay-note office-preview-source">
      ONLYOFFICE · {{ editable ? '文档编辑' : '只读预览' }}
      <a href="https://github.com/unestgroup/office-wasm-viewer" target="_blank" rel="noopener"
        >GitHub 项目</a
      >
      <a :href="sourceHref || undefined" target="_blank" rel="noopener">源码与许可</a>
    </p>
  </div>
</template>
