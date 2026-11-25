<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Camera, Pause, Play } from 'lucide-vue-next'

const recording = ref<HTMLElement>()
const motion = matchMedia('(prefers-reduced-motion: reduce)')
const requested = ref(!motion.matches)
const inView = ref(false)
const documentVisible = ref(!document.hidden)
const playing = computed(() => requested.value && inView.value && documentVisible.value)
let observer: IntersectionObserver | undefined
function visibilityChanged() {
  documentVisible.value = !document.hidden
}
function motionChanged() {
  if (motion.matches) requested.value = false
}
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
  observer?.disconnect()
  document.removeEventListener('visibilitychange', visibilityChanged)
  motion.removeEventListener('change', motionChanged)
})
</script>

<template>
  <figure ref="recording" class="sptl-desktop-recording" id="recording">
    <div class="sptl-recording-toolbar">
      <span><Camera :size="17" aria-hidden="true" /> 本机实拍</span>
      <button
        type="button"
        @click="requested = !requested"
        :aria-label="playing ? '暂停实拍动图' : '播放实拍动图'"
        :aria-pressed="playing"
      >
        <Pause v-if="playing" :size="16" aria-hidden="true" /><Play
          v-else
          :size="16"
          aria-hidden="true"
        />
        {{ playing ? '暂停动图' : '播放动图' }}
      </button>
    </div>
    <div class="sptl-recording-taskbar">
      <span>任务栏歌词</span>
      <a
        class="sptl-recording-strip"
        href="/images/sptl/cover-circle.webp"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="查看任务栏实拍原图（在新标签页打开）"
      >
        <img
          src="/images/sptl/cover-circle.webp"
          alt="SPTL 本机任务栏实拍：圆形封面与双行同步歌词"
          width="740"
          height="74"
        />
      </a>
    </div>
    <a
      class="sptl-recording-stage"
      href="/images/sptl/hero-live.gif"
      target="_blank"
      rel="noopener noreferrer"
      aria-label="查看本机实拍动图原文件（在新标签页打开）"
    >
      <img
        :src="playing ? '/images/sptl/hero-live.gif' : '/images/sptl/hero-poster.webp'"
        alt="SPTL 实机录屏：歌词弹窗中的逐字高亮、圆形封面旋转与播放控制"
        width="602"
        height="694"
        decoding="async"
        fetchpriority="high"
      />
    </a>
    <figcaption>
      <p>任务栏与歌词弹窗的真实画面，动图里可以细看逐字高亮与圆形封面。</p>
      <span>实机录屏 · 无音频 · 可以暂停细看</span>
    </figcaption>
  </figure>
</template>
