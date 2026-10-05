<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import {
  ArrowDown,
  ArrowDownToLine,
  ArrowLeft,
  ArrowRight,
  Pause,
  Play,
  RotateCcw,
  RotateCw,
} from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import GameResult from './GameResult.vue'
import { useGameMotion } from './useGameMotion'
import {
  blocks,
  dropBlock,
  dropInterval,
  ghostBlock,
  lockBlock,
  newTetris,
  rotateBlock,
  shapes,
  shiftBlock,
} from './tetris'

const game = ref(newTetris()),
  level = ref(0),
  started = ref(false),
  paused = ref(false),
  busy = ref(false)
const boardElement = ref<HTMLElement>(),
  clearing = ref<number[]>([]),
  locked = ref<number[] | null>(null)
const motion = useGameMotion()
let timer: ReturnType<typeof setTimeout> | undefined,
  version = 0
const playing = computed(
  () => started.value && !paused.value && !busy.value && game.value.status === 'playing',
)
const cells = computed(() => {
  const result: string[] = (locked.value || game.value.board).map((v) => (v ? 'fixed' : ''))
  if (!locked.value && game.value.status === 'playing') {
    for (const { x, y } of blocks(ghostBlock(game.value)))
      if (y >= 0 && !result[y * 10 + x]) result[y * 10 + x] = 'ghost'
    for (const { x, y } of blocks(game.value.active)) if (y >= 0) result[y * 10 + x] = 'active'
  }
  return result
})
const nextShape = computed(() => shapes[game.value.queue[0]!]!)
const status = computed(() =>
  game.value.status === 'won'
    ? '30 行挑战完成！漂亮的一局。'
    : game.value.status === 'lost'
      ? '方块堆到顶了，再来一局吧。'
      : '',
)
function stopTimer() {
  if (timer) clearTimeout(timer)
  timer = undefined
}
function schedule() {
  stopTimer()
  if (playing.value)
    timer = setTimeout(() => down(false), dropInterval(game.value.lines, level.value))
}
async function settle() {
  if (!playing.value) return
  stopTimer()
  busy.value = true
  const current = ++version,
    result = lockBlock(game.value)
  if (result.rows.length) {
    locked.value = result.locked
    clearing.value = result.rows
    await nextTick()
    if (current !== version) return
    await motion.settle(
      Array.from(boardElement.value?.querySelectorAll('.is-clearing') || []).map((el) =>
        motion.animate(
          el,
          [
            { opacity: 1, transform: 'scale(1)' },
            { opacity: 0, transform: 'scale(.6)' },
          ],
          { duration: 180, fill: 'both' },
        ),
      ),
    )
    if (current !== version) return
  }
  game.value = result.game
  locked.value = null
  clearing.value = []
  busy.value = false
  schedule()
}
function down(manual = true) {
  if (!playing.value) return
  const next = shiftBlock(game.value, 0, 1)
  if (next === game.value) void settle()
  else {
    game.value = manual ? { ...next, score: next.score + 1 } : next
    schedule()
  }
}
function move(dx: number) {
  if (playing.value) game.value = shiftBlock(game.value, dx, 0)
}
function rotate() {
  if (playing.value) game.value = rotateBlock(game.value)
}
function drop() {
  if (playing.value) {
    game.value = dropBlock(game.value)
    void settle()
  }
}
function togglePause() {
  if (game.value.status !== 'playing') return
  if (!started.value) {
    started.value = true
    paused.value = false
  } else paused.value = !paused.value
  if (paused.value) {
    stopTimer()
    motion.finish()
  } else schedule()
  boardElement.value?.focus({ preventScroll: true })
}
function restart() {
  version++
  stopTimer()
  motion.cancel()
  busy.value = false
  clearing.value = []
  locked.value = null
  game.value = newTetris()
  started.value = false
  paused.value = false
}
function pauseAway() {
  if (started.value && game.value.status === 'playing') {
    paused.value = true
    stopTimer()
    motion.finish()
  }
}
function visibility() {
  if (document.hidden) pauseAway()
}
window.addEventListener('blur', pauseAway)
document.addEventListener('visibilitychange', visibility)
onBeforeUnmount(() => {
  version++
  stopTimer()
  window.removeEventListener('blur', pauseAway)
  document.removeEventListener('visibilitychange', visibility)
})
function onKey(event: KeyboardEvent) {
  if (event.altKey || event.ctrlKey || event.metaKey) return
  const key = event.key.toLowerCase()
  if (
    !['arrowleft', 'arrowright', 'arrowup', 'arrowdown', 'a', 'd', 'w', 's', ' ', 'p'].includes(key)
  )
    return
  event.preventDefault()
  if (key === 'p') {
    if (!event.repeat) togglePause()
    return
  }
  if (key === 'arrowleft' || key === 'a') move(-1)
  else if (key === 'arrowright' || key === 'd') move(1)
  else if (key === 'arrowup' || key === 'w') {
    if (!event.repeat) rotate()
  } else if (key === 'arrowdown' || key === 's') down()
  else if (!event.repeat) drop()
}
</script>

<template>
  <div class="game-layout">
    <section class="game-surface tetris-surface" aria-label="俄罗斯方块游戏">
      <div class="game-toolbar">
        <div class="game-stats">
          <div>
            <span>本局得分</span><strong>{{ game.score }}</strong>
          </div>
          <div>
            <span>消除行数</span><strong>{{ game.lines }} <small>/ 30</small></strong>
          </div>
          <div>
            <span>当前阶段</span><strong>{{ Math.min(6, 1 + Math.floor(game.lines / 5)) }}</strong>
          </div>
        </div>
        <div class="game-actions">
          <label class="game-select"
            >起始速度<select v-model.number="level" @change="restart">
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
            />{{ !started ? '开始游戏' : paused ? '继续游戏' : '暂停' }}
          </button>
          <div class="game-restart-actions">
            <button class="game-button" @click="restart">
              <RotateCcw :size="16" aria-hidden="true" />重新开始</button
            ><GameFullscreenButton />
          </div>
        </div>
      </div>
      <div class="tetris-play">
        <div
          ref="boardElement"
          class="tetris-board"
          tabindex="0"
          role="group"
          aria-label="俄罗斯方块棋盘，左右移动，上旋转，下加速，空格落下，P 暂停"
          :aria-busy="busy"
          @keydown="onKey"
        >
          <span
            v-for="(cell, i) in cells"
            :key="i"
            class="tetris-cell"
            :class="[
              cell && `is-${cell}`,
              { 'is-clearing': clearing.includes(Math.floor(i / 10)) },
            ]"
            aria-hidden="true"
          ></span>
          <div
            v-if="game.status === 'playing' && (!started || paused)"
            class="tetris-curtain"
            role="status"
          >
            <strong>{{ paused ? '已暂停' : '准备好了吗？' }}</strong
            ><span>{{ paused ? '点击继续，接着这一局。' : '点击开始，让方块落下。' }}</span>
          </div>
          <GameResult
            v-if="status"
            :message="status"
            :tone="game.status === 'won' ? 'success' : 'ended'"
          />
        </div>
        <aside class="tetris-side" aria-label="下一块">
          <span class="overline">NEXT</span><span>下一块</span>
          <div
            class="tetris-next"
            :style="{ gridTemplateColumns: `repeat(${nextShape.length}, 1fr)` }"
            aria-hidden="true"
          >
            <i v-for="(v, i) in nextShape.flat()" :key="i" :class="{ 'is-filled': v }"></i>
          </div>
          <p>黑白之间，<br />留一点余地。</p>
        </aside>
      </div>
      <div class="tetris-controls" role="group" aria-label="方块操作">
        <button class="game-button" :disabled="!playing" aria-label="向左移动" @click="move(-1)">
          <ArrowLeft :size="20" />
        </button>
        <button class="game-button" :disabled="!playing" aria-label="旋转方块" @click="rotate">
          <RotateCw :size="20" />
        </button>
        <button class="game-button" :disabled="!playing" aria-label="向右移动" @click="move(1)">
          <ArrowRight :size="20" />
        </button>
        <button class="game-button" :disabled="!playing" aria-label="向下加速" @click="down()">
          <ArrowDown :size="20" />
        </button>
        <button class="game-button" :disabled="!playing" aria-label="直接落下" @click="drop">
          <ArrowDownToLine :size="20" />
        </button>
      </div>
    </section>
  </div>
</template>
