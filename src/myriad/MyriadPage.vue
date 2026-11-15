<script setup lang="ts">
import { defineAsyncComponent, onBeforeUnmount, onMounted, ref } from 'vue'
import { ArrowRight, Box, Home, Monitor } from 'lucide-vue-next'
import SiteFooter from '../components/SiteFooter.vue'
import { usePageLoading } from '../composables/usePageLoading'

const viewport = matchMedia('(max-width: 760px)')
const mobile = ref(viewport.matches)
const updateViewport = () => (mobile.value = viewport.matches)
onMounted(() => viewport.addEventListener('change', updateViewport))
onBeforeUnmount(() => viewport.removeEventListener('change', updateViewport))
const loading = usePageLoading()
const Desktop = defineAsyncComponent(async () => {
  loading.pending()
  return (await import('./MyriadDesktop.vue')).default
})
</script>

<template>
  <div class="myriad-page" :class="{ 'error-page': mobile }">
    <main v-if="!mobile" id="main" class="myriad-main" tabindex="-1" aria-label="万象导航">
      <Desktop @ready="loading.resolved" />
    </main>
    <template v-else>
      <main id="main" class="error-main shell" tabindex="-1">
        <section class="error-card" aria-labelledby="myriad-mobile-title">
          <div class="error-art" aria-hidden="true">
            <div class="error-art-caption"><Box :size="16" />你的上网起点</div>
            <span class="error-code"><Monitor :size="100" /></span>
            <div class="error-blocks">
              <span v-for="block in 5" :key="block"><i /></span>
            </div>
            <span class="error-art-note">换个屏幕，再见万象。</span>
          </div>
          <div class="error-content">
            <p class="error-label">MYRIAD / 万象导航</p>
            <h1 id="myriad-mobile-title">抱歉，万象暂不支持手机</h1>
            <p class="error-description">
              请在电脑浏览器打开，使用快捷方式、搜索和小组件。这里的数据保存在当前浏览器。
            </p>
            <div class="error-actions">
              <a class="button primary" href="/"><Home :size="17" />返回首页</a>
              <a class="button secondary" href="/tool">看看工具<ArrowRight :size="17" /></a>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </template>
  </div>
</template>
