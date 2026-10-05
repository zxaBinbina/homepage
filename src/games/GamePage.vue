<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import SiteFooter from '../components/SiteFooter.vue'
import { gameCatalog, type GameId } from './catalog'

const props = defineProps<{ id: GameId }>()
const game = computed(() => gameCatalog[props.id])
const components = {
  twenty48: defineAsyncComponent(() => import('./NumberGame.vue')),
  minesweeper: defineAsyncComponent(() => import('./MinesweeperGame.vue')),
  solitaire: defineAsyncComponent(() => import('./SolitaireGame.vue')),
}
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
      <component :is="components[id]" :key="id" />
      <p class="games-note">游戏在当前页面中进行，离开或刷新会重新开局。</p>
    </main>
    <SiteFooter />
  </div>
</template>
