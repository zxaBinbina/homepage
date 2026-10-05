<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { Flag, MousePointer2, RotateCcw } from 'lucide-vue-next'
import { flagMine, mineLevels, newMineGame, revealMine, type MineCell } from './minesweeper'

const level = ref(0)
const game = ref(newMineGame())
const flagMode = ref(false)
function setMode(flag: boolean) {
  flagMode.value = flag
  notice.value = ''
}
const elapsed = ref(0)
const focused = ref(0)
const boardElement = ref<HTMLElement>()
const flagged = computed(() => game.value.cells.filter((cell) => cell.flag).length)
const safe = computed(() => game.value.cells.filter((cell) => cell.open && !cell.mine).length)
const ended = computed(() => game.value.status === 'won' || game.value.status === 'lost')
const notice = ref('')
const status = computed(() =>
  game.value.status === 'won'
    ? '所有安全格都找到了，恭喜过关！'
    : game.value.status === 'lost'
      ? '踩到地雷了。休息一下，再来一局吧。'
      : notice.value ||
        (game.value.status === 'ready'
          ? '点击任意格子开始，首步及周围八格一定安全。'
          : flagMode.value
            ? '插旗模式：点击未翻开的格子，标记或取消地雷。'
            : '数字表示周围八格中的地雷数，慢慢推理下一步。'),
)
let timer: ReturnType<typeof setInterval> | undefined
let started = 0
function stopTimer() {
  clearInterval(timer)
  timer = undefined
}
onBeforeUnmount(stopTimer)
function restart() {
  stopTimer()
  const config = mineLevels[level.value]!
  game.value = newMineGame(config.size, config.mines)
  elapsed.value = 0
  flagMode.value = false
  focused.value = 0
  notice.value = ''
}
function flag(index: number) {
  if (ended.value) return
  const next = flagMine(game.value, index)
  notice.value =
    next === game.value && !game.value.cells[index]!.open
      ? '旗子已经用完了，可以先取消一个标记。'
      : ''
  game.value = next
}
function reveal(index: number) {
  if (ended.value) return
  if (flagMode.value && !game.value.cells[index]!.open) {
    flag(index)
    return
  }
  notice.value = ''
  const previous = game.value.status
  game.value = revealMine(game.value, index)
  if (previous === 'ready' && game.value.status === 'playing') {
    started = Date.now()
    timer = setInterval(() => {
      elapsed.value = Math.floor((Date.now() - started) / 1000)
    }, 1000)
  }
  if (ended.value) stopTimer()
}
function label(cell: MineCell, index: number) {
  const position = `第 ${Math.floor(index / game.value.size) + 1} 行第 ${(index % game.value.size) + 1} 列`
  return `${position}：${cell.flag ? (ended.value && !cell.mine ? '标记错误' : '已插旗') : cell.open || (ended.value && cell.mine) ? (cell.mine ? '地雷' : cell.adjacent ? `周围 ${cell.adjacent} 颗地雷` : '空白') : '未翻开'}`
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
        ><button class="game-button" @click="restart">
          <RotateCcw :size="16" aria-hidden="true" />重新开始
        </button>
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
            ><span v-else-if="cell.flag" aria-hidden="true">⚑</span
            ><span v-else-if="ended && cell.mine" aria-hidden="true">✹</span
            ><span v-else-if="cell.open && cell.adjacent" aria-hidden="true">{{
              cell.adjacent
            }}</span>
          </button>
        </div>
      </div>
      <p
        class="game-status"
        :class="{ 'is-success': game.status === 'won', 'is-ended': game.status === 'lost' }"
        role="status"
      >
        {{ status }}
      </p>
    </section>
    <aside class="game-guide">
      <p class="overline">HOW TO PLAY</p>
      <h2>每个数字，都是线索。</h2>
      <ol>
        <li>翻开格子，数字代表周围八格中的地雷数量。</li>
        <li>确定是地雷时插旗。翻开所有非雷格即可获胜，不需要把旗子全部用完。</li>
        <li>一个数字周围的旗子够了，再点它就会翻开周围剩余格子。标错旗也可能踩雷。</li>
      </ol>
      <p>电脑：左键翻开、右键插旗；也可用方向键移动焦点，回车或空格翻开，F 插旗。</p>
      <p>
        手机：用棋盘上方的「翻开 /
        插旗」切换操作。挑战棋盘在窄屏内可左右滚动。更换难度会开始新的一局。
      </p>
    </aside>
  </div>
</template>
