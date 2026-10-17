<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { RotateCcw, Undo2 } from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import { camps, headquarters, location, moveJunqi, newJunqi, rankNames, rows, cols, chooseJunqi, type JState } from './junqi'
const game = ref<JState>(newJunqi()), history = ref<JState[]>([]), thinking = ref(false), notice = ref('点击你的长条棋子，再选择高亮的行走位置。')
let timer: ReturnType<typeof setTimeout> | undefined
const selected = computed(() => game.value.selected)
const status = computed(() => game.value.finished ? game.value.finished === 1 ? '你夺得军旗，获胜！' : '电脑夺得军旗，再来一局吧。' : thinking.value ? '电脑思考中…' : game.value.turn === 1 ? '轮到你' : '轮到电脑')
function restart() { clearTimeout(timer); game.value = newJunqi(); history.value = []; thinking.value = false; notice.value = '点击你的长条棋子，再选择高亮的行走位置。' }
function act(at: number) { if (game.value.finished || thinking.value) return; if (selected.value === null) { if (game.value.board[at]?.side === 1) game.value = { ...game.value, selected: at }; return }; if (game.value.board[at]?.side === 1) { game.value = { ...game.value, selected: at }; return }; const next = moveJunqi(game.value, selected.value, at); if (!next) { notice.value = '这枚棋子不能这样走，铁路可长走，公路只能走一步。'; return }; history.value.push(game.value); game.value = next; notice.value = '行棋完成。'; scheduleComputer() }
function scheduleComputer() { if (game.value.finished || game.value.turn !== -1) return; thinking.value = true; timer = setTimeout(() => { const move = chooseJunqi(game.value); if (move) { const next = moveJunqi(game.value, move[0], move[1]); if (next) game.value = next }; thinking.value = false }, 500) }
function undo() { clearTimeout(timer); thinking.value = false; const previous = history.value.pop(); if (previous) game.value = previous }
function label(at: number) { const piece = game.value.board[at]; return `${location(at)}${piece ? `${piece.side === 1 ? '红方' : '蓝方'}${piece.flag ? '军旗' : rankNames[piece.rank]}` : camps.has(at) ? '行营，安全区' : headquarters.has(at) ? '大本营' : '空位'}` }
onBeforeUnmount(() => clearTimeout(timer))
</script>
<template>
  <div class="game-layout"><section class="game-surface strategy-surface junqi-surface" aria-label="军旗棋盘">
    <div class="game-toolbar"><div class="game-stats"><div><span>战局</span><strong role="status">{{ status }}</strong></div><div><span>你的棋子</span><strong>{{ game.board.filter(p => p?.side === 1).length }}</strong></div></div><div class="game-actions"><button class="game-button" :disabled="!history.length || thinking" @click="undo"><Undo2 :size="16" aria-hidden="true" />悔棋</button><button class="game-button" @click="restart"><RotateCcw :size="16" aria-hidden="true" />重新开始</button><GameFullscreenButton /></div></div>
    <div class="junqi-legend"><span>公路</span><span>铁路</span><span>行营安全区</span><span>大本营</span></div>
    <div class="junqi-board-frame"><div class="junqi-board" role="grid" :aria-label="status"><svg class="junqi-roads" viewBox="0 0 500 1200" preserveAspectRatio="none" aria-hidden="true"><g class="junqi-road-lines"><path d="M50 50H450M50 150H450M50 250H450M50 350H450M50 450H450M50 550H450M50 650H450M50 750H450M50 850H450M50 950H450M50 1050H450M50 1150H450M50 50V1150M150 50V550M150 650V1150M250 50V1150M350 50V550M350 650V1150M450 50V1150"/><path class="junqi-diagonal" d="M150 150L250 250M350 150L250 250M150 350L250 250M350 350L250 250M150 850L250 950M350 850L250 950M150 1050L250 950M350 1050L250 950"/><path class="junqi-rail" d="M50 50H450M50 1150H450M50 550V650M450 550V650M250 50V1150"/></g><text x="250" y="605" text-anchor="middle">山 界</text></svg><button v-for="at in rows * cols" :key="at - 1" class="junqi-cell" :class="{ 'is-camp': camps.has(at - 1), 'is-base': headquarters.has(at - 1), 'is-selected': selected === at - 1 }" :aria-label="label(at - 1)" :disabled="thinking || !!game.finished" @click="act(at - 1)"><span v-if="game.board[at - 1]" class="junqi-piece" :class="game.board[at - 1]!.side === 1 ? 'is-red' : 'is-blue'"><b>{{ game.board[at - 1]!.flag ? '军旗' : game.board[at - 1]!.mine ? '地雷' : rankNames[game.board[at - 1]!.rank] }}</b><small>{{ game.board[at - 1]!.side === 1 ? '红' : '蓝' }}</small></span><span v-else class="junqi-terrain" aria-hidden="true">{{ camps.has(at - 1) ? '营' : headquarters.has(at - 1) ? '旗' : '' }}</span></button></div></div>
    <p class="junqi-notice" role="status">{{ notice }}</p>
  </section></div>
</template>
