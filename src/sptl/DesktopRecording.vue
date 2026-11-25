<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Camera, Pause, Play } from 'lucide-vue-next'
import { useTheme } from '../composables/useTheme'

const { light } = useTheme()
const folder = computed(() => `/images/sptl/${light.value ? 'light' : 'dark'}/`)
const recording = ref<HTMLElement>()
const video = ref<HTMLVideoElement>()
const taskbar = ref<HTMLVideoElement>()
const motion = matchMedia('(prefers-reduced-motion: reduce)')
const requested = ref(!motion.matches)
const inView = ref(false)
const documentVisible = ref(!document.hidden)
const playing = ref(false)
const canPlay = computed(() => requested.value && inView.value && documentVisible.value)
let observer: IntersectionObserver | undefined
let savedTime = 0
const loadedPlayers = new Set<HTMLVideoElement>()
function playbackChanged() {
  playing.value = !!video.value && !video.value.paused
}
function syncPlayback() {
  const ready =
    !!video.value &&
    !!taskbar.value &&
    loadedPlayers.has(video.value) &&
    loadedPlayers.has(taskbar.value)
  for (const player of [video.value, taskbar.value]) {
    if (!player) continue
    if (!canPlay.value) player.pause()
    else if (ready) {
      if (
        player === taskbar.value &&
        video.value &&
        Math.abs(player.currentTime - video.value.currentTime) > 0.15
      )
        player.currentTime = video.value.currentTime
      void player.play().catch(playbackChanged)
    }
  }
}
function mediaLoaded(event: Event) {
  const player = event.target as HTMLVideoElement
  if (!player.currentSrc.includes(folder.value)) return
  player.currentTime = Math.min(savedTime, Math.max(0, player.duration - 0.05))
  loadedPlayers.add(player)
  syncPlayback()
}
function visibilityChanged() {
  documentVisible.value = !document.hidden
}
function motionChanged() {
  if (motion.matches) requested.value = false
}
watch(canPlay, syncPlayback)
watch(light, () => {
  if (video.value && loadedPlayers.has(video.value)) savedTime = video.value.currentTime
  loadedPlayers.clear()
  video.value?.pause()
  taskbar.value?.pause()
})
onMounted(() => {
  if ('IntersectionObserver' in window) {
    observer = new IntersectionObserver(
      ([entry]) => {
        inView.value = !!entry?.isIntersecting
      },
      { threshold: 0.05 },
    )
    if (recording.value) observer.observe(recording.value)
  } else inView.value = true
  document.addEventListener('visibilitychange', visibilityChanged)
  motion.addEventListener('change', motionChanged)
})
onBeforeUnmount(() => {
  video.value?.pause()
  taskbar.value?.pause()
  observer?.disconnect()
  document.removeEventListener('visibilitychange', visibilityChanged)
  motion.removeEventListener('change', motionChanged)
})
</script>

<template>
  <figure ref="recording" class="sptl-desktop-recording" id="recording">
    <div class="sptl-recording-toolbar">
      <span
        ><Camera :size="17" aria-hidden="true" /> 普通模式 · KDE {{ light ? '浅色' : '深色' }}</span
      >
      <button
        type="button"
        @click="requested = !playing"
        :aria-label="playing ? '暂停实拍视频' : '播放实拍视频'"
        :aria-pressed="playing"
      >
        <Pause v-if="playing" :size="16" aria-hidden="true" /><Play
          v-else
          :size="16"
          aria-hidden="true"
        />
        {{ playing ? '暂停视频' : '播放视频' }}
      </button>
    </div>
    <div class="sptl-recording-taskbar">
      <span>任务栏歌词</span>
      <div class="sptl-recording-strip">
        <video
          ref="taskbar"
          :src="folder + 'taskbar-compact.mp4'"
          :poster="folder + 'taskbar-compact-poster.webp'"
          muted
          loop
          playsinline
          preload="metadata"
          width="460"
          height="74"
          aria-label="普通模式任务栏连续实录"
          @loadedmetadata="mediaLoaded"
        />
      </div>
    </div>
    <div class="sptl-recording-stage">
      <video
        ref="video"
        :src="folder + 'hero.mp4'"
        :poster="folder + 'hero-poster.webp'"
        muted
        loop
        playsinline
        preload="metadata"
        width="600"
        height="694"
        aria-label="普通模式歌词弹窗连续实录"
        @loadedmetadata="mediaLoaded"
        @play="playbackChanged"
        @pause="playbackChanged"
      />
    </div>
    <figcaption>
      <p>从《经过》的第一句开始，实拍逐字歌词、圆形封面与播放控制。</p>
      <span>连续实录 · 30 帧/秒 · 无音轨 · 可暂停</span>
      <a
        class="sptl-text-link"
        :href="folder + 'hero.mp4'"
        target="_blank"
        rel="noopener noreferrer"
        >查看原视频</a
      >
    </figcaption>
  </figure>
</template>
