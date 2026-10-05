<script setup lang="ts">
import { computed, inject, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { gameFullscreenKey } from './fullscreen'
import { RotateCcw, Smartphone, Undo2, X } from 'lucide-vue-next'
import PlayingCard from './PlayingCard.vue'
import GameFullscreenButton from './GameFullscreenButton.vue'
import SolitaireCelebration from './SolitaireCelebration.vue'
import { useGameMotion } from './useGameMotion'
import { cardId, useSolitaireDrag, type CardPosition } from './useSolitaireDrag'
import {
  canFinish,
  cardName,
  drawCard,
  finishSolitaire,
  moveCard,
  newSolitaire,
  redCard,
  solitaireWon,
  sourceCards,
  suitNames,
  suits,
  type CardSource,
  type CardTarget,
  type SolitaireGame,
} from './solitaire'

const game = ref(newSolitaire())
const fullscreen = inject(gameFullscreenKey)
const selected = ref<CardSource | null>(null)
const history = ref<SolitaireGame[]>([])
const surface = ref<HTMLElement>()
const scroll = ref<HTMLElement>()
const stage = ref<HTMLElement>()
const motion = useGameMotion()
const moving = ref(false)
const celebrating = ref(false)
const celebrationKey = ref(0)
const celebrationOrigins = ref<{ x: number; y: number }[]>([])
const orientationDismissed = ref(false)
const won = computed(() => solitaireWon(game.value))
const collected = computed(() => game.value.foundations.reduce((sum, pile) => sum + pile.length, 0))
const dragging = useSolitaireDrag({
  game,
  surface,
  scroll,
  canStart: () => !moving.value && !won.value,
  scale: () => fullscreen?.scale.value ?? 1,
  select: (source) => {
    selected.value = source
  },
  drop: (source, target, origins) => {
    const next = moveCard(game.value, source, target)
    if (next) {
      void commit(next, origins)
    }
  },
  cancel: () => {
    selected.value = null
  },
})
const { drag: dragState, ghost: dragGhost } = dragging
const locked = computed(() => moving.value || !!dragState.value)
let turn = 0
function positions() {
  const result = new Map<string, CardPosition>()
  surface.value?.querySelectorAll<HTMLElement>('[data-card-id]').forEach((element) => {
    const rect = element.getBoundingClientRect()
    result.set(element.dataset.cardId!, {
      x: rect.left,
      y: rect.top,
      width: rect.width,
      height: rect.height,
      faceUp: !element.classList.contains('card-back'),
    })
  })
  return result
}
function celebrate() {
  if (!won.value || motion.reduced.value || document.hidden) return
  const bounds = stage.value?.getBoundingClientRect()
  if (!bounds) return
  celebrationOrigins.value = Array.from(surface.value!.querySelectorAll('.foundation-card')).map(
    (element) => {
      const rect = element.getBoundingClientRect()
      return { x: rect.left + rect.width / 2 - bounds.left, y: rect.top - bounds.top }
    },
  )
  celebrationKey.value++
  celebrating.value = true
}
async function commit(next: SolitaireGame, origins?: Map<string, CardPosition>, remember = true) {
  if (locked.value || next === game.value) return
  const current = ++turn
  const before = positions()
  origins?.forEach((position, id) => before.set(id, position))
  const previouslyWon = won.value
  celebrating.value = false
  if (remember) {
    history.value.push(game.value)
    if (history.value.length > 100) history.value.shift()
  }
  moving.value = true
  game.value = next
  selected.value = null
  await nextTick()
  if (current !== turn) return
  fullscreen?.fit()
  const scale = fullscreen?.scale.value ?? 1
  const animated: HTMLElement[] = []
  const stacks = new Set<HTMLElement>()
  const animations: (Animation | null)[] = []
  surface.value?.querySelectorAll<HTMLElement>('[data-card-id]').forEach((element) => {
    const old = before.get(element.dataset.cardId!)
    if (!old) return
    const rect = element.getBoundingClientRect()
    const dx = (old.x - rect.left) / scale,
      dy = (old.y - rect.top) / scale
    const flip = old.faceUp !== !element.classList.contains('card-back')
    if (Math.abs(dx) < 0.5 && Math.abs(dy) < 0.5 && !flip) return
    element.classList.add('is-card-moving')
    const stack = element.closest<HTMLElement>('.solitaire-slot, .solitaire-column')
    if (stack) {
      stack.classList.add('is-stack-moving')
      stacks.add(stack)
    }
    animated.push(element)
    const frames: Keyframe[] = flip
      ? [
          { transform: `translate3d(${dx}px,${dy}px,0) rotateY(180deg) rotateZ(0deg)` },
          {
            transform: `translate3d(${dx * 0.5}px,${dy * 0.5 - 18}px,42px) rotateY(90deg) rotateZ(-6deg)`,
            offset: 0.5,
          },
          { transform: 'translate3d(0,0,0) rotateY(0deg) rotateZ(0deg)' },
        ]
      : [{ transform: `translate(${dx}px,${dy}px)` }, { transform: 'translate(0,0)' }]
    animations.push(
      motion.animate(element, frames, {
        duration: flip ? 340 : 260,
        fill: 'both',
        ...(flip ? { easing: 'ease-in-out' } : {}),
      }),
    )
  })
  await motion.settle(animations)
  animated.forEach((element) => element.classList.remove('is-card-moving'))
  stacks.forEach((element) => element.classList.remove('is-stack-moving'))
  if (current !== turn) return
  moving.value = false
  if (won.value && !previouslyWon) celebrate()
}
function stopMotion() {
  turn++
  dragging.reset()
  motion.cancel()
  surface.value
    ?.querySelectorAll('.is-card-moving')
    .forEach((element) => element.classList.remove('is-card-moving'))
  surface.value
    ?.querySelectorAll('.is-stack-moving')
    .forEach((element) => element.classList.remove('is-stack-moving'))
  surface.value
    ?.querySelectorAll('.is-recycling-card')
    .forEach((element) => element.classList.remove('is-recycling-card'))
  moving.value = false
  celebrating.value = false
}
function restart() {
  stopMotion()
  game.value = newSolitaire()
  history.value = []
  selected.value = null
}
function undo() {
  if (locked.value) return
  const previous = history.value.pop()
  if (previous) {
    void commit(previous, undefined, false)
  }
}
async function recycleStock() {
  const original = game.value
  const result = drawCard(original)
  if (result === original) return
  if (motion.reduced.value || document.hidden) {
    void commit(result)
    return
  }
  const current = ++turn
  history.value.push(original)
  if (history.value.length > 100) history.value.shift()
  selected.value = null
  moving.value = true

  const cards = Array.from(
    surface.value!.querySelectorAll<HTMLElement>('.waste-stack [data-card-id]'),
  ).reverse()
  const stack = cards[0]!.closest<HTMLElement>('.solitaire-slot')!
  const to = surface.value!.querySelector('.stock-card')!.getBoundingClientRect()
  const scale = fullscreen?.scale.value ?? 1
  // Stagger readable flips on a shared timeline; the whole sequence stays below 500ms.
  const duration = Math.max(160, 260 - cards.length * 5)
  const total = Math.min(400, duration + (cards.length - 1) * 70)
  const stagger = cards.length > 1 ? (total - duration) / (cards.length - 1) : 0
  stack.classList.add('is-stack-moving')
  const animations = cards.map((element, index) => {
    const from = element.getBoundingClientRect()
    const dx = (to.left - from.left) / scale,
      dy = (to.top - from.top) / scale
    const zIndex = 130 + index
    element.classList.add('is-recycling-card')
    return motion.animate(
      element,
      [
        { transform: 'translate3d(0,0,0) rotateY(0deg) rotateZ(0deg)', zIndex },
        {
          transform: `translate3d(${dx * 0.5}px,${dy * 0.5 - 18}px,42px) rotateY(90deg) rotateZ(6deg)`,
          offset: 0.5,
          zIndex,
        },
        { transform: `translate3d(${dx}px,${dy}px,0) rotateY(180deg) rotateZ(0deg)`, zIndex },
      ],
      { duration, delay: index * stagger, fill: 'forwards', easing: 'ease-in-out' },
    )
  })
  await motion.settle(animations)
  cards.forEach((element) => element.classList.remove('is-recycling-card'))
  stack.classList.remove('is-stack-moving')
  if (current !== turn) return
  game.value = result
  moving.value = false
}
function draw() {
  if (locked.value) return
  if (!game.value.stock.length) {
    void recycleStock()
    return
  }
  void commit(drawCard(game.value))
}
function select(source: CardSource) {
  if (locked.value || won.value || !sourceCards(game.value, source).length) return
  if (JSON.stringify(selected.value) === JSON.stringify(source)) {
    cancel()
    return
  }
  selected.value = source
}
function cancel() {
  if (dragState.value) {
    dragging.cancel()
    return
  }
  selected.value = null
}
function allowed(target: CardTarget) {
  return selected.value ? !!moveCard(game.value, selected.value, target) : false
}
function place(target: CardTarget) {
  if (locked.value || !selected.value) return
  const next = moveCard(game.value, selected.value, target)
  if (next) {
    void commit(next)
  }
}
function clickTableau(pile: number, index: number) {
  if (selected.value && !(selected.value.kind === 'tableau' && selected.value.pile === pile))
    place({ kind: 'tableau', pile })
  else select({ kind: 'tableau', pile, index })
}
function clickFoundation(pile: number) {
  if (locked.value) return
  if (selected.value?.kind === 'foundation' && selected.value.pile === pile) cancel()
  else if (selected.value) place({ kind: 'foundation', pile })
  else select({ kind: 'foundation', pile })
}
function selectedCard(pile: number, index: number) {
  return (
    selected.value?.kind === 'tableau' &&
    selected.value.pile === pile &&
    index >= selected.value.index
  )
}
function finish() {
  void commit(finishSolitaire(game.value))
}
watch(motion.reduced, (value) => {
  if (value) celebrating.value = false
})
onMounted(() => window.addEventListener('resize', motion.finish))
onBeforeUnmount(() => {
  stopMotion()
  window.removeEventListener('resize', motion.finish)
})
</script>

<template>
  <section
    ref="surface"
    class="game-surface solitaire-surface"
    :class="{ 'is-dragging': dragState }"
    :aria-busy="moving"
    aria-label="经典纸牌接龙"
    @keydown.esc="cancel"
    @pointermove="dragging.move"
    @pointerdown.capture="dragging.newPress"
    @pointerup="dragging.up"
    @pointercancel="dragging.pointerCancel"
    @lostpointercapture="dragging.pointerCancel"
    @touchmove="dragging.touchMove"
    @click.capture="dragging.clickCapture"
  >
    <div class="game-toolbar">
      <div class="game-stats">
        <div>
          <span>已收牌</span><strong>{{ collected }}<small> / 52</small></strong>
        </div>
        <div>
          <span>步数</span><strong>{{ game.moves }}</strong>
        </div>
      </div>
      <div class="game-actions">
        <button class="game-button" :disabled="locked || !history.length" @click="undo">
          <Undo2 :size="16" aria-hidden="true" />撤销
        </button>
        <div class="game-restart-actions">
          <button class="game-button" @click="restart">
            <RotateCcw :size="16" aria-hidden="true" />重新开始</button
          ><GameFullscreenButton />
        </div>
      </div>
    </div>
    <div v-if="!orientationDismissed" class="solitaire-orientation-hint">
      <Smartphone :size="18" aria-hidden="true" /><span>横屏游玩体验更好。</span
      ><button class="game-button" aria-label="关闭横屏提示" @click="orientationDismissed = true">
        <X :size="16" aria-hidden="true" />
      </button>
    </div>
    <div ref="stage" class="solitaire-stage">
      <div
        ref="scroll"
        class="solitaire-scroll"
        tabindex="0"
        role="region"
        aria-label="纸牌桌面，窄屏可左右滚动查看七列"
      >
        <div class="solitaire-table">
          <div class="solitaire-top">
            <div class="solitaire-slot">
              <span class="pile-label">牌堆 · {{ game.stock.length }}</span>
              <div class="stock-stack">
                <div
                  v-if="game.stock.length > 1"
                  class="playing-card card-back stock-underlay"
                  aria-hidden="true"
                >
                  <span class="stock-mark">✦</span>
                </div>
                <button
                  class="playing-card stock-card"
                  :class="{ 'card-back': game.stock.length }"
                  :disabled="locked || (!game.stock.length && !game.waste.length) || won"
                  :data-card-id="game.stock.length ? cardId(game.stock.at(-1)!) : undefined"
                  :aria-label="
                    game.stock.length
                      ? `翻一张牌，牌堆剩余 ${game.stock.length} 张`
                      : game.waste.length
                        ? '重新翻牌'
                        : '牌堆已空'
                  "
                  @click="draw"
                >
                  <span v-if="game.stock.length" class="stock-mark" aria-hidden="true">✦</span
                  ><span v-else class="stock-recycle"
                    ><RotateCcw :size="22" aria-hidden="true" />{{
                      game.waste.length ? '再翻一轮' : '空'
                    }}</span
                  >
                </button>
              </div>
            </div>
            <div class="solitaire-slot">
              <span class="pile-label">翻牌 · {{ game.waste.length }}</span>
              <div class="waste-stack">
                <template v-for="(card, index) in game.waste" :key="cardId(card)">
                  <button
                    v-if="index === game.waste.length - 1"
                    class="playing-card"
                    :class="{
                      'is-red': redCard(card),
                      'is-selected': selected?.kind === 'waste',
                      'is-drag-origin': dragging.isOrigin(card),
                    }"
                    :data-card-id="cardId(card)"
                    :aria-label="`选择翻牌 ${cardName(card)}`"
                    :aria-pressed="selected?.kind === 'waste'"
                    @click="select({ kind: 'waste' })"
                    @pointerdown="dragging.down($event, { kind: 'waste' })"
                    @contextmenu.prevent
                    @dragstart.prevent
                  >
                    <PlayingCard :card="card" />
                  </button>
                  <div
                    v-else
                    class="playing-card waste-covered"
                    :class="{ 'is-red': redCard(card) }"
                    :data-card-id="cardId(card)"
                    aria-hidden="true"
                  >
                    <PlayingCard :card="card" />
                  </div>
                </template>
                <div
                  v-if="!game.waste.length"
                  class="card-placeholder"
                  aria-label="翻牌区为空"
                ></div>
              </div>
            </div>
            <div aria-hidden="true"></div>
            <div v-for="(pile, index) in game.foundations" :key="index" class="solitaire-slot">
              <span class="pile-label">{{ suitNames[index] }}</span
              ><button
                class="playing-card foundation-card"
                :class="{
                  'is-red': index % 2 === 1,
                  'is-empty': !pile.length,
                  'is-target': allowed({ kind: 'foundation', pile: index }),
                  'is-selected': selected?.kind === 'foundation' && selected.pile === index,
                  'is-drag-origin': pile.length && dragging.isOrigin(pile.at(-1)!),
                  'is-drop-target': dragging.isTarget('foundation', index),
                }"
                :data-card-id="pile.length ? cardId(pile.at(-1)!) : undefined"
                data-drop-kind="foundation"
                :data-drop-pile="index"
                :aria-label="`${suitNames[index]}收牌区，${pile.length ? cardName(pile.at(-1)!) : '空，从 A 开始'}`"
                @click="clickFoundation(index)"
                @pointerdown="
                  pile.length && dragging.down($event, { kind: 'foundation', pile: index })
                "
                @contextmenu.prevent
                @dragstart.prevent
              >
                <PlayingCard v-if="pile.length" :card="pile.at(-1)!" /><span
                  v-else
                  class="foundation-symbol"
                  aria-hidden="true"
                  >{{ suits[index] }}<small>A → K</small></span
                >
              </button>
            </div>
          </div>
          <div class="solitaire-columns">
            <div
              v-for="(pile, column) in game.tableau"
              :key="column"
              class="solitaire-column"
              :class="{ 'is-drop-target': dragging.isTarget('tableau', column) }"
              data-drop-kind="tableau"
              :data-drop-pile="column"
            >
              <button
                class="pile-target"
                :class="{ 'is-target': allowed({ kind: 'tableau', pile: column }) }"
                :aria-label="`放到第 ${column + 1} 列`"
                @click="place({ kind: 'tableau', pile: column })"
              >
                第 {{ column + 1 }} 列<span
                  v-if="allowed({ kind: 'tableau', pile: column })"
                  aria-hidden="true"
                >
                  ↓</span
                >
              </button>
              <div
                class="tableau-stack"
                :style="{
                  paddingBottom: `calc(${Math.max(0, pile.length - 1)} * var(--card-step))`,
                }"
              >
                <button
                  v-if="!pile.length"
                  class="card-placeholder empty-column"
                  :aria-label="`第 ${column + 1} 列为空，可放 K`"
                  @click="place({ kind: 'tableau', pile: column })"
                >
                  K
                </button>
                <template v-for="(card, index) in pile" :key="`${card.suit}-${card.rank}`">
                  <button
                    v-if="card.faceUp"
                    class="playing-card tableau-card"
                    :class="{
                      'is-red': redCard(card),
                      'is-selected': selectedCard(column, index),
                      'is-drag-origin': dragging.isOrigin(card),
                    }"
                    :data-card-id="cardId(card)"
                    :style="{ top: `calc(${index} * var(--card-step))` }"
                    :aria-label="`第 ${column + 1} 列，${cardName(card)}${index < pile.length - 1 ? `，及下方 ${pile.length - index - 1} 张牌` : ''}`"
                    :aria-pressed="selectedCard(column, index)"
                    @click="clickTableau(column, index)"
                    @pointerdown="dragging.down($event, { kind: 'tableau', pile: column, index })"
                    @contextmenu.prevent
                    @dragstart.prevent
                  >
                    <PlayingCard :card="card" />
                  </button>
                  <div
                    v-else
                    class="playing-card tableau-card card-back"
                    :data-card-id="cardId(card)"
                    :style="{ top: `calc(${index} * var(--card-step))` }"
                    role="img"
                    :aria-label="`第 ${column + 1} 列，未翻开的牌`"
                  ></div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
      <SolitaireCelebration
        v-if="celebrating"
        :key="celebrationKey"
        :origins="celebrationOrigins"
        @finished="celebrating = false"
      />
    </div>
    <div class="game-actions solitaire-bottom">
      <button class="game-button" :disabled="!selected || moving" @click="cancel">取消选牌</button
      ><button class="game-button" :disabled="locked || !canFinish(game)" @click="finish">
        自动完成</button
      ><span>所有暗牌翻开且牌堆与翻牌区清空后，可自动完成。</span>
      <button v-if="celebrating" class="game-button" @click="celebrating = false">跳过庆祝</button>
      <button
        v-else-if="won && !motion.reduced.value"
        class="game-button"
        :disabled="moving"
        @click="celebrate"
      >
        重播庆祝
      </button>
    </div>
    <p v-show="won" class="game-status is-success" role="status">
      {{ won ? '52 张牌全部归位，接龙成功！' : '' }}
    </p>
  </section>
  <Teleport :to="(fullscreen?.active.value ? fullscreen.overlay.value : surface) || 'body'"
    ><div v-if="dragState" class="solitaire-drag-layer" aria-hidden="true">
      <div
        ref="dragGhost"
        class="solitaire-drag-stack"
        :style="{
          left: `${dragState.x}px`,
          top: `${dragState.y}px`,
          width: `${dragState.width}px`,
          height: `${dragState.height + (dragState.cards.length - 1) * dragState.step}px`,
        }"
      >
        <div
          v-for="(card, index) in dragState.cards"
          :key="cardId(card)"
          class="playing-card"
          :class="{ 'is-red': redCard(card) }"
          :style="{ top: `${index * dragState.step}px` }"
        >
          <PlayingCard :card="card" />
        </div>
      </div></div
  ></Teleport>
</template>
