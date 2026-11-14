<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { ChevronDown, MessageSquare } from 'lucide-vue-next'
import CollapsePanel from '../components/CollapsePanel.vue'

const props = defineProps<{ open: boolean; paged: boolean; from: number }>()
const emit = defineEmits<{ 'update:open': [open: boolean]; settled: [] }>()
const details = ref<HTMLDetailsElement>()
const nativeOpen = ref(props.open)
const expanded = ref(props.open)
let change = 0

watch(
  () => [props.open, props.paged],
  async () => {
    const token = ++change
    if (props.paged) {
      nativeOpen.value = props.open
      expanded.value = props.open
      await nextTick()
      if (token === change) emit('settled')
    } else if (props.open) {
      nativeOpen.value = true
      await nextTick()
      if (token !== change) return
      void details.value?.offsetHeight
      expanded.value = true
    } else if (expanded.value) {
      expanded.value = false
    } else {
      // A rapid reversal can arrive before the opening transition starts.
      nativeOpen.value = false
      await nextTick()
      if (token === change) emit('settled')
    }
  },
)
function settle() {
  if (!props.open) nativeOpen.value = false
  emit('settled')
}
function onNativeToggle() {
  if (details.value && details.value.open !== nativeOpen.value)
    emit('update:open', details.value.open)
}
</script>

<template>
  <details
    ref="details"
    class="reader-author-note"
    :open="nativeOpen"
    :data-note-start="from"
    @toggle="onNativeToggle"
  >
    <summary :aria-expanded="open" @click.prevent="emit('update:open', !open)">
      <MessageSquare :size="17" aria-hidden="true" />
      <span>作者的话</span>
      <span class="reader-note-action">{{ open ? '收起' : '展开' }}</span>
      <ChevronDown
        class="reader-note-chevron"
        :class="{ 'is-open': open }"
        :size="17"
        aria-hidden="true"
      />
    </summary>
    <div v-if="paged" class="reader-note-content" :inert="!open"><slot /></div>
    <CollapsePanel v-else :open="expanded" @settled="settle">
      <div class="reader-note-content"><slot /></div>
    </CollapsePanel>
  </details>
</template>
