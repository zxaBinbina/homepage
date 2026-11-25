<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Camera, Pause, Play } from 'lucide-vue-next'

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
function playbackChanged() {
  playing.value = !!video.value && !video.value.paused
}
function syncPlayback() {
  for (const player of [video.value, taskbar.value]) {
    if (!player) continue
    if (!canPlay.value) player.pause()
    else {
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
function visibilityChanged() {
  documentVisible.value = !document.hidden
}
function motionChanged() {
  if (motion.matches) requested.value = false
}
watch(canPlay, syncPlayback)
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
      <span><Camera :size="17" aria-hidden="true" /> 普通模式 · KDE 深色</span>
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
      <span>任务栏歌词 · 可左右查看</span>
      <div class="sptl-recording-strip">
        <video
          ref="taskbar"
          src="/images/sptl/dark/taskbar.mp4"
          poster="/images/sptl/dark/taskbar-poster.webp"
          muted
          loop
          playsinline
          preload="metadata"
          width="740"
          height="74"
          aria-label="普通模式任务栏连续实录"
          @loadedmetadata="syncPlayback"
        />
      </div>
    </div>
    <div class="sptl-recording-stage">
      <video
        ref="video"
        src="/images/sptl/dark/hero.mp4"
        poster="/images/sptl/dark/hero-poster.webp"
        muted
        loop
        playsinline
        preload="metadata"
        width="600"
        height="694"
        aria-label="普通模式歌词弹窗连续实录"
        @loadedmetadata="syncPlayback"
        @play="playbackChanged"
        @pause="playbackChanged"
      />
    </div>
    <figcaption>
      <p>从《经过》的第一句歌词开始，连续呈现逐字高亮、圆形封面和普通播放控制。</p>
      <span>屏幕连续录制 · 30 帧/秒 · 无音轨 · 可暂停细看</span>
      <a
        class="sptl-text-link"
        href="/images/sptl/dark/hero.mp4"
        target="_blank"
        rel="noopener noreferrer"
        >查看原视频</a
      >
    </figcaption>
  </figure>
</template>
