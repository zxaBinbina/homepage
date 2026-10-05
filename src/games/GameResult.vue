<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useGameMotion } from './useGameMotion'

const props = defineProps<{
  message: string
  tone?: 'success' | 'ended'
  noAnimation?: boolean
}>()
const element = ref<HTMLElement>()
const motion = useGameMotion(computed(() => !!props.noAnimation))
onMounted(() => {
  void motion.settle([
    motion.animate(element.value, [{ opacity: 0 }, { opacity: 1 }], { duration: 180 }),
  ])
})
</script>

<template>
  <div ref="element" class="game-result" role="status">
    <div class="game-result-content">
      <p class="game-status game-result-message" :class="tone && `is-${tone}`">
        {{ message }}
      </p>
      <slot />
    </div>
  </div>
</template>
