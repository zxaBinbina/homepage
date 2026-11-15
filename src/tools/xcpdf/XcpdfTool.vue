<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RotateCcw, ExternalLink } from 'lucide-vue-next'
import { xcpdfToolCatalog, type XcpdfToolId } from './catalog'

const props = defineProps<{ toolId: XcpdfToolId }>()
const frame = ref<HTMLIFrameElement>()
const ready = ref(false)
const error = ref('')
const height = ref(640)
const generation = ref(0)
let observer: MutationObserver | undefined
let animation = 0
let timeout: ReturnType<typeof setTimeout> | undefined
let frameLoaded = false
const themeKeys = {
  '--bg': '--bg',
  '--card-bg': '--panel',
  '--primary': '--blue',
  '--action-bg': '--primary-action',
  '--primary-hover': '--primary-action-hover',
  '--text': '--text',
  '--text-secondary': '--muted',
  '--border': '--border',
  '--danger': '--status-danger',
  '--action-text': '--primary-action-text',
  '--success': '--status-success',
  '--panel-hover': '--panel-hover',
  '--shadow-color': '--shadow',
  '--scrollbar-thumb': '--scrollbar-thumb',
  '--scrollbar-thumb-hover': '--scrollbar-thumb-hover',
  '--scrollbar-track': '--scrollbar-track',
  '--selection-bg': '--selection-bg',
} as const

function sendTheme() {
  if (!frameLoaded) return
  const style = getComputedStyle(document.documentElement)
  const tokens = Object.fromEntries(
    Object.entries(themeKeys).map(([key, value]) => [key, style.getPropertyValue(value).trim()]),
  )
  tokens['--preview-h'] = `${Math.max(320, Math.min(620, window.innerHeight - 340))}px`
  frame.value?.contentWindow?.postMessage(
    {
      type: 'xcpdf:init',
      panel: xcpdfToolCatalog[props.toolId].panel,
      generation: generation.value,
      tokens,
      theme: document.documentElement.dataset.theme,
    },
    '*',
  )
}
function scheduleTheme() {
  cancelAnimationFrame(animation)
  animation = requestAnimationFrame(sendTheme)
}
function loaded() {
  frameLoaded = true
  sendTheme()
  timeout = setTimeout(() => {
    if (!ready.value) error.value = 'PDF 工具暂时未能初始化，请重新开始。'
  }, 20000)
}
async function receive(event: MessageEvent) {
  if (
    event.source !== frame.value?.contentWindow ||
    event.origin !== 'null' ||
    event.data?.generation !== generation.value
  )
    return
  if (event.data.type === 'xcpdf:ready') {
    ready.value = true
    clearTimeout(timeout)
  } else if (event.data.type === 'xcpdf:height' && Number.isFinite(event.data.height)) {
    height.value = Math.max(240, Math.min(30000, event.data.height))
  } else if (event.data.type === 'xcpdf:copy' && typeof event.data.text === 'string') {
    let success = false
    try {
      await navigator.clipboard.writeText(event.data.text)
      success = true
    } catch {
      /* Feedback belongs to the originating control. */
    }
    ;(event.source as Window).postMessage(
      {
        type: 'xcpdf:copied',
        request: event.data.request,
        generation: event.data.generation,
        success,
      },
      '*',
    )
  } else if (event.data.type === 'xcpdf:error') {
    error.value = String(event.data.message || '处理失败，请重新开始。').slice(0, 300)
  }
}
async function reset() {
  frameLoaded = false
  ready.value = false
  error.value = ''
  clearTimeout(timeout)
  ++generation.value
  await nextTick()
}
watch(() => props.toolId, reset)
onMounted(() => {
  window.addEventListener('message', receive)
  window.addEventListener('resize', scheduleTheme)
  observer = new MutationObserver(scheduleTheme)
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme', 'data-palette', 'style', 'class'],
  })
})
onBeforeUnmount(() => {
  observer?.disconnect()
  cancelAnimationFrame(animation)
  clearTimeout(timeout)
  window.removeEventListener('message', receive)
  window.removeEventListener('resize', scheduleTheme)
  // Removing the sandbox discards files, results, pending tasks and worker contexts.
  if (frame.value) frame.value.src = 'about:blank'
})
</script>

<template>
  <section class="tool-page xcpdf-tool">
    <p v-if="error" class="xcpdf-error" role="alert">{{ error }}</p>
    <div class="xcpdf-frame-wrap" :aria-busy="!ready">
      <p v-if="!ready && !error" class="xcpdf-wait" role="status">正在准备 PDF 工具…</p>
      <iframe
        :key="`${toolId}-${generation}`"
        ref="frame"
        src="/tool-assets/xcpdf/runtime.html"
        :title="`${xcpdfToolCatalog[toolId].name}操作区`"
        sandbox="allow-scripts allow-downloads allow-modals"
        referrerpolicy="same-origin"
        :style="{ height: `${height}px`, visibility: ready ? 'visible' : 'hidden' }"
        @load="loaded"
      />
    </div>
    <div class="xcpdf-footer">
      <button class="xcpdf-reset" type="button" @click="reset">
        <RotateCcw :size="14" aria-hidden="true" />取消并清空
      </button>
      <p class="xcpdf-credit">
        源自
        <a
          href="https://github.com/wallechfox/offline-pdf-tools/tree/98424086829730f3dd7313a8871bbbbb49e80cd8"
          target="_blank"
          rel="noopener noreferrer"
          >相声的技术备忘录 · XCPDF <ExternalLink :size="12" aria-hidden="true"
        /></a>
        · <a href="/licenses/xcpdf.txt" target="_blank" rel="noopener noreferrer">MIT 开源许可</a> ·
        <a href="/licenses/xcpdf-dependencies.txt" target="_blank" rel="noopener noreferrer"
          >第三方声明</a
        >
      </p>
    </div>
  </section>
</template>
