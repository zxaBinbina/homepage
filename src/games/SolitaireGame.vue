<script setup lang="ts">
import { computed, ref } from 'vue'
import { RotateCcw, Undo2 } from 'lucide-vue-next'
import PlayingCard from './PlayingCard.vue'
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
const selected = ref<CardSource | null>(null)
const history = ref<SolitaireGame[]>([])
const notice = ref('先翻一张牌，或选择桌面上的明牌开始。')
const won = computed(() => solitaireWon(game.value))
const collected = computed(() => game.value.foundations.reduce((sum, pile) => sum + pile.length, 0))
const wasteTop = computed(() => game.value.waste.at(-1))
const status = computed(() => {
  if (won.value) return '52 张牌全部归位，接龙成功！'
  if (!selected.value) return notice.value
  const cards = sourceCards(game.value, selected.value)
  return `已选 ${cardName(cards[0]!)}${cards.length > 1 ? ` 起的 ${cards.length} 张牌` : ''}，点击目标列或上方收牌区。${notice.value}`
})
function commit(next: SolitaireGame) {
  if (next === game.value) return
  history.value.push(game.value)
  if (history.value.length > 100) history.value.shift()
  game.value = next
  selected.value = null
}
function restart() {
  game.value = newSolitaire()
  history.value = []
  selected.value = null
  notice.value = '新牌已发好，慢慢来。'
}
function undo() {
  const previous = history.value.pop()
  if (previous) {
    game.value = previous
    selected.value = null
    notice.value = '已撤销上一步。'
  }
}
function draw() {
  selected.value = null
  const recycling = !game.value.stock.length
  commit(drawCard(game.value))
  notice.value = recycling ? '已收回翻牌，再点牌堆从头翻起。' : '翻出一张新牌，看看能放在哪里。'
}
function select(source: CardSource) {
  if (won.value || !sourceCards(game.value, source).length) return
  if (JSON.stringify(selected.value) === JSON.stringify(source)) {
    cancel()
    return
  }
  selected.value = source
  notice.value = ''
}
function cancel() {
  selected.value = null
  notice.value = '已取消选牌。'
}
function allowed(target: CardTarget) {
  return selected.value ? !!moveCard(game.value, selected.value, target) : false
}
function place(target: CardTarget) {
  if (!selected.value) {
    notice.value = '先点击一张明牌，再选择放置的位置。'
    return
  }
  const next = moveCard(game.value, selected.value, target)
  if (next) {
    commit(next)
    notice.value = '移动成功。'
  } else
    notice.value =
      target.kind === 'foundation'
        ? '收牌区需要同花色，按 A 到 K 顺序放入单张牌。'
        : '请按红黑交替、数字递减放置；空列只接受 K 开头的牌。'
}
function clickTableau(pile: number, index: number) {
  if (selected.value && !(selected.value.kind === 'tableau' && selected.value.pile === pile))
    place({ kind: 'tableau', pile })
  else select({ kind: 'tableau', pile, index })
}
function clickFoundation(pile: number) {
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
  commit(finishSolitaire(game.value))
  notice.value = '已将剩余牌收好。'
}
</script>

<template>
  <section class="game-surface solitaire-surface" aria-label="经典纸牌接龙" @keydown.esc="cancel">
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
        <button class="game-button" :disabled="!history.length" @click="undo">
          <Undo2 :size="16" aria-hidden="true" />撤销</button
        ><button class="game-button" @click="restart">
          <RotateCcw :size="16" aria-hidden="true" />重新开始
        </button>
      </div>
    </div>
    <p class="game-status solitaire-status" :class="{ 'is-success': won }" role="status">
      {{ status }}
    </p>
    <div
      class="solitaire-scroll"
      tabindex="0"
      role="region"
      aria-label="纸牌桌面，窄屏可左右滚动查看七列"
    >
      <div class="solitaire-table">
        <div class="solitaire-top">
          <div class="solitaire-slot">
            <span class="pile-label">牌堆 · {{ game.stock.length }}</span
            ><button
              class="playing-card stock-card"
              :class="{ 'card-back': game.stock.length }"
              :disabled="(!game.stock.length && !game.waste.length) || won"
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
          <div class="solitaire-slot">
            <span class="pile-label">翻牌 · {{ game.waste.length }}</span
            ><button
              v-if="wasteTop"
              class="playing-card"
              :class="{ 'is-red': redCard(wasteTop), 'is-selected': selected?.kind === 'waste' }"
              :aria-label="`选择翻牌 ${cardName(wasteTop)}`"
              :aria-pressed="selected?.kind === 'waste'"
              @click="select({ kind: 'waste' })"
            >
              <PlayingCard :card="wasteTop" />
            </button>
            <div v-else class="card-placeholder" aria-label="翻牌区为空">翻牌</div>
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
              }"
              :aria-label="`${suitNames[index]}收牌区，${pile.length ? cardName(pile.at(-1)!) : '空，从 A 开始'}`"
              @click="clickFoundation(index)"
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
          <div v-for="(pile, column) in game.tableau" :key="column" class="solitaire-column">
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
                height: `calc(var(--card-height) + ${Math.max(0, pile.length - 1)} * var(--card-step))`,
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
                  :class="{ 'is-red': redCard(card), 'is-selected': selectedCard(column, index) }"
                  :style="{ top: `calc(${index} * var(--card-step))` }"
                  :aria-label="`第 ${column + 1} 列，${cardName(card)}${index < pile.length - 1 ? `，及下方 ${pile.length - index - 1} 张牌` : ''}`"
                  :aria-pressed="selectedCard(column, index)"
                  @click="clickTableau(column, index)"
                >
                  <PlayingCard :card="card" />
                </button>
                <div
                  v-else
                  class="playing-card tableau-card card-back"
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
    <div class="game-actions solitaire-bottom">
      <button class="game-button" :disabled="!selected" @click="cancel">取消选牌</button
      ><button class="game-button" :disabled="!canFinish(game)" @click="finish">自动完成</button
      ><span>所有暗牌翻开且牌堆与翻牌区清空后，可自动完成。</span>
    </div>
  </section>
  <aside class="game-guide solitaire-guide">
    <div>
      <p class="overline">HOW TO PLAY</p>
      <h2>一张一张，理出头绪。</h2>
    </div>
    <ol>
      <li>经典 Klondike 接龙，每次翻一张，牌堆可无限循环。点击明牌选中，再点击目标列或收牌区。</li>
      <li>桌面按红黑交替、数字递减排列，可以整段移动。空列只接受 K 或以 K 开头的牌组。</li>
      <li>上方四个收牌区按同花色 A → K 排列。移开暗牌上方的牌后，暗牌会自动翻开。</li>
      <li>
        点击已选的牌、按 Escape 或点击「取消选牌」可重选。可以撤销最近 100
        次操作，收牌区的牌也能移回桌面。
      </li>
    </ol>
    <p>随机牌局不保证每局可解。无路可走时，可以撤销或重新发牌。手机上左右滑动牌桌查看全部七列。</p>
  </aside>
</template>
