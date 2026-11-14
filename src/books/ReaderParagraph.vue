<script setup lang="ts">
import { computed } from 'vue'
import { highlightText, inlineParts, type NoteRange } from './authorNotes'

const props = withDefaults(
  defineProps<{ text: string; number: number; highlight: string; notes?: NoteRange[] }>(),
  { notes: () => [] },
)
const parts = computed(() => inlineParts(props.text, props.notes))
</script>

<template>
  <p class="reader-paragraph" :data-paragraph="number" tabindex="-1">
    <span
      v-for="(part, n) in parts"
      :key="n"
      :class="{ 'reader-inline-note': part.note }"
      :title="part.note ? '作者注释' : undefined"
    >
      <template v-for="(fragment, position) in highlightText(part.text, highlight)" :key="position"
        ><mark v-if="fragment.match">{{ fragment.text }}</mark
        ><template v-else>{{ fragment.text }}</template></template
      >
    </span>
  </p>
</template>
