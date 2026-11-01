<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import CodeBlock from './CodeBlock.vue'
import SegmentedControl from '../../components/SegmentedControl.vue'

const props = defineProps<{ items: { label: string; code: string; language: string }[] }>()
const active = ref(0)
const id = useId()
const options = computed(() =>
  props.items.map((item, index) => ({
    value: index,
    label: item.label,
    id: `${id}-tab-${index}`,
    controls: `${id}-panel`,
  })),
)
</script>

<template>
  <div class="gaze-code">
    <SegmentedControl
      v-model="active"
      :options="options"
      class="gaze-code-tabs"
      semantics="tabs"
      :label="`代码选项：${items.map((i) => i.label).join('、')}`"
      wrap
    />
    <CodeBlock
      :id="`${id}-panel`"
      role="tabpanel"
      :aria-labelledby="`${id}-tab-${active}`"
      tabindex="0"
      :code="items[active]?.code ?? ''"
      :language="items[active]?.language ?? 'text'"
      :label="items[active]?.label"
    />
  </div>
</template>
