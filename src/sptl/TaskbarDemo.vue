<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { AudioLines, Grid2X2, Pause, Play, SkipBack, SkipForward } from 'lucide-vue-next'
import SegmentedControl from '../components/SegmentedControl.vue'

const examples = [
  { text: '把今天唱给你听', translation: 'Sing today for you' },
  { text: '让旋律陪你走过每一步', translation: 'A melody for every step' },
  { text: '忙碌之外，留一点时间给自己', translation: 'A little time, just for you' },
]
const scene = ref<HTMLElement>()
const layout = ref<'double' | 'single'>('double')
const index = ref(0)
const progress = ref(0)
const playing = ref(false)
const current = computed(() => examples[index.value]!)
const elapsed = computed(
  () => `0:${String(Math.floor((index.value * 6500 + progress.value) / 1000)).padStart(2, '0')}`,
)
const highlight = computed(() => `${Math.min(100, (progress.value / 6500) * 100)}%`)
let visible = false
let observer: IntersectionObserver | undefined
let timer: ReturnType<typeof setInterval> | undefined
let previous = 0
const motion = matchMedia('(prefers-reduced-motion: reduce)')

function step(direction: number) {
  index.value = (index.value + direction + examples.length) % examples.length
  progress.value = 0
  previous = performance.now()
}
function toggle() {
  playing.value = !playing.value
  previous = performance.now()
}
function stopForReducedMotion() {
  if (motion.matches) playing.value = false
}
onMounted(() => {
  playing.value = !motion.matches
  previous = performance.now()
  visible = true
  if ('IntersectionObserver' in window) {
    observer = new IntersectionObserver(([entry]) => {
      visible = !!entry?.isIntersecting
      previous = performance.now()
    })
    if (scene.value) observer.observe(scene.value)
  }
  timer = setInterval(() => {
    const now = performance.now()
    if (playing.value && visible && !document.hidden) {
      progress.value += Math.min(now - previous, 250)
      if (progress.value >= 6500) step(1)
    }
    previous = now
  }, 80)
  motion.addEventListener('change', stopForReducedMotion)
})
onBeforeUnmount(() => {
  clearInterval(timer)
  observer?.disconnect()
  motion.removeEventListener('change', stopForReducedMotion)
})
</script>

<template>
  <div ref="scene" class="sptl-demo" aria-label="任务栏歌词交互演示">
    <div class="sptl-demo-toolbar">
      <span><i></i><i></i><i></i></span>
      <span>YOUR DESKTOP / SPTL</span>
      <AudioLines :size="17" aria-hidden="true" />
    </div>
    <div class="sptl-demo-desktop">
      <div class="sptl-demo-record" aria-hidden="true">
        <div><AudioLines :size="42" /></div>
      </div>
      <p class="sptl-demo-motto">专注眼前，<br /><span>音乐在身边。</span></p>
      <div class="sptl-demo-track">
        <span>演示曲目</span><b>今天的旋律</b><span>SPTL · 示例歌词</span>
      </div>
      <div class="sptl-demo-panel" aria-live="off">
        <Grid2X2 class="sptl-demo-launcher" :size="20" aria-hidden="true" />
        <div class="sptl-demo-widget">
          <div class="sptl-demo-cover" aria-hidden="true"><AudioLines :size="22" /></div>
          <div class="sptl-demo-lyrics">
            <p class="sptl-demo-primary" :style="{ '--lyric-progress': highlight }">
              {{ current.text }}
            </p>
            <p>{{ layout === 'double' ? current.translation : '今天的旋律 · SPTL' }}</p>
          </div>
          <div class="sptl-demo-controls">
            <button type="button" @click="step(-1)" aria-label="上一句演示歌词" title="上一句">
              <SkipBack :size="16" />
            </button>
            <button
              type="button"
              @click="toggle"
              :aria-label="playing ? '暂停歌词演示' : '播放歌词演示'"
              :title="playing ? '暂停' : '播放'"
            >
              <Pause v-if="playing" :size="17" /><Play v-else :size="17" />
            </button>
            <button type="button" @click="step(1)" aria-label="下一句演示歌词" title="下一句">
              <SkipForward :size="16" />
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="sptl-demo-bottom">
      <SegmentedControl
        v-model="layout"
        :options="[
          { value: 'double', label: '双行歌词' },
          { value: 'single', label: '歌词 + 信息' },
        ]"
        label="演示歌词布局"
      />
      <span class="sptl-demo-time">{{ elapsed }} / 0:19</span>
    </div>
    <p class="sptl-demo-caption">试试切换布局、暂停或换一句。此处为歌词演示，不播放音频。</p>
  </div>
</template>
