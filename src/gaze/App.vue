<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch } from 'vue'
import './style.css'
import SiteFooter from '../components/SiteFooter.vue'
import HomePage from './components/HomePage.vue'
import GuidePage from './components/GuidePage.vue'

const props = defineProps<{ guide: string | null }>()
const motion = matchMedia('(prefers-reduced-motion: reduce)')
let revealObserver: IntersectionObserver | undefined
const animations = new Set<Animation>()
function observeReveals() {
  revealObserver?.disconnect()
  animations.forEach((animation) => animation.cancel())
  animations.clear()
  if (motion.matches || !('IntersectionObserver' in window) || !Element.prototype.animate) return
  revealObserver = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue
        revealObserver?.unobserve(entry.target)
        // Content is visible by default; an unavailable animation never hides it.
        const animation = entry.target.animate(
          [
            { opacity: 0, translate: '0 20px' },
            { opacity: 1, translate: '0 0' },
          ],
          { duration: 650, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' },
        )
        animations.add(animation)
        animation.onfinish = () => animations.delete(animation)
      }
    },
    { threshold: 0.08 },
  )
  document.querySelectorAll('.gaze-reveal').forEach((element) => revealObserver?.observe(element))
}
// 根路由层把 Gaze 子站作为一个整体（key 'gaze'），站内页面切换由内部过渡完成。
watch(() => props.guide, observeReveals, { flush: 'post' })
onMounted(() => {
  observeReveals()
  motion.addEventListener('change', observeReveals)
})
onBeforeUnmount(() => {
  revealObserver?.disconnect()
  animations.forEach((animation) => animation.cancel())
  motion.removeEventListener('change', observeReveals)
})
</script>
<template>
  <Transition name="gaze-content" mode="out-in" @after-enter="observeReveals">
    <GuidePage v-if="guide" :key="`guide-${guide}`" :guide-id="guide" />
    <HomePage v-else key="gaze-home" />
  </Transition>
  <SiteFooter />
</template>
