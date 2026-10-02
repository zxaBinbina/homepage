<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Check,
  CircleX,
  Fingerprint,
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
const outcome = ref<'success' | 'failure'>('success')
const frame = ref(reduced.value ? 24 : 0)
const manual = ref(false)
const phase = computed(() =>
  frame.value < 16 ? 'typing' : frame.value < 24 ? 'checking' : outcome.value,
)
const running = computed(() => !reduced.value && !paused.value && inView.value && visible.value)
const password = computed(() => '•'.repeat(Math.min(frame.value, 16)))
const caption = computed(
  () =>
    ({
      typing: '正在输入访问密码',
      checking: '正在验证身份',
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
      ([entry]) => {
        inView.value = !!entry?.isIntersecting
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
  >
    <div class="demo-toolbar">
      <span class="demo-dots" aria-hidden="true"><i></i><i></i><i></i></span
      ><span><LockKeyhole :size="12" /> auth.example.com</span
      ><span class="demo-badge">模拟演示</span>
    </div>
    <div class="demo-scene">
      <div class="demo-heading">
        <span class="demo-shield"><ShieldCheck :size="23" /></span>
        <div>
          <h2>连接之前，确认是你。</h2>
          <p>RDP Access Auth</p>
        </div>
      </div>
      <div class="demo-field">
        <span>需要授权的公网 IPv4</span>
        <div class="demo-input">
          <Monitor :size="15" /><span>203.0.113.42</span><span class="demo-example">示例</span>
        </div>
      </div>
      <div class="demo-field">
        <span>访问密码</span>
        <div class="demo-input demo-password" aria-label="模拟输入密码">
          <KeyRound :size="15" /><span aria-hidden="true"
            >{{ password }}<i v-if="phase === 'typing'" class="demo-caret"></i
          ></span>
        </div>
      </div>
      <div class="demo-submit" aria-hidden="true">
        <LoaderCircle v-if="phase === 'checking'" class="demo-spinner" :size="16" /><LockKeyhole
          v-else
          :size="16"
        />{{ phase === 'checking' ? '验证中…' : '认证并授权' }}
      </div>
      <p class="demo-alternative"><Fingerprint :size="15" /> 也支持通行密钥与临时密码</p>
      <Transition name="demo-result">
        <div
          v-if="phase === 'success' || phase === 'failure'"
          :key="phase"
          class="demo-result"
          :class="phase"
        >
          <span class="demo-result-icon"
            ><Check v-if="phase === 'success'" :size="27" /><CircleX v-else :size="27"
          /></span>
          <h3>{{ phase === 'success' ? '认证成功' : '认证失败' }}</h3>
          <p>
            {{ phase === 'success' ? '此公网 IPv4 已获得准入。' : '密码不正确，暂未放行此 IP。' }}
          </p>
          <div class="demo-result-detail">
            <ShieldCheck v-if="phase === 'success'" :size="16" /><LockKeyhole
              v-else
              :size="16"
            /><span>{{
              phase === 'success' ? '6 小时内可发起新的 RDP 连接' : '检查访问密码后，可以再次尝试'
            }}</span>
          </div>
          <p class="demo-result-footnote">
            {{
              phase === 'success'
                ? '接下来，使用系统账户登录远程桌面。'
                : '连续失败会触发认证限流与封禁。'
            }}
          </p>
        </div>
      </Transition>
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
  padding: 16px 20px;
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
  padding: 28px;
  min-height: 354px;
}
.demo-heading {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}
.demo-shield {
  display: grid;
  place-items: center;
  width: 43px;
  height: 43px;
  color: var(--blue);
  background: color-mix(in srgb, var(--blue) 10%, transparent);
  border-radius: 13px;
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
.demo-example {
  margin-left: auto;
  color: var(--muted);
  font: 10px sans-serif;
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
  margin-top: 22px;
}
.demo-alternative {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: var(--muted);
  font-size: 11px;
  margin-top: 16px;
}
.demo-result {
  position: absolute;
  inset: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 18px;
  text-align: center;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--panel);
  box-shadow: 0 12px 40px var(--shadow);
}
.demo-result-icon {
  display: grid;
  place-items: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--demo-status) 12%, transparent);
  color: var(--demo-status);
  margin-bottom: 20px;
}
.demo-result.success {
  --demo-status: var(--status-success);
}
.demo-result.failure {
  --demo-status: var(--status-danger);
}
.demo-result h3 {
  font-size: 24px;
  margin-bottom: 10px;
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
  margin: 22px 0 18px;
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
  padding: 12px 16px 0;
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
  padding: 12px 20px 20px;
  color: var(--text);
  min-height: 76px;
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
    padding: 20px;
  }
  .demo-heading h2 {
    font-size: 16px;
  }
  .demo-toolbar {
    padding: 14px;
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
