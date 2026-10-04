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
  border-radius: 24px;
  background: var(--panel);
  box-shadow: 0 24px 65px var(--shadow);
  overflow: hidden;
}
.exposure-toolbar {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 14px;
  min-height: 42px;
  padding: 8px 14px;
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
  gap: 7px;
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
  aspect-ratio: 16 / 10;
  min-height: 370px;
  overflow: hidden;
  background: #1d396a;
}
.exposure-wallpaper {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at 78% 22%, rgba(171, 212, 255, 0.72) 0 3%, transparent 3.3%),
    radial-gradient(circle at 22% 25%, rgba(170, 210, 249, 0.4) 0 2%, transparent 2.4%),
    linear-gradient(155deg, #162d61 0%, #2d6095 53%, #a2bfd4 100%);
}
.exposure-wallpaper::before,
.exposure-wallpaper::after {
  position: absolute;
  content: '';
  inset: auto -8% -9% -8%;
  height: 58%;
  background: linear-gradient(145deg, rgba(18, 48, 88, 0.8), rgba(31, 93, 129, 0.2));
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
  background: linear-gradient(145deg, rgba(8, 31, 65, 0.82), rgba(29, 77, 108, 0.24));
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
  background: rgba(187, 221, 241, 0.18);
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
  background: rgba(213, 237, 246, 0.13);
  transform: rotate(36deg) skewX(-15deg);
}
.exposure-star {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(232, 246, 255, 0.72);
  box-shadow: 0 0 9px rgba(232, 246, 255, 0.9);
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
  gap: 8px;
}
.exposure-notice {
  position: relative;
  width: 100%;
  padding: 8px 11px 9px;
  border: 1px solid rgba(228, 239, 255, 0.26);
  border-radius: 10px;
  background: rgba(21, 31, 48, 0.96);
  color: #edf4ff;
  box-shadow: 0 12px 36px rgba(3, 13, 31, 0.42);
  backdrop-filter: blur(18px);
}
.exposure-notice-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 5px;
  color: rgba(237, 244, 255, 0.58);
  font-size: 9px;
}
.exposure-notice-app {
  color: #dbeaff;
  font-size: 10px;
  font-weight: 600;
}
.exposure-notice-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: auto;
}
.exposure-notice-actions button {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: 0;
  border-radius: 5px;
  background: transparent;
  color: rgba(237, 244, 255, 0.62);
}
.exposure-notice-actions button:hover,
.exposure-notice-actions button:focus-visible {
  background: rgba(237, 244, 255, 0.12);
  color: #edf4ff;
}
.exposure-notice-progress {
  height: 1px;
  background: rgba(129, 201, 255, 0.9);
  transform-origin: left;
}
.exposure-notice-body {
  display: flex;
  align-items: flex-start;
  gap: 11px;
  margin-top: 0;
  padding-top: 10px;
}
.exposure-notice-icon {
  display: grid;
  place-items: center;
  width: 39px;
  height: 39px;
  flex-shrink: 0;
  border-radius: 7px;
  background: linear-gradient(145deg, #2dc5ef, #2586d0);
  color: #f4fbff;
  box-shadow: inset 0 0 0 2px rgba(205, 241, 255, 0.28);
}
.exposure-notice-body strong {
  display: block;
  color: #f3f7ff;
  font-size: 14px;
  line-height: 1.4;
}
.exposure-notice-body p {
  color: rgba(237, 244, 255, 0.73);
  font-size: 10px;
  line-height: 1.55;
}
.exposure-notice-body strong + p {
  margin-top: 5px;
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
  padding: 7px 13px;
  bottom: 10px;
  transform: translateX(-50%);
  border: 1px solid rgba(228, 239, 255, 0.2);
  border-radius: 18px;
  background: rgba(15, 27, 49, 0.82);
  color: rgba(239, 249, 255, 0.8);
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 28px rgba(3, 13, 31, 0.38);
}
.exposure-taskbar-launch,
.exposure-taskbar-status {
  gap: 13px;
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
  color: #edf4ff;
  font-size: 11px;
  line-height: 1.05;
  text-align: right;
}
.exposure-taskbar-time small {
  color: rgba(239, 249, 255, 0.62);
  font-size: 8px;
}
.exposure-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px 4px;
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
  gap: 3px;
  flex-shrink: 0;
}
.exposure-controls button {
  display: grid;
  place-items: center;
  width: 38px;
  min-height: 38px;
  padding: 0;
  border-radius: 20px;
  background: transparent;
  color: var(--muted);
}
.exposure-controls button:hover {
  background: var(--panel-hover);
  color: var(--text);
}
.exposure-caption {
  min-height: 44px;
  padding: 4px 14px 12px;
  color: var(--text);
  font-size: 11px;
  line-height: 1.6;
}
.exposure-caption span {
  display: block;
  color: var(--muted);
  font-size: 10px;
}
:global(html[data-theme='light'] .exposure-wallpaper) {
  background:
    radial-gradient(circle at 78% 22%, rgba(255, 255, 255, 0.9) 0 3%, transparent 3.3%),
    radial-gradient(circle at 22% 25%, rgba(255, 255, 255, 0.72) 0 2%, transparent 2.4%),
    linear-gradient(155deg, #7caed4 0%, #a9cee5 53%, #dfeaf0 100%);
}
:global(html[data-theme='light'] .exposure-wallpaper::before) {
  background: linear-gradient(145deg, rgba(53, 105, 140, 0.42), rgba(91, 155, 177, 0.18));
}
:global(html[data-theme='light'] .exposure-wallpaper::after) {
  background: linear-gradient(145deg, rgba(31, 76, 112, 0.48), rgba(86, 145, 167, 0.16));
}
:global(html[data-theme='light'] .exposure-notice) {
  border-color: rgba(40, 77, 112, 0.2);
  background: rgba(248, 252, 255, 0.96);
  color: #172a3d;
  box-shadow: 0 12px 36px rgba(30, 67, 100, 0.22);
}
:global(html[data-theme='light'] .exposure-notice-head) {
  color: rgba(23, 42, 61, 0.58);
}
:global(html[data-theme='light'] .exposure-notice-app),
:global(html[data-theme='light'] .exposure-notice-body strong) {
  color: #18334c;
}
:global(html[data-theme='light'] .exposure-notice-actions button) {
  color: rgba(23, 42, 61, 0.58);
}
:global(html[data-theme='light'] .exposure-notice-actions button:hover),
:global(html[data-theme='light'] .exposure-notice-actions button:focus-visible) {
  background: rgba(23, 75, 117, 0.1);
  color: #18334c;
}
:global(html[data-theme='light'] .exposure-notice-body p) {
  color: rgba(23, 42, 61, 0.7);
}
:global(html[data-theme='light'] .exposure-taskbar) {
  border-color: rgba(40, 77, 112, 0.2);
  background: rgba(244, 250, 255, 0.78);
  color: rgba(23, 52, 76, 0.82);
  box-shadow: 0 10px 28px rgba(30, 67, 100, 0.2);
}
:global(html[data-theme='light'] .exposure-taskbar-time) {
  color: #17344e;
}
:global(html[data-theme='light'] .exposure-taskbar-time small) {
  color: rgba(23, 52, 76, 0.62);
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
      inset 0 0 0 2px rgba(205, 241, 255, 0.28),
      0 0 0 rgba(82, 178, 238, 0);
  }
  to {
    box-shadow:
      inset 0 0 0 2px rgba(205, 241, 255, 0.28),
      0 0 14px rgba(82, 178, 238, 0.42);
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
    padding-left: 21px;
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
    padding: 6px 8px 7px;
    border-radius: 8px;
  }
  .exposure-notice-head {
    gap: 6px;
    padding-bottom: 3px;
  }
  .exposure-notice-app {
    font-size: 9px;
  }
  .exposure-notice-actions button {
    width: 18px;
    height: 18px;
  }
  .exposure-notice-body {
    gap: 8px;
    padding-top: 7px;
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
    margin-top: 3px;
  }
  .exposure-taskbar {
    width: calc(100% - 16px);
    padding-inline: 9px;
  }
  .exposure-taskbar-launch,
  .exposure-taskbar-status {
    gap: 8px;
  }
  .exposure-taskbar-time {
    margin-left: -4px;
  }
  .exposure-footer {
    align-items: flex-start;
  }
  .exposure-state {
    gap: 5px;
  }
  .exposure-state > span:last-child {
    width: 100%;
    padding-left: 11px;
  }
}
</style>
