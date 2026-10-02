<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Check,
  CircleX,
  Fingerprint,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  LockKeyhole,
  Monitor,
  Pause,
  Play,
  RotateCcw,
  ShieldCheck,
} from 'lucide-vue-next'

const root = ref<HTMLElement>()
const motion = matchMedia('(prefers-reduced-motion: reduce)')
const reduced = ref(motion.matches)
const paused = ref(false)
const inView = ref(false)
const visible = ref(!document.hidden)
const methods = [
  { id: 'password', label: '固定密码' },
  { id: 'temporary', label: '临时密码' },
  { id: 'passkey', label: '通行密钥' },
] as const
type Method = (typeof methods)[number]['id']
const method = ref<Method>('password')
const failureMessage = computed(
  () =>
    ({
      password: '密码不正确，暂未放行此 IP。',
      temporary: '临时密码不正确或已使用，请确认最新密码。',
      passkey: '设备确认已取消或超时，可重试或改用密码。',
    })[method.value],
)
const outcome = ref<'success' | 'failure'>('success')
const frame = ref(reduced.value ? 24 : 0)
const manual = ref(false)
const phase = computed(() =>
  frame.value < 16 ? 'typing' : frame.value < 24 ? 'checking' : outcome.value,
)
const running = computed(() => !reduced.value && !paused.value && inView.value && visible.value)
const revealPassword = ref(false)
const samplePassword = 'Demo-only-123456!'
const sampleWords = ['钻石', '苹果', '蛋糕']
const password = computed(() =>
  (revealPassword.value ? samplePassword : '•'.repeat(16)).slice(0, Math.min(frame.value, 16)),
)
function temporaryWord(index: number) {
  const count = Math.max(0, Math.min(2, Math.floor(frame.value / 2) - index * 2))
  return (revealPassword.value ? sampleWords[index]! : '••').slice(0, count)
}
const caption = computed(
  () =>
    ({
      typing:
        method.value === 'passkey'
          ? '正在请求设备确认通行密钥'
          : method.value === 'temporary'
            ? '正在输入三个中文词组成的临时密码'
            : '正在输入访问密码',
      checking: method.value === 'passkey' ? '模拟设备确认后，验证通行密钥' : '正在验证身份',
      success: '认证成功，允许此 IPv4 建立新连接',
      failure: '认证失败，此 IPv4 仍未获得准入',
    })[phase.value],
)
let timer: ReturnType<typeof setTimeout> | undefined
let observer: IntersectionObserver | undefined
function schedule() {
  clearTimeout(timer)
  if (!running.value) return
  timer = setTimeout(() => {
    frame.value += 1
    if (frame.value >= 48) {
      frame.value = 0
      if (outcome.value === 'failure') {
        const index = methods.findIndex((item) => item.id === method.value)
        method.value = methods[(index + 1) % methods.length]!.id
      }
      outcome.value = outcome.value === 'success' ? 'failure' : 'success'
      manual.value = false
    }
    schedule()
  }, 150)
}
watch(running, schedule)
function demonstrate(result: 'success' | 'failure') {
  outcome.value = result
  manual.value = true
  frame.value = reduced.value ? 24 : 0
  paused.value = false
  schedule()
}
function selectMethod(value: Method) {
  method.value = value
  revealPassword.value = false
  demonstrate('success')
}
function onVisibility() {
  visible.value = !document.hidden
}
function onMotion() {
  reduced.value = motion.matches
  if (reduced.value) frame.value = 24
}
onMounted(() => {
  if ('IntersectionObserver' in window) {
    observer = new IntersectionObserver(
      (entries) => {
        inView.value = !!entries.at(-1)?.isIntersecting
      },
      { threshold: 0.15 },
    )
    if (root.value) observer.observe(root.value)
  } else inView.value = true
  document.addEventListener('visibilitychange', onVisibility)
  motion.addEventListener('change', onMotion)
})
onBeforeUnmount(() => {
  clearTimeout(timer)
  observer?.disconnect()
  document.removeEventListener('visibilitychange', onVisibility)
  motion.removeEventListener('change', onMotion)
})
</script>

<template>
  <section
    ref="root"
    class="auth-demo"
    :class="{ 'is-running': running }"
    aria-label="认证流程动画演示"
    :data-phase="phase"
    :data-method="method"
  >
    <div class="demo-toolbar">
      <span class="demo-dots" aria-hidden="true"><i></i><i></i><i></i></span
      ><span><LockKeyhole :size="12" /> auth.example.com</span
      ><span class="demo-badge">模拟演示</span>
    </div>
    <div class="demo-scene">
      <div class="demo-heading">
        <img class="demo-shield" src="/images/rdp-access-auth.png" alt="" width="43" height="43" />
        <div>
          <h2>验证访问身份</h2>
          <p>RDP Access Auth · 选择你习惯的认证方式</p>
        </div>
      </div>
      <div class="demo-tabs" role="group" aria-label="选择模拟认证方式">
        <button
          v-for="item in methods"
          :key="item.id"
          type="button"
          :aria-pressed="method === item.id"
          @click="selectMethod(item.id)"
        >
          {{ item.label }}
        </button>
      </div>
      <div class="demo-stage">
        <div class="demo-credential" :inert="phase === 'success' || phase === 'failure'">
          <Transition name="demo-result">
            <div v-if="phase === 'failure'" class="demo-error">
              <CircleX :size="18" />
              <div>
                <h3>认证失败</h3>
                <p>{{ failureMessage }}</p>
              </div>
            </div>
          </Transition>
          <div v-if="method !== 'passkey'" class="demo-field">
            <div v-if="method === 'temporary'" class="demo-temporary" aria-label="模拟三段临时密码">
              <span v-for="(_, index) in sampleWords" :key="index" class="demo-input"
                >{{ temporaryWord(index)
                }}<i
                  v-if="phase === 'typing' && Math.min(2, Math.floor(frame / 4)) === index"
                  class="demo-caret"
                ></i
              ></span>
              <button
                type="button"
                class="demo-eye"
                :aria-label="revealPassword ? '隐藏示例密码' : '显示示例密码'"
                @click="revealPassword = !revealPassword"
              >
                <EyeOff v-if="revealPassword" :size="16" /><Eye v-else :size="16" />
              </button>
            </div>
            <div v-else class="demo-input demo-password" aria-label="模拟输入密码">
              <KeyRound :size="15" /><span aria-hidden="true"
                >{{ password }}<i v-if="phase === 'typing'" class="demo-caret"></i></span
              ><button
                type="button"
                class="demo-eye"
                :aria-label="revealPassword ? '隐藏示例密码' : '显示示例密码'"
                @click="revealPassword = !revealPassword"
              >
                <EyeOff v-if="revealPassword" :size="16" /><Eye v-else :size="16" />
              </button>
            </div>
          </div>
          <div
            v-else
            class="demo-passkey"
            :class="{ 'is-confirming': phase === 'typing' || phase === 'checking' }"
          >
            <Fingerprint :size="32" aria-hidden="true" />
            <strong>{{
              phase === 'checking'
                ? '设备已确认，正在验证…'
                : phase === 'failure'
                  ? '设备确认未完成'
                  : '请在设备上确认'
            }}</strong>
            <p>使用指纹、面容或设备 PIN · 模拟提示</p>
          </div>
          <p v-if="method === 'temporary'" class="demo-method-note">
            每格一个词，无需横线；成功后轮换。
          </p>
          <p v-else-if="method === 'passkey'" class="demo-method-note">
            首次使用需先用密码登录并绑定通行密钥。
          </p>
        </div>
        <div class="demo-network">
          <Monitor :size="15" /><span>连接网络的 IPv4</span><code>203.0.113.42</code>
        </div>
        <div class="demo-submit" aria-hidden="true">
          <LoaderCircle v-if="phase === 'checking'" class="demo-spinner" :size="16" /><LockKeyhole
            v-else
            :size="16"
          />{{
            phase === 'checking'
              ? '验证中…'
              : method === 'passkey'
                ? '使用通行密钥连接'
                : '认证并授权'
          }}
        </div>
        <p class="demo-alternative"><ShieldCheck :size="15" /> 6 小时准入 · 仍需系统账户登录</p>
        <Transition name="demo-result">
          <div v-if="phase === 'success'" :key="phase" class="demo-result" :class="phase">
            <div class="demo-result-title">
              <span class="demo-result-icon"><Check :size="20" /></span>
              <h3>认证成功</h3>
            </div>
            <p>已授权网络：203.0.113.42</p>
            <div class="demo-result-detail">
              <ShieldCheck :size="16" /><span>6 小时内可发起新的 RDP 连接</span>
            </div>
            <div class="demo-address">desktop.example.com:3389</div>
            <div v-if="method === 'temporary'" class="demo-rotation">
              <strong>本次临时密码已作废</strong>
              <p>下一条密码（仅示例）</p>
              <code>钻石-苹果-蛋糕</code>
            </div>
            <p class="demo-result-footnote">接下来，使用系统账户登录远程桌面。</p>
          </div>
        </Transition>
      </div>
    </div>
    <div class="demo-progress" aria-hidden="true">
      <span :style="{ transform: `scaleX(${(frame + 1) / 48})` }"></span>
    </div>
    <div class="demo-controls">
      <div class="demo-scenarios" role="group" aria-label="选择演示场景">
        <button :aria-pressed="outcome === 'success'" @click="demonstrate('success')">
          成功流程</button
        ><button :aria-pressed="outcome === 'failure'" @click="demonstrate('failure')">
          失败流程
        </button>
      </div>
      <div v-if="!reduced" class="demo-playback">
        <button
          :aria-label="paused ? '播放演示' : '暂停演示'"
          :title="paused ? '播放演示' : '暂停演示'"
          @click="paused = !paused"
        >
          <Play v-if="paused" :size="16" /><Pause v-else :size="16" /></button
        ><button aria-label="重播演示" title="重播演示" @click="demonstrate(outcome)">
          <RotateCcw :size="16" />
        </button>
      </div>
    </div>
    <p class="demo-caption" :aria-live="manual ? 'polite' : 'off'" aria-atomic="true">
      {{ caption
      }}<span>{{
        reduced
          ? '已减少动态效果 · 点击切换结果'
          : paused
            ? '演示已暂停'
            : '仅作流程展示，不提交密码或发起认证'
      }}</span>
    </p>
  </section>
</template>

<style scoped>
.auth-demo {
  min-width: 0;
  border: 1px solid var(--border);
  border-radius: 24px;
  background: var(--panel);
  box-shadow: 0 24px 65px var(--shadow);
  overflow: hidden;
}
.demo-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border);
  font-size: 11px;
  color: var(--muted);
}
.demo-toolbar > span:nth-child(2) {
  display: flex;
  align-items: center;
  gap: 7px;
}
.demo-dots {
  display: flex;
  gap: 5px;
}
.demo-dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--muted);
  opacity: 0.35;
}
.demo-badge {
  padding: 3px 8px;
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 10px;
  white-space: nowrap;
}
.demo-scene {
  position: relative;
  padding: 16px 20px;
}
.demo-heading {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.demo-shield {
  width: 43px;
  height: 43px;
  object-fit: contain;
  flex-shrink: 0;
}
.demo-heading h2 {
  font-size: 18px;
  letter-spacing: -0.5px;
}
.demo-heading p {
  color: var(--muted);
  font-size: 11px;
  margin-top: 4px;
}
.demo-tabs {
  display: flex;
  gap: 4px;
  padding: 5px;
  border: 1px solid var(--border);
  border-radius: 28px;
  background: var(--bg);
  font-size: 11px;
  color: var(--muted);
}
.demo-tabs button {
  min-width: 0;
  min-height: 44px;
  color: var(--muted);
  background: transparent;
  font: inherit;
  flex: 1;
  text-align: center;
  padding: 9px 3px;
  border-radius: 22px;
}
.demo-tabs button[aria-pressed='true'] {
  background: var(--panel-hover);
  color: var(--blue);
}
.demo-stage {
  position: relative;
  min-height: 270px;
  padding-top: 1px;
}
.demo-credential {
  position: relative;
  min-height: 110px;
  padding-top: 1px;
}
.demo-passkey {
  display: grid;
  grid-template-columns: 32px 1fr;
  align-items: center;
  justify-items: center;
  gap: 4px;
  margin-top: 10px;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--bg);
  text-align: center;
  color: var(--blue);
}
.demo-passkey > svg {
  grid-row: span 2;
}
.demo-passkey strong {
  font-size: 13px;
}
.demo-passkey p,
.demo-method-note {
  font-size: 11px;
  color: var(--muted);
}
.demo-method-note {
  margin-top: 10px;
  line-height: 1.8;
}
.demo-rotation {
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 0;
  width: 100%;
  font-size: 12px;
}
.demo-rotation p {
  font-size: 11px;
  margin: 4px 0;
}
.demo-rotation code {
  color: var(--blue);
}
.demo-tabs button:hover {
  color: var(--text);
  background: var(--panel-hover);
}
.demo-network {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 9px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-top: 8px;
  color: var(--muted);
  font-size: 11px;
}
.demo-network code {
  margin-left: auto;
  color: var(--blue);
  font-size: 11px;
}
.demo-error {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: flex;
  gap: 9px;
  align-items: center;
  margin-top: 16px;
  padding: 12px;
  border: 1px solid color-mix(in srgb, var(--status-danger) 25%, transparent);
  background: var(--panel);
  border-radius: 12px;
  color: var(--status-danger);
}
.demo-error h3 {
  font-size: 13px;
  margin: 0 0 3px;
}
.demo-error p {
  font-size: 11px;
  margin: 0;
}
.demo-address {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--blue);
  background: var(--bg);
  font: 12px monospace;
  overflow-wrap: anywhere;
  max-width: 100%;
  margin-bottom: 0;
}
.demo-field {
  margin-top: 16px;
  font-size: 11px;
  color: var(--muted);
}
.demo-input {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 43px;
  padding: 0 13px;
  border: 1px solid var(--border);
  background: var(--bg);
  border-radius: 9px;
  margin-top: 6px;
  color: var(--text);
  font: 13px monospace;
}
.demo-temporary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) 36px;
  gap: 6px;
  align-items: center;
}
.demo-temporary .demo-input {
  justify-content: center;
  padding-inline: 4px;
}
.demo-eye {
  display: grid;
  place-items: center;
  width: 36px;
  min-height: 40px;
  padding: 0;
  flex-shrink: 0;
  background: transparent;
  color: var(--muted);
  border-radius: 9px;
  margin-left: auto;
}
.demo-eye:hover {
  color: var(--text);
  background: var(--panel-hover);
}
.demo-password > span {
  flex: 1;
}
.demo-password {
  padding-right: 3px;
}
.demo-password {
  border-color: var(--blue);
}
.demo-password > span {
  display: flex;
  align-items: center;
  letter-spacing: 2px;
  min-width: 0;
}
.demo-caret {
  width: 1px;
  height: 14px;
  background: var(--blue);
  margin-left: 2px;
}
.demo-submit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 43px;
  background: #4ea4ef;
  color: #0c1c31;
  border-radius: 22px;
  font-size: 12px;
  font-weight: 600;
  margin-top: 10px;
}
.demo-alternative {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: var(--muted);
  font-size: 11px;
  margin-top: 8px;
}
.demo-result {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px;
  gap: 7px;
  text-align: center;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--panel);
  box-shadow: 0 12px 40px var(--shadow);
}
.demo-result-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
.demo-result-icon {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--demo-status) 12%, transparent);
  color: var(--demo-status);
  margin-bottom: 0;
}
.demo-result.success {
  --demo-status: var(--status-success);
}
.demo-result h3 {
  font-size: 20px;
  margin-bottom: 0;
}
.demo-result p {
  color: var(--muted);
  font-size: 13px;
}
.demo-result-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 0;
  color: var(--demo-status);
  font-size: 12px;
}
.demo-result .demo-result-footnote {
  font-size: 11px;
}
.demo-progress {
  height: 2px;
  background: var(--border);
}
.demo-progress span {
  display: block;
  height: 100%;
  background: var(--blue);
  transform-origin: left;
}
.demo-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 4px 12px 0;
}
.demo-scenarios,
.demo-playback {
  display: flex;
  gap: 4px;
}
.demo-controls button {
  min-width: 44px;
  min-height: 44px;
  border-radius: 22px;
  background: transparent;
  color: var(--muted);
  display: grid;
  place-items: center;
  font-size: 11px;
  padding: 0 12px;
}
.demo-controls button:hover {
  color: var(--text);
  background: var(--panel-hover);
}
.demo-scenarios button[aria-pressed='true'] {
  background: var(--panel-hover);
  color: var(--blue);
  box-shadow: inset 0 0 0 1px var(--border);
}
.demo-playback button {
  padding: 0;
}
.demo-caption {
  font-size: 11px;
  padding: 6px 16px 12px;
  color: var(--text);
  min-height: 54px;
}
.demo-caption span {
  display: block;
  color: var(--muted);
  margin-top: 4px;
  font-size: 10px;
}
.demo-result-enter-active,
.demo-result-leave-active {
  transition:
    opacity 0.3s var(--motion-ease),
    transform 0.35s var(--motion-ease);
}
.demo-result-enter-from,
.demo-result-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.97);
}
@media (prefers-reduced-motion: no-preference) {
  .is-running .is-confirming > svg {
    animation: demo-confirm 1.2s ease-in-out infinite alternate;
  }
  .is-running .demo-caret {
    animation: demo-blink 1s steps(2, jump-none) infinite;
  }
  .is-running .demo-spinner {
    animation: demo-spin 1s linear infinite;
  }
  .demo-controls button {
    transition:
      background 0.2s,
      color 0.2s;
  }
  .demo-progress span {
    transition: transform 0.15s linear;
  }
}
@keyframes demo-confirm {
  from {
    opacity: 0.5;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1.05);
  }
}
@keyframes demo-blink {
  to {
    opacity: 0;
  }
}
@keyframes demo-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (max-width: 480px) {
  .demo-scene {
    padding: 16px;
  }
  .demo-heading h2 {
    font-size: 16px;
  }
  .demo-toolbar {
    padding: 8px 14px;
  }
  .demo-controls {
    padding-inline: 10px;
    gap: 2px;
  }
  .demo-controls button {
    padding-inline: 10px;
  }
  .demo-playback {
    gap: 0;
  }
  .demo-playback button {
    padding: 0;
  }
  .demo-dots {
    display: none;
  }
}
</style>
