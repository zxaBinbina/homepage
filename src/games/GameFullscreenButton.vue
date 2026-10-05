<script setup lang="ts">
import { inject } from 'vue'
import { Maximize2, Minimize2 } from 'lucide-vue-next'
import { gameFullscreenKey } from './fullscreen'

const fullscreen = inject(gameFullscreenKey)!
</script>

<template>
  <button
    class="game-button game-fullscreen-toggle"
    :aria-pressed="fullscreen.active.value"
    :aria-label="fullscreen.active.value ? '退出全屏' : '网页全屏'"
    :title="fullscreen.active.value ? '退出全屏（Esc）' : '网页全屏'"
    @click="fullscreen.toggle"
  >
    <Minimize2 v-if="fullscreen.active.value" :size="18" aria-hidden="true" />
    <Maximize2 v-else :size="18" aria-hidden="true" />
  </button>
</template>
