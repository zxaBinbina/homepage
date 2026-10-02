<script setup lang="ts">
import { Moon, Sun } from 'lucide-vue-next'
import { useTheme } from '../composables/useTheme'
const { light, toggleTheme } = useTheme()
</script>
<template>
  <button
    class="icon-button theme-toggle"
    @click="toggleTheme"
    :aria-label="light ? '切换深色主题' : '切换浅色主题'"
    :title="light ? '切换深色主题' : '切换浅色主题'"
  >
    <Moon v-if="light" :size="17" aria-hidden="true" /><Sun v-else :size="17" aria-hidden="true" />
  </button>
</template>
