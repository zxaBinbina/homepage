<script setup lang="ts">
import type { Screenshot } from './screenshots'
defineProps<{ shot: Screenshot }>()
</script>

<template>
  <figure class="sptl-feature-photo">
    <a
      class="sptl-photo-viewport"
      :class="{ 'is-panel': shot.panel }"
      :href="shot.original || shot.src"
      target="_blank"
      rel="noopener noreferrer"
      :aria-label="`${shot.caption}，查看本机实拍原图（在新标签页打开）`"
    >
      <img
        :src="shot.src"
        :alt="`SPTL 本机实拍：${shot.caption}`"
        :width="shot.width"
        :height="shot.height"
        decoding="async"
      />
    </a>
    <figcaption>{{ shot.caption }}</figcaption>
  </figure>
</template>
