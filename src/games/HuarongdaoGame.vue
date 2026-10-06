<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import { RotateCcw, Undo2 } from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import GameResult from './GameResult.vue'
import { useGameMotion } from './useGameMotion'
import {
  moveSliding,
  newSliding,
  slidingNeighbors,
  slidingSolved,
  type SlidingSize,
  type SlidingState,
} from './huarongdao'

const size = ref<SlidingSize>(4),
  game = ref(newSliding()),
  busy = ref(false)
const history = ref<SlidingState[]>([]),
  boardElement = ref<HTMLElement>()
const focused = ref(game.value.board.find((tile) => tile !== 0)!)
const motion = useGameMotion()
const won = computed(() => slidingSolved(game.value.board))
const correct = computed(() => game.value.board.filter((tile, i) => tile && tile === i + 1).length)
const movable = computed(() =>
  slidingNeighbors(game.value.board.indexOf(0), game.value.size).map((i) => game.value.board[i]),
)
const tiles = computed(() =>
  game.value.board.flatMap((tile, index) => (tile ? [{ tile, index }] : [])),
)
let version = 0
function position(index: number) {
  return `translate(${(index % game.value.size) * 100}%, ${Math.floor(index / game.value.size) * 100}%)`
}
async function move(tile: number) {
  if (busy.value) return
  const before = game.value,
    after = moveSliding(before, tile)
  if (after === before) return
  busy.value = true
  const current = ++version,
    to = before.board.indexOf(0),
    from = before.board.indexOf(tile)
  await motion.settle([
    motion.animate(
      boardElement.value?.querySelector(`[data-tile="${tile}"]`),
      [{ transform: position(from) }, { transform: position(to) }],
      { duration: 200, fill: 'both' },
    ),
  ])
  if (current !== version) return
  history.value = [...history.value.slice(-99), before]
  game.value = after
  busy.value = false
  focused.value = tile
  await nextTick()
  if (current === version)
    boardElement.value
      ?.querySelector<HTMLButtonElement>(`[data-tile="${tile}"]`)
      ?.focus({ preventScroll: true })
}
function undo() {
  if (!history.value.length && !busy.value) return
  // During a slide, cancel that uncommitted move without also undoing the previous one.
  version++
  motion.cancel()
  if (!busy.value) game.value = history.value.pop()!
  busy.value = false
}
function restart() {
  version++
  motion.cancel()
  busy.value = false
  history.value = []
  game.value = newSliding(size.value)
  focused.value = game.value.board.find((tile) => tile !== 0)!
}
function onKey(event: KeyboardEvent) {
  if (event.altKey || event.ctrlKey || event.metaKey) return
  const step = (
    {
      ArrowLeft: -1,
      ArrowRight: 1,
      ArrowUp: -game.value.size,
      ArrowDown: game.value.size,
    } as Record<string, number>
  )[event.key]
  if (!step) return
  event.preventDefault()
  if (busy.value || won.value) return
  const index = game.value.board.indexOf(focused.value)
  let next = index + step
  while (
    next >= 0 &&
    next < game.value.board.length &&
    (Math.abs(step) !== 1 ||
      Math.floor(next / game.value.size) === Math.floor(index / game.value.size))
  ) {
    const tile = game.value.board[next]
    if (tile) {
      focused.value = tile
      boardElement.value
        ?.querySelector<HTMLButtonElement>(`[data-tile="${tile}"]`)
        ?.focus({ preventScroll: true })
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
    <section class="game-surface sliding-surface" aria-label="华容道游戏" :aria-busy="busy">
      <div class="game-toolbar">
        <div class="game-stats">
          <div>
            <span>移动步数</span><strong>{{ game.moves }}</strong>
          </div>
          <div>
            <span>已归位</span
            ><strong
              >{{ correct }} <small>/ {{ size * size - 1 }}</small></strong
            >
          </div>
        </div>
        <div class="game-actions">
          <label class="game-select"
            >棋盘大小<select v-model.number="size" @change="restart">
              <option :value="3">3 × 3</option>
              <option :value="4">4 × 4</option>
              <option :value="5">5 × 5</option>
            </select></label
          >
          <button class="game-button" :disabled="!history.length && !busy" @click="undo">
            <Undo2 :size="16" aria-hidden="true" />撤销
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
        class="sliding-board"
        :style="{ '--sliding-size': size }"
        role="group"
        aria-label="华容道棋盘，方向键选方块，回车或空格移动"
        @keydown="onKey"
      >
        <span
          class="sliding-empty"
          :style="{ transform: position(game.board.indexOf(0)) }"
          aria-hidden="true"
        ></span>
        <button
          v-for="{ tile, index } in tiles"
          :key="tile"
          class="sliding-tile"
          :class="{ 'is-movable': movable.includes(tile), 'is-correct': tile === index + 1 }"
          :data-tile="tile"
          :data-index="index"
          :style="{ transform: position(index) }"
          :tabindex="focused === tile && !won ? 0 : -1"
          :aria-disabled="busy || won || !movable.includes(tile)"
          :aria-label="`数字 ${tile}，第 ${Math.floor(index / size) + 1} 行第 ${(index % size) + 1} 列${movable.includes(tile) ? '，可移动' : ''}`"
          @focus="focused = tile"
          @click="move(tile)"
        >
          <span>{{ tile }}<i v-if="tile === index + 1" aria-hidden="true"></i></span>
        </button>
        <GameResult
          v-if="won && !busy"
          :message="`全部归位！你用了 ${game.moves} 步。`"
          tone="success"
        />
      </div>
    </section>
  </div>
</template>
