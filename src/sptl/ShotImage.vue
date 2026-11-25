<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from '../composables/useTheme'
import type { Screenshot } from './screenshots'
const props = defineProps<{ shot: Screenshot }>()
const { light } = useTheme()
const current = computed(() => (light.value ? { ...props.shot, ...props.shot.light } : props.shot))
</script>

<template>
  <figure class="sptl-feature-photo">
    <div class="sptl-photo-viewport" :class="{ 'is-panel': current.panel }">
      <img
        :src="current.src"
        :alt="`SPTL 本机实拍：${current.caption}`"
        :width="current.width"
        :height="current.height"
        decoding="async"
      />
    </div>
    <figcaption>{{ current.caption }}</figcaption>
  </figure>
</template>
