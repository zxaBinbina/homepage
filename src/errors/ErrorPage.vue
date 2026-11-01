<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute } from 'vue-router'
import { ArrowLeft, ArrowRight, Box, Compass, Home, Mail, RefreshCw } from 'lucide-vue-next'
import SiteFooter from '../components/SiteFooter.vue'
import { errorCatalog, type ErrorPageName } from './catalog'

const props = defineProps<{ error: ErrorPageName }>()
const details = computed(() => errorCatalog[props.error])
const route = useRoute()
const page = ref<HTMLElement>()
const reloading = ref(false)
const canGoBack = ref(false)

function updateBackAvailability() {
  const navigation = (window as Window & { navigation?: { canGoBack?: boolean } }).navigation
  if (typeof navigation?.canGoBack === 'boolean') {
    // Only show a previous entry the browser can confirm; cross-origin history is opaque.
    canGoBack.value = navigation.canGoBack
    return
  }
  // Older browsers: a concrete route recorded by Vue Router is positive evidence.
  // Its numeric position and history.length are only estimates on an initial visit.
  const state = window.history.state
  canGoBack.value =
    state?.current === route.fullPath &&
    typeof state.back === 'string' &&
    state.back.startsWith('/')
}

watch(() => route.fullPath, updateBackAvailability, { immediate: true, flush: 'post' })
onMounted(() => window.addEventListener('pageshow', updateBackAvailability))
let retryId = 0
onBeforeUnmount(() => {
  retryId += 1
  window.removeEventListener('pageshow', updateBackAvailability)
})
onBeforeRouteLeave(() => {
  // Cancel before the destination bundle downloads, while this page is still mounted.
  retryId += 1
  reloading.value = false
})

async function retry() {
  if (reloading.value) return
  const currentRetry = ++retryId
  reloading.value = true
  await nextTick()
  // Root transitions bound the exit. Child entrance/problem animations may be paused.
  await Promise.allSettled(page.value?.getAnimations().map((animation) => animation.finished) ?? [])
  if (currentRetry === retryId) window.location.reload()
}

function goBack() {
  updateBackAvailability()
  if (canGoBack.value) window.history.back()
}
</script>

<template>
  <div ref="page" class="error-page" :class="{ 'is-reloading': reloading }" :inert="reloading">
    <main id="main" class="error-main shell" tabindex="-1">
      <section class="error-card" aria-labelledby="error-title">
        <div class="error-art" aria-hidden="true">
          <div class="error-art-caption"><Box :size="16" /> 在代码与方块之间</div>
          <span class="error-code">{{ details.code }}</span>
          <div class="error-blocks">
            <span v-for="block in 5" :key="block"><i></i></span>
          </div>
          <span class="error-art-note">换个方向，继续探索。</span>
        </div>
        <div class="error-content">
          <p class="error-label">{{ details.code }} / {{ details.label }}</p>
          <h1 id="error-title">{{ details.title }}</h1>
          <p class="error-description">{{ details.description }}</p>
          <div class="error-actions">
            <a class="button primary" href="/"><Home :size="17" aria-hidden="true" />返回首页</a>
            <button v-if="canGoBack" class="button secondary" type="button" @click="goBack">
              <ArrowLeft :size="17" aria-hidden="true" />返回上一页
            </button>
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
