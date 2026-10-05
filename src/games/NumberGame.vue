<script setup lang="ts">
import GameFullscreenButton from './GameFullscreenButton.vue'
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import { useGameMotion } from './useGameMotion'
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, RotateCcw, Undo2 } from 'lucide-vue-next'
import {
  moveNumbers,
  newNumberGame,
  numbersOver,
  traceSlide,
  type Direction,
  type NumberGame,
} from './twenty48'

const game = ref(newNumberGame())
const history = ref<NumberGame[]>([])
const boardElement = ref<HTMLElement>()
const noAnimation = ref(false)
const motion = useGameMotion(noAnimation)
const animationsOff = computed({
  get: () => noAnimation.value || motion.reduced.value,
  set: (value: boolean) => {
    noAnimation.value = value
  },
})
const busy = ref(false)
const sliding = ref(false)
const flights = ref<
  { from: number; value: number; x: number; y: number; size: number; dx: number; dy: number }[]
>([])
let turn = 0
function stopMotion() {
  turn++
  motion.cancel()
  busy.value = false
  sliding.value = false
  flights.value = []
  gesture = null
}
onBeforeUnmount(stopMotion)
const over = computed(() => numbersOver(game.value.board))
const largest = computed(() => Math.max(...game.value.board))
const feedback = ref('点击棋盘后使用方向键，或直接在棋盘上滑动。')
const status = computed(() =>
  over.value
    ? '没有可移动的方块了。试试撤销，或重新开一局。'
    : largest.value >= 2048
      ? '合成 2048 了！你也可以继续挑战更大的数字。'
      : feedback.value,
)
const directions = [
  { id: 'up', label: '向上移动', icon: ArrowUp },
  { id: 'left', label: '向左移动', icon: ArrowLeft },
  { id: 'down', label: '向下移动', icon: ArrowDown },
  { id: 'right', label: '向右移动', icon: ArrowRight },
] as const

async function move(direction: Direction) {
  if (busy.value) return
  const trace = traceSlide(game.value.board, direction)
  const next = moveNumbers(game.value, direction)
  if (next === game.value) {
    feedback.value = '这个方向暂时无法移动，换个方向试试。'
    return
  }
  history.value.push(game.value)
  if (history.value.length > 100) history.value.shift()
  const gained = next.score - game.value.score
  const current = ++turn
  busy.value = true
  const board = boardElement.value
  if (board && !animationsOff.value && !document.hidden) {
    const origin = board.getBoundingClientRect()
    const cells = Array.from(board.querySelectorAll<HTMLElement>('.number-tile')).map((cell) =>
      cell.getBoundingClientRect(),
    )
    flights.value = trace.movements.map((tile) => {
      const from = cells[tile.from]!,
        to = cells[tile.to]!
      return {
        from: tile.from,
        value: tile.value,
        x: from.left - origin.left - board.clientLeft,
        y: from.top - origin.top - board.clientTop,
        size: from.width,
        dx: to.left - from.left,
        dy: to.top - from.top,
      }
    })
    sliding.value = true
    await nextTick()
    if (current !== turn) return
    await motion.settle(
      Array.from(board.querySelectorAll('.number-flight')).map((element, index) => {
        const tile = flights.value[index]!
        return motion.animate(
          element,
          [
            { transform: 'translate(0, 0)' },
            { transform: `translate(${tile.dx}px, ${tile.dy}px)` },
          ],
          { duration: 140, fill: 'both' },
        )
      }),
    )
    if (current !== turn) return
  }
  game.value = next
  sliding.value = false
  flights.value = []
  feedback.value = gained
    ? `合并成功，本步 +${gained} 分。`
    : '方块已移动，继续寻找可以合并的数字。'
  await nextTick()
  if (current !== turn) return
  const cells = board?.querySelectorAll('.number-tile')
  const spawned = next.board.findIndex((value, index) => value && !trace.board[index])
  await motion.settle([
    ...trace.merges.map((index) =>
      motion.animate(
        cells?.[index],
        [
          { transform: 'scale(1)' },
          { transform: 'scale(1.16)', offset: 0.45 },
          { transform: 'scale(1)' },
        ],
        { duration: 90 },
      ),
    ),
    motion.animate(
      cells?.[spawned],
      [
        { transform: 'scale(.3)', opacity: 0 },
        { transform: 'scale(1)', opacity: 1 },
      ],
      { duration: 90 },
    ),
  ])
  if (current === turn) busy.value = false
}
function restart() {
  stopMotion()
  game.value = newNumberGame()
  history.value = []
  feedback.value = '新的一局，出发吧。'
}
function undo() {
  if (busy.value) return
  const previous = history.value.pop()
  if (previous) {
    game.value = previous
    feedback.value = '已撤销上一步。'
  }
}
function onKey(event: KeyboardEvent) {
  if (event.ctrlKey || event.metaKey || event.altKey) return
  const map: Record<string, Direction> = {
    ArrowUp: 'up',
    ArrowDown: 'down',
    ArrowLeft: 'left',
    ArrowRight: 'right',
    w: 'up',
    s: 'down',
    a: 'left',
    d: 'right',
  }
  const direction = map[event.key]
  if (direction) {
    event.preventDefault()
    move(direction)
  }
}
let gesture: { x: number; y: number; id: number } | null = null
function pointerStart(event: PointerEvent) {
  if (busy.value || !event.isPrimary || event.button !== 0) return
  gesture = { x: event.clientX, y: event.clientY, id: event.pointerId }
  boardElement.value?.setPointerCapture(event.pointerId)
  boardElement.value?.focus({ preventScroll: true })
}
function pointerEnd(event: PointerEvent) {
  if (!gesture || gesture.id !== event.pointerId) return
  const dx = event.clientX - gesture.x,
    dy = event.clientY - gesture.y
  gesture = null
  if (Math.max(Math.abs(dx), Math.abs(dy)) < 24) return
  move(Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : dy > 0 ? 'down' : 'up')
}
</script>

<template>
  <div class="game-layout">
    <section class="game-surface number-surface" aria-label="2048 游戏">
      <div class="game-toolbar">
        <div class="game-stats">
          <div>
            <span>本局得分</span><strong>{{ game.score }}</strong>
          </div>
          <div>
            <span>最大方块</span><strong>{{ largest }}</strong>
          </div>
        </div>
        <div class="game-actions">
          <button class="game-button" :disabled="busy || !history.length" @click="undo">
            <Undo2 :size="16" aria-hidden="true" />撤销
          </button>
          <div class="game-restart-actions">
            <button class="game-button" @click="restart">
              <RotateCcw :size="16" aria-hidden="true" />重新开始</button
            ><GameFullscreenButton />
          </div>
          <label class="number-motion-toggle"
            ><input
              v-model="animationsOff"
              type="checkbox"
              :disabled="motion.reduced.value"
            />无动画<span v-if="motion.reduced.value">（系统设置）</span></label
          >
        </div>
      </div>
      <div class="number-play" @keydown="onKey">
        <div
          ref="boardElement"
          class="number-board"
          :class="{ 'is-sliding': sliding }"
          :aria-busy="busy"
          tabindex="0"
          role="group"
          aria-label="2048 棋盘，使用方向键或 WASD 移动"
          aria-describedby="number-status"
          @pointerdown="pointerStart"
          @pointerup="pointerEnd"
          @pointercancel="gesture = null"
          @lostpointercapture="gesture = null"
        >
          <div
            v-for="(value, index) in game.board"
            :key="index"
            class="number-tile number-face"
            :data-level="value ? Math.min(11, Math.log2(value)) : 0"
            :aria-label="`第 ${Math.floor(index / 4) + 1} 行第 ${(index % 4) + 1} 列：${value || '空'}`"
          >
            <span :key="value">{{ value || '' }}</span>
          </div>
          <div v-if="sliding" class="number-flight-layer" aria-hidden="true">
            <div
              v-for="tile in flights"
              :key="tile.from"
              class="number-flight number-face"
              :data-level="Math.min(11, Math.log2(tile.value))"
              :style="{
                left: `${tile.x}px`,
                top: `${tile.y}px`,
                width: `${tile.size}px`,
                height: `${tile.size}px`,
              }"
            >
              {{ tile.value }}
            </div>
          </div>
        </div>
        <div class="number-directions" role="group" aria-label="移动方向">
          <button
            v-for="direction in directions"
            :key="direction.id"
            class="game-button"
            :aria-label="direction.label"
            :title="direction.label"
            :disabled="busy"
            @click="move(direction.id)"
          >
            <component :is="direction.icon" :size="20" aria-hidden="true" />
          </button>
        </div>
      </div>
      <p
        id="number-status"
        class="game-status"
        :class="{ 'is-success': largest >= 2048, 'is-ended': over }"
        role="status"
      >
        {{ status }}
      </p>
    </section>
    <aside class="game-guide">
      <p class="overline">HOW TO PLAY</p>
      <h2>让相同的数字相遇。</h2>
      <ol>
        <li>向一个方向移动，所有方块都会滑到那一侧。</li>
        <li>相同数字碰在一起就会合并，每步每块只合并一次。</li>
        <li>合成 2048 即达成目标，也可以继续向更大数字挑战。</li>
      </ol>
      <p>电脑：点击棋盘后按方向键或 WASD。手机：在棋盘上滑动，也可以使用下方方向按钮。</p>
      <p>走错一步也没关系，最多可以撤销最近 100 步。</p>
    </aside>
  </div>
</template>
