<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { Camera, Check, ScanFace } from 'lucide-vue-next'

const steps = [
  { icon: 'camera', text: '等待摄像头…' },
  { icon: 'scan', text: '正在寻找面部…' },
  { icon: 'scan', text: '检测到面部，正在比对特征…' },
  { icon: 'scan', text: '活体检测通过。' },
  { icon: 'check', text: '认证成功，欢迎回来。' },
] as const
const step = ref(0)
const reduced = matchMedia('(prefers-reduced-motion: reduce)')
let timer: ReturnType<typeof setInterval> | undefined
function iconFor(name: string) {
  return name === 'camera' ? Camera : name === 'check' ? Check : ScanFace
}
onMounted(() => {
  if (reduced.matches) {
    step.value = steps.length - 1
    return
  }
  timer = setInterval(() => {
    step.value = (step.value + 1) % steps.length
  }, 1800)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div
    class="gaze-scan"
    :class="{ 'beam-on': !reduced.matches && step > 0 && step < steps.length - 1 }"
  >
    <div class="gaze-scan-stage">
      <div class="gaze-scan-face">
        <img src="/images/gaze.svg" alt="Gaze 图标" width="84" height="84" />
      </div>
      <div class="gaze-scan-beam" aria-hidden="true"></div>
    </div>
    <div class="gaze-scan-status" :class="{ success: step === steps.length - 1 }" role="status">
      <component :is="iconFor(steps[step].icon)" :size="17" aria-hidden="true" />
      <span>{{ steps[step].text }}</span>
      <div class="gaze-scan-dots" aria-hidden="true">
        <span v-for="(item, index) in steps" :key="item.text" :class="{ on: index <= step }"></span>
      </div>
    </div>
  </div>
</template>
