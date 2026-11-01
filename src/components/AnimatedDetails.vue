<script setup lang="ts">
import { ref } from 'vue'
import CollapsePanel from './CollapsePanel.vue'

const details = ref<HTMLDetailsElement>()
const expanded = ref(false)
let nativeOpen = false

function toggle() {
  if (!details.value) return
  if (!expanded.value) {
    nativeOpen = true
    details.value.open = true
    // Expose the collapsed grid before changing its target height.
    void details.value.offsetHeight
  }
  expanded.value = !expanded.value
}
function settle(open: boolean) {
  if (!open && details.value) {
    nativeOpen = false
    details.value.open = false
  }
}
function onNativeToggle() {
  if (!details.value || details.value.open === nativeOpen) return
  // Preserve native opening, for example browser Find revealing a match.
  nativeOpen = details.value.open
  expanded.value = nativeOpen
}
</script>

<template>
  <details ref="details" @toggle="onNativeToggle">
    <summary :aria-expanded="expanded" @click.prevent="toggle"><slot name="summary" /></summary>
    <CollapsePanel :open="expanded" @settled="settle"><slot /></CollapsePanel>
  </details>
</template>
