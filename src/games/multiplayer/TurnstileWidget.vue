<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { turnstileApi as api, loadTurnstile } from './turnstileClient'
const props = defineProps<{ action: 'room_create' | 'room_join' }>()
const emit = defineEmits<{ verified: [token: string] }>()
const target = ref<HTMLElement>(),
  error = ref(''),
  siteKey = ref<string | null>(null),
  loading = ref(true)
const theme = ref(document.documentElement.dataset.theme === 'light' ? 'light' : 'dark'),
  compact = ref(false)
let widget: string | undefined,
  disposed = false,
  resize: ResizeObserver | undefined,
  observer: MutationObserver | undefined,
  controller: AbortController | undefined
let generation = 0
async function render() {
  const current = ++generation
  emit('verified', '')
  if (widget) {
    api()?.remove(widget)
    widget = undefined
  }
  await nextTick()
  if (disposed || current !== generation || !target.value || !siteKey.value || !api()) return
  try {
    widget = api()!.render(target.value, {
      sitekey: siteKey.value,
      action: props.action,
      theme: theme.value,
      size: compact.value ? 'compact' : 'flexible',
      language: 'zh-CN',
      callback: (token: string) => {
        if (current === generation) {
          error.value = ''
          emit('verified', token)
        }
      },
      'expired-callback': () => {
        if (current === generation) emit('verified', '')
      },
      'error-callback': () => {
        if (current === generation) {
          emit('verified', '')
          error.value = '安全验证暂时无法加载，请重试。'
        }
      },
    })
  } catch {
    error.value = '安全验证暂时无法显示，请重试。'
  }
}
async function load() {
  loading.value = true
  error.value = ''
  controller?.abort()
  controller = new AbortController()
  try {
    const response = await fetch('/api/games/rooms/config', { signal: controller.signal })
    if (!response.ok) throw new Error('安全验证服务暂时不可用。')
    siteKey.value = ((await response.json()) as { siteKey: string | null }).siteKey
    if (!siteKey.value) throw new Error('联机验证尚未配置，请稍后再来。')
    await loadTurnstile()
    if (!disposed) await render()
  } catch (e) {
    if (!disposed && !(e instanceof DOMException && e.name === 'AbortError'))
      error.value = e instanceof Error ? e.message : '安全验证暂时不可用。'
  } finally {
    loading.value = false
  }
}
function reset() {
  emit('verified', '')
  if (widget) api()?.reset(widget)
}
defineExpose({ reset })
watch([() => props.action, theme, compact], () => {
  void render()
})
onMounted(() => {
  observer = new MutationObserver(() => {
    theme.value = document.documentElement.dataset.theme === 'light' ? 'light' : 'dark'
  })
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
  resize = new ResizeObserver(() => {
    compact.value = (target.value?.clientWidth ?? 300) < 300
  })
  if (target.value) resize.observe(target.value)
  void load()
})
onBeforeUnmount(() => {
  disposed = true
  generation++
  controller?.abort()
  observer?.disconnect()
  resize?.disconnect()
  if (widget) api()?.remove(widget)
})
</script>

<template>
  <div class="room-turnstile">
    <div ref="target" aria-label="Cloudflare 安全验证"></div>
    <p v-if="loading" class="room-help" role="status">正在加载安全验证…</p>
    <p v-if="error" class="room-feedback" role="alert">
      {{ error }} <button class="game-button" type="button" @click="load">重试验证</button>
    </p>
  </div>
</template>
