<template>
  <ToolPage fill>
    <template #options>
      <Segmented
        v-model="width"
        label="预览宽度"
        :options="[
          { value: 'phone', label: '手机' },
          { value: 'tablet', label: '平板' },
          { value: 'full', label: '自适应' },
        ]"
      />
      <Toggle v-model="allowScripts" label="运行脚本" />
      <button class="btn btn--sm" type="button" @click="editor.openFile()">
        <AppIcon name="docOpen" :size="16" />打开 HTML 文件…
      </button>
      <span v-if="fileName" class="badge" :title="fileName"
        ><AppIcon name="docText" :size="14" />{{ fileName }}</span
      >
    </template>

    <div class="split">
      <CodePane
        ref="editor"
        v-model="html"
        label="HTML"
        :sample="sample"
        accept=".html,.htm,text/html,text/plain"
        placeholder="<h1>Hello</h1> — or drop an .html file here"
        @file="(f) => (fileName = f.name)"
      />
      <Teleport to="body" :disabled="!previewMax"
        ><div class="freemium-workbench pane-portal">
          <section
            :role="previewMax ? 'dialog' : undefined"
            :aria-modal="previewMax || undefined"
            ref="previewEl"
            class="card preview"
            :class="{ 'preview--max': previewMax }"
            aria-labelledby="preview-title"
            @keydown.esc="previewMax = false"
          >
            <header class="preview__bar">
              <h2 id="preview-title" class="t-subhead t-semibold">预览</h2>
              <span class="badge" :class="allowScripts ? '' : 'badge--ok'">
                <AppIcon :name="allowScripts ? 'play' : 'shield'" :size="14" />
                {{ allowScripts ? '已隔离，脚本开启' : '已隔离，脚本关闭' }}
              </span>
              <span class="preview__size t-caption t-secondary">{{ widthLabel }}</span>
              <button
                class="icon-btn icon-btn--sm"
                type="button"
                :aria-label="previewMax ? '退出全屏编辑' : '展开预览'"
                :title="previewMax ? '退出全屏编辑（Esc）' : '全屏编辑'"
                @click="previewMax = !previewMax"
              >
                <AppIcon :name="previewMax ? 'collapse' : 'expand'" :size="16" />
              </button>
              <button
                class="icon-btn icon-btn--sm"
                type="button"
                aria-label="全屏查看预览"
                title="全屏"
                @click="enterFullscreen"
              >
                <AppIcon name="fullscreen" :size="16" />
              </button>
            </header>
            <div class="preview__stage">
              <iframe
                :key="allowScripts ? 'js' : 'nojs'"
                class="preview__frame"
                :style="{ width: frameWidth }"
                :sandbox="allowScripts ? 'allow-scripts' : ''"
                :srcdoc="srcdoc"
                title="HTML 渲染预览"
                referrerpolicy="no-referrer"
              />
            </div>
          </section></div
      ></Teleport>
    </div>
  </ToolPage>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ToolPage from '../../components/ToolPage.vue'
import { useToolModal } from '../../composables/useToolModal'
import CodePane from '../../components/CodePane.vue'
import AppIcon from '../../components/AppIcon.vue'
import Segmented from '../../components/ui/Segmented.vue'
import Toggle from '../../components/ui/Toggle.vue'
import { takeHandoff } from '../../composables/useHandoff'
import { load, save } from '../../composables/storage'

const sample = `<!doctype html>
<html>
<head>
  <style>
    body { font-family: system-ui, sans-serif; margin: 32px; color: #1d1d1f; }
    .card { padding: 20px; border-radius: 16px; background: #f2f2f7; }
    button { padding: 8px 16px; border: 0; border-radius: 999px; background: #0088ff; color: #fff; font-weight: 600; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Hello, Freemium</h1>
    <p>This preview runs in a sandboxed frame.</p>
    <button onclick="this.textContent = 'Scripts are on'">Click me</button>
  </div>
</body>
</html>`

const html = ref(sessionGet() || '')
const debounced = ref(html.value)
const width = ref(load('freemium:htmlpreview:width', 'full'))
// Scripts are opt-in and always run with an opaque origin. Network requests are blocked.
const allowScripts = ref(load('freemium:htmlpreview:scripts', false))
watch(allowScripts, (v) => save('freemium:htmlpreview:scripts', v))
const editor = ref(null)
const previewEl = ref(null)
const previewMax = ref(false)
useToolModal(previewMax, previewEl)
const fileName = ref('')

// True full screen for the rendered page; falls back to the in-app full-window view
// where the Fullscreen API isn't available (e.g. iPhone Safari).
function enterFullscreen() {
  const el = previewEl.value
  if (el?.requestFullscreen)
    el.requestFullscreen().catch(() => {
      previewMax.value = true
    })
  else if (el?.webkitRequestFullscreen) el.webkitRequestFullscreen()
  else previewMax.value = true
}

function sessionGet() {
  try {
    return null
  } catch {
    return null
  }
}

let t = null
watch(html, (v) => {
  clearTimeout(t)
  t = setTimeout(() => {
    debounced.value = v
  }, 200)
  try {
    void 0
  } catch {
    /* ignore */
  }
})
watch(width, (v) => save('freemium:htmlpreview:width', v))

// With scripts off the sandbox would block them anyway; dropping them avoids console noise.
const previewHtml = computed(() =>
  allowScripts.value
    ? debounced.value
    : debounced.value
        .replace(/<script\b[\s\S]*?<\/script\s*>/gi, '')
        .replace(/\son[a-z]+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, ''),
)

// Place CSP before user markup; user-supplied policies cannot loosen it.
const srcdoc = computed(
  () =>
    `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; media-src data: blob:; connect-src 'none'; form-action 'none'; base-uri 'none'">${previewHtml.value}`,
)
onBeforeUnmount(() => clearTimeout(t))

const frameWidth = computed(() => ({ phone: '390px', tablet: '820px', full: '100%' })[width.value])
const widthLabel = computed(
  () => ({ phone: '390 px', tablet: '820 px', full: '自适应' })[width.value],
)

onMounted(() => {
  const handed = takeHandoff()
  if (handed != null) {
    html.value = handed
    debounced.value = handed
  }
})
</script>

<style scoped>
.preview {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 360px;
  overflow: hidden;
}
.preview__bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px 8px;
}
.preview__size {
  margin-left: auto;
}
.preview--max {
  position: fixed;
  z-index: 1100;
  inset: calc(env(safe-area-inset-top) + var(--inset))
    calc(env(safe-area-inset-right) + var(--inset)) calc(env(safe-area-inset-bottom) + var(--inset))
    calc(env(safe-area-inset-left) + var(--inset));
  border-radius: var(--radius-window);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
}
.preview:fullscreen {
  border-radius: 0;
  background: var(--bg-2);
}
.preview:fullscreen .preview__stage {
  margin: 0;
  border-radius: 0;
}
.preview:fullscreen .preview__frame {
  border-radius: 0;
}
.preview__stage {
  flex: 1;
  min-height: 0;
  display: flex;
  justify-content: center;
  overflow: auto;
  margin: 0 8px 8px;
  border-radius: var(--radius-field);
  background: var(--bg-3);
}
.preview__frame {
  flex: none;
  max-width: none;
  height: 100%;
  min-height: 320px;
  border: 0;
  background: #fff;
  border-radius: var(--radius-field);
  transition: width var(--dur) var(--ease);
}
</style>
