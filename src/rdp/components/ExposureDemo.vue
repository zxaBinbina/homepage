<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Bell,
  Bluetooth,
  ClipboardList,
  ChevronUp,
  Keyboard,
  Monitor,
  MonitorUp,
  Pause,
  Play,
  RotateCcw,
  Settings2,
  TerminalSquare,
  Volume2,
  Wifi,
  X,
} from 'lucide-vue-next'

const root = ref<HTMLElement>()
const motion = matchMedia('(prefers-reduced-motion: reduce)')
const reduced = ref(motion.matches)
const paused = ref(false)
const inView = ref(false)
const visible = ref(!document.hidden)
type ExposureNotice = {
  id: number
  remaining: number
  startedAt: number
}

const noticeDuration = 5000
const noticeInterval = 1800
const noticeGap = 500
const notices = ref<ExposureNotice[]>([
  {
    id: 0,
    remaining: noticeDuration,
    startedAt: 0,
  },
])
const clockTime = ref('')
const clockDate = ref('')
const orderedNotices = computed(() => [...notices.value].reverse())
const running = computed(() => !reduced.value && !paused.value && inView.value && visible.value)

let noticeTimer: ReturnType<typeof setTimeout> | undefined
let clockTimer: ReturnType<typeof setInterval> | undefined
let observer: IntersectionObserver | undefined
let nextNoticeId = 1

function pad(value: number) {
  return String(value).padStart(2, '0')
}

function updateClock() {
  const now = new Date()
  clockTime.value = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
  const weekday = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][now.getDay()]
  clockDate.value = `${weekday} ${pad(now.getMonth() + 1)}/${pad(now.getDate())}`
}

function clearSchedule() {
  clearTimeout(noticeTimer)
  noticeTimer = undefined
}

function addNotice() {
  notices.value = [
    ...notices.value,
    {
      id: nextNoticeId++,
      remaining: noticeDuration,
      startedAt: running.value ? performance.now() : 0,
    },
  ].slice(-2)
}

function pauseSchedule() {
  const now = performance.now()
  notices.value = notices.value.map((notice) => ({
    ...notice,
    remaining: notice.startedAt
      ? Math.max(0, notice.remaining - (now - notice.startedAt))
      : notice.remaining,
    startedAt: 0,
  }))
  clearSchedule()
}

function removeNotice(id: number) {
  notices.value = notices.value.filter((notice) => notice.id !== id)
}

function schedule() {
  clearSchedule()
  if (!running.value) return

  const now = performance.now()
  notices.value = notices.value.map((notice) =>
    notice.startedAt ? notice : { ...notice, startedAt: now },
  )
  const expired = notices.value.find((notice) => notice.remaining - (now - notice.startedAt) <= 0)
  if (expired) {
    removeNotice(expired.id)
    noticeTimer = setTimeout(() => {
      if (running.value && notices.value.length < 2) addNotice()
      schedule()
    }, noticeGap)
    return
  }

  if (notices.value.length < 2) {
    const nextExpiry = notices.value.length
      ? Math.max(0, notices.value[0].remaining - (now - notices.value[0].startedAt))
      : Infinity
    const nextAt = notices.value.length ? Math.min(noticeInterval, nextExpiry) : 0
    noticeTimer = setTimeout(() => {
      addNotice()
      schedule()
    }, nextAt)
    return
  }

  const nextExpiry = Math.min(
    ...notices.value.map((notice) => notice.remaining - (now - notice.startedAt)),
  )
  noticeTimer = setTimeout(schedule, Math.max(0, nextExpiry))
}

function replay() {
  clearSchedule()
  nextNoticeId = 0
  notices.value = []
  paused.value = false
  addNotice()
  schedule()
}

function dismissNotice(id: number) {
  if (!notices.value.some((notice) => notice.id === id)) return
  removeNotice(id)
  schedule()
}

function onVisibility() {
  visible.value = !document.hidden
}

function onMotion() {
  reduced.value = motion.matches
  if (reduced.value) paused.value = false
  schedule()
}

watch(running, (active) => {
  if (active) schedule()
  else pauseSchedule()
})

onMounted(() => {
  if ('IntersectionObserver' in window) {
    observer = new IntersectionObserver(
      (entries) => {
        inView.value = !!entries.at(-1)?.isIntersecting
      },
      { threshold: 0.15 },
    )
    if (root.value) observer.observe(root.value)
  } else {
    inView.value = true
  }
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  document.addEventListener('visibilitychange', onVisibility)
  motion.addEventListener('change', onMotion)
})

onBeforeUnmount(() => {
  clearSchedule()
  clearInterval(clockTimer)
  observer?.disconnect()
  document.removeEventListener('visibilitychange', onVisibility)
  motion.removeEventListener('change', onMotion)
})
</script>

<template>
  <section
    ref="root"
    class="exposure-demo"
    :class="{ 'is-running': running, 'is-paused': !running }"
    :data-notice-count="notices.length"
    aria-label="直接暴露远程桌面的风险动画"
  >
    <div class="exposure-toolbar">
      <span class="exposure-window-title"><TerminalSquare :size="14" /> KDE Desktop</span>
    </div>

    <div class="exposure-desktop">
      <div class="exposure-wallpaper" aria-hidden="true">
        <span class="exposure-mountain exposure-mountain-back"></span>
        <span class="exposure-mountain exposure-mountain-front"></span>
        <span class="exposure-star star-one"></span>
        <span class="exposure-star star-two"></span>
        <span class="exposure-star star-three"></span>
      </div>

      <TransitionGroup name="exposure-notices" tag="div" class="exposure-notices">
        <div
          v-for="notice in orderedNotices"
          :key="notice.id"
          class="exposure-notice"
          role="status"
        >
          <div class="exposure-notice-head">
            <span class="exposure-notice-app"><Bell :size="13" /> KDE系统集成</span>
            <span class="exposure-notice-actions">
              <button type="button" aria-label="通知设置" title="通知设置">
                <Settings2 :size="13" />
              </button>
              <button
                type="button"
                aria-label="关闭通知"
                title="关闭通知"
                @click="dismissNotice(notice.id)"
              >
                <X :size="13" />
              </button>
            </span>
          </div>
          <div class="exposure-notice-progress" aria-hidden="true"></div>
          <div class="exposure-notice-body">
            <div class="exposure-notice-icon"><Monitor :size="28" /></div>
            <div>
              <strong>远程控制会话已开始</strong>
              <p>Krdp 正在行使特殊权限：</p>
              <p>- 查看屏幕上的内容</p>
              <p>- 控制输入设备</p>
            </div>
          </div>
        </div>
      </TransitionGroup>

      <div class="exposure-taskbar">
        <div class="exposure-taskbar-launch">
          <img
            class="exposure-launcher"
            src="/images/fedora-launcher.png"
            alt=""
            width="30"
            height="30"
          />
        </div>
        <div class="exposure-taskbar-status">
          <MonitorUp :size="14" />
          <ClipboardList :size="14" />
          <Keyboard :size="14" />
          <Bluetooth :size="14" />
          <Wifi :size="14" />
          <Volume2 :size="14" />
          <ChevronUp :size="14" />
          <span class="exposure-taskbar-time"
            >{{ clockTime }}<br /><small>{{ clockDate }}</small></span
          >
        </div>
      </div>
    </div>

    <div class="exposure-footer">
      <div class="exposure-state">
        <span class="exposure-state-dot"></span><b>没有人在控制这台电脑</b
        ><span>只是有人一直在尝试账户密码</span>
      </div>
    </div>
    <p class="exposure-caption">
      这不是“有人已经登录”的提示，而是暴露在公网后的噪音：系统不断收到新的猜测。
    </p>
  </section>
</template>

<style scoped>
.exposure-demo {
  min-width: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  background: var(--panel);
  box-shadow: 0 24px 65px var(--shadow);
  overflow: hidden;
}
.exposure-toolbar {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: var(--space-md);
  min-height: 42px;
  padding: var(--space-xs) var(--space-md);
  border-bottom: 1px solid var(--border);
  color: var(--muted);
  font-size: 11px;
}
.exposure-window-title,
.exposure-toolbar-label,
.exposure-notice-app,
.exposure-state,
.exposure-taskbar-status,
.exposure-taskbar-launch {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}
.exposure-window-title {
  color: var(--text);
  font-weight: 600;
}
.exposure-toolbar-label {
  color: var(--status-danger);
  white-space: nowrap;
}
.exposure-desktop {
  position: relative;
  isolation: isolate;
  width: 100%;
  aspect-ratio: 16 / 10;
  min-height: 370px;
  overflow: hidden;
  background: var(--rdp-demo-sky-start);
}
.exposure-wallpaper {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at 78% 22%, var(--rdp-demo-orb-one) 0 3%, transparent 3.3%),
    radial-gradient(circle at 22% 25%, var(--rdp-demo-orb-two) 0 2%, transparent 2.4%),
    linear-gradient(
      155deg,
      var(--rdp-demo-sky-start) 0%,
      var(--rdp-demo-sky-mid) 53%,
      var(--rdp-demo-sky-end) 100%
    );
}
.exposure-wallpaper::before,
.exposure-wallpaper::after {
  position: absolute;
  content: '';
  inset: auto -8% -9% -8%;
  height: 58%;
  background: linear-gradient(
    145deg,
    var(--rdp-demo-mountain-back-start),
    var(--rdp-demo-mountain-back-end)
  );
  clip-path: polygon(
    0 59%,
    10% 47%,
    24% 62%,
    37% 29%,
    54% 56%,
    68% 34%,
    84% 60%,
    100% 18%,
    100% 100%,
    0 100%
  );
}
.exposure-wallpaper::after {
  inset: auto -10% -13% -10%;
  height: 43%;
  background: linear-gradient(
    145deg,
    var(--rdp-demo-mountain-front-start),
    var(--rdp-demo-mountain-front-end)
  );
  clip-path: polygon(
    0 60%,
    18% 43%,
    31% 66%,
    49% 37%,
    62% 58%,
    78% 31%,
    100% 52%,
    100% 100%,
    0 100%
  );
}
.exposure-mountain {
  position: absolute;
  width: 19%;
  aspect-ratio: 1;
  border-radius: 50% 50% 0 0;
  background: color-mix(in srgb, var(--rdp-demo-sky-end) 18%, transparent);
  filter: blur(1px);
}
.exposure-mountain-back {
  right: 20%;
  bottom: 30%;
  transform: rotate(28deg) skewX(-12deg);
}
.exposure-mountain-front {
  right: 8%;
  bottom: 26%;
  width: 25%;
  background: color-mix(in srgb, var(--rdp-demo-sky-end) 13%, transparent);
  transform: rotate(36deg) skewX(-15deg);
}
.exposure-star {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--rdp-demo-orb-one);
  box-shadow: 0 0 9px var(--rdp-demo-orb-one);
}
.star-one {
  top: 20%;
  left: 18%;
}
.star-two {
  top: 30%;
  left: 42%;
  width: 3px;
  height: 3px;
}
.star-three {
  top: 14%;
  right: 19%;
  width: 3px;
  height: 3px;
}
.exposure-notices {
  position: absolute;
  z-index: 4;
  right: calc((100% - min(92%, 620px)) / 2);
  bottom: 76px;
  width: min(250px, calc(100% - 34px));
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.exposure-notice {
  position: relative;
  width: 100%;
  padding: var(--space-xs) var(--space-sm) var(--space-xs);
  border: 1px solid var(--rdp-demo-notice-border);
  border-radius: var(--radius-sm);
  background: var(--rdp-demo-notice-bg);
  color: var(--rdp-demo-notice-text);
  box-shadow: 0 12px 36px var(--rdp-demo-notice-shadow);
  backdrop-filter: blur(18px);
}
.exposure-notice-head {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding-bottom: var(--space-2xs);
  color: var(--rdp-demo-notice-muted);
  font-size: 9px;
}
.exposure-notice-app {
  color: var(--rdp-demo-notice-app);
  font-size: 10px;
  font-weight: 600;
}
.exposure-notice-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
  margin-left: auto;
}
.exposure-notice-actions button {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-2xs);
  background: transparent;
  color: var(--rdp-demo-notice-action);
}
.exposure-notice-actions button:hover,
.exposure-notice-actions button:focus-visible {
  background: var(--rdp-demo-notice-hover-bg);
  color: var(--rdp-demo-notice-hover-text);
}
.exposure-notice-progress {
  height: 1px;
  background: color-mix(in srgb, var(--blue) 90%, transparent);
  transform-origin: left;
}
.exposure-notice-body {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  margin-top: 0;
  padding-top: var(--space-sm);
}
.exposure-notice-icon {
  display: grid;
  place-items: center;
  width: 39px;
  height: 39px;
  flex-shrink: 0;
  border-radius: var(--radius-xs);
  background: linear-gradient(145deg, var(--primary-action-hover), var(--primary-action));
  color: var(--primary-action-text);
  box-shadow: inset 0 0 0 2px color-mix(in srgb, var(--primary-action-text) 28%, transparent);
}
.exposure-notice-body strong {
  display: block;
  color: var(--rdp-demo-notice-strong);
  font-size: 14px;
  line-height: 1.4;
}
.exposure-notice-body p {
  color: var(--rdp-demo-notice-body);
  font-size: 10px;
  line-height: 1.55;
}
.exposure-notice-body strong + p {
  margin-top: var(--space-2xs);
}
.exposure-taskbar {
  position: absolute;
  z-index: 5;
  left: 50%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: min(92%, 620px);
  min-height: 50px;
  padding: var(--space-xs) var(--space-sm);
  bottom: 10px;
  transform: translateX(-50%);
  border: 1px solid var(--rdp-demo-taskbar-border);
  border-radius: var(--radius-lg);
  background: var(--rdp-demo-taskbar-bg);
  color: var(--rdp-demo-taskbar-text);
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 28px var(--rdp-demo-taskbar-shadow);
}
.exposure-taskbar-launch,
.exposure-taskbar-status {
  gap: var(--space-sm);
}
.exposure-launcher {
  display: block;
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  object-fit: contain;
  border-radius: 50%;
}
.exposure-taskbar-time {
  min-width: 66px;
  margin-left: -6px;
  color: var(--rdp-demo-taskbar-time);
  font-size: 11px;
  line-height: 1.05;
  text-align: right;
}
.exposure-taskbar-time small {
  color: var(--rdp-demo-taskbar-muted);
  font-size: 8px;
}
.exposure-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md) var(--space-2xs);
}
.exposure-state {
  min-width: 0;
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 10px;
}
.exposure-state b {
  color: var(--status-success);
  font-size: 11px;
}
.exposure-state-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--status-success);
  box-shadow: 0 0 8px color-mix(in srgb, var(--status-success) 65%, transparent);
}
.exposure-controls {
  display: flex;
  gap: var(--space-2xs);
  flex-shrink: 0;
}
.exposure-controls button {
  display: grid;
  place-items: center;
  width: 38px;
  min-height: 38px;
  padding: 0;
  border-radius: var(--radius-lg);
  background: transparent;
  color: var(--muted);
}
.exposure-controls button:hover {
  background: var(--panel-hover);
  color: var(--text);
}
.exposure-caption {
  min-height: 44px;
  padding: var(--space-2xs) var(--space-md) var(--space-sm);
  color: var(--text);
  font-size: 11px;
  line-height: 1.6;
}
.exposure-caption span {
  display: block;
  color: var(--muted);
  font-size: 10px;
}
@media (prefers-reduced-motion: no-preference) {
  .exposure-notices-move {
    transition: transform 0.35s var(--motion-ease) 0.35s;
  }
  .exposure-notices-enter-active,
  .exposure-notices-leave-active {
    transition:
      transform 0.35s var(--motion-ease),
      opacity 0.35s ease;
  }
  .exposure-notices-leave-active {
    position: absolute;
    width: 100%;
  }
  .exposure-notices-enter-from {
    opacity: 0;
    transform: translateX(18px);
  }
  .exposure-notices-leave-to {
    opacity: 0;
    transform: translateY(8px);
  }
  .is-running .exposure-notice-icon {
    animation: exposure-notice-pulse 1.2s ease-in-out infinite alternate;
  }
  .is-running .exposure-notice-progress {
    animation: exposure-notice-progress 5s linear forwards;
  }
  .is-paused .exposure-notice-progress {
    animation-play-state: paused;
  }
  .exposure-controls button {
    transition:
      background 0.2s,
      color 0.2s;
  }
}
@keyframes exposure-notice-progress {
  from {
    transform: scaleX(1);
  }
  to {
    transform: scaleX(0);
  }
}
@keyframes exposure-notice-enter {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes exposure-notice-pulse {
  from {
    box-shadow:
      inset 0 0 0 2px color-mix(in srgb, var(--primary-action-text) 28%, transparent),
      0 0 0 color-mix(in srgb, var(--blue) 0%, transparent);
  }
  to {
    box-shadow:
      inset 0 0 0 2px color-mix(in srgb, var(--primary-action-text) 28%, transparent),
      0 0 14px color-mix(in srgb, var(--blue) 42%, transparent);
  }
}
@media (max-width: 760px) {
  .exposure-desktop {
    min-height: 325px;
  }
  .exposure-notices {
    width: min(250px, calc(100% - 34px));
    bottom: 72px;
  }
}
@media (max-width: 480px) {
  .exposure-toolbar {
    grid-template-columns: 1fr auto;
  }
  .exposure-toolbar-label {
    grid-column: 1 / -1;
    grid-row: 2;
    margin-top: -6px;
    padding-left: var(--space-lg);
  }
  .exposure-desktop {
    min-height: 310px;
  }
  .exposure-notices {
    right: 8px;
    bottom: 72px;
    width: min(210px, calc(100% - 34px));
  }
  .exposure-notice {
    padding: var(--space-xs) var(--space-xs) var(--space-xs);
    border-radius: var(--radius-xs);
  }
  .exposure-notice-head {
    gap: var(--space-xs);
    padding-bottom: var(--space-2xs);
  }
  .exposure-notice-app {
    font-size: 9px;
  }
  .exposure-notice-actions button {
    width: 18px;
    height: 18px;
  }
  .exposure-notice-body {
    gap: var(--space-xs);
    padding-top: var(--space-xs);
  }
  .exposure-notice-icon {
    width: 30px;
    height: 30px;
  }
  .exposure-notice-body strong {
    font-size: 12px;
    line-height: 1.3;
  }
  .exposure-notice-body p {
    font-size: 9px;
    line-height: 1.35;
  }
  .exposure-notice-body strong + p {
    margin-top: var(--space-2xs);
  }
  .exposure-taskbar {
    width: calc(100% - 16px);
    padding-inline: var(--space-xs);
  }
  .exposure-taskbar-launch,
  .exposure-taskbar-status {
    gap: var(--space-xs);
  }
  .exposure-taskbar-time {
    margin-left: -4px;
  }
  .exposure-footer {
    align-items: flex-start;
  }
  .exposure-state {
    gap: var(--space-2xs);
  }
  .exposure-state > span:last-child {
    width: 100%;
    padding-left: var(--space-sm);
  }
}
</style>
