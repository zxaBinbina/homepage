<script setup lang="ts">
import { ref } from 'vue'
import CodeBlock from './CodeBlock.vue'

defineProps<{ items: { label: string; code: string; language: string }[] }>()
const active = ref(0)
</script>

<template>
  <div class="gaze-code">
    <div
      class="gaze-code-tabs"
      role="tablist"
      :aria-label="`代码选项：${items.map((i) => i.label).join('、')}`"
    >
      <button
        v-for="(item, index) in items"
        :key="item.label"
        role="tab"
        :aria-selected="active === index"
        :tabindex="active === index ? 0 : -1"
        @click="active = index"
      >
        {{ item.label }}
      </button>
    </div>
    <CodeBlock
      :code="items[active]?.code ?? ''"
      :language="items[active]?.language ?? 'text'"
      :label="items[active]?.label"
    />
  </div>
</template>
