<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, provide, ref } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import SiteFooter from '../components/SiteFooter.vue'
import GameGuide from './GameGuide.vue'
import { gameCatalog, type GameId } from './catalog'
import { gameFullscreenKey } from './fullscreen'
import { useGameMotion } from './useGameMotion'
import { useGameFit } from './useGameFit'

const props = defineProps<{ id: GameId }>()
const game = computed(() => gameCatalog[props.id])
const components = {
  twenty48: defineAsyncComponent(() => import('./NumberGame.vue')),
  minesweeper: defineAsyncComponent(() => import('./MinesweeperGame.vue')),
  solitaire: defineAsyncComponent(() => import('./SolitaireGame.vue')),
  tetris: defineAsyncComponent(() => import('./TetrisGame.vue')),
  sudoku: defineAsyncComponent(() => import('./SudokuGame.vue')),
  xiangqi: defineAsyncComponent(() => import('./BoardGame.vue')),
  gomoku: defineAsyncComponent(() => import('./BoardGame.vue')),
  snake: defineAsyncComponent(() => import('./SnakeGame.vue')),
  popstar: defineAsyncComponent(() => import('./PopstarGame.vue')),
  huarongdao: defineAsyncComponent(() => import('./HuarongdaoGame.vue')),
  jump: defineAsyncComponent(() => import('./JumpGame.vue')),
}
const fullscreen = ref(false)
const fullscreenDialog = ref<HTMLDialogElement>()
const viewport = ref<HTMLElement>()
const fitFrame = ref<HTMLElement>()
const fitContent = ref<HTMLElement>()
const { scale, fit } = useGameFit(fullscreen, fitFrame, fitContent)
const placeholderHeight = ref(0)
const motion = useGameMotion()
let previousScroll = { left: 0, top: 0 }
let transition = 0
let leaving = false
function focusToggle() {
  viewport.value
    ?.querySelector<HTMLButtonElement>('.game-fullscreen-toggle')
    ?.focus({ preventScroll: true })
}
async function fade(element: HTMLElement | undefined, from: number, to: number, duration: number) {
  await motion.settle([
    motion.animate(element, [{ opacity: from }, { opacity: to }], { duration, fill: 'both' }),
  ])
}
async function toggleFullscreen() {
  if (leaving) return
  const current = ++transition
  const opacity = fullscreenDialog.value
    ? Number(getComputedStyle(fullscreenDialog.value).opacity)
    : 1
  motion.cancel()
  if (fullscreen.value) {
    leaving = true
    await fade(fullscreenDialog.value, opacity, 0, 140)
    if (current !== transition) return
    fullscreen.value = false
    await nextTick()
    if (current !== transition) return
    fullscreenDialog.value?.close()
    document.documentElement.classList.remove('game-fullscreen-open')
    window.scrollTo({ ...previousScroll, behavior: 'instant' })
    leaving = false
    focusToggle()
    await fade(viewport.value, 0, 1, 120)
  } else {
    previousScroll = { left: window.scrollX, top: window.scrollY }
    // Keep the document canvas and footer stationary while Teleport moves the game.
    placeholderHeight.value = viewport.value?.getBoundingClientRect().height ?? 0
    fullscreenDialog.value?.showModal()
    fullscreen.value = true
    document.documentElement.classList.add('game-fullscreen-open')
    await nextTick()
    if (current !== transition) return
    fit()
    focusToggle()
    await fade(fullscreenDialog.value, 0, 1, 180)
  }
}
provide(gameFullscreenKey, {
  active: fullscreen,
  toggle: toggleFullscreen,
  scale,
  fit,
  overlay: fullscreenDialog,
})
function closeFullscreen() {
  if (fullscreen.value) void toggleFullscreen()
}
onBeforeUnmount(() => {
  transition++
  fullscreen.value = false
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
      </header>
      <div :style="{ minHeight: fullscreen ? `${placeholderHeight}px` : undefined }">
        <Teleport :to="fullscreenDialog || 'body'" :disabled="!fullscreen">
          <section
            ref="viewport"
            class="game-viewport"
            :class="{ 'is-fullscreen': fullscreen }"
            :style="{
              '--game-fit-min':
                id === 'solitaire' ? '560px' : id === 'minesweeper' ? '440px' : '360px',
              '--game-fit-max': id === 'solitaire' ? '1100px' : '760px',
            }"
            :aria-label="game.name"
          >
            <div ref="fitFrame" class="game-play-content">
              <div ref="fitContent" class="game-fit-content">
                <GameGuide :id="id" />
                <component
                  :is="components[id]"
                  :key="id"
                  v-bind="id === 'xiangqi' || id === 'gomoku' ? { kind: id } : {}"
                />
              </div>
            </div>
          </section>
        </Teleport>
      </div>
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
