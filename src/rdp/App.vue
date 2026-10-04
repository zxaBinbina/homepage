<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch } from 'vue'
import './style.css'
import ProjectFooter from './components/ProjectFooter.vue'
import OverviewPage from './components/OverviewPage.vue'
import WikiPage from './components/WikiPage.vue'
import DownloadsPage from './components/DownloadsPage.vue'
const props = defineProps<{ view: 'rdp' | 'wiki' | 'downloads' }>()
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
  document.querySelectorAll('.rdp-reveal').forEach((element) => revealObserver?.observe(element))
}
watch(() => props.view, observeReveals, { flush: 'post' })
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
  <Transition name="rdp-content" mode="out-in">
    <WikiPage v-if="view === 'wiki'" key="wiki-content" />
    <DownloadsPage v-else-if="view === 'downloads'" key="downloads-content" />
    <OverviewPage v-else key="overview-content" />
  </Transition>
  <ProjectFooter />
</template>
