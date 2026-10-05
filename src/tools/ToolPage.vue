<script setup lang="ts">
import { computed } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import SiteFooter from '../components/SiteFooter.vue'
import { toolCatalog, type ToolId } from './catalog'
import TextTools from './components/TextTools.vue'
import TimestampTool from './components/TimestampTool.vue'
import UuidTool from './components/UuidTool.vue'

const props = defineProps<{ id: ToolId }>()
const tool = computed(() => toolCatalog[props.id])
</script>

<template>
  <div>
    <main id="main" class="tool-main shell">
      <a class="tool-back" href="/tool"><ArrowLeft :size="16" aria-hidden="true" />全部工具</a>
      <header class="tool-heading">
        <p class="overline">TOOLBOX / {{ tool.label }}</p>
        <h1>{{ tool.name }}</h1>
      </header>
      <TimestampTool v-if="id === 'timestamp'" />
      <UuidTool v-else-if="id === 'uuid'" />
      <TextTools v-else :id="id" />
      <p v-if="tool.hint" class="tool-hint">{{ tool.hint }}</p>
    </main>
    <SiteFooter />
  </div>
</template>
