<script setup lang="ts">
import { computed, inject, nextTick, ref, watch } from 'vue'
import { Flag, Check } from 'lucide-vue-next'
import ChessPiece from '../ChessPiece.vue'
import PlayingCard from '../PlayingCard.vue'
import GameResult from '../GameResult.vue'
import { useGameMotion } from '../useGameMotion'
import { useBoardKeyboard } from '../useBoardKeyboard'
import { gameFullscreenKey } from '../fullscreen'
import { cardLabel, classify } from '../doudizhu'
import { camps, headquarters, rail, neighbors } from '../junqi'
import type { Card } from '../solitaire'
import type { OnlineKind, GameView, RoomPlayer, RoomCommand } from './types'
const props = defineProps<{
  kind: OnlineKind
  game: GameView
  players: RoomPlayer[]
  seat: number
  enabled: boolean
  pending: boolean
}>()
const emit = defineEmits<{ action: [command: Omit<RoomCommand, 'revision'>] }>()
const board = ref<HTMLElement>(),
  focused = ref(0),
  selected = ref<number | null>(null),
  preview = ref<number | null>(null),
  selectedCards = ref<number[]>([]),
  promotionTo = ref<number | null>(null),
  moving = ref(false)
focused.value =
  props.kind === 'chess'
    ? props.seat === 0
      ? 52
      : 12
    : props.kind === 'xiangqi'
      ? props.seat === 0
        ? 54
        : 27
      : props.kind === 'junqi'
        ? props.seat === 0
          ? 30
          : 0
        : props.kind === 'gomoku'
          ? 112
          : 40
let transition = 0
const motion = useGameMotion(),
  fullscreen = inject(gameFullscreenKey)
const count =
  props.kind === 'chess' ? 64 : props.kind === 'gomoku' ? 225 : props.kind === 'junqi' ? 60 : 81
const promotionNames: Record<string, string> = { q: '后', r: '车', b: '象', n: '马' }
const columns =
  props.kind === 'chess' ? 8 : props.kind === 'gomoku' ? 15 : props.kind === 'junqi' ? 5 : 9
const keyboard = useBoardKeyboard(board, focused, columns, props.kind === 'xiangqi' ? 90 : count)
const canAct = computed(
  () =>
    props.enabled &&
    !props.pending &&
    !moving.value &&
    (props.game.status === 'setup'
      ? !props.game.setupReady.includes(props.seat)
      : props.game.status === 'scoring' ||
        (props.game.status === 'playing' && props.game.turn === props.seat)),
)
const side = computed(() => (props.seat === 0 ? 1 : -1))
const targets = computed(() => props.game.targets[selected.value ?? -1] ?? [])
const opponents = computed(() => [(props.seat + 2) % 3, (props.seat + 1) % 3])
const name = (seat: number) => props.players.find((p) => p.seat === seat)?.name ?? '已离开的玩家'
const promotionOptions = computed(() =>
  promotionTo.value === null
    ? []
    : (props.game.promotions[selected.value + ':' + promotionTo.value] ?? []),
)
const resultText = computed(() =>
  !props.game.result
    ? ''
    : (props.game.result.winners.includes(props.seat)
        ? '你赢了！'
        : props.game.result.winners.length
          ? '本局结束。'
          : '本局和棋。') + props.game.result.message,
)
function clear() {
  selected.value = null
  preview.value = null
  promotionTo.value = null
  selectedCards.value = []
}
function send(command: Omit<RoomCommand, 'revision'>) {
  emit('action', command)
  clear()
}
function act(at: number) {
  focused.value = at
  if (!canAct.value) return
  if (props.game.status === 'scoring') {
    if (props.game.board[at]) send({ type: 'dead', to: at })
    return
  }
  if (props.kind === 'go' || props.kind === 'gomoku') {
    if (!targets.value.includes(at)) return
    if (preview.value === at) send({ type: 'move', to: at })
    else preview.value = at
  } else {
    if (selected.value !== null && targets.value.includes(at)) {
      if ((props.game.promotions[selected.value + ':' + at] ?? []).length) promotionTo.value = at
      else send({ type: 'move', from: selected.value, to: at })
    } else selected.value = props.game.board[at]?.side === side.value ? at : null
  }
}
function promote(piece: string) {
  if (selected.value !== null && promotionTo.value !== null)
    send({ type: 'move', from: selected.value, to: promotionTo.value, promotion: piece })
}
function label(at: number) {
  const piece = props.game.board[at]
  return (
    '第 ' +
    (Math.floor(at / columns) + 1) +
    ' 行，第 ' +
    ((at % columns) + 1) +
    ' 列：' +
    (piece ? (piece.side === side.value ? '我方' : '对方') + piece.label : '空位')
  )
}
watch(
  () => props.game.ply,
  async (ply, previous) => {
    const current = ++transition
    clear()
    motion.cancel()
    moving.value = false
    if (ply <= previous || !props.game.last || props.kind === 'doudizhu') return
    const last = props.game.last
    moving.value = true
    await nextTick()
    if (current !== transition) return
    const cells = board.value?.querySelectorAll('.board-cell'),
      from = cells?.[last.from]?.getBoundingClientRect(),
      to = cells?.[last.to]?.getBoundingClientRect()
    const piece = cells?.[last.to]?.querySelector('.strategy-piece, .junqi-piece')
    const scale = fullscreen?.scale.value || 1
    const start =
      from && to
        ? {
            transform:
              'translate(' + (from.x - to.x) / scale + 'px,' + (from.y - to.y) / scale + 'px)',
            opacity: 0.7,
          }
        : { transform: 'scale(.5)', opacity: 0.3 }
    await motion.settle([
      motion.animate(piece, [start, { transform: 'translate(0,0) scale(1)', opacity: 1 }], {
        duration:
          props.kind === 'xiangqi' || props.kind === 'chess' || props.kind === 'junqi' ? 240 : 180,
      }),
    ])
    if (current === transition) moving.value = false
  },
)
watch(() => props.game.status, clear)
function cardFor(card: { rank: number; id: number }): Card {
  return {
    suit: card.id % 4,
    rank:
      card.rank >= 13 ? card.rank + 1 : card.rank === 11 ? 1 : card.rank === 12 ? 2 : card.rank + 3,
    faceUp: true,
  }
}
function toggleCard(id: number) {
  if (canAct.value)
    selectedCards.value = selectedCards.value.includes(id)
      ? selectedCards.value.filter((n) => n !== id)
      : [...selectedCards.value, id]
}
const combination = computed(() =>
  classify(props.game.hand.filter((c) => selectedCards.value.includes(c.id))),
)
function point(at: number) {
  const r = Math.floor(at / 5)
  return { x: 50 + (at % 5) * 100, y: 30 + r * 60 + (r >= 6 ? 80 : 0) }
}
const edges = Array.from({ length: 60 }, (_, at) =>
  neighbors(at)
    .filter((to) => to > at)
    .map((to) => [at, to] as const),
).flat()
const diagonals = [...camps].flatMap((at) =>
  [-6, -4, 4, 6]
    .filter((d) => at + d >= 0 && at + d < 60 && Math.abs(((at + d) % 5) - (at % 5)) === 1)
    .map((d) => [at, at + d] as const),
)
const path = (edges: readonly (readonly [number, number])[]) =>
  edges
    .map(([from, to]) => {
      const a = point(from),
        b = point(to)
      return 'M' + a.x + ' ' + a.y + 'L' + b.x + ' ' + b.y
    })
    .join('')
const roadPath = path([...edges, ...diagonals]),
  railPath = path(edges.filter(([a, b]) => rail(a) && rail(b)))
</script>

<template>
  <div v-if="kind === 'doudizhu'" class="room-dd-board">
    <div class="dd-arena">
      <div class="dd-bottom" aria-label="地主底牌">
        <span>地主底牌</span>
        <div class="dd-bottom-cards">
          <template v-if="game.bottom.length"
            ><span
              v-for="card in game.bottom"
              :key="card.id"
              class="dd-mini-card playing-card"
              :class="{ 'is-red': cardFor(card).suit === 1 || cardFor(card).suit === 3 }"
              :aria-label="cardLabel(card)"
              ><PlayingCard :card="cardFor(card)" /></span
          ></template>
          <span
            v-for="n in game.bottom.length ? 0 : 3"
            :key="n"
            class="dd-mini-card playing-card is-hidden"
            aria-label="未揭晓的底牌"
            ><span class="dd-card-back">✦</span></span
          >
        </div>
        <span class="dd-bottom-caption">{{
          game.landlord < 0 ? '叫分后揭晓' : name(game.landlord) + '是地主'
        }}</span>
      </div>
      <article
        v-for="(opponent, index) in opponents"
        :key="opponent"
        class="dd-seat"
        :class="[
          index === 0 ? 'dd-seat-left' : 'dd-seat-right',
          { 'is-current': game.turn === opponent },
        ]"
      >
        <div class="dd-seat-avatar">{{ name(opponent).slice(0, 1) }}</div>
        <h2>{{ name(opponent) }}</h2>
        <span class="dd-role">{{
          game.landlord < 0
            ? game.bids[opponent] < 0
              ? '等待叫分'
              : game.bids[opponent]
                ? '叫 ' + game.bids[opponent] + ' 分'
                : '不叫'
            : game.landlord === opponent
              ? '地主'
              : '农民'
        }}</span>
        <p class="dd-remaining">
          剩余 <strong>{{ game.counts[opponent] }}</strong> 张
        </p>
      </article>
      <div class="dd-table">
        <div class="dd-trick">
          <span class="dd-trick-label">{{
            game.lastCards.length
              ? name(game.lastPlayer) + '出的牌'
              : game.landlord < 0
                ? '先看看手牌，再决定叫几分。'
                : '等待领出'
          }}</span>
          <TransitionGroup name="dd-play" tag="div" class="dd-played"
            ><span
              v-for="card in game.lastCards"
              :key="card.id"
              class="dd-mini-card playing-card"
              :class="{ 'is-red': cardFor(card).suit === 1 || cardFor(card).suit === 3 }"
              :aria-label="cardLabel(card)"
              ><PlayingCard :card="cardFor(card)" /></span
          ></TransitionGroup>
        </div>
      </div>
      <GameResult
        v-if="game.result"
        :message="resultText"
        :tone="game.result.winners.includes(seat) ? 'success' : 'ended'"
      />
    </div>
    <div class="dd-controls">
      <div v-if="game.landlord < 0" class="dd-actions">
        <button class="game-button" :disabled="!canAct" @click="send({ type: 'move', bid: 0 })">
          不叫</button
        ><button
          v-for="n in 3"
          :key="n"
          class="game-button"
          :disabled="!canAct || n <= Math.max(...game.bids)"
          @click="send({ type: 'move', bid: n })"
        >
          叫 {{ n }} 分
        </button>
      </div>
      <div v-else class="dd-actions">
        <button
          class="game-button"
          :disabled="!canAct || !game.canPass"
          @click="send({ type: 'move', cards: [] })"
        >
          不出</button
        ><button class="game-button" :disabled="!canAct" @click="selectedCards = [...game.hint]">
          提示</button
        ><button
          class="game-button room-primary"
          :disabled="!canAct || !combination"
          @click="send({ type: 'move', cards: [...selectedCards] })"
        >
          出牌
        </button>
      </div>
      <span class="dd-selection">{{
        selectedCards.length
          ? '已选 ' + selectedCards.length + ' 张' + (combination ? ' · ' + combination.kind : '')
          : '点选手牌，可选择多张。'
      }}</span>
    </div>
    <div class="dd-hand-area" :class="{ 'is-current': game.turn === seat }">
      <div class="dd-hand-heading">
        <span class="dd-self"
          ><strong>{{ name(seat) }}</strong
          ><span class="dd-role">{{
            game.landlord < 0 ? '我的手牌' : game.landlord === seat ? '地主' : '农民'
          }}</span></span
        ><span>{{ game.hand.length }} 张</span>
      </div>
      <TransitionGroup tag="div" name="dd-hand" class="dd-hand-row room-hand" aria-label="我的手牌"
        ><button
          v-for="card in game.hand"
          :key="card.id"
          class="dd-card"
          :class="{ 'is-selected': selectedCards.includes(card.id) }"
          :disabled="!canAct"
          :aria-pressed="selectedCards.includes(card.id)"
          :aria-label="cardLabel(card)"
          @click="toggleCard(card.id)"
        >
          <span
            class="playing-card"
            :class="{ 'is-red': cardFor(card).suit === 1 || cardFor(card).suit === 3 }"
            ><PlayingCard :card="cardFor(card)"
          /></span></button
      ></TransitionGroup>
    </div>
  </div>
  <template v-else>
    <div :class="{ 'junqi-board-frame': kind === 'junqi' }">
      <div
        ref="board"
        class="room-board"
        :class="kind === 'junqi' ? 'junqi-board' : ['strategy-board', kind + '-board']"
        role="group"
        :aria-label="'联机棋盘，方向键选格，回车操作'"
        :aria-busy="moving || pending"
        @keydown="keyboard"
        @keydown.esc="clear"
      >
        <svg
          v-if="kind === 'xiangqi'"
          class="strategy-lines"
          viewBox="0 0 900 1000"
          aria-hidden="true"
        >
          <path v-for="y in 10" :key="'h' + y" :d="'M 50 ' + (y * 100 - 50) + ' H 850'" />
          <path
            v-for="x in 9"
            :key="'v' + x"
            :d="
              x === 1 || x === 9
                ? 'M ' + (x * 100 - 50) + ' 50 V 950'
                : 'M ' + (x * 100 - 50) + ' 50 V 450 M ' + (x * 100 - 50) + ' 550 V 950'
            "
          />
          <path d="M350 50 L550 250 M550 50 L350 250 M350 750 L550 950 M550 750 L350 950" />
          <text x="240" y="510">楚 河</text>
          <text x="660" y="510">汉 界</text>
        </svg>
        <svg
          v-else-if="kind === 'gomoku' || kind === 'go'"
          class="strategy-lines"
          :viewBox="'0 0 ' + columns * 100 + ' ' + columns * 100"
          aria-hidden="true"
        >
          <path
            v-for="n in columns"
            :key="n"
            :d="
              'M 50 ' +
              (n * 100 - 50) +
              ' H ' +
              (columns * 100 - 50) +
              ' M ' +
              (n * 100 - 50) +
              ' 50 V ' +
              (columns * 100 - 50)
            "
          />
          <circle :cx="columns * 50" :cy="columns * 50" r="8" />
        </svg>
        <svg
          v-else-if="kind === 'junqi'"
          class="junqi-roads"
          viewBox="0 0 500 800"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <path class="junqi-road" :d="roadPath" />
          <path class="junqi-rail-under" :d="railPath" />
          <path class="junqi-rail" :d="railPath" />
          <g
            v-for="n in 60"
            :key="n"
            class="junqi-station"
            :class="{ 'is-camp': camps.has(n - 1), 'is-base': headquarters.has(n - 1) }"
            :transform="'translate(' + point(n - 1).x + ',' + point(n - 1).y + ')'"
          >
            <ellipse v-if="camps.has(n - 1)" rx="40" ry="22" />
            <rect
              v-else
              x="-40"
              y="-20"
              width="80"
              height="40"
              :rx="headquarters.has(n - 1) ? 8 : 4"
            />
          </g>
          <text class="junqi-boundary" x="250" y="400" text-anchor="middle">山 界</text>
        </svg>
        <button
          v-for="(piece, at) in game.board"
          :key="at"
          class="board-cell"
          :class="[
            kind === 'junqi' ? 'junqi-cell' : 'strategy-cell',
            {
              'chess-cell': kind === 'chess',
              'is-dark': kind === 'chess' && (Math.floor(at / 8) + (at % 8)) % 2 === 1,
              'is-selected': selected === at || preview === at,
              'is-target': selected !== null && targets.includes(at),
              'is-last': game.last?.to === at,
              'is-last-to': game.last?.to === at,
              'is-origin': game.last?.from === at,
              'is-last-from': game.last?.from === at,
              'is-camp': kind === 'junqi' && camps.has(at),
              'is-base': kind === 'junqi' && headquarters.has(at),
              'is-dead': game.dead.includes(at),
            },
          ]"
          :style="
            kind === 'junqi'
              ? { gridColumn: (at % 5) + 1, gridRow: Math.floor(at / 5) + 1 + (at >= 30 ? 1 : 0) }
              : undefined
          "
          :tabindex="at === focused ? 0 : -1"
          :data-at="at"
          :data-square="
            kind === 'chess' ? 'abcdefgh'[at % 8] + (8 - Math.floor(at / 8)) : undefined
          "
          :aria-label="label(at)"
          :aria-disabled="!canAct"
          :aria-pressed="selected === at || preview === at"
          @click="act(at)"
          @focus="focused = at"
        >
          <span v-if="kind === 'chess' && at % 8 === 0" class="chess-coordinate chess-rank">{{
            8 - Math.floor(at / 8)
          }}</span
          ><span v-if="kind === 'chess' && at >= 56" class="chess-coordinate chess-file">{{
            'abcdefgh'[at % 8]
          }}</span>
          <span
            v-if="kind === 'junqi' && piece"
            class="junqi-piece"
            :class="{
              'is-self': piece.side === side,
              'is-enemy': piece.side !== side,
              'is-hidden': piece.hidden,
            }"
            ><b>{{ piece.label }}</b
            ><small>{{ piece.side === side ? '我方' : '对方' }}</small></span
          >
          <span v-else-if="kind === 'junqi' && camps.has(at)" class="junqi-terrain">行营</span
          ><Flag
            v-else-if="kind === 'junqi' && headquarters.has(at)"
            class="junqi-terrain"
            :size="16"
          />
          <span
            v-else-if="piece || preview === at"
            class="strategy-piece"
            :class="{
              'is-red': kind === 'xiangqi' && piece && piece.side === 1,
              'is-black':
                kind === 'xiangqi' ? piece && piece.side === -1 : (piece?.side ?? side) === 1,
              'is-white': kind !== 'xiangqi' && (piece?.side ?? side) === -1,
              'is-preview': preview === at,
            }"
            ><ChessPiece
              v-if="kind === 'chess' && piece?.piece"
              :piece="piece.piece"
              :side="piece.side === 1 ? 'w' : 'b'"
            /><template v-else-if="kind === 'xiangqi'">{{ piece?.label }}</template></span
          >
          <span
            v-if="kind === 'junqi' && selected !== null && targets.includes(at)"
            class="junqi-target"
            >●</span
          >
          <span
            v-if="kind === 'go' && !piece && game.score?.ownership[at]"
            class="go-territory"
            :class="game.score.ownership[at] === 1 ? 'is-black' : 'is-white'"
          ></span>
        </button>
        <GameResult
          v-if="game.result && !moving"
          :message="resultText"
          :tone="game.result.winners.includes(seat) ? 'success' : 'ended'"
        />
      </div>
    </div>
    <div
      v-if="promotionOptions.length"
      class="chess-promotion"
      role="group"
      aria-label="选择升变棋子"
    >
      <span>兵升变为</span
      ><button
        v-for="piece in promotionOptions"
        :key="piece"
        class="game-button"
        :disabled="!canAct"
        @click="promote(piece)"
      >
        {{ promotionNames[piece] }}</button
      ><button class="game-button" @click="clear">取消</button>
    </div>
    <div v-if="kind === 'gomoku' || kind === 'go'" class="gomoku-confirm">
      <span>{{
        game.status === 'scoring'
          ? '点选整块死子，再点恢复；双方确认后结算。'
          : preview === null
            ? '先选一个交点，再确认落子。'
            : '第 ' +
              (Math.floor(preview / columns) + 1) +
              ' 行，第 ' +
              ((preview % columns) + 1) +
              ' 列'
      }}</span>
      <div class="game-actions">
        <template v-if="game.status === 'scoring'"
          ><button
            class="game-button"
            :disabled="!canAct || game.scoreReady.includes(seat)"
            @click="send({ type: 'score' })"
          >
            <Check :size="16" />{{
              game.scoreReady.includes(seat) ? '已确认，等待对手' : '确认数子'
            }}</button
          ><button class="game-button" :disabled="!canAct" @click="send({ type: 'resume-play' })">
            继续对局
          </button></template
        ><template v-else
          ><button
            class="game-button"
            :disabled="!canAct || preview === null"
            @click="preview !== null && send({ type: 'move', to: preview })"
          >
            确认落子</button
          ><button
            v-if="kind === 'go'"
            class="game-button"
            :disabled="!canAct"
            @click="send({ type: 'move', to: -1 })"
          >
            停一手
          </button></template
        >
      </div>
    </div>
    <div v-if="kind === 'junqi' && game.status === 'setup'" class="gomoku-confirm">
      <span>交换两枚我方棋子布阵，双方确认后开始。</span
      ><button
        class="game-button room-primary"
        :disabled="!canAct"
        @click="send({ type: 'setup-ready' })"
      >
        {{ game.setupReady.includes(seat) ? '已确认，等待对手' : '确认布阵' }}
      </button>
    </div>
  </template>
</template>
