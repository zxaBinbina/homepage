<script setup>
// Adapted from jaywcjlove/tools packages/css-easing-animation (MIT).
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import presets from './easing.json'
import ToolPage from '../freemium/components/ToolPage.vue'
import CodePane from '../freemium/components/CodePane.vue'
const choice = ref('easeInOutCubic')
const points = ref([0.65, 0, 0.35, 1])
const second = ref(0.8)
const effect = ref('translate')
const active = ref(false)
const svg = ref(null)
let dragging = null
let captured = null
let startPoints = null
const valid = computed(
  () =>
    points.value.every(Number.isFinite) &&
    points.value[0] >= 0 &&
    points.value[0] <= 1 &&
    points.value[2] >= 0 &&
    points.value[2] <= 1 &&
    second.value >= 0 &&
    second.value <= 5,
)
const curve = computed(() => `cubic-bezier(${points.value.join(', ')})`)
const output = computed(() =>
  valid.value
    ? `.block {\n  transition: ${effect.value === 'opacity' ? 'opacity' : 'transform'} ${second.value}s ${curve.value};\n}`
    : '',
)
const xy = (i) => ({ x: 30 + points.value[i * 2] * 240, y: 220 - points.value[i * 2 + 1] * 140 })
const path = computed(() => `M30 220 C${xy(0).x} ${xy(0).y}, ${xy(1).x} ${xy(1).y}, 270 80`)
function preset() {
  const entry = presets.find((p) => p.label === choice.value)
  if (entry) points.value = entry.point.split(',').map(Number)
}
function down(event, index) {
  if (event.button !== 0 || dragging !== null) return
  startPoints = [...points.value]
  dragging = index
  captured = event.currentTarget
  captured.setPointerCapture(event.pointerId)
}
function move(event) {
  if (dragging === null || !svg.value) return
  const box = svg.value.getBoundingClientRect()
  const x = ((event.clientX - box.left) * 300) / box.width
  const y = ((event.clientY - box.top) * 300) / box.height
  points.value[dragging * 2] = Math.round(Math.max(0, Math.min(1, (x - 30) / 240)) * 100) / 100
  points.value[dragging * 2 + 1] =
    Math.round(Math.max(-0.5, Math.min(1.5, (220 - y) / 140)) * 100) / 100
  choice.value = 'custom'
}
function end(event, cancel = false) {
  if (cancel && startPoints) points.value = startPoints
  dragging = null
  startPoints = null
  if (event?.pointerId !== undefined && captured?.hasPointerCapture(event.pointerId))
    captured.releasePointerCapture(event.pointerId)
  captured = null
}
function key(event, index) {
  const directions = {
    ArrowLeft: [-0.01, 0],
    ArrowRight: [0.01, 0],
    ArrowUp: [0, 0.01],
    ArrowDown: [0, -0.01],
  }
  const direction = directions[event.key]
  if (!direction) return
  event.preventDefault()
  points.value[index * 2] =
    Math.round(Math.max(0, Math.min(1, points.value[index * 2] + direction[0])) * 100) / 100
  points.value[index * 2 + 1] =
    Math.round(Math.max(-0.5, Math.min(1.5, points.value[index * 2 + 1] + direction[1])) * 100) /
    100
  choice.value = 'custom'
}
watch([points, second, effect], () => (active.value = false), { deep: true })
onBeforeUnmount(() => end(null, true))
</script>
<template>
  <ToolPage>
    <template #options
      ><label class="jay-field"
        >缓动预设<select v-model="choice" class="field" @change="preset">
          <option value="custom">自定义</option>
          <option v-for="p in presets" :key="p.label" :value="p.label">{{ p.label }}</option>
        </select></label
      ><label class="jay-field"
        >时长（秒）<input
          v-model.number="second"
          class="field"
          type="number"
          min="0"
          max="5"
          step="0.1" /></label
    ></template>
    <div class="split">
      <section class="jay-panel">
        <svg
          ref="svg"
          class="jay-bezier"
          viewBox="0 0 300 300"
          role="group"
          aria-label="贝塞尔曲线编辑器"
          @keydown.esc="end(null, true)"
        >
          <path d="M30 80V220H270V80Z M30 150H270 M150 80V220" class="jay-bezier-grid" />
          <path
            :d="`M30 220L${xy(0).x} ${xy(0).y} M270 80L${xy(1).x} ${xy(1).y}`"
            class="jay-bezier-handles"
          />
          <path :d="path" class="jay-bezier-line" />
          <circle
            v-for="i in [0, 1]"
            :key="i"
            :cx="xy(i).x"
            :cy="xy(i).y"
            r="12"
            tabindex="0"
            role="button"
            :aria-label="`控制点 ${i + 1}，方向键微调`"
            @pointerdown="down($event, i)"
            @pointermove="move"
            @pointerup="end($event)"
            @pointercancel="end($event, true)"
            @lostpointercapture="end($event)"
            @keydown="key($event, i)"
          />
        </svg>
        <div class="jay-form-grid">
          <label v-for="(name, i) in ['x1', 'y1', 'x2', 'y2']" :key="name" class="jay-field"
            >{{ name
            }}<input
              v-model.number="points[i]"
              class="field"
              type="number"
              :min="i % 2 ? -0.5 : 0"
              :max="i % 2 ? 1.5 : 1"
              step="0.01"
              @input="choice = 'custom'"
          /></label>
        </div>
      </section>
      <section class="jay-panel">
        <div class="jay-actions">
          <label class="jay-field"
            >预览效果<select v-model="effect" class="field">
              <option value="translate">位移</option>
              <option value="width">宽度</option>
              <option value="height">高度</option>
              <option value="opacity">透明度</option>
            </select></label
          ><button
            class="btn btn--prominent"
            :disabled="!valid"
            :aria-pressed="active"
            @click="active = !active"
          >
            {{ active ? '还原预览' : '播放预览' }}
          </button>
        </div>
        <div class="jay-easing-stage">
          <div
            class="jay-easing-block"
            :class="active ? `is-${effect}` : ''"
            :style="{ '--easing': curve, '--duration': `${second}s` }"
          ></div>
        </div>
        <p class="jay-note">拖动控制点，或用方向键和数值输入微调。跟随系统的减少动态效果设置。</p>
      </section>
    </div>
    <CodePane
      :model-value="output"
      :error="valid ? '' : '横坐标应在 0–1 之间，时长应在 0–5 秒之间。'"
      label="CSS"
      readonly
      download="easing.css"
    />
  </ToolPage>
</template>
