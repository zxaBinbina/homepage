<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { Bot, Crown, Lightbulb, RotateCcw, UserRound, X } from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import GameResult from './GameResult.vue'
import PlayingCard from './PlayingCard.vue'
import type { Card } from './solitaire'
import {
  bid,
  canBeat,
  cardLabel,
  cardText,
  chooseComputer,
  classify,
  computerBid,
  newDoudizhu,
  playDoudizhu,
  type DDCard,
} from './doudizhu'

type TableMove = { cards: DDCard[]; label: string }
const emptyMoves = (): TableMove[] => Array.from({ length: 3 }, () => ({ cards: [], label: '' }))
const game = ref(newDoudizhu())
const selected = ref<number[]>([])
const moves = ref(emptyMoves())
const notice = ref('先看看手牌，再决定叫几分。')
const names = ['你', '电脑 A', '电脑 B']
const handFrame = ref<HTMLElement>()
const compactHand = ref(false)
const focusedCard = ref(game.value.hands[0]![0]!.id)
let observer: ResizeObserver | undefined
let handWidth = 0
let timer: ReturnType<typeof setTimeout> | undefined

const mine = computed(() => game.value.hands[0]!)
const bidding = computed(() => game.value.landlord < 0)
const allPassed = computed(() => bidding.value && game.value.bidCount === 3)
const canAct = computed(
  () => game.value.turn === 0 && game.value.finished === null && !allPassed.value,
)
const picked = computed(() => mine.value.filter((card) => selected.value.includes(card.id)))
const combination = computed(() => classify(picked.value))
const valid = computed(
  () => !bidding.value && canAct.value && canBeat(picked.value, game.value.last),
)
const won = computed(
  () => (game.value.finished === game.value.landlord) === (game.value.landlord === 0),
)
const outcome = computed(() =>
  game.value.finished === null ? '' : won.value ? '你赢了！' : '这局对方获胜，再来一局吧。',
)
const status = computed(
  () =>
    (game.value.finished !== null ? '本局结束' : '') ||
    (allPassed.value
      ? '大家都不叫，重新发牌吧'
      : `${names[game.value.turn]}${bidding.value ? '叫分' : '出牌'}`),
)
const handRows = computed(() => {
  const split = Math.ceil(mine.value.length / 2)
  return compactHand.value && mine.value.length > 10
    ? [mine.value.slice(0, split), mine.value.slice(split)]
    : [mine.value]
})
const selectionText = computed(() => {
  if (bidding.value) return canAct.value ? '好牌在手，叫几分？' : '等电脑叫分'
  if (game.value.finished !== null) return '本局结束'
  if (!canAct.value) return '等对方出牌'
  if (!selected.value.length)
    return game.value.last.length ? '选牌压过上一手，或选择不出' : '轮到你领出，选一手好牌'
  if (!combination.value) return `已选 ${selected.value.length} 张 · 尚未组成牌型`
  return `${combination.value.kind} · ${selected.value.length} 张${valid.value ? '' : ' · 还压不过上一手'}`
})
function identity(player: number) {
  return bidding.value ? '待定' : game.value.landlord === player ? '地主' : '农民'
}
function current(player: number) {
  return game.value.turn === player && game.value.finished === null && !allPassed.value
}
function red(card: DDCard) {
  return card.rank === 14 || (card.rank < 13 && card.id % 2 === 1)
}
function cardFor(card: DDCard): Card {
  const rank =
    card.rank < 11
      ? card.rank + 3
      : card.rank === 11
        ? 1
        : card.rank === 12
          ? 2
          : card.rank === 13
            ? 14
            : 15
  return { suit: card.rank < 13 ? card.id % 4 : 0, rank, faceUp: true }
}
function stop() {
  clearTimeout(timer)
  timer = undefined
}
function restart() {
  stop()
  cancelSweep()
  game.value = newDoudizhu()
  selected.value = []
  moves.value = emptyMoves()
  focusedCard.value = mine.value[0]!.id
  notice.value = '先看看手牌，再决定叫几分。'
}
function commitBid(score: number) {
  const player = game.value.turn,
    next = bid(game.value, score)
  if (!next) return
  moves.value[player] = { cards: [], label: score ? `叫 ${score} 分` : '不叫' }
  game.value = next
  if (next.landlord >= 0) {
    moves.value = emptyMoves()
    focusedCard.value = mine.value[0]!.id
    notice.value = `${names[next.landlord]}成为地主，收下三张底牌并先出。`
  }
  schedule()
}
function commitCards(cards: DDCard[]) {
  const player = game.value.turn,
    next = playDoudizhu(game.value, cards)
  if (!next) {
    notice.value = '请选择合法牌型，并大过上一手。'
    return
  }
  cancelSweep()
  moves.value[player] = {
    cards: cards.length ? next.last : [],
    label: cards.length ? classify(cards)!.kind : '不出',
  }
  // Two passes start a fresh trick. Clear a seat's previous play when its next turn starts.
  if (!next.last.length) moves.value = emptyMoves()
  else if (next.finished === null) moves.value[next.turn] = { cards: [], label: '' }
  game.value = next
  selected.value = []
  if (!mine.value.some((card) => card.id === focusedCard.value))
    focusedCard.value = mine.value[0]?.id ?? -1
  notice.value =
    outcome.value ||
    (!next.last.length
      ? `${names[next.turn]}重新领出。`
      : `${names[player]}${cards.length ? `打出${classify(cards)!.kind}` : '选择不出'}`)
  schedule()
}
function schedule() {
  stop()
  if (game.value.finished !== null || game.value.turn === 0 || allPassed.value) return
  timer = setTimeout(() => {
    timer = undefined
    if (bidding.value)
      commitBid(computerBid(game.value.hands[game.value.turn]!, Math.max(...game.value.bids)))
    else commitCards(chooseComputer(game.value))
  }, 650)
}
function toggle(card: DDCard) {
  if (!canAct.value || bidding.value) return
  selected.value = selected.value.includes(card.id)
    ? selected.value.filter((id) => id !== card.id)
    : [...selected.value, card.id]
}
function hint() {
  if (!canAct.value || bidding.value) return
  const cards = chooseComputer(game.value)
  selected.value = cards.map((card) => card.id)
  notice.value = cards.length
    ? `建议：${classify(cards)!.kind}，点击「出牌」确认。`
    : '建议这一手不出。'
}
function play() {
  if (valid.value) commitCards(picked.value)
}
function pass() {
  if (canAct.value && !bidding.value && game.value.last.length) commitCards([])
}
function chooseBid(score: number) {
  if (canAct.value && bidding.value) commitBid(score)
}
function clearSelection() {
  cancelSweep()
  selected.value = []
}
async function handKey(event: KeyboardEvent) {
  const target = (event.target as HTMLElement).closest<HTMLButtonElement>('.dd-card')
  if (
    !target ||
    !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)
  )
    return
  event.preventDefault()
  const index = mine.value.findIndex((card) => card.id === Number(target.dataset.cardId))
  const rowSize = handRows.value[0]!.length
  const next =
    event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? mine.value.length - 1
        : index +
          (event.key === 'ArrowLeft'
            ? -1
            : event.key === 'ArrowRight'
              ? 1
              : event.key === 'ArrowUp'
                ? -rowSize
                : rowSize)
  focusedCard.value = mine.value[Math.max(0, Math.min(mine.value.length - 1, next))]!.id
  await nextTick()
  handFrame.value
    ?.querySelector<HTMLButtonElement>(`[data-card-id="${focusedCard.value}"]`)
    ?.focus({ preventScroll: true })
}

// Horizontal sweeps select a range; vertical touch gestures keep native page scrolling.
type Sweep = {
  pointer: number
  target: HTMLButtonElement
  x: number
  y: number
  start: number
  initial: number[]
  remove: boolean
  active: boolean
}
let sweep: Sweep | undefined
let suppressClick = false
function startSweep(event: PointerEvent) {
  if (!canAct.value || bidding.value || !event.isPrimary || event.button !== 0 || sweep) return
  const target = (event.target as HTMLElement).closest<HTMLButtonElement>('.dd-card')
  if (!target) return
  const id = Number(target.dataset.cardId)
  suppressClick = false
  sweep = {
    pointer: event.pointerId,
    target,
    x: event.clientX,
    y: event.clientY,
    start: mine.value.findIndex((card) => card.id === id),
    initial: [...selected.value],
    remove: selected.value.includes(id),
    active: false,
  }
  target.setPointerCapture(event.pointerId)
}
function moveSweep(event: PointerEvent) {
  if (!sweep || sweep.pointer !== event.pointerId) return
  if (!sweep.active) {
    if (Math.abs(event.clientY - sweep.y) > Math.abs(event.clientX - sweep.x)) {
      cancelSweep()
      return
    }
    if (Math.abs(event.clientX - sweep.x) < 6) return
    sweep.active = true
  }
  event.preventDefault()
  const target = document
    .elementFromPoint(event.clientX, event.clientY)
    ?.closest<HTMLButtonElement>('.dd-card')
  if (!target || !handFrame.value?.contains(target)) return
  const index = mine.value.findIndex((card) => card.id === Number(target.dataset.cardId))
  const range = mine.value
    .slice(Math.min(index, sweep.start), Math.max(index, sweep.start) + 1)
    .map((card) => card.id)
  selected.value = sweep.remove
    ? sweep.initial.filter((id) => !range.includes(id))
    : [...new Set([...sweep.initial, ...range])]
}
function endSweep(event: PointerEvent) {
  if (!sweep || sweep.pointer !== event.pointerId) return
  suppressClick = sweep.active
  sweep = undefined
}
function cancelSweep() {
  if (!sweep) return
  const previous = sweep
  sweep = undefined
  if (previous.active) selected.value = previous.initial
  if (previous.target.hasPointerCapture(previous.pointer))
    previous.target.releasePointerCapture(previous.pointer)
  suppressClick = false
}
function handClick(event: MouseEvent) {
  if (suppressClick && event.detail > 0) {
    event.preventDefault()
    event.stopPropagation()
    suppressClick = false
  }
}
onMounted(() => {
  observer = new ResizeObserver((entries) => {
    const width = entries[0]!.contentRect.width
    const compact = width < 540
    if (Math.abs(width - handWidth) > 1) cancelSweep()
    handWidth = width
    compactHand.value = compact
  })
  if (handFrame.value) observer.observe(handFrame.value)
  window.addEventListener('blur', cancelSweep)
})
onBeforeUnmount(() => {
  stop()
  cancelSweep()
  observer?.disconnect()
  window.removeEventListener('blur', cancelSweep)
})
</script>

<template>
  <div class="game-layout dd-layout">
    <section
      class="game-surface doudizhu-surface"
      aria-label="斗地主牌桌"
      @keydown.esc="clearSelection"
    >
      <div class="game-toolbar dd-toolbar">
        <div class="dd-round-heading">
          <span class="dd-round-mark" aria-hidden="true">♠</span>
          <div>
            <span class="dd-phase">{{ bidding ? '叫分阶段' : '三人对局' }}</span
            ><strong class="strategy-turn" role="status">{{ status }}</strong>
          </div>
        </div>
        <div class="dd-toolbar-end">
          <span class="dd-multiplier"
            >本局倍数 <strong>×{{ game.multiplier }}</strong></span
          >
          <div class="game-actions">
            <button class="game-button" @click="restart">
              <RotateCcw :size="16" aria-hidden="true" />重新发牌</button
            ><GameFullscreenButton />
          </div>
        </div>
      </div>

      <div class="dd-arena">
        <div class="dd-bottom" aria-label="地主底牌">
          <span>地主底牌</span>
          <div class="dd-bottom-cards">
            <span
              v-for="(card, i) in game.bottom"
              :key="i"
              class="dd-mini-card playing-card"
              :class="{ 'is-red': red(card), 'is-hidden': bidding }"
              :aria-label="bidding ? '未揭晓的底牌' : cardLabel(card)"
              ><span v-if="bidding" class="dd-card-back" aria-hidden="true">✦</span
              ><PlayingCard v-else :card="cardFor(card)"
            /></span>
          </div>
          <span class="dd-bottom-caption">{{
            bidding ? '叫分后揭晓' : `${names[game.landlord]}是地主`
          }}</span>
        </div>

        <article
          v-for="player in [2, 1]"
          :key="player"
          class="dd-seat"
          :class="[
            player === 2 ? 'dd-seat-left' : 'dd-seat-right',
            { 'is-current': current(player), 'is-landlord': game.landlord === player },
          ]"
          :aria-label="`${names[player]}，${identity(player)}，剩余 ${game.hands[player]!.length} 张`"
        >
          <div class="dd-seat-avatar">
            <Bot :size="26" aria-hidden="true" /><Crown
              v-if="game.landlord === player"
              class="dd-crown"
              :size="16"
              aria-hidden="true"
            />
          </div>
          <h2>{{ names[player] }}</h2>
          <span class="dd-role"
            ><Crown v-if="game.landlord === player" :size="12" aria-hidden="true" />{{
              identity(player)
            }}<span v-if="current(player)" class="dd-turn-dot" aria-hidden="true"></span
          ></span>
          <div
            class="dd-remaining"
            :class="{ 'is-low': !bidding && game.hands[player]!.length <= 2 }"
          >
            <span class="dd-deck" aria-hidden="true">✦</span
            ><strong>{{ game.hands[player]!.length }}</strong
            ><span>张</span>
          </div>
          <p class="dd-seat-status">
            {{
              current(player)
                ? bidding
                  ? '正在叫分'
                  : '正在思考'
                : moves[player]!.label || (bidding ? '等待叫分' : '等待出牌')
            }}
          </p>
          <p v-if="game.finished !== null && game.hands[player]!.length" class="dd-revealed">
            {{ game.hands[player]!.map(cardText).join(' · ') }}
          </p>
        </article>

        <div class="dd-table">
          <div class="dd-table-watermark" aria-hidden="true">
            <span>♠ ♥ ♣ ♦</span><span>好牌慢慢打</span>
          </div>
          <div
            v-for="player in [2, 1, 0]"
            :key="player"
            class="dd-trick"
            :class="[
              `dd-trick-${player}`,
              { 'is-leading': game.last.length && game.lastPlayer === player },
            ]"
            :aria-label="`${names[player]}的出牌`"
          >
            <span class="dd-trick-label">{{ moves[player]!.label }}</span>
            <TransitionGroup name="dd-play" tag="div" class="dd-played"
              ><span
                v-for="card in moves[player]!.cards"
                :key="card.id"
                class="dd-play-card playing-card"
                :class="{ 'is-red': red(card) }"
                :aria-label="cardLabel(card)"
                ><PlayingCard :card="cardFor(card)" /></span
            ></TransitionGroup>
          </div>
          <GameResult
            v-if="game.finished !== null || allPassed"
            :message="allPassed ? '这局都不叫，换副好牌吧。' : outcome"
            :tone="!allPassed && won ? 'success' : 'ended'"
            ><p v-if="!allPassed" class="dd-result-detail">
              {{ game.finished === game.landlord ? '地主' : '农民' }}获胜 · 本局
              {{ game.multiplier }} 倍
            </p>
            <button class="game-button dd-primary" @click="restart">
              <RotateCcw :size="16" aria-hidden="true" />再来一局
            </button></GameResult
          >
        </div>
      </div>

      <div class="dd-controls">
        <div v-if="bidding && !allPassed" class="dd-actions">
          <button
            v-for="score in [0, 1, 2, 3]"
            :key="score"
            class="game-button"
            :class="{ 'dd-primary': score === 3 }"
            :disabled="!canAct || (score > 0 && score <= Math.max(...game.bids))"
            @click="chooseBid(score)"
          >
            {{ score ? `叫 ${score} 分` : '不叫' }}
          </button>
        </div>
        <div v-else-if="!allPassed && game.finished === null" class="dd-actions">
          <button class="game-button" :disabled="!canAct || !game.last.length" @click="pass">
            不出</button
          ><button class="game-button dd-primary" :disabled="!valid" @click="play">出牌</button
          ><button class="game-button" :disabled="!canAct" @click="hint">
            <Lightbulb :size="16" aria-hidden="true" />提示</button
          ><button
            class="game-button dd-clear"
            :disabled="!selected.length"
            @click="clearSelection"
          >
            <X :size="16" aria-hidden="true" />重选
          </button>
        </div>
        <p class="dd-selection" :class="{ 'is-valid': valid }" role="status">{{ selectionText }}</p>
      </div>

      <section
        class="dd-hand-area"
        :class="{ 'is-compact': compactHand, 'is-current': current(0) }"
        aria-label="你的手牌区域"
      >
        <div class="dd-hand-heading">
          <div class="dd-self">
            <span class="dd-self-avatar"><UserRound :size="18" aria-hidden="true" /></span
            ><strong>你</strong
            ><span class="dd-role"
              ><Crown v-if="game.landlord === 0" :size="13" aria-hidden="true" />{{
                identity(0)
              }}</span
            ><span>{{ mine.length }} 张</span>
          </div>
          <span class="dd-hand-tip">{{ bidding ? '从大到小排列' : '点选 / 划选手牌' }}</span>
        </div>
        <div
          ref="handFrame"
          class="dd-hand"
          role="group"
          aria-label="你的手牌"
          aria-describedby="dd-hand-help"
          @keydown="handKey"
          @pointerdown="startSweep"
          @pointermove="moveSweep"
          @pointerup="endSweep"
          @pointercancel="cancelSweep"
          @lostpointercapture="cancelSweep"
          @click.capture="handClick"
        >
          <TransitionGroup
            v-for="(row, i) in handRows"
            :key="`${compactHand ? 'compact' : 'wide'}-${i}`"
            name="dd-hand"
            tag="div"
            class="dd-hand-row"
            ><button
              v-for="card in row"
              :key="card.id"
              class="dd-card"
              :class="{ 'is-selected': selected.includes(card.id), 'is-ten': card.rank === 7 }"
              :data-card-id="card.id"
              :aria-label="cardLabel(card)"
              :aria-pressed="selected.includes(card.id)"
              :tabindex="card.id === focusedCard ? 0 : -1"
              :disabled="!canAct || bidding"
              @focus="focusedCard = card.id"
              @click="toggle(card)"
            >
              <span class="playing-card" :class="{ 'is-red': red(card) }"
                ><PlayingCard :card="cardFor(card)" /><span
                  v-if="selected.includes(card.id)"
                  class="dd-selected-mark"
                  aria-hidden="true"
                  >✓</span
                ></span
              >
            </button></TransitionGroup
          >
        </div>
        <p id="dd-hand-help" class="sr-only">
          方向键、Home 或 End 移动到手牌，回车或空格选牌，Escape
          清空选择。也可以点击或横向划过多张牌。
        </p>
      </section>
      <p class="sr-only" role="status">{{ notice }}</p>
    </section>
  </div>
</template>
