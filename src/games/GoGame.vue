<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import { Check, RotateCcw, Undo2 } from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import GameResult from './GameResult.vue'
import { useGameMotion } from './useGameMotion'
import { useBoardKeyboard } from './useBoardKeyboard'
import { useComputer } from './useComputer'
import { goGroup, goKomi, goSize, newGo, passGo, playGo, scoreGo, type GoState } from './go'

const game = ref(newGo()),
  computerFirst = ref(false),
  difficulty = ref(0)
const player = computed(() => (computerFirst.value ? -1 : 1))
const boardElement = ref<HTMLElement>(),
  selected = ref(40),
  pending = ref<number | null>(null)
const history = ref<GoState[]>([]),
  busy = ref(false),
  finished = ref(false),
  dead = ref<number[]>([]),
  notice = ref('')
const removed = ref<{ at: number; side: number }[]>([])
const motion = useGameMotion(),
  onKey = useBoardKeyboard(boardElement, selected, goSize, goSize * goSize)
const scoring = computed(() => game.value.passes >= 2 && !finished.value)
const score = computed(() => scoreGo(game.value.board, dead.value))
const canPlay = computed(
  () => !busy.value && !finished.value && !scoring.value && game.value.turn === player.value,
)
const outcome = computed(
  () =>
    `${score.value.winner === player.value ? '你赢了！' : '电脑赢了。'}${score.value.winner === 1 ? '黑' : '白'}棋胜 ${score.value.margin} 点。`,
)
let revision = 0
const computer = useComputer<number, GoState>('go', (at) => {
  if (game.value.turn === player.value || game.value.passes >= 2 || finished.value) return
  if (at === null || (at !== -1 && 'error' in playGo(game.value, at))) {
    computer.error.value = '电脑暂时没能完成思考，请重试或悔棋。'
    return
  }
  void commit(at)
})
const turnText = computed(() =>
  finished.value
    ? '本局结束'
    : busy.value
      ? '落子中'
      : scoring.value
        ? '核对死子与地盘'
        : computer.error.value
          ? '等待重试'
          : game.value.turn !== player.value
            ? '电脑思考中…'
            : '轮到你了',
)
function requestComputer() {
  if (game.value.turn !== player.value && game.value.passes < 2 && !finished.value)
    computer.run(game.value, difficulty.value, -player.value)
}
async function commit(at: number) {
  const move = at === -1 ? { state: passGo(game.value), captured: [] } : playGo(game.value, at)
  if ('error' in move) {
    notice.value = move.error
    return
  }
  const token = ++revision
  busy.value = true
  removed.value = move.captured.map((n) => ({ at: n, side: game.value.board[n]! }))
  const side = game.value.turn
  game.value = move.state
  pending.value = null
  notice.value =
    at === -1
      ? `${side === player.value ? '你' : '电脑'}停了一手。${game.value.passes >= 2 ? '请核对死子后确认数子。' : ''}`
      : move.captured.length
        ? `提走 ${move.captured.length} 颗${side === 1 ? '白' : '黑'}子。`
        : ''
  await nextTick()
  if (token !== revision) return
  const animations = [
    motion.animate(
      boardElement.value?.querySelectorAll('.board-cell')[at]?.querySelector('.strategy-piece'),
      [
        { transform: 'scale(.5)', opacity: 0.3 },
        { transform: 'scale(1)', opacity: 1 },
      ],
      { duration: 180 },
    ),
  ]
  boardElement.value?.querySelectorAll('.go-captured .strategy-piece').forEach((piece) =>
    animations.push(
      motion.animate(
        piece,
        [
          { transform: 'scale(1)', opacity: 1 },
          { transform: 'scale(.6)', opacity: 0 },
        ],
        { duration: 180 },
      ),
    ),
  )
  await motion.settle(animations)
  if (token !== revision) return
  removed.value = []
  busy.value = false
  requestComputer()
}
function remember() {
  history.value.push(game.value)
  if (history.value.length > 100) history.value.shift()
}
function play(at: number) {
  selected.value = at
  if (finished.value || busy.value) return
  if (scoring.value) {
    if (!game.value.board[at]) return
    const group = goGroup(game.value.board, at).stones
    dead.value = dead.value.includes(at)
      ? dead.value.filter((n) => !group.includes(n))
      : [...dead.value, ...group]
    notice.value = dead.value.includes(at)
      ? `已标记 ${group.length} 颗死子，再点可恢复。`
      : '已恢复这块棋子。'
    return
  }
  if (!canPlay.value) return
  const move = playGo(game.value, at)
  if ('error' in move) {
    pending.value = null
    notice.value = move.error
    return
  }
  notice.value = ''
  if (pending.value === at) confirmStone()
  else pending.value = at
}
function confirmStone() {
  if (pending.value === null || !canPlay.value) return
  const at = pending.value
  if ('error' in playGo(game.value, at)) return
  remember()
  void commit(at)
}
function pass() {
  if (!canPlay.value) return
  remember()
  void commit(-1)
}
function cancel() {
  revision++
  computer.cancel()
  computer.error.value = ''
  motion.cancel()
  busy.value = false
  pending.value = null
  removed.value = []
  dead.value = []
  finished.value = false
  notice.value = ''
}
function undo() {
  const previous = history.value.pop()
  if (!previous) return
  cancel()
  game.value = previous
}
function restart() {
  cancel()
  game.value = newGo()
  history.value = []
  selected.value = 40
  requestComputer()
}
function toggleFirst() {
  computerFirst.value = !computerFirst.value
  restart()
}
function resume() {
  if (!scoring.value || busy.value) return
  dead.value = []
  notice.value = ''
  game.value = { ...game.value, passes: 0 }
  requestComputer()
}
function finish() {
  if (scoring.value && !busy.value) {
    finished.value = true
    notice.value = ''
  }
}
onBeforeUnmount(() => {
  revision++
})
function label(at: number) {
  return `第 ${Math.floor(at / goSize) + 1} 行第 ${(at % goSize) + 1} 列：${game.value.board[at] === 1 ? '黑棋' : game.value.board[at] === -1 ? '白棋' : pending.value === at ? '待落子' : '空位'}${dead.value.includes(at) ? '，已标记死子' : ''}${game.value.last === at ? '，上一手' : ''}`
}
</script>

<template>
  <div class="game-layout">
    <section
      class="game-surface strategy-surface go-surface"
      aria-label="围棋游戏"
      :aria-busy="busy || computer.thinking.value"
    >
      <div class="game-toolbar">
        <div class="game-stats">
          <div>
            <span>{{ computerFirst ? '你执白棋 · 电脑执黑棋' : '你执黑棋 · 电脑执白棋' }}</span
            ><strong class="strategy-turn" role="status">{{ turnText }}</strong>
          </div>
          <div>
            <span>黑提子 / 白提子</span
            ><strong>{{ game.captures[0] }} <small>/</small> {{ game.captures[1] }}</strong>
          </div>
        </div>
        <div class="game-actions">
          <label class="game-select"
            >电脑难度<select v-model.number="difficulty" @change="restart">
              <option :value="0">休闲</option>
              <option :value="1">挑战</option>
            </select></label
          >
          <button
            class="game-button"
            :aria-pressed="computerFirst"
            title="切换先手会重新开局"
            @click="toggleFirst"
          >
            <Check v-if="computerFirst" :size="16" aria-hidden="true" />机器先手
          </button>
          <button class="game-button" :disabled="!history.length" @click="undo">
            <Undo2 :size="16" aria-hidden="true" />悔棋
          </button>
          <div class="game-restart-actions">
            <button class="game-button" @click="restart">
              <RotateCcw :size="16" aria-hidden="true" />重新开始</button
            ><GameFullscreenButton />
          </div>
        </div>
      </div>
      <div v-if="computer.error.value" class="strategy-error" role="alert">
        <span>{{ computer.error.value }}</span
        ><button class="game-button" @click="requestComputer">重试电脑落子</button>
      </div>
      <div
        ref="boardElement"
        class="strategy-board go-board"
        role="group"
        aria-label="九路围棋棋盘，方向键选点，回车预览，再次回车落子；数子时点选整块死子"
        @keydown="onKey"
        @keydown.esc="pending = null"
      >
        <svg class="strategy-lines" viewBox="0 0 900 900" aria-hidden="true">
          <path
            v-for="n in goSize"
            :key="n"
            :d="`M 50 ${n * 100 - 50} H 850 M ${n * 100 - 50} 50 V 850`"
          />
          <circle
            v-for="point in [
              [250, 250],
              [650, 250],
              [450, 450],
              [250, 650],
              [650, 650],
            ]"
            :key="point.join()"
            :cx="point[0]"
            :cy="point[1]"
            r="7"
          />
        </svg>
        <button
          v-for="(stone, i) in game.board"
          :key="i"
          class="board-cell strategy-cell"
          :class="{
            'is-selected': pending === i,
            'is-last': game.last === i,
            'is-dead': dead.includes(i),
          }"
          :tabindex="!finished && selected === i ? 0 : -1"
          :aria-label="label(i)"
          :aria-pressed="scoring ? dead.includes(i) : pending === i"
          :aria-disabled="finished || busy || (!scoring && !canPlay)"
          @click="play(i)"
          @focus="selected = i"
        >
          <span
            v-if="stone || pending === i"
            class="strategy-piece"
            :class="{
              'is-black': (stone || player) === 1,
              'is-white': (stone || player) === -1,
              'is-preview': pending === i,
            }"
            aria-hidden="true"
            ><span v-if="dead.includes(i)" class="go-dead-mark">×</span></span
          >
          <span
            v-if="scoring && (!stone || dead.includes(i)) && score.ownership[i]"
            class="go-territory"
            :class="score.ownership[i] === 1 ? 'is-black' : 'is-white'"
            aria-hidden="true"
          ></span>
        </button>
        <span
          v-for="stone in removed"
          :key="stone.at"
          class="go-captured"
          :style="{
            left: `${((stone.at % goSize) / goSize) * 100}%`,
            top: `${(Math.floor(stone.at / goSize) / goSize) * 100}%`,
          }"
          aria-hidden="true"
          ><span class="strategy-piece" :class="stone.side === 1 ? 'is-black' : 'is-white'"></span
        ></span>
        <GameResult
          v-if="finished"
          :message="outcome"
          :tone="score.winner === player ? 'success' : 'ended'"
          ><p class="go-final-score">
            黑 {{ score.black }} · 白 {{ score.white }}（含贴目）
          </p></GameResult
        >
      </div>
      <div v-if="scoring" class="go-scoring">
        <p>黑 {{ score.black }} 点 · 白 {{ score.white }} 点（含贴 {{ goKomi }} 目）</p>
        <p class="board-hint">点选整块死子，再点可恢复。小方块预览地盘；死活未定时可以继续对局。</p>
        <div class="game-actions">
          <button class="game-button" :disabled="busy" @click="finish">确认数子</button
          ><button class="game-button" :disabled="busy" @click="resume">继续对局</button>
        </div>
      </div>
      <div v-else-if="!finished" class="gomoku-confirm">
        <span>{{
          pending === null
            ? '9 路棋盘 · 白贴 6.5 目'
            : `第 ${Math.floor(pending / goSize) + 1} 行，第 ${(pending % goSize) + 1} 列`
        }}</span>
        <button class="game-button" :disabled="pending === null || !canPlay" @click="confirmStone">
          确认落子
        </button>
        <button class="game-button" :disabled="!canPlay" @click="pass">停一手</button>
      </div>
      <p class="board-hint go-notice" role="status">
        {{
          notice ||
          (finished
            ? '本局结束，可以悔棋或重新开始。'
            : scoring
              ? '双方已停一手，确认前请核对死子。'
              : '先选交点，再确认落子。围住对方的气，就能提子。')
        }}
      </p>
    </section>
  </div>
</template>
