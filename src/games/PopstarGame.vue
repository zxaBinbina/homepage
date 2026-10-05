<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import { ArrowRight, RotateCcw, Sparkles } from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import GameResult from './GameResult.vue'
import { useGameMotion } from './useGameMotion'
import { newPopstar, nextStarLevel, popStars, starGroup, starPoints, starTarget } from './popstar'

const game = ref(newPopstar()),
  selected = ref<number[]>([]),
  busy = ref(false),
  focusIndex = ref(90)
const boardElement = ref<HTMLElement>()
const motion = useGameMotion()
const colors = ['蓝色', '绿色', '黄色', '紫色', '红色']
const marks = ['●', '◆', '✦', '✿', '♥']
const tiles = computed(() =>
  game.value.board.flatMap((tile, index) => (tile ? [{ ...tile, index }] : [])),
)
const selectedSet = computed(() => new Set(selected.value))
const ended = computed(() => !busy.value && game.value.status !== 'playing')
let version = 0
function position(index: number) {
  return `translate(${(index % 10) * 100}%, ${Math.floor(index / 10) * 100}%)`
}
function focusCell(index = focusIndex.value) {
  const available = tiles.value.map((tile) => tile.index)
  focusIndex.value = available.includes(index)
    ? index
    : available.reduce(
        (best, cell) => (Math.abs(cell - index) < Math.abs(best - index) ? cell : best),
        available[0] ?? 90,
      )
  boardElement.value
    ?.querySelector<HTMLButtonElement>(`[data-index="${focusIndex.value}"]`)
    ?.focus({ preventScroll: true })
}
function choose(index: number) {
  if (busy.value || game.value.status !== 'playing') return
  focusIndex.value = index
  if (selectedSet.value.has(index)) {
    void remove()
    return
  }
  const group = starGroup(game.value.board, index)
  selected.value = group.length >= 2 ? group : []
}
async function remove() {
  if (busy.value || selected.value.length < 2 || game.value.status !== 'playing') return
  const next = popStars(game.value, selected.value[0]!)
  const previous = new Map(tiles.value.map((tile) => [tile.id, tile.index]))
  const current = ++version
  busy.value = true
  await nextTick()
  if (current !== version) return
  await motion.settle(
    Array.from(boardElement.value?.querySelectorAll('.is-selected .star-gem') || []).map(
      (element) =>
        motion.animate(
          element,
          [
            { opacity: 1, transform: 'scale(1)' },
            { opacity: 0, transform: 'scale(.2) rotate(18deg)' },
          ],
          { duration: 180, fill: 'both' },
        ),
    ),
  )
  if (current !== version) return
  selected.value = []
  game.value = next
  await nextTick()
  if (current !== version) return
  await motion.settle(
    Array.from(boardElement.value?.querySelectorAll<HTMLElement>('.star-cell') || []).map(
      (element) => {
        const index = Number(element.dataset.index),
          from = previous.get(Number(element.dataset.id))!
        if (from === index) return null
        // Percentages refer to the tile itself, so falling also works inside scaled fullscreen.
        return motion.animate(
          element,
          [{ transform: position(from) }, { transform: position(index) }],
          { duration: 240, fill: 'both' },
        )
      },
    ),
  )
  if (current !== version) return
  busy.value = false
  await nextTick()
  if (current !== version) return
  if (ended.value)
    boardElement.value
      ?.querySelector<HTMLButtonElement>('.game-result button')
      ?.focus({ preventScroll: true })
  else focusCell()
}
function restart() {
  version++
  motion.cancel()
  busy.value = false
  selected.value = []
  focusIndex.value = 90
  game.value = newPopstar()
}
async function nextLevel() {
  if (busy.value || game.value.status !== 'passed') return
  game.value = nextStarLevel(game.value)
  selected.value = []
  focusIndex.value = 90
  await nextTick()
  focusCell()
}
function onKey(event: KeyboardEvent) {
  if (
    event.altKey ||
    event.ctrlKey ||
    event.metaKey ||
    !(event.target instanceof Element) ||
    !event.target.closest('.star-cell')
  )
    return
  const steps: Record<string, number> = {
    ArrowLeft: -1,
    ArrowRight: 1,
    ArrowUp: -10,
    ArrowDown: 10,
  }
  if (event.key === 'Escape') {
    selected.value = []
    return
  }
  const step = steps[event.key]
  if (!step) return
  event.preventDefault()
  if (busy.value || game.value.status !== 'playing') return
  let next = focusIndex.value + step
  while (
    next >= 0 &&
    next < 100 &&
    (Math.abs(step) === 10 || Math.floor(next / 10) === Math.floor(focusIndex.value / 10))
  ) {
    if (game.value.board[next]) {
      focusCell(next)
      return
    }
    next += step
  }
}
onBeforeUnmount(() => {
  version++
})
</script>

<template>
  <div class="game-layout">
    <section class="game-surface popstar-surface" aria-label="消灭星星游戏" :aria-busy="busy">
      <div class="game-toolbar">
        <div class="game-stats">
          <div>
            <span>当前关卡</span><strong>{{ game.level }}</strong>
          </div>
          <div>
            <span>累计得分</span><strong>{{ game.score }}</strong>
          </div>
          <div>
            <span>目标分数</span><strong>{{ starTarget(game.level) }}</strong>
          </div>
        </div>
        <div class="game-actions">
          <button class="game-button" :disabled="busy || selected.length < 2" @click="remove">
            <Sparkles :size="16" aria-hidden="true" />{{
              selected.length
                ? `消除 ${selected.length} 颗 · +${starPoints(selected.length)}`
                : '消除选中'
            }}
          </button>
          <div class="game-restart-actions">
            <button class="game-button" @click="restart">
              <RotateCcw :size="16" aria-hidden="true" />重新开始</button
            ><GameFullscreenButton />
          </div>
        </div>
      </div>
      <div
        ref="boardElement"
        class="popstar-board"
        role="group"
        aria-label="星星棋盘，方向键选格，回车点选，再次回车消除"
        @keydown="onKey"
      >
        <button
          v-for="tile in tiles"
          :key="tile.id"
          class="star-cell"
          :class="{ 'is-selected': selectedSet.has(tile.index) }"
          :data-id="tile.id"
          :data-index="tile.index"
          :style="{ transform: position(tile.index) }"
          :tabindex="!ended && tile.index === focusIndex ? 0 : -1"
          :aria-label="`第 ${Math.floor(tile.index / 10) + 1} 行，第 ${(tile.index % 10) + 1} 列，${colors[tile.color]}星星`"
          :aria-pressed="selectedSet.has(tile.index)"
          :aria-disabled="busy || game.status !== 'playing'"
          @click="choose(tile.index)"
          @focus="focusIndex = tile.index"
        >
          <span class="star-gem" :data-color="tile.color" aria-hidden="true"
            ><span class="star-shape">★</span><small>{{ marks[tile.color] }}</small></span
          >
        </button>
        <GameResult
          v-if="ended"
          :tone="game.status === 'passed' ? 'success' : 'ended'"
          :message="
            game.status === 'passed'
              ? `第 ${game.level} 关完成！继续收集星星吧。`
              : '还差一点分数，再试一次吧。'
          "
        >
          <p class="popstar-summary">剩余 {{ tiles.length }} 颗 · 奖励 {{ game.bonus }} 分</p>
          <button v-if="game.status === 'passed'" class="game-button" @click="nextLevel">
            下一关<ArrowRight :size="16" aria-hidden="true" />
          </button>
          <button v-else class="game-button" @click="restart">再来一局</button>
        </GameResult>
      </div>
    </section>
  </div>
</template>
