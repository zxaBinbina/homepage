<script setup>
defineProps({ fill: Boolean })
</script>
<template>
  <div class="tool-page" :class="{ 'tool-page--fill': fill }">
    <div v-if="$slots.actions" class="tool-page__actions"><slot name="actions" /></div>
    <div v-if="$slots.options" class="tool-page__options" role="group" aria-label="工具选项">
      <slot name="options" />
    </div>
    <div class="tool-page__body"><slot /></div>
  </div>
</template>
