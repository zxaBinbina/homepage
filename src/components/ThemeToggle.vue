<script setup lang="ts">
import { computed } from 'vue'
import { Monitor, Moon, Sun } from 'lucide-vue-next'
import { useTheme } from '../composables/useTheme'
const { mode, nextMode, cycleTheme } = useTheme()
const labels = { dark: '深色模式', light: '浅色模式', auto: '自动模式（跟随系统）' }
const hint = computed(() => `当前为${labels[mode.value]}，点击切换${labels[nextMode.value]}`)
</script>
<template>
  <button
    class="icon-button theme-toggle"
    type="button"
    :data-mode="mode"
    @click="cycleTheme"
    :aria-label="hint"
    :title="hint"
  >
    <Monitor v-if="mode === 'auto'" :size="17" aria-hidden="true" />
    <Moon v-else-if="mode === 'dark'" :size="17" aria-hidden="true" />
    <Sun v-else :size="17" aria-hidden="true" />
  </button>
</template>
