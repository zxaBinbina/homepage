<script setup lang="ts">
import { AlertTriangle, ChevronRight, Flame, Info, Lightbulb, ShieldAlert } from 'lucide-vue-next'
import CodeBlock from './CodeBlock.vue'
import CodeGroup from './CodeGroup.vue'
import BlockList from './BlockList.vue'

type Block =
  | { type: 'html'; html: string }
  | { type: 'code'; code: string; language: string; label?: string }
  | { type: 'code-group'; items: { label: string; code: string; language: string }[] }
  | { type: 'admonition'; kind: string; title: string; blocks: Block[] }
  | { type: 'details'; title: string; blocks: Block[] }
  | { type: 'heading'; depth: number; id: string; html: string; text: string }

defineProps<{ blocks: Block[] }>()

const admonitionMeta: Record<string, { icon: typeof Info; label: string }> = {
  note: { icon: Info, label: '说明' },
  info: { icon: Info, label: '信息' },
  tip: { icon: Lightbulb, label: '提示' },
  important: { icon: ShieldAlert, label: '重要' },
  warning: { icon: AlertTriangle, label: '警告' },
  caution: { icon: AlertTriangle, label: '注意' },
  danger: { icon: Flame, label: '危险' },
}
function meta(kind: string) {
  return admonitionMeta[kind] ?? admonitionMeta.note!
}
</script>

<template>
  <template v-for="(block, index) in blocks" :key="index">
    <component
      :is="`h${block.depth}`"
      v-if="block.type === 'heading'"
      :id="block.id"
      class="gaze-sub-heading"
      tabindex="-1"
      v-html="block.html"
    ></component>
    <div v-else-if="block.type === 'html'" class="gaze-prose" v-html="block.html"></div>
    <CodeBlock
      v-else-if="block.type === 'code'"
      :code="block.code"
      :language="block.language"
      :label="block.label"
    />
    <CodeGroup v-else-if="block.type === 'code-group'" :items="block.items" />
    <div
      v-else-if="block.type === 'admonition'"
      class="gaze-admonition"
      :class="`gaze-admonition-${block.kind}`"
    >
      <p class="gaze-admonition-title">
        <component :is="meta(block.kind).icon" :size="15" aria-hidden="true" />{{
          block.title || meta(block.kind).label
        }}
      </p>
      <BlockList :blocks="block.blocks" />
    </div>
    <details v-else class="gaze-details">
      <summary>
        <ChevronRight :size="16" aria-hidden="true" />{{ block.title || '展开查看' }}
      </summary>
      <div class="gaze-details-body">
        <BlockList :blocks="block.blocks" />
      </div>
    </details>
  </template>
</template>
