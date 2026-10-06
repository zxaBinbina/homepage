<script setup lang="ts">
import { computed, inject, nextTick, onBeforeUnmount, ref } from 'vue'
import { Check, RotateCcw, Undo2 } from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import GameResult from './GameResult.vue'
import ChessPiece from './ChessPiece.vue'
import { gameFullscreenKey } from './fullscreen'
import { useGameMotion } from './useGameMotion'
import { useBoardKeyboard } from './useBoardKeyboard'
import { useComputer } from './useComputer'
import {
  Chess,
  chessResult,
  newChess,
  pieceNames,
  playChess,
  squareAt,
  squareIndex,
  type ChessState,
  type ChessTurn,
} from './chess'
import type { PieceSymbol } from 'chess.js'

const game = ref(newChess()),
  computerFirst = ref(false),
  difficulty = ref(0)
const player = computed(() => (computerFirst.value ? 'b' : 'w'))
const rules = computed(() => new Chess(game.value.fen))
const board = computed(() => rules.value.board().flat())
const result = computed(() => chessResult(game.value))
const legal = computed(() => (result.value ? [] : rules.value.moves({ verbose: true })))
const selected = ref(52),
  source = ref<number | null>(null),
  promotion = ref<ChessTurn | null>(null)
const promotionElement = ref<HTMLElement>(),
  boardElement = ref<HTMLElement>(),
  busy = ref(false)
const history = ref<ChessState[]>([]),
  motion = useGameMotion(),
  fullscreen = inject(gameFullscreenKey)
const onKey = useBoardKeyboard(boardElement, selected, 8, 64)
const targets = computed(() =>
  legal.value.filter((m) => m.from === squareAt(source.value ?? -1)).map((m) => squareIndex(m.to)),
)
const canPlay = computed(() => !busy.value && !result.value && rules.value.turn() === player.value)
let revision = 0
const computer = useComputer<ChessTurn, ChessState>('chess', (move) => {
  if (rules.value.turn() === player.value || result.value) return
  if (!move || !playChess(game.value, move)) {
    computer.error.value = '电脑暂时没能完成思考，请重试或悔棋。'
    return
  }
  void commit(move)
})
const turnText = computed(() =>
  result.value
    ? '本局结束'
    : computer.error.value
      ? '等待重试'
      : busy.value
        ? '走子中'
        : promotion.value
          ? '请选择升变棋子'
          : rules.value.turn() !== player.value
            ? '电脑思考中…'
            : rules.value.isCheck()
              ? '你被将军了，请应将'
              : '轮到你了',
)
const outcome = computed(() =>
  !result.value
    ? ''
    : !result.value.winner
      ? `本局和棋：${result.value.reason}。`
      : result.value.winner === (player.value === 'w' ? 1 : -1)
        ? '你赢了！将死对方国王。'
        : '电脑赢了，再试试另一种走法吧。',
)
function requestComputer() {
  if (!result.value && rules.value.turn() !== player.value)
    computer.run(game.value, difficulty.value, computerFirst.value ? 1 : -1)
}
async function commit(move: ChessTurn) {
  const next = playChess(game.value, move)
  if (!next) return
  const token = ++revision
  busy.value = true
  const before = board.value
  // Include the rook in castling; each piece is animated in game coordinates.
  const pairs = [{ from: squareIndex(move.from), to: squareIndex(move.to) }]
  if (before[pairs[0]!.from]?.type === 'k' && Math.abs(pairs[0]!.from - pairs[0]!.to) === 2) {
    const row = Math.floor(pairs[0]!.from / 8) * 8
    pairs.push(pairs[0]!.to % 8 === 6 ? { from: row + 7, to: row + 5 } : { from: row, to: row + 3 })
  }
  const cells = boardElement.value?.querySelectorAll('.board-cell')
  const offsets = pairs.map((p) => ({
    ...p,
    fromRect: cells?.[p.from]?.getBoundingClientRect(),
    toRect: cells?.[p.to]?.getBoundingClientRect(),
  }))
  game.value = next
  source.value = null
  promotion.value = null
  await nextTick()
  if (token !== revision) return
  const scale = fullscreen?.scale.value || 1
  await motion.settle(
    offsets.map((p) =>
      motion.animate(
        cells?.[p.to]?.querySelector('.strategy-piece'),
        [
          {
            transform: `translate(${((p.fromRect?.x ?? 0) - (p.toRect?.x ?? 0)) / scale}px, ${((p.fromRect?.y ?? 0) - (p.toRect?.y ?? 0)) / scale}px)`,
            opacity: 0.7,
          },
          { transform: 'translate(0, 0)', opacity: 1 },
        ],
        { duration: 240 },
      ),
    ),
  )
  if (token !== revision) return
  busy.value = false
  requestComputer()
}
function remember() {
  history.value.push(game.value)
  if (history.value.length > 100) history.value.shift()
}
async function play(at: number) {
  selected.value = at
  if (!canPlay.value || promotion.value) return
  if (board.value[at]?.color === player.value) {
    source.value = source.value === at ? null : at
    return
  }
  const moves = legal.value.filter(
    (m) => m.from === squareAt(source.value ?? -1) && m.to === squareAt(at),
  )
  if (!moves.length) return
  if (moves.some((m) => m.promotion)) {
    promotion.value = { from: moves[0]!.from, to: moves[0]!.to }
    await nextTick()
    promotionElement.value
      ?.querySelector<HTMLButtonElement>('button')
      ?.focus({ preventScroll: true })
  } else {
    remember()
    void commit(moves[0]!)
  }
}
function promote(piece: PieceSymbol) {
  if (!promotion.value || !canPlay.value) return
  const move = { ...promotion.value, promotion: piece }
  remember()
  void commit(move)
  void focusBoard()
}
async function focusBoard() {
  await nextTick()
  boardElement.value
    ?.querySelector<HTMLButtonElement>(`[data-square="${squareAt(selected.value)}"]`)
    ?.focus({ preventScroll: true })
}
function clearSelection() {
  const hadPromotion = !!promotion.value
  source.value = null
  promotion.value = null
  if (hadPromotion) void focusBoard()
}
function cancel() {
  revision++
  computer.cancel()
  computer.error.value = ''
  motion.cancel()
  busy.value = false
  source.value = null
  promotion.value = null
}
function undo() {
  const previous = history.value.pop()
  if (!previous) return
  cancel()
  game.value = previous
}
function restart() {
  cancel()
  game.value = newChess()
  history.value = []
  selected.value = computerFirst.value ? 12 : 52
  requestComputer()
}
function toggleFirst() {
  computerFirst.value = !computerFirst.value
  restart()
}
onBeforeUnmount(() => {
  revision++
})
function label(i: number) {
  const piece = board.value[i]
  return `${squareAt(i)}：${piece ? (piece.color === 'w' ? '白' : '黑') + pieceNames[piece.type] : '空位'}${targets.value.includes(i) ? '，可走到此处' : ''}${game.value.last?.to === squareAt(i) ? '，上一手' : ''}`
}
</script>

<template>
  <div class="game-layout">
    <section
      class="game-surface strategy-surface chess-surface"
      aria-label="国际象棋单机版游戏"
      :aria-busy="busy || computer.thinking.value"
    >
      <div class="game-toolbar">
        <div class="game-stats">
          <div>
            <span>{{ computerFirst ? '你执黑棋 · 电脑执白棋' : '你执白棋 · 电脑执黑棋' }}</span
            ><strong class="strategy-turn" role="status">{{ turnText }}</strong>
          </div>
          <div>
            <span>你的步数</span
            ><strong>{{ Math.ceil(Math.max(0, game.ply - (computerFirst ? 1 : 0)) / 2) }}</strong>
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
        class="strategy-board chess-board"
        role="group"
        aria-label="国际象棋单机版棋盘，方向键选格，回车选棋或走棋"
        @keydown="onKey"
        @keydown.esc="clearSelection"
      >
        <button
          v-for="(piece, i) in board"
          :key="i"
          class="board-cell strategy-cell chess-cell"
          :class="{
            'is-dark': (Math.floor(i / 8) + (i % 8)) % 2 === 1,
            'is-selected': source === i,
            'is-target': targets.includes(i) && canPlay,
            'is-last': game.last?.to === squareAt(i),
            'is-origin': game.last?.from === squareAt(i),
            'is-check': piece?.type === 'k' && piece.color === rules.turn() && rules.isCheck(),
          }"
          :data-square="squareAt(i)"
          :tabindex="!result && !promotion && i === selected ? 0 : -1"
          :aria-label="label(i)"
          :aria-pressed="source === i"
          :aria-disabled="!canPlay || !!promotion"
          @click="play(i)"
          @focus="selected = i"
        >
          <span v-if="i % 8 === 0" class="chess-coordinate chess-rank" aria-hidden="true">{{
            8 - Math.floor(i / 8)
          }}</span>
          <span v-if="i >= 56" class="chess-coordinate chess-file" aria-hidden="true">{{
            'abcdefgh'[i % 8]
          }}</span>
          <span v-if="piece" class="strategy-piece"
            ><ChessPiece :piece="piece.type" :side="piece.color"
          /></span>
        </button>
        <GameResult
          v-if="outcome && !busy"
          :message="outcome"
          :tone="
            result?.winner
              ? result.winner === (player === 'w' ? 1 : -1)
                ? 'success'
                : 'ended'
              : undefined
          "
        />
      </div>
      <div
        v-if="promotion"
        ref="promotionElement"
        class="chess-promotion"
        role="group"
        aria-label="选择升变棋子"
        @keydown.esc.stop="clearSelection"
      >
        <p role="status">兵已到达底线，选择升变棋子：</p>
        <div class="game-actions">
          <button
            v-for="piece in ['q', 'r', 'b', 'n'] as const"
            :key="piece"
            class="game-button"
            @click="promote(piece)"
          >
            <ChessPiece :piece="piece" :side="player" />{{ pieceNames[piece] }}</button
          ><button class="game-button" @click="clearSelection">取消</button>
        </div>
      </div>
      <p v-else class="board-hint">
        {{
          source === null
            ? '先选自己的棋子，再点蓝色标记的落点。'
            : '圆点是可走位置，虚线圈表示可以吃子。Esc 取消选棋。'
        }}
      </p>
    </section>
  </div>
</template>
