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
    <Transition name="theme-icon" mode="out-in">
      <Monitor v-if="mode === 'auto'" key="auto" :size="17" aria-hidden="true" />
      <Moon v-else-if="mode === 'dark'" key="dark" :size="17" aria-hidden="true" />
      <Sun v-else key="light" :size="17" aria-hidden="true" />
    </Transition>
  </button>
</template>
