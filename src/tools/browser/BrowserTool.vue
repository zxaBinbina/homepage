<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  EyeOff,
  Globe,
  LockKeyhole,
  LogOut,
  Maximize,
  Monitor,
  RotateCw,
  Smartphone,
  RectangleHorizontal,
} from 'lucide-vue-next'

const apiOrigin = import.meta.env.VITE_BIN_API_ORIGIN || 'https://api.zxabinbina.cc.cd'
const browseOrigin = import.meta.env.VITE_BIN_BROWSE_ORIGIN || 'https://browse.zxabinbina.cc.cd'
const initialAddress = 'https://www.bing.com/search?bin_view=lite'
const supported =
  /Windows NT|Linux/.test(navigator.userAgent) &&
  /Chrome\/|Chromium\/|Edg\//.test(navigator.userAgent) &&
  !/Android|Mobile|iPhone|iPad|iPod/i.test(navigator.userAgent)
const password = ref(''),
  showPassword = ref(false),
  busy = ref(false),
  token = ref('')
const error = ref(''),
  ready = ref(false),
  loading = ref(false),
  initSent = ref(false)
const attempt = ref(''),
  bridgeUrl = ref(''),
  bridgeVisible = ref(false),
  startupStage = ref('正在准备浏览环境…')
const address = ref(initialAddress),
  addressDirty = ref(false),
  current = ref(''),
  expiresAt = ref(0),
  now = ref(Date.now())
const trail = ref<string[]>([]),
  position = ref(-1)
const bridge = ref<HTMLIFrameElement>(),
  workbench = ref<HTMLElement>(),
  viewport = ref<HTMLElement>()
const area = ref({ width: 1000, height: 640 }),
  simulation = ref(false)
const device = ref('desktop'),
  width = ref(1280),
  height = ref(720),
  zoom = ref('auto'),
  identity = ref('actual')
let clock: ReturnType<typeof setInterval> | undefined,
  loadTimer: ReturnType<typeof setTimeout> | undefined,
  startupTimer: ReturnType<typeof setTimeout> | undefined
let resize: ResizeObserver | undefined, themeObserver: MutationObserver | undefined
let finishLogout: ((cleared: boolean) => void) | undefined,
  loggingOut = false
let lifecycle = 0
const presets = [
  { id: 'desktop', name: '桌面 · 1280 × 720', width: 1280, height: 720, ua: 'actual' },
  { id: 'fullhd', name: '桌面 · 1920 × 1080', width: 1920, height: 1080, ua: 'actual' },
  { id: 'iphone', name: 'iPhone · 390 × 844', width: 390, height: 844, ua: 'iphone' },
  { id: 'android', name: 'Android · 412 × 915', width: 412, height: 915, ua: 'android' },
  { id: 'tablet', name: 'iPad · 820 × 1180', width: 820, height: 1180, ua: 'ipad' },
]
const userAgents: Record<string, string> = {
  actual: '',
  windows:
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
  linux:
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
  android:
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
  iphone:
    'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1',
  ipad: 'Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1',
}
const frameWidth = computed(() =>
  simulation.value ? width.value : Math.max(240, area.value.width),
)
const frameHeight = computed(() =>
  simulation.value ? height.value : Math.max(240, area.value.height),
)
const scale = computed(() =>
  !simulation.value
    ? 1
    : zoom.value === 'auto'
      ? Math.min(1, area.value.width / frameWidth.value, area.value.height / frameHeight.value)
      : Number(zoom.value),
)
const minutes = computed(() => Math.max(0, Math.ceil((expiresAt.value - now.value) / 60000)))
const shortcuts = [
  { name: 'Bing 搜索', url: 'https://cn.bing.com/' },
  { name: 'Bing 简洁搜索', url: 'https://www.bing.com/search?bin_view=lite' },
  { name: '云·原神', url: 'https://ys.mihoyo.com/cloud/' },
  { name: '抖音精选', url: 'https://www.douyin.com/jingxuan' },
]
function send(type: string, data: Record<string, unknown> = {}) {
  bridge.value?.contentWindow?.postMessage(
    { channel: 'bin-browser', type, attempt: attempt.value, ...data },
    browseOrigin,
  )
}
function theme() {
  send('theme', {
    theme: document.documentElement.dataset.theme || 'dark',
    background: getComputedStyle(document.documentElement).getPropertyValue('--bg').trim(),
  })
}
function initialize() {
  if (initSent.value || !token.value) return
  initSent.value = true
  send('init', {
    token: token.value,
    expiresAt: expiresAt.value,
    ua: simulation.value ? userAgents[identity.value] : '',
  })
  theme()
}
function rebuildEnvironment() {
  if (!token.value || loggingOut) return
  clearTimeout(startupTimer)
  clearTimeout(loadTimer)
  ready.value = false
  initSent.value = false
  error.value = ''
  loading.value = false
  current.value = ''
  address.value = initialAddress
  addressDirty.value = false
  trail.value = []
  position.value = -1
  startupStage.value = '正在清理上次会话…'
  attempt.value = crypto.randomUUID()
  bridgeUrl.value = `${browseOrigin}/reset?attempt=${attempt.value}`
  bridgeVisible.value = true
  startupTimer = setTimeout(() => {
    if (ready.value) return
    error.value = `${startupStage.value.replace(/…$/, '')}超时。请点击“清理并重建”；若仍失败，请关闭其他浏览器工具标签页后重试。`
    startupStage.value = '浏览环境启动失败'
    bridgeVisible.value = false
  }, 50000)
}
async function login() {
  if (busy.value || !password.value) return
  busy.value = true
  error.value = ''
  const generation = lifecycle
  try {
    const response = await fetch(`${apiOrigin}/v1/auth/login`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ password: password.value }),
      credentials: 'omit',
      signal: AbortSignal.timeout(20000),
    })
    const result = await response.json()
    if (generation !== lifecycle) return
    if (!response.ok) throw new Error(result.error || '暂时无法进入，请稍后重试。')
    password.value = ''
    showPassword.value = false
    token.value = result.token
    expiresAt.value = result.expiresAt
    now.value = Date.now()
    rebuildEnvironment()
    await nextTick()
    observeViewport()
  } catch (cause) {
    if (generation !== lifecycle) return
    error.value =
      cause instanceof Error && cause.name !== 'TimeoutError'
        ? cause.message
        : '连接超时，请检查网络后重试。'
  } finally {
    busy.value = false
  }
}
function normalize(value: string) {
  const text = value.trim()
  if (!text) throw new Error('请输入网址。')
  const url = new URL(/^[a-z][a-z\d+.-]*:/i.test(text) ? text : `https://${text}`)
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password)
    throw new Error('请输入不含账号密码的 HTTP 或 HTTPS 网址。')
  return url.href
}
function go(value = address.value) {
  if (!ready.value) return
  try {
    const url = normalize(value)
    address.value = url
    addressDirty.value = false
    error.value = ''
    markLoading()
    send('go', { url })
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '网址不正确。'
  }
}
function markLoading() {
  loading.value = true
  clearTimeout(loadTimer)
  loadTimer = setTimeout(() => {
    if (loading.value) error.value = '目标网页加载较久，可以稍等片刻，或刷新后再试。'
  }, 35000)
}
function move(step: number) {
  const next = position.value + step
  if (next < 0 || next >= trail.value.length) return
  position.value = next
  go(trail.value[next])
}
function reload() {
  error.value = ''
  markLoading()
  send('reload')
}
async function logout(message = '') {
  if (loggingOut) return
  loggingOut = true
  const cleared = await new Promise<boolean>((resolve) => {
    finishLogout = resolve
    send('stop')
    clearTimeout(loadTimer)
    ready.value = false
    setTimeout(() => resolve(false), 6000)
  })
  finishLogout = undefined
  forgetSession()
  error.value = message
  if (!cleared) error.value = '会话已结束。浏览环境未确认清理完成，下次进入前会再次清理。'
  loggingOut = false
  resize?.disconnect()
}
function forgetSession() {
  lifecycle++
  token.value = ''
  password.value = ''
  showPassword.value = false
  current.value = ''
  address.value = initialAddress
  addressDirty.value = false
  trail.value = []
  position.value = -1
  expiresAt.value = 0
  bridgeVisible.value = false
  ready.value = false
  initSent.value = false
  loading.value = false
  clearTimeout(loadTimer)
  clearTimeout(startupTimer)
}
function leavePage() {
  if (token.value) {
    send('stop')
    navigator.sendBeacon(`${browseOrigin}/clear`, '')
  }
  forgetSession()
}
function applyIdentity() {
  if (ready.value) send('device', { ua: simulation.value ? userAgents[identity.value] : '' })
}
function selectDevice() {
  const preset = presets.find((item) => item.id === device.value)
  if (preset) {
    width.value = preset.width
    height.value = preset.height
    identity.value = preset.ua
    applyIdentity()
  }
}
function clampSize() {
  width.value = Math.min(3840, Math.max(240, Math.round(Number(width.value) || 1280)))
  height.value = Math.min(2160, Math.max(240, Math.round(Number(height.value) || 720)))
  device.value = 'custom'
}
function rotate() {
  ;[width.value, height.value] = [height.value, width.value]
  clampSize()
}
function toggleSimulation() {
  simulation.value = !simulation.value
  applyIdentity()
}
async function fullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen()
    else await workbench.value?.requestFullscreen()
  } catch {
    error.value = '浏览器未允许全屏，请检查权限后重试。'
  }
}
function observeViewport() {
  resize?.disconnect()
  if (viewport.value) {
    resize = new ResizeObserver((entries) => {
      const box = entries[0]?.contentRect
      if (box) area.value = { width: Math.floor(box.width), height: Math.floor(box.height) }
    })
    resize.observe(viewport.value)
  }
}
function receive(event: MessageEvent) {
  if (
    event.origin !== browseOrigin ||
    event.source !== bridge.value?.contentWindow ||
    event.data?.channel !== 'bin-browser' ||
    event.data.attempt !== attempt.value
  )
    return
  const data = event.data
  if (data.type === 'reset-done') {
    startupStage.value = '正在加载浏览环境…'
    bridgeUrl.value = `${browseOrigin}/?attempt=${attempt.value}`
  }
  if (data.type === 'stage' && !ready.value && typeof data.message === 'string')
    startupStage.value = data.message
  if (data.type === 'stopped') finishLogout?.(data.cleared === true)
  if (data.type === 'boot') initialize()
  if (data.type === 'ready') {
    ready.value = true
    clearTimeout(startupTimer)
    clearTimeout(loadTimer)
    error.value = ''
    go()
  }
  if (data.type === 'loading') markLoading()
  if (data.type === 'loaded') {
    loading.value = false
    clearTimeout(loadTimer)
  }
  if (data.type === 'error') {
    error.value = data.message || '网页加载失败。'
    loading.value = false
    clearTimeout(loadTimer)
    if (data.fatal) {
      clearTimeout(startupTimer)
      ready.value = false
      bridgeVisible.value = false
      startupStage.value = '浏览环境启动失败'
    }
  }
  if (data.type === 'expired') void logout('本次访问已结束，请重新输入密码。')
  if (data.type === 'url' && typeof data.url === 'string') {
    try {
      const url = normalize(data.url)
      current.value = url
      if (!addressDirty.value) address.value = url
      if (trail.value[position.value] !== url) {
        trail.value = [...trail.value.slice(0, position.value + 1), url].slice(-100)
        position.value = trail.value.length - 1
      }
    } catch {
      /* Ignore internal about:blank and malformed navigation notices. */
    }
  }
}
onMounted(() => {
  window.addEventListener('message', receive)
  window.addEventListener('pagehide', leavePage)
  themeObserver = new MutationObserver(theme)
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme', 'data-palette'],
  })
  clock = setInterval(() => {
    now.value = Date.now()
    if (token.value && now.value >= expiresAt.value) void logout('本次访问已结束，请重新输入密码。')
  }, 1000)
})
onBeforeUnmount(() => {
  leavePage()
  clearInterval(clock)
  clearTimeout(loadTimer)
  resize?.disconnect()
  themeObserver?.disconnect()
  window.removeEventListener('message', receive)
  window.removeEventListener('pagehide', leavePage)
})
</script>

<template>
  <section
    v-if="!supported"
    class="browser-unavailable"
    aria-labelledby="browser-unsupported-title"
  >
    <Monitor :size="40" aria-hidden="true" />
    <p class="overline">DESKTOP ONLY</p>
    <h2 id="browser-unsupported-title">抱歉，暂不支持此设备</h2>
    <p>请在 Windows 10 或 Linux 电脑上，使用 Microsoft Edge 或 Google Chrome 打开此工具。</p>
    <a class="button button-primary" href="/tool">返回工具集</a>
  </section>
  <section v-else-if="!token" class="browser-login" aria-labelledby="browser-login-title">
    <div class="browser-login-copy">
      <span class="browser-lock-icon"><LockKeyhole :size="26" aria-hidden="true" /></span>
      <p class="overline">YOUR LITTLE WINDOW</p>
      <h2 id="browser-login-title">打开另一扇窗。</h2>
      <p>输入访问密码，在这里搜索、阅读和浏览网页。</p>
      <div class="browser-login-tags">
        <span>私人入口</span><span>桌面浏览</span><span>设备模拟</span>
      </div>
    </div>
    <form class="browser-login-form" @submit.prevent="login">
      <label for="browser-password">访问密码</label>
      <div class="browser-password-field">
        <input
          id="browser-password"
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="current-password"
          placeholder="请输入访问密码"
          required
          maxlength="256"
          :disabled="busy"
        />
        <button
          type="button"
          :aria-label="showPassword ? '隐藏密码' : '显示密码'"
          :aria-pressed="showPassword"
          @click="showPassword = !showPassword"
        >
          <component :is="showPassword ? EyeOff : Eye" :size="18" />
        </button>
      </div>
      <p v-if="error" class="browser-error" role="alert">{{ error }}</p>
      <button class="button button-primary" type="submit" :disabled="busy" :aria-busy="busy">
        <LockKeyhole :size="16" />{{ busy ? '正在验证…' : '进入浏览器' }}
      </button>
      <p class="browser-caption">每次访问最长一小时，密码不会保存在页面中。</p>
    </form>
  </section>
  <section v-else ref="workbench" class="browser-workbench" aria-label="网页浏览器">
    <div class="browser-topline">
      <span><Globe :size="16" />私人浏览窗口</span>
      <div>
        <span class="browser-caption">剩余 {{ minutes }} 分钟</span
        ><button
          type="button"
          class="browser-icon-button"
          aria-label="结束浏览并退出"
          title="结束浏览并退出"
          @click="logout()"
        >
          <LogOut :size="18" />
        </button>
      </div>
    </div>
    <form class="browser-addressbar" @submit.prevent="go()">
      <div class="browser-navigation">
        <button
          type="button"
          class="browser-icon-button"
          aria-label="后退"
          :disabled="!ready || position <= 0"
          @click="move(-1)"
        >
          <ArrowLeft :size="18" />
        </button>
        <button
          type="button"
          class="browser-icon-button"
          aria-label="前进"
          :disabled="!ready || position >= trail.length - 1"
          @click="move(1)"
        >
          <ArrowRight :size="18" />
        </button>
        <button
          type="button"
          class="browser-icon-button"
          aria-label="刷新网页"
          :disabled="!ready"
          @click="reload"
        >
          <RotateCw :size="18" :class="{ 'browser-spinning': loading }" />
        </button>
      </div>
      <label class="browser-url"
        ><Globe :size="16" aria-hidden="true" /><input
          v-model="address"
          @input="addressDirty = true"
          type="text"
          aria-label="目标网址"
          placeholder="输入网址，例如 cn.bing.com"
          spellcheck="false"
          autocomplete="off"
          :disabled="!ready"
      /></label>
      <button class="browser-go" type="submit" :disabled="!ready">前往</button>
      <button
        type="button"
        class="browser-icon-button"
        aria-label="切换设备模拟"
        title="设备模拟"
        :aria-pressed="simulation"
        @click="toggleSimulation"
      >
        <Smartphone :size="18" />
      </button>
      <button
        type="button"
        class="browser-icon-button"
        aria-label="切换浏览器全屏"
        title="全屏"
        @click="fullscreen"
      >
        <Maximize :size="18" />
      </button>
    </form>
    <div class="browser-shortcuts">
      <button
        v-for="site in shortcuts"
        :key="site.url"
        type="button"
        :disabled="!ready"
        @click="go(site.url)"
      >
        {{ site.name }}</button
      ><span role="status">{{ !ready ? startupStage : loading ? '正在打开网页…' : '已就绪' }}</span>
      <button
        type="button"
        class="browser-rebuild"
        title="清除本次浏览数据并重新启动，访问密码仍有效"
        @click="rebuildEnvironment"
      >
        清理并重建
      </button>
    </div>
    <div v-if="simulation" class="browser-devices" aria-label="设备模拟选项">
      <label
        >设备<select v-model="device" @change="selectDevice">
          <option v-for="preset in presets" :key="preset.id" :value="preset.id">
            {{ preset.name }}
          </option>
          <option value="custom">自定义尺寸</option>
        </select></label
      >
      <div class="browser-dimensions">
        <label
          >宽<input
            v-model.number="width"
            type="number"
            min="240"
            max="3840"
            aria-label="模拟宽度"
            @change="clampSize" /></label
        ><span>×</span
        ><label
          >高<input
            v-model.number="height"
            type="number"
            min="240"
            max="2160"
            aria-label="模拟高度"
            @change="clampSize" /></label
        ><button type="button" class="browser-icon-button" aria-label="切换横竖屏" @click="rotate">
          <RectangleHorizontal :size="18" />
        </button>
      </div>
      <label
        >缩放<select v-model="zoom">
          <option value="auto">适应窗口</option>
          <option
            v-for="value in [0.25, 0.5, 0.75, 1, 1.25, 1.5]"
            :key="value"
            :value="String(value)"
          >
            {{ value * 100 }}%
          </option>
        </select></label
      >
      <label
        >设备标识<select v-model="identity" @change="applyIdentity">
          <option value="actual">当前浏览器</option>
          <option value="windows">Windows / Chrome</option>
          <option value="linux">Linux / Chrome</option>
          <option value="android">Android / Chrome</option>
          <option value="iphone">iPhone / Safari</option>
          <option value="ipad">iPad / Safari</option>
        </select></label
      >
      <p>模拟显示尺寸和设备标识，浏览器内核及真实触摸能力不变。</p>
    </div>
    <p v-if="error" class="browser-inline-error" role="alert">{{ error }}</p>
    <div ref="viewport" class="browser-viewport" :class="{ 'is-simulating': simulation }">
      <div
        class="browser-frame-size"
        :style="{ width: `${frameWidth * scale}px`, height: `${frameHeight * scale}px` }"
      >
        <iframe
          v-if="bridgeVisible"
          :key="attempt"
          ref="bridge"
          :src="bridgeUrl"
          title="网页浏览环境"
          class="browser-frame"
          :style="{
            width: `${frameWidth}px`,
            height: `${frameHeight}px`,
            transform: `scale(${scale})`,
          }"
          allow="autoplay; fullscreen; gamepad; clipboard-read; clipboard-write"
          sandbox="allow-scripts allow-same-origin allow-forms allow-downloads allow-pointer-lock allow-presentation allow-modals"
          referrerpolicy="no-referrer"
        />
        <p v-else class="browser-stage-message">
          {{ startupStage }}，可使用上方“清理并重建”重新进入。
        </p>
      </div>
    </div>
    <div class="browser-statusbar">
      <span :title="current">{{ current || '准备打开网页' }}</span
      ><span v-if="simulation">{{ width }} × {{ height }} · {{ Math.round(scale * 100) }}%</span>
    </div>
    <p class="browser-compatibility">
      部分网站的登录、视频或云游戏可能无法使用；实时连接以实际测试结果为准。
    </p>
  </section>
</template>
