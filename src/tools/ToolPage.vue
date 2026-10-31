<script setup lang="ts">
import { computed } from 'vue'
import { usePageLoading } from '../composables/usePageLoading'
import { ArrowLeft, ShieldCheck } from 'lucide-vue-next'
import SiteFooter from '../components/SiteFooter.vue'
import AppToasts from './freemium/components/AppToasts.vue'
import { toolCatalog, type ToolId } from './catalog'
import { toolComponents } from './components'
const props = defineProps<{ id: ToolId }>()
const tool = computed(() => toolCatalog[props.id])
const { pending, resolved, failed } = usePageLoading()
function reload() {
  location.reload()
}
</script>
<template>
  <div class="tool-route">
    <main id="main" class="tool-main shell">
      <a class="tool-back" href="/tool"><ArrowLeft :size="16" aria-hidden="true" />全部工具</a>
      <header class="tool-heading">
        <p class="overline">TOOLBOX / {{ tool.label }}</p>
        <h1>{{ tool.name }}</h1>
        <p>{{ tool.description }}</p>
      </header>
      <div class="freemium-workbench">
        <div v-if="failed" class="tool-load-state" role="alert">
          <p>工具暂时未能加载，请重新加载后再试。</p>
          <button class="button button-primary" type="button" @click="reload">重新加载</button>
        </div>
        <Suspense v-else @pending="pending" @resolve="resolved">
          <component :is="toolComponents[id]" />
          <template #fallback><div class="tool-load-state" aria-busy="true"></div></template>
        </Suspense>
        <AppToasts />
      </div>
      <p class="tool-privacy">
        <ShieldCheck :size="15" aria-hidden="true" />{{
          id === 'generate-github-badges'
            ? '在本地生成引用；打开徽章链接时，内容会发送给对应徽章服务。'
            : '在浏览器内处理，输入不上传、不保存。'
        }}
      </p>
    </main>
    <SiteFooter />
  </div>
</template>
