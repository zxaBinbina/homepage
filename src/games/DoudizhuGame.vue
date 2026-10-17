<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { RotateCcw, Lightbulb, X } from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import PlayingCard from './PlayingCard.vue'
import type { Card } from './solitaire'
import { bid, cardLabel, cardText, chooseComputer, classify, computerBid, newDoudizhu, canBeat, playDoudizhu, type DDCard } from './doudizhu'
const game = ref(newDoudizhu()), selected = ref<number[]>([]), notice = ref('先看看手牌，再决定叫几分。')
const actions = ref(['等待叫分', '等待叫分', '等待叫分'])
const names = ['你', '电脑 A', '电脑 B']
let timer: ReturnType<typeof setTimeout> | undefined
const mine = computed(() => game.value.hands[0]!)
const bidding = computed(() => game.value.landlord < 0)
const allPassed = computed(() => bidding.value && game.value.bidCount === 3)
const canAct = computed(() => game.value.turn === 0 && game.value.finished === null && !allPassed.value)
const picked = computed(() => mine.value.filter(c => selected.value.includes(c.id)))
const valid = computed(() => !bidding.value && canAct.value && canBeat(picked.value, game.value.last))
const outcome = computed(() => game.value.finished === null ? '' : (game.value.finished === game.value.landlord) === (game.value.landlord === 0) ? '你赢了！' : '这局对方获胜，再来一局吧。')
const status = computed(() => outcome.value || (allPassed.value ? '大家都不叫，重新发牌吧' : `${names[game.value.turn]}${bidding.value ? '叫分' : '出牌'}`))
function cardFor(card: DDCard): Card { return { suit: card.rank < 13 ? card.id % 4 : 0, rank: card.rank < 13 ? card.rank + 3 : card.rank === 13 ? 14 : 15, faceUp: true } }
function stop() { clearTimeout(timer); timer = undefined }
function restart() { stop(); game.value = newDoudizhu(); selected.value = []; actions.value = ['等待叫分', '等待叫分', '等待叫分']; notice.value = '先看看手牌，再决定叫几分。' }
function commitBid(score: number) {
  const player = game.value.turn, next = bid(game.value, score)
  if (!next) return
  actions.value[player] = score ? `叫 ${score} 分` : '不叫'
  game.value = next
  if (next.landlord >= 0) { actions.value = ['等待出牌', '等待出牌', '等待出牌']; notice.value = `${names[next.landlord]}成为地主，收下三张底牌并先出。` }
  schedule()
}
function commitCards(cards: DDCard[]) {
  const player = game.value.turn, next = playDoudizhu(game.value, cards)
  if (!next) { notice.value = '请选择合法牌型，并大过上一手。'; return }
  actions.value[player] = cards.length ? `${classify(cards)!.kind} · ${cards.map(cardText).join(' ')}` : '不出'
  game.value = next; selected.value = []
  notice.value = !next.last.length ? `${names[next.turn]}重新领出，可以选择任意合法牌型。` : `${names[player]}${cards.length ? '已出牌' : '选择不出'}`
  schedule()
}
function schedule() {
  stop()
  if (game.value.finished !== null || game.value.turn === 0 || allPassed.value) return
  timer = setTimeout(() => { timer = undefined; if (bidding.value) commitBid(computerBid(game.value.hands[game.value.turn]!, Math.max(...game.value.bids))); else commitCards(chooseComputer(game.value)) }, 650)
}
function toggle(c: DDCard) { if (!canAct.value || bidding.value) return; selected.value = selected.value.includes(c.id) ? selected.value.filter(id => id !== c.id) : [...selected.value, c.id] }
function hint() {
  if (!canAct.value || bidding.value) return
  const cards = chooseComputer(game.value)
  selected.value = cards.map(c => c.id)
  notice.value = cards.length ? `建议：${classify(cards)!.kind}，点击「出牌」确认。` : '建议这一手不出。'
}
function play() { if (valid.value) commitCards(picked.value) }
function pass() { if (canAct.value && !bidding.value && game.value.last.length) commitCards([]) }
function chooseBid(score: number) { if (canAct.value && bidding.value) commitBid(score) }
onBeforeUnmount(stop)
</script>

<template>
  <div class="game-layout">
    <section class="game-surface doudizhu-surface" aria-label="斗地主牌桌" @keydown.esc="selected = []">
      <div class="game-toolbar">
        <div class="game-stats"><div><span>{{ bidding ? '叫分阶段' : `你是${game.landlord === 0 ? '地主' : '农民'}` }}</span><strong class="strategy-turn" role="status">{{ status }}</strong></div><div><span>本局倍数</span><strong>{{ game.multiplier }}<small> 倍</small></strong></div></div>
        <div class="game-actions"><button class="game-button" @click="restart"><RotateCcw :size="16" aria-hidden="true" />重新发牌</button><GameFullscreenButton /></div>
      </div>
      <div class="dd-opponents">
        <article v-for="p in [1, 2]" :key="p" :class="{ 'is-current': game.turn === p && game.finished === null }"><span class="overline">{{ game.landlord < 0 ? '等待身份' : game.landlord === p ? '地主' : '农民' }}</span><h2>{{ names[p] }} <small>{{ game.hands[p]!.length }} 张</small></h2><p>{{ actions[p] }}</p><p v-if="game.finished !== null">手牌：{{ game.hands[p]!.map(cardText).join(' ') }}</p></article>
      </div>
      <div class="dd-table">
        <div class="dd-bottom"><span>地主底牌</span><span v-for="(card, i) in game.bottom" :key="i" class="dd-mini-card">{{ bidding ? '?' : cardText(card) }}</span></div>
        <p class="dd-last-label">{{ game.last.length ? `${names[game.lastPlayer]} · ${classify(game.last)?.kind}` : bidding ? '一副牌，三个人，慢慢来。' : '新一轮 · 自由领出' }}</p>
        <TransitionGroup name="dd-play" tag="div" class="dd-played"><span v-for="c in game.last" :key="c.id" class="dd-play-card playing-card"><PlayingCard :card="cardFor(c)" /></span></TransitionGroup>
      </div>
      <section class="dd-hand-area" aria-label="你的手牌区域">
        <div class="dd-hand-heading"><span>你的手牌 · {{ mine.length }} 张</span><span>{{ selected.length ? `已选 ${selected.length} 张` : '点击选牌，再确认出牌' }}</span></div>
        <TransitionGroup name="dd-hand" tag="div" class="dd-hand" role="group" aria-label="你的手牌">
          <button v-for="c in mine" :key="c.id" class="dd-card playing-card" :class="{ 'is-selected': selected.includes(c.id) }" :aria-label="cardLabel(c)" :aria-pressed="selected.includes(c.id)" :disabled="!canAct || bidding" @click="toggle(c)"><PlayingCard :card="cardFor(c)" /></button>
        </TransitionGroup>
      </section>
      <div v-if="bidding && !allPassed" class="dd-actions"><button v-for="score in [0, 1, 2, 3]" :key="score" class="game-button" :disabled="!canAct || (score > 0 && score <= Math.max(...game.bids))" @click="chooseBid(score)">{{ score ? `叫 ${score} 分` : '不叫' }}</button></div>
      <div v-else-if="allPassed || game.finished !== null" class="dd-actions"><button class="game-button" @click="restart">再来一局</button></div>
      <div v-else class="dd-actions"><button class="game-button" :disabled="!valid" @click="play">出牌</button><button class="game-button" :disabled="!canAct || !game.last.length" @click="pass">不出</button><button class="game-button" :disabled="!canAct" @click="hint"><Lightbulb :size="16" aria-hidden="true" />提示</button><button class="game-button" :disabled="!selected.length" @click="selected = []"><X :size="16" aria-hidden="true" />重选</button></div>
      <p class="dd-notice" role="status">{{ notice }}<template v-if="selected.length"> · {{ classify(picked)?.kind ?? '尚未组成合法牌型' }}</template></p>
    </section>
  </div>
</template>
