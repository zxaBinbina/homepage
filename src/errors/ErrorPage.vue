<script setup lang="ts">
import { computed } from 'vue'
import { ArrowRight, Box, Compass, Home, Mail, RefreshCw } from 'lucide-vue-next'
import SiteFooter from '../components/SiteFooter.vue'
import { errorCatalog, type ErrorPageName } from './catalog'

const props = defineProps<{ error: ErrorPageName }>()
const details = computed(() => errorCatalog[props.error])
function retry() {
  window.location.reload()
}
</script>

<template>
  <div class="error-page">
    <main id="main" class="error-main shell" tabindex="-1">
      <section class="error-card" aria-labelledby="error-title">
        <div class="error-art" aria-hidden="true">
          <div class="error-art-caption"><Box :size="16" /> 在代码与方块之间</div>
          <span class="error-code">{{ details.code }}</span>
          <div class="error-blocks">
            <span></span><span></span><span></span><span></span><span></span>
          </div>
          <span class="error-art-note">换个方向，继续探索。</span>
        </div>
        <div class="error-content">
          <p class="error-label">{{ details.code }} / {{ details.label }}</p>
          <h1 id="error-title">{{ details.title }}</h1>
          <p class="error-description">{{ details.description }}</p>
          <div class="error-actions">
            <a class="button primary" href="/"><Home :size="17" aria-hidden="true" />返回首页</a>
            <button v-if="details.retry" class="button secondary" type="button" @click="retry">
              <RefreshCw :size="17" aria-hidden="true" />重新加载
            </button>
            <a v-else class="button secondary" href="/project">
              看看作品<ArrowRight :size="17" aria-hidden="true" />
            </a>
          </div>
          <a class="error-contact" href="/#contact"><Mail :size="15" aria-hidden="true" />联系我</a>
        </div>
      </section>
      <nav class="error-explore" aria-label="继续探索">
        <span><Compass :size="17" aria-hidden="true" />还有这些地方可以逛逛</span>
        <a href="/tool">实用工具<ArrowRight :size="15" aria-hidden="true" /></a>
        <a href="/game">玩会儿游戏<ArrowRight :size="15" aria-hidden="true" /></a>
      </nav>
    </main>
    <SiteFooter />
  </div>
</template>
