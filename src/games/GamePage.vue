<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, provide, ref } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import SiteFooter from '../components/SiteFooter.vue'
import { gameCatalog, type GameId } from './catalog'
import { gameFullscreenKey } from './fullscreen'

const props = defineProps<{ id: GameId }>()
const game = computed(() => gameCatalog[props.id])
const components = {
  twenty48: defineAsyncComponent(() => import('./NumberGame.vue')),
  minesweeper: defineAsyncComponent(() => import('./MinesweeperGame.vue')),
  solitaire: defineAsyncComponent(() => import('./SolitaireGame.vue')),
}
const fullscreen = ref(false)
const fullscreenDialog = ref<HTMLDialogElement>()
const viewport = ref<HTMLElement>()
async function toggleFullscreen() {
  if (fullscreen.value) {
    fullscreen.value = false
    await nextTick()
    fullscreenDialog.value?.close()
    document.documentElement.classList.remove('game-fullscreen-open')
  } else {
    fullscreenDialog.value?.showModal()
    fullscreen.value = true
    document.documentElement.classList.add('game-fullscreen-open')
    await nextTick()
  }
  // Existing game instances move with Teleport, preserving the current game and undo history.
  viewport.value
    ?.querySelector<HTMLButtonElement>('.game-fullscreen-toggle')
    ?.focus({ preventScroll: true })
}
provide(gameFullscreenKey, { active: fullscreen, toggle: toggleFullscreen })
function closeFullscreen() {
  if (fullscreen.value) void toggleFullscreen()
}
onBeforeUnmount(() => {
  fullscreenDialog.value?.close()
  document.documentElement.classList.remove('game-fullscreen-open')
})
</script>

<template>
  <div>
    <main id="main" class="game-main shell" :class="`game-page-${id}`">
      <a href="/game" class="tool-back"><ArrowLeft :size="16" aria-hidden="true" />全部游戏</a>
      <header class="game-heading">
        <div>
          <p class="overline">{{ game.label }}</p>
          <h1>{{ game.name }}</h1>
        </div>
        <p>{{ game.controls }}</p>
      </header>
      <Teleport :to="fullscreenDialog || 'body'" :disabled="!fullscreen">
        <section
          ref="viewport"
          class="game-viewport"
          :class="{ 'is-fullscreen': fullscreen }"
          :aria-label="game.name"
        >
          <div class="game-play-content">
            <component :is="components[id]" :key="id" />
          </div>
        </section>
      </Teleport>
      <p class="games-note">游戏在当前页面中进行，离开或刷新会重新开局。</p>
    </main>
    <SiteFooter />
    <dialog
      ref="fullscreenDialog"
      class="game-fullscreen-dialog"
      :aria-label="`${game.name}，网页全屏`"
      @cancel.prevent="closeFullscreen"
      @close="closeFullscreen"
    ></dialog>
  </div>
</template>
