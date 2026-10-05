<script setup lang="ts">
import { computed, inject, nextTick, onBeforeUnmount, ref } from 'vue'
import { RotateCcw, Undo2 } from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import { gameFullscreenKey } from './fullscreen'
import { useBoardKeyboard } from './useBoardKeyboard'
import { useGameMotion } from './useGameMotion'
import { useComputer } from './useComputer'
import { winningLine } from './gomoku'
import {
  applyChessMove,
  blackNames,
  chessName,
  chessNames,
  chessOutcome,
  inCheck,
  legalChessMoves,
  newXiangqi,
  type ChessMove,
} from './xiangqi'

const props = defineProps<{ kind: 'gomoku' | 'xiangqi' }>()
const chess = props.kind === 'xiangqi',
  columns = chess ? 9 : 15
const makeBoard = () => (chess ? newXiangqi() : Array<number>(225).fill(0))
const board = ref(makeBoard()),
  turn = ref(1),
  difficulty = ref(0),
  selected = ref(chess ? 58 : 112)
const source = ref<number | null>(null),
  pending = ref<number | null>(null),
  last = ref<ChessMove | null>(null)
const quiet = ref(0),
  positions = ref<string[]>([board.value.join(',') + ':1']),
  busy = ref(false)
const boardElement = ref<HTMLElement>(),
  motion = useGameMotion(),
  fullscreen = inject(gameFullscreenKey)
const onKey = useBoardKeyboard(boardElement, selected, columns, chess ? 90 : 225)
type Snapshot = { board: number[]; last: ChessMove | null; quiet: number; positions: string[] }
const history = ref<Snapshot[]>([])
let revision = 0
const line = computed(() => (!chess && last.value ? winningLine(board.value, last.value.to) : []))
const winner = computed(() =>
  chess
    ? chessOutcome(board.value, turn.value)
    : line.value.length
      ? board.value[last.value!.to]!
      : 0,
)
const draw = computed(
  () =>
    !winner.value &&
    (chess
      ? quiet.value >= 120 ||
        positions.value.filter((p) => p === positions.value.at(-1)).length >= 3
      : board.value.every(Boolean)),
)
const ended = computed(() => !!winner.value || draw.value)
const legal = computed(() =>
  chess && turn.value === 1 && !ended.value ? legalChessMoves(board.value, 1) : [],
)
const targets = computed(() => legal.value.filter((m) => m.from === source.value).map((m) => m.to))
const checked = computed(() => chess && !ended.value && inCheck(board.value, turn.value))
const outcome = computed(() =>
  winner.value === 1
    ? '你赢了！这一局走得漂亮。'
    : winner.value === -1
      ? '电脑赢了，再试试另一种走法吧。'
      : draw.value
        ? chess
          ? '本局和棋，可以重新开一局。'
          : '棋盘已满，本局和棋。'
        : '',
)
const computer = useComputer<number | ChessMove>(props.kind, (move) => {
  if (turn.value !== -1 || ended.value) return
  if (move === null) {
    computer.error.value = '电脑暂时没能完成思考，请重试或悔棋。'
    return
  }
  const valid = chess
    ? typeof move !== 'number' &&
      legalChessMoves(board.value, -1).some((m) => m.from === move.from && m.to === move.to)
    : typeof move === 'number' &&
      Number.isInteger(move) &&
      move >= 0 &&
      move < 225 &&
      !board.value[move]
  if (!valid) {
    computer.error.value = '电脑暂时没能完成思考，请重试或悔棋。'
    return
  }
  void commit(typeof move === 'number' ? { from: -1, to: move } : move)
})
const turnText = computed(() =>
  ended.value
    ? '本局结束'
    : computer.error.value
      ? '等待重试'
      : busy.value
        ? '落子中'
        : turn.value === -1
          ? '电脑思考中…'
          : checked.value
            ? '你被将军了，请应将'
            : '轮到你了',
)
function requestComputer() {
  if (turn.value === -1 && !ended.value) computer.run(board.value, difficulty.value)
}
async function commit(move: ChessMove) {
  const current = ++revision
  busy.value = true
  const cells = boardElement.value?.querySelectorAll('.board-cell')
  const from = cells?.[move.from]?.getBoundingClientRect(),
    to = cells?.[move.to]?.getBoundingClientRect()
  quiet.value = chess && board.value[move.to] ? 0 : quiet.value + 1
  if (chess) board.value = applyChessMove(board.value, move)
  else {
    const next = [...board.value]
    next[move.to] = turn.value
    board.value = next
  }
  last.value = move
  source.value = null
  pending.value = null
  turn.value = -turn.value
  positions.value = [...positions.value, board.value.join(',') + ':' + turn.value]
  await nextTick()
  if (revision !== current) return
  const piece = boardElement.value
    ?.querySelectorAll('.board-cell')
    [move.to]?.querySelector('.strategy-piece')
  const scale = fullscreen?.scale.value || 1
  const start =
    from && to
      ? {
          transform: `translate(${(from.x - to.x) / scale}px, ${(from.y - to.y) / scale}px)`,
          opacity: 0.7,
        }
      : { transform: 'scale(.5)', opacity: 0.3 }
  await motion.settle([
    motion.animate(piece, [start, { transform: 'translate(0, 0) scale(1)', opacity: 1 }], {
      duration: chess ? 240 : 180,
    }),
  ])
  if (revision !== current) return
  busy.value = false
  requestComputer()
}
function remember() {
  history.value.push({
    board: [...board.value],
    last: last.value,
    quiet: quiet.value,
    positions: [...positions.value],
  })
  if (history.value.length > 100) history.value.shift()
}
function play(at: number) {
  selected.value = at
  if (turn.value !== 1 || busy.value || ended.value) return
  if (chess) {
    if (board.value[at]! > 0) {
      source.value = source.value === at ? null : at
      return
    }
    const move = legal.value.find((m) => m.from === source.value && m.to === at)
    if (move) {
      remember()
      void commit(move)
    }
  } else if (!board.value[at]) {
    if (pending.value === at) confirmStone()
    else pending.value = at
  }
}
function confirmStone() {
  if (pending.value === null || turn.value !== 1 || busy.value || ended.value) return
  const at = pending.value
  if (board.value[at]) return
  remember()
  void commit({ from: -1, to: at })
}
function clearSelection() {
  source.value = null
  pending.value = null
}
function cancelTurn() {
  revision++
  computer.cancel()
  computer.error.value = ''
  motion.cancel()
  busy.value = false
  clearSelection()
}
function undo() {
  const previous = history.value.pop()
  if (!previous) return
  cancelTurn()
  board.value = previous.board
  last.value = previous.last
  quiet.value = previous.quiet
  positions.value = previous.positions
  turn.value = 1
}
function restart() {
  cancelTurn()
  board.value = makeBoard()
  turn.value = 1
  history.value = []
  last.value = null
  quiet.value = 0
  positions.value = [board.value.join(',') + ':1']
  selected.value = chess ? 58 : 112
}
onBeforeUnmount(() => {
  revision++
})
function label(value: number, i: number) {
  const location = `第 ${Math.floor(i / columns) + 1} 行第 ${(i % columns) + 1} 列：`
  const piece = value
    ? chess
      ? chessName(value)
      : value === 1
        ? '黑棋'
        : '白棋'
    : pending.value === i
      ? '待落子'
      : '空位'
  return (
    location +
    piece +
    (targets.value.includes(i) ? '，可走到此处' : '') +
    (last.value?.to === i ? '，上一手' : '')
  )
}
</script>

<template>
  <div class="game-layout">
    <section
      class="game-surface strategy-surface"
      :aria-label="chess ? '中国象棋游戏' : '五子棋游戏'"
      :aria-busy="busy || computer.thinking.value"
    >
      <div class="game-toolbar">
        <div class="game-stats">
          <div>
            <span>{{ chess ? '你执红棋 · 电脑执黑棋' : '你执黑棋 · 电脑执白棋' }}</span
            ><strong class="strategy-turn" role="status">{{ turnText }}</strong>
          </div>
          <div>
            <span>你的步数</span><strong>{{ Math.ceil((positions.length - 1) / 2) }}</strong>
          </div>
        </div>
        <div class="game-actions">
          <label class="game-select"
            >电脑难度<select v-model.number="difficulty" @change="restart">
              <option :value="0">休闲</option>
              <option :value="1">挑战</option>
            </select></label
          >
          <button class="game-button" :disabled="!history.length" @click="undo">
            <Undo2 :size="16" aria-hidden="true" />悔棋
          </button>
          <div class="game-restart-actions">
            <button class="game-button" @click="restart">
              <RotateCcw :size="16" aria-hidden="true" />重新开始</button
            ><GameFullscreenButton />
          </div>
          <p
            v-show="outcome"
            class="game-status"
            :class="{ 'is-success': winner === 1, 'is-ended': winner === -1 }"
            role="status"
          >
            {{ outcome }}
          </p>
        </div>
      </div>
      <div v-if="computer.error.value" class="strategy-error" role="alert">
        <span>{{ computer.error.value }}</span
        ><button class="game-button" @click="requestComputer">重试电脑落子</button>
      </div>
      <div
        ref="boardElement"
        class="strategy-board"
        :class="chess ? 'xiangqi-board' : 'gomoku-board'"
        role="group"
        :aria-label="
          chess
            ? '中国象棋棋盘，方向键选格，回车选棋或走棋'
            : '五子棋棋盘，方向键选格，回车预览，再次回车落子'
        "
        @keydown="onKey"
        @keydown.esc="clearSelection"
      >
        <svg v-if="chess" class="strategy-lines" viewBox="0 0 900 1000" aria-hidden="true">
          <path v-for="y in 10" :key="`h${y}`" :d="`M 50 ${y * 100 - 50} H 850`" />
          <path
            v-for="x in 9"
            :key="`v${x}`"
            :d="
              x === 1 || x === 9
                ? `M ${x * 100 - 50} 50 V 950`
                : `M ${x * 100 - 50} 50 V 450 M ${x * 100 - 50} 550 V 950`
            "
          />
          <path d="M350 50 L550 250 M550 50 L350 250 M350 750 L550 950 M550 750 L350 950" />
          <text x="240" y="510">楚 河</text>
          <text x="660" y="510">汉 界</text>
        </svg>
        <svg v-else class="strategy-lines" viewBox="0 0 1500 1500" aria-hidden="true">
          <path
            v-for="n in 15"
            :key="n"
            :d="`M 50 ${n * 100 - 50} H 1450 M ${n * 100 - 50} 50 V 1450`"
          />
          <circle
            v-for="point in [
              [350, 350],
              [1150, 350],
              [750, 750],
              [350, 1150],
              [1150, 1150],
            ]"
            :key="point.join()"
            :cx="point[0]"
            :cy="point[1]"
            r="9"
          />
        </svg>
        <button
          v-for="(piece, i) in board"
          :key="i"
          class="board-cell strategy-cell"
          :class="{
            'is-selected': source === i || pending === i,
            'is-target': targets.includes(i),
            'is-last': last?.to === i,
            'is-origin': chess && last?.from === i,
            'is-winning': line.includes(i),
            'is-check': chess && checked && piece === turn,
          }"
          :tabindex="i === selected ? 0 : -1"
          :aria-label="label(piece, i)"
          :aria-disabled="ended || turn !== 1 || busy"
          :aria-pressed="source === i || pending === i"
          @click="play(i)"
          @focus="selected = i"
        >
          <span
            v-if="piece || pending === i"
            class="strategy-piece"
            :class="{
              'is-red': chess && piece > 0,
              'is-black': chess ? piece < 0 : piece === 1 || pending === i,
              'is-white': !chess && piece === -1,
              'is-preview': pending === i,
            }"
            aria-hidden="true"
            >{{ chess ? (piece > 0 ? chessNames : blackNames)[Math.abs(piece)] : '' }}</span
          >
        </button>
      </div>
      <div v-if="!chess" class="gomoku-confirm">
        <span>{{
          pending === null
            ? '先选一个交点，再确认落子。'
            : `第 ${Math.floor(pending / 15) + 1} 行，第 ${(pending % 15) + 1} 列`
        }}</span
        ><button
          class="game-button"
          :disabled="pending === null || turn !== 1 || busy || ended"
          @click="confirmStone"
        >
          确认落子
        </button>
      </div>
    </section>
  </div>
</template>
