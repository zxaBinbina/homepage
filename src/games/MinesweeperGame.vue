<script setup lang="ts">
import GameFullscreenButton from './GameFullscreenButton.vue'
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import { useGameMotion } from './useGameMotion'
import { Flag, MousePointer2, RotateCcw } from 'lucide-vue-next'
import { flagMine, mineLevels, newMineGame, revealMine, type MineCell } from './minesweeper'

const level = ref(0)
const game = ref(newMineGame())
const flagMode = ref(false)
function setMode(flag: boolean) {
  flagMode.value = flag
}
const elapsed = ref(0)
const focused = ref(0)
const boardElement = ref<HTMLElement>()
const motion = useGameMotion()
const scanning = ref(false)
const burst = ref<{ x: number; y: number } | null>(null)
let effect = 0
function stopEffects() {
  effect++
  motion.cancel()
  scanning.value = false
  burst.value = null
}
onBeforeUnmount(stopEffects)
async function animateReveal(previous: typeof game.value, index: number) {
  const current = ++effect
  motion.cancel()
  const board = boardElement.value
  const next = game.value
  scanning.value = next.status === 'won' && !motion.reduced.value && !document.hidden
  if (!board) {
    scanning.value = false
    return
  }
  await nextTick()
  if (current !== effect) return
  const cells = board.querySelectorAll<HTMLElement>('.mine-cell')
  const distance = (i: number) =>
    Math.max(
      Math.abs(Math.floor(i / next.size) - Math.floor(index / next.size)),
      Math.abs((i % next.size) - (index % next.size)),
    )
  const flips = next.cells.flatMap((cell, i) =>
    cell.open && !cell.mine && !previous.cells[i]!.open
      ? [
          motion.animate(
            cells[i],
            [
              { transform: 'perspective(500px) rotateX(-90deg)', opacity: 0.3 },
              { transform: 'perspective(500px) rotateX(0deg)', opacity: 1 },
            ],
            { duration: 190, delay: Math.min(150, distance(i) * 22), fill: 'backwards' },
          ),
        ]
      : [],
  )
  if (
    next.status === 'lost' &&
    next.exploded !== null &&
    !motion.reduced.value &&
    !document.hidden
  ) {
    const cell = cells[next.exploded]!.getBoundingClientRect(),
      area = board.getBoundingClientRect()
    burst.value = {
      x: cell.left - area.left + cell.width / 2,
      y: cell.top - area.top + cell.height / 2,
    }
    await nextTick()
    if (current !== effect) return
    flips.push(
      motion.animate(
        board.querySelector('.mine-shockwave'),
        [
          { transform: 'scale(.1)', opacity: 0.95 },
          { transform: 'scale(2.6)', opacity: 0 },
        ],
        { duration: 520 },
      ),
    )
    board.querySelectorAll('.mine-spark').forEach((spark, i) => {
      const angle = (i * Math.PI) / 5
      flips.push(
        motion.animate(
          spark,
          [
            { transform: 'translate(0,0) scale(1)', opacity: 1 },
            {
              transform: `translate(${Math.cos(angle) * 85}px,${Math.sin(angle) * 85}px) scale(.2)`,
              opacity: 0,
            },
          ],
          { duration: 460, easing: 'ease-out' },
        ),
      )
    })
    flips.push(
      motion.animate(
        cells[next.exploded],
        [
          { transform: 'scale(1)' },
          { transform: 'scale(.75)', offset: 0.25 },
          { transform: 'scale(1.12)', offset: 0.6 },
          { transform: 'scale(1)' },
        ],
        { duration: 300 },
      ),
    )
    next.cells.forEach((cell, i) => {
      if (cell.mine)
        flips.push(
          motion.animate(
            cells[i]?.querySelector('.mine-symbol'),
            [
              { opacity: 0, transform: 'scale(.2)' },
              { opacity: 1, transform: 'scale(1)' },
            ],
            { duration: 210, delay: Math.min(250, distance(i) * 35), fill: 'backwards' },
          ),
        )
    })
  }
  await motion.settle(flips)
  if (current !== effect) return
  burst.value = null
  if (scanning.value) {
    await motion.settle([
      motion.animate(
        board.querySelector('.mine-scanner'),
        [
          { transform: 'translateY(-100%)', opacity: 0 },
          { transform: 'translateY(-95%)', opacity: 1, offset: 0.04 },
          { transform: 'translateY(0)', opacity: 1, offset: 0.96 },
          { transform: 'translateY(5%)', opacity: 0 },
        ],
        { duration: 1100, easing: 'linear' },
      ),
      ...next.cells.flatMap((cell, i) =>
        cell.mine
          ? [
              motion.animate(
                cells[i]?.querySelector('.mine-symbol'),
                [
                  { opacity: 0, transform: 'scale(.4)' },
                  { opacity: 1, transform: 'scale(1.2)', offset: 0.6 },
                  { opacity: 1, transform: 'scale(1)' },
                ],
                {
                  duration: 180,
                  delay: ((Math.floor(i / next.size) + 0.5) / next.size) * 1000,
                  fill: 'both',
                },
              ),
            ]
          : [],
      ),
    ])
    if (current === effect) scanning.value = false
  }
}
const flagged = computed(() => game.value.cells.filter((cell) => cell.flag).length)
const safe = computed(() => game.value.cells.filter((cell) => cell.open && !cell.mine).length)
const ended = computed(() => game.value.status === 'won' || game.value.status === 'lost')
const status = computed(() =>
  game.value.status === 'won'
    ? '所有安全格都找到了，恭喜过关！'
    : game.value.status === 'lost'
      ? '踩到地雷了。休息一下，再来一局吧。'
      : '',
)
let timer: ReturnType<typeof setInterval> | undefined
let started = 0
function stopTimer() {
  clearInterval(timer)
  timer = undefined
}
onBeforeUnmount(stopTimer)
function restart() {
  stopEffects()
  stopTimer()
  const config = mineLevels[level.value]!
  game.value = newMineGame(config.size, config.mines)
  elapsed.value = 0
  flagMode.value = false
  focused.value = 0
}
function flag(index: number) {
  if (ended.value) return
  const next = flagMine(game.value, index)
  game.value = next
}
function reveal(index: number) {
  if (ended.value) return
  if (flagMode.value && !game.value.cells[index]!.open) {
    flag(index)
    return
  }
  const previous = game.value
  game.value = revealMine(game.value, index)
  if (previous.status === 'ready' && game.value.status === 'playing') {
    started = Date.now()
    timer = setInterval(() => {
      elapsed.value = Math.floor((Date.now() - started) / 1000)
    }, 1000)
  }
  if (ended.value) stopTimer()
  if (previous !== game.value) void animateReveal(previous, index)
}
function label(cell: MineCell, index: number) {
  const position = `第 ${Math.floor(index / game.value.size) + 1} 行第 ${(index % game.value.size) + 1} 列`
  return `${position}：${ended.value && cell.mine ? (game.value.status === 'won' ? '已排除地雷' : '地雷') : cell.flag ? (ended.value ? '标记错误' : '已插旗') : cell.open ? (cell.adjacent ? `周围 ${cell.adjacent} 颗地雷` : '空白') : '未翻开'}`
}
function onKey(event: KeyboardEvent, index: number) {
  if (event.ctrlKey || event.metaKey || event.altKey) return
  if (event.key.toLowerCase() === 'f') {
    event.preventDefault()
    flag(index)
    return
  }
  const size = game.value.size
  const row = Math.floor(index / size),
    column = index % size
  const targets: Record<string, number> = {
    ArrowLeft: row * size + Math.max(0, column - 1),
    ArrowRight: row * size + Math.min(size - 1, column + 1),
    ArrowUp: Math.max(0, row - 1) * size + column,
    ArrowDown: Math.min(size - 1, row + 1) * size + column,
    Home: row * size,
    End: row * size + size - 1,
  }
  const target = targets[event.key]
  if (target !== undefined) {
    event.preventDefault()
    focused.value = target
    boardElement.value?.querySelectorAll<HTMLButtonElement>('button')[target]?.focus()
  }
}
</script>

<template>
  <div class="game-layout">
    <section class="game-surface mine-surface" aria-label="扫雷游戏">
      <div class="game-toolbar">
        <div class="game-stats">
          <div>
            <span>剩余旗子</span><strong>{{ game.mines - flagged }}</strong>
          </div>
          <div>
            <span>用时 / 秒</span><strong>{{ elapsed }}</strong>
          </div>
          <div>
            <span>安全格</span
            ><strong
              >{{ safe }}<small> / {{ game.size * game.size - game.mines }}</small></strong
            >
          </div>
        </div>
      </div>
      <div class="game-actions mine-actions">
        <label class="game-select"
          ><span id="mine-level-label">难度</span
          ><select v-model="level" aria-labelledby="mine-level-label" @change="restart">
            <option v-for="(item, index) in mineLevels" :key="item.size" :value="index">
              {{ item.name }}
            </option>
          </select></label
        >
        <div class="game-restart-actions">
          <button class="game-button" @click="restart">
            <RotateCcw :size="16" aria-hidden="true" />重新开始</button
          ><GameFullscreenButton />
        </div>
      </div>
      <div class="mine-mode" role="group" aria-label="扫雷操作模式">
        <button class="game-button" :aria-pressed="!flagMode" @click="setMode(false)">
          <MousePointer2 :size="16" aria-hidden="true" />翻开</button
        ><button class="game-button" :aria-pressed="flagMode" @click="setMode(true)">
          <Flag :size="16" aria-hidden="true" />插旗
        </button>
      </div>
      <div
        class="mine-board-scroll"
        tabindex="0"
        role="region"
        aria-label="扫雷棋盘，较大棋盘可左右滚动"
      >
        <div
          ref="boardElement"
          class="mine-board"
          :class="{ 'is-scanning': scanning }"
          :style="{ '--mine-size': game.size }"
          role="group"
          aria-label="使用方向键选择格子，回车翻开，F 插旗"
        >
          <button
            v-for="(cell, index) in game.cells"
            :key="index"
            class="mine-cell"
            :class="{
              'is-open': cell.open,
              'is-flag': cell.flag,
              'is-mine': ended && cell.mine,
              'is-exploded': game.exploded === index,
              'is-wrong': ended && cell.flag && !cell.mine,
              'is-found': game.status === 'won' && cell.mine,
            }"
            :data-number="cell.open ? cell.adjacent : 0"
            :aria-label="label(cell, index)"
            :aria-disabled="ended"
            :tabindex="focused === index ? 0 : -1"
            @focus="focused = index"
            @click="reveal(index)"
            @contextmenu.prevent="flag(index)"
            @keydown="onKey($event, index)"
          >
            <span v-if="ended && cell.flag && !cell.mine" aria-hidden="true">×</span
            ><span v-else-if="ended && cell.mine" class="mine-symbol" aria-hidden="true">✹</span
            ><span v-else-if="cell.flag" aria-hidden="true">⚑</span
            ><span v-else-if="cell.open && cell.adjacent" aria-hidden="true">{{
              cell.adjacent
            }}</span>
          </button>
          <div class="mine-effects" aria-hidden="true">
            <div
              v-if="burst"
              class="mine-burst"
              :style="{ left: `${burst.x}px`, top: `${burst.y}px` }"
            >
              <i class="mine-shockwave"></i><i v-for="i in 10" :key="i" class="mine-spark"></i>
            </div>
            <div v-if="scanning" class="mine-scanner"></div>
          </div>
        </div>
      </div>
      <p
        v-show="status"
        class="game-status"
        :class="{ 'is-success': game.status === 'won', 'is-ended': game.status === 'lost' }"
        role="status"
      >
        {{ status }}
      </p>
    </section>
  </div>
</template>
