<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, RotateCcw, Undo2 } from 'lucide-vue-next'
import {
  moveNumbers,
  newNumberGame,
  numbersOver,
  type Direction,
  type NumberGame,
} from './twenty48'

const game = ref(newNumberGame())
const history = ref<NumberGame[]>([])
const boardElement = ref<HTMLElement>()
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

function move(direction: Direction) {
  const next = moveNumbers(game.value, direction)
  if (next === game.value) {
    feedback.value = '这个方向暂时无法移动，换个方向试试。'
    return
  }
  history.value.push(game.value)
  if (history.value.length > 100) history.value.shift()
  const gained = next.score - game.value.score
  game.value = next
  feedback.value = gained
    ? `合并成功，本步 +${gained} 分。`
    : '方块已移动，继续寻找可以合并的数字。'
}
function restart() {
  game.value = newNumberGame()
  history.value = []
  feedback.value = '新的一局，出发吧。'
}
function undo() {
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
  if (!event.isPrimary || event.button !== 0) return
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
          <button class="game-button" :disabled="!history.length" @click="undo">
            <Undo2 :size="16" aria-hidden="true" />撤销</button
          ><button class="game-button" @click="restart">
            <RotateCcw :size="16" aria-hidden="true" />重新开始
          </button>
        </div>
      </div>
      <div class="number-play" @keydown="onKey">
        <div
          ref="boardElement"
          class="number-board"
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
            class="number-tile"
            :data-level="value ? Math.min(11, Math.log2(value)) : 0"
            :aria-label="`第 ${Math.floor(index / 4) + 1} 行第 ${(index % 4) + 1} 列：${value || '空'}`"
          >
            <span :key="value">{{ value || '' }}</span>
          </div>
        </div>
        <div class="number-directions" role="group" aria-label="移动方向">
          <button
            v-for="direction in directions"
            :key="direction.id"
            class="game-button"
            :aria-label="direction.label"
            :title="direction.label"
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
