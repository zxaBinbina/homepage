<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import {
  Apple,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Pause,
  Play,
  RotateCcw,
} from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import GameResult from './GameResult.vue'
import { useGameMotion } from './useGameMotion'
import {
  canTurn,
  newSnake,
  snakeInterval,
  stepSnake,
  type SnakeDirection,
  type SnakePoint,
} from './snake'

const game = ref(newSnake()),
  speed = ref(1),
  started = ref(false),
  paused = ref(false)
const boardElement = ref<HTMLElement>()
const motion = useGameMotion()
const playing = computed(() => started.value && !paused.value && game.value.status === 'playing')
const interval = computed(() => snakeInterval(game.value.score, speed.value))
const controls = [
  { direction: 'up', name: '向上', icon: ArrowUp },
  { direction: 'left', name: '向左', icon: ArrowLeft },
  { direction: 'down', name: '向下', icon: ArrowDown },
  { direction: 'right', name: '向右', icon: ArrowRight },
] as const
let timer: ReturnType<typeof setTimeout> | undefined
let turns: SnakeDirection[] = [],
  version = 0
let pointer: { id: number; x: number; y: number } | null = null
function stopTimer() {
  clearTimeout(timer)
  timer = undefined
}
function schedule() {
  stopTimer()
  if (playing.value) timer = setTimeout(tick, interval.value)
}
async function tick() {
  if (!playing.value) return
  const current = version,
    previousScore = game.value.score
  game.value = stepSnake(game.value, turns.shift() || game.value.direction)
  schedule()
  if (game.value.score !== previousScore) {
    await nextTick()
    if (current !== version) return
    void motion.settle([
      motion.animate(
        boardElement.value?.querySelector('.snake-food svg'),
        [
          { transform: 'scale(.3)', opacity: 0 },
          { transform: 'scale(1)', opacity: 1 },
        ],
        { duration: 180 },
      ),
    ])
  }
}
function turn(direction: SnakeDirection) {
  if (!playing.value || turns.length >= 2) return
  const from = turns.at(-1) || game.value.direction
  if (canTurn(from, direction)) turns.push(direction)
}
function togglePause() {
  if (game.value.status !== 'playing') return
  if (!started.value) {
    started.value = true
    paused.value = false
  } else paused.value = !paused.value
  turns = []
  schedule()
  boardElement.value?.focus({ preventScroll: true })
}
function restart() {
  version++
  stopTimer()
  motion.cancel()
  cancelPointer()
  turns = []
  game.value = newSnake()
  started.value = false
  paused.value = false
}
function pauseAway() {
  if (playing.value) {
    paused.value = true
    stopTimer()
    turns = []
  }
  cancelPointer()
}
function visibility() {
  if (document.hidden) pauseAway()
}
window.addEventListener('blur', pauseAway)
document.addEventListener('visibilitychange', visibility)
onBeforeUnmount(() => {
  version++
  stopTimer()
  cancelPointer()
  window.removeEventListener('blur', pauseAway)
  document.removeEventListener('visibilitychange', visibility)
})
function onKey(event: KeyboardEvent) {
  if (event.altKey || event.ctrlKey || event.metaKey) return
  const key = event.key.toLowerCase()
  const directions: Record<string, SnakeDirection> = {
    arrowup: 'up',
    w: 'up',
    arrowdown: 'down',
    s: 'down',
    arrowleft: 'left',
    a: 'left',
    arrowright: 'right',
    d: 'right',
  }
  if (directions[key]) {
    event.preventDefault()
    if (!event.repeat) turn(directions[key])
  } else if (key === 'p' || (key === ' ' && event.target === boardElement.value)) {
    event.preventDefault()
    if (!event.repeat) togglePause()
  }
}
function pointerDown(event: PointerEvent) {
  if (!playing.value || !event.isPrimary || event.button !== 0) return
  pointer = { id: event.pointerId, x: event.clientX, y: event.clientY }
  boardElement.value?.setPointerCapture(event.pointerId)
  boardElement.value?.focus({ preventScroll: true })
}
function cancelPointer() {
  if (pointer && boardElement.value?.hasPointerCapture(pointer.id))
    boardElement.value.releasePointerCapture(pointer.id)
  pointer = null
}
function pointerUp(event: PointerEvent) {
  if (!pointer || event.pointerId !== pointer.id) return
  const dx = event.clientX - pointer.x,
    dy = event.clientY - pointer.y
  cancelPointer()
  if (Math.max(Math.abs(dx), Math.abs(dy)) < 12) return
  turn(Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : dy > 0 ? 'down' : 'up')
}
function position(point: SnakePoint) {
  return { transform: `translate(${point.x * 100}%, ${point.y * 100}%)` }
}
</script>

<template>
  <div class="game-layout">
    <section class="game-surface snake-surface" aria-label="贪吃蛇游戏">
      <div class="game-toolbar">
        <div class="game-stats">
          <div>
            <span>本局得分</span><strong>{{ game.score }}</strong>
          </div>
          <div>
            <span>蛇身长度</span><strong>{{ game.body.length }}</strong>
          </div>
        </div>
        <div class="game-actions">
          <label class="game-select"
            >起始速度<select v-model.number="speed" @change="restart">
              <option :value="0">舒缓</option>
              <option :value="1">标准</option>
              <option :value="2">挑战</option>
            </select></label
          >
          <button class="game-button" :disabled="game.status !== 'playing'" @click="togglePause">
            <Pause v-if="started && !paused" :size="16" aria-hidden="true" /><Play
              v-else
              :size="16"
              aria-hidden="true"
            />
            {{ !started ? '开始游戏' : paused ? '继续游戏' : '暂停' }}
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
        class="snake-board"
        :class="{ 'is-still': !playing || motion.reduced.value }"
        :style="{ '--snake-step': `${Math.min(interval - 15, 110)}ms` }"
        tabindex="0"
        role="group"
        aria-label="贪吃蛇棋盘，方向键或 WASD 转向，P 或空格暂停"
        @keydown="onKey"
        @pointerdown="pointerDown"
        @pointerup="pointerUp"
        @pointercancel="cancelPointer"
        @lostpointercapture="cancelPointer"
      >
        <span
          v-for="(point, i) in game.body"
          :key="i"
          class="snake-segment"
          :class="{ 'is-head': i === 0 }"
          :data-direction="game.direction"
          :style="position(point)"
          aria-hidden="true"
          ><i></i
        ></span>
        <span v-if="game.food" class="snake-food" :style="position(game.food)" aria-hidden="true"
          ><Apple
        /></span>
        <GameResult
          v-if="game.status !== 'playing'"
          :tone="game.status === 'won' ? 'success' : 'ended'"
          :message="game.status === 'won' ? '填满整个棋盘了，太厉害了！' : '撞到了，再来一局吧。'"
        />
        <GameResult
          v-else-if="!started || paused"
          :message="paused ? '已暂停，休息一下。' : '准备好了吗？'"
        >
          <button class="game-button" @click.stop="togglePause">
            <Play :size="16" aria-hidden="true" />{{ paused ? '继续这一局' : '出发吧' }}
          </button>
        </GameResult>
      </div>
      <div class="number-directions" role="group" aria-label="贪吃蛇方向操作" @keydown="onKey">
        <button
          v-for="control in controls"
          :key="control.direction"
          class="game-button"
          :disabled="!playing"
          :aria-label="control.name"
          @click="turn(control.direction)"
        >
          <component :is="control.icon" :size="20" aria-hidden="true" />
        </button>
      </div>
    </section>
  </div>
</template>
