<template>
  <span
    class="tool-icon"
    :style="{ '--tile': `var(--${color})`, '--s': `${size}px` }"
    aria-hidden="true"
  >
    <AppIcon :name="icon" :size="Math.round(size * 0.62)" :weight="2" />
  </span>
</template>

<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  icon: { type: String, required: true },
  color: { type: String, default: 'blue' },
  size: { type: Number, default: 28 },
})
</script>

<style scoped>
.tool-icon {
  display: inline-grid;
  place-items: center;
  flex: none;
  width: var(--s);
  height: var(--s);
  border-radius: 14px;
  color: var(--blue);
  background: color-mix(in srgb, var(--blue) 8%, transparent);
  border: 1px solid var(--border);
}
</style>
