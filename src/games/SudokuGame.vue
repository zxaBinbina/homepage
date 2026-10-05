<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { Eraser, Lightbulb, Pencil, RotateCcw, Undo2 } from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import { newSudoku, peers, sudokuConflicts } from './sudoku'
import { useBoardKeyboard } from './useBoardKeyboard'
import { useGameMotion } from './useGameMotion'

const level = ref(0),
  puzzle = ref(newSudoku()),
  board = ref([...puzzle.value.puzzle])
const notes = ref<number[][]>(Array.from({ length: 81 }, () => [])),
  selected = ref(board.value.findIndex((v) => !v))
const noteMode = ref(false),
  hints = ref(0),
  boardElement = ref<HTMLElement>()
type Snapshot = { board: number[]; notes: number[][] }
const history = ref<Snapshot[]>([]),
  motion = useGameMotion()
const onArrow = useBoardKeyboard(boardElement, selected, 9, 81)
const conflicts = computed(() => sudokuConflicts(board.value))
const won = computed(() => board.value.every(Boolean) && !conflicts.value.some(Boolean))
const filled = computed(() => board.value.filter(Boolean).length)
const message = computed(() => (won.value ? '全部填对了，这一局解开了！' : ''))
function remember() {
  history.value.push({ board: [...board.value], notes: notes.value.map((v) => [...v]) })
  if (history.value.length > 100) history.value.shift()
}
async function enter(value: number, hint = false) {
  const at = selected.value
  if (won.value || puzzle.value.puzzle[at]) return
  if (noteMode.value && value && !hint) {
    if (board.value[at]) return
    remember()
    notes.value[at] = notes.value[at]!.includes(value)
      ? notes.value[at]!.filter((n) => n !== value)
      : [...notes.value[at]!, value].sort()
  } else {
    if (board.value[at] === value && notes.value[at]!.length === 0) return
    remember()
    board.value[at] = value
    notes.value[at] = []
    if (value)
      notes.value = notes.value.map((set, i) =>
        peers(at, i) ? set.filter((n) => n !== value) : set,
      )
  }
  await nextTick()
  void motion.settle([
    motion.animate(
      boardElement.value?.querySelectorAll('.sudoku-value')[at],
      [
        { opacity: 0.25, transform: 'scale(.8)' },
        { opacity: 1, transform: 'scale(1)' },
      ],
      { duration: 160 },
    ),
  ])
}
function hint() {
  if (won.value) return
  if (
    puzzle.value.puzzle[selected.value] ||
    board.value[selected.value] === puzzle.value.solution[selected.value]
  )
    selected.value = board.value.findIndex((v, i) => v !== puzzle.value.solution[i])
  if (selected.value < 0) return
  hints.value++
  void enter(puzzle.value.solution[selected.value]!, true)
}
function undo() {
  const previous = history.value.pop()
  if (previous) {
    board.value = previous.board
    notes.value = previous.notes
    motion.cancel()
  }
}
function restart() {
  motion.cancel()
  puzzle.value = newSudoku(level.value)
  board.value = [...puzzle.value.puzzle]
  notes.value = Array.from({ length: 81 }, () => [])
  selected.value = board.value.findIndex((v) => !v)
  history.value = []
  hints.value = 0
}
function onKey(event: KeyboardEvent) {
  if (event.ctrlKey || event.metaKey || event.altKey) return
  if (/^[1-9]$/.test(event.key)) {
    event.preventDefault()
    void enter(Number(event.key))
  } else if (['Backspace', 'Delete', '0'].includes(event.key)) {
    event.preventDefault()
    void enter(0)
  } else if (event.key.toLowerCase() === 'n') {
    event.preventDefault()
    noteMode.value = !noteMode.value
  } else void onArrow(event)
}
</script>

<template>
  <div class="game-layout">
    <section class="game-surface sudoku-surface" aria-label="数独游戏">
      <div class="game-toolbar">
        <div class="game-stats">
          <div>
            <span>已填格数</span><strong>{{ filled }} <small>/ 81</small></strong>
          </div>
          <div>
            <span>使用提示</span><strong>{{ hints }}</strong>
          </div>
        </div>
        <div class="game-actions">
          <label class="game-select"
            >题目难度<select v-model.number="level" @change="restart">
              <option :value="0">入门</option>
              <option :value="1">标准</option>
              <option :value="2">进阶</option>
            </select></label
          >
          <button class="game-button" :disabled="!history.length" @click="undo">
            <Undo2 :size="16" aria-hidden="true" />撤销
          </button>
          <div class="game-restart-actions">
            <button class="game-button" @click="restart">
              <RotateCcw :size="16" aria-hidden="true" />重新开始</button
            ><GameFullscreenButton />
          </div>
          <p v-show="message" class="game-status is-success" role="status">
            {{ message }}
          </p>
        </div>
      </div>
      <div class="sudoku-play">
        <div
          ref="boardElement"
          class="sudoku-board"
          role="group"
          aria-label="数独棋盘，方向键选格，数字键填写，N 切换笔记"
          @keydown="onKey"
        >
          <button
            v-for="(value, i) in board"
            :key="i"
            class="board-cell sudoku-cell"
            :class="{
              'is-given': puzzle.puzzle[i],
              'is-selected': i === selected,
              'is-peer': i !== selected && peers(i, selected),
              'is-matching': value && value === board[selected],
              'is-conflict': conflicts[i],
              'is-box-right': i % 9 === 2 || i % 9 === 5,
              'is-box-bottom': Math.floor(i / 9) === 2 || Math.floor(i / 9) === 5,
            }"
            :tabindex="i === selected ? 0 : -1"
            :aria-label="`第 ${Math.floor(i / 9) + 1} 行第 ${(i % 9) + 1} 列：${value || (notes[i]!.length ? '笔记 ' + notes[i]!.join('、') : '空格')}${puzzle.puzzle[i] ? '，题目数字' : ''}${conflicts[i] ? '，重复' : ''}`"
            :aria-pressed="i === selected"
            @click="selected = i"
            @focus="selected = i"
          >
            <span class="sudoku-value">{{ value || '' }}</span
            ><span v-if="!value" class="sudoku-notes" aria-hidden="true"
              ><small v-for="n in 9" :key="n">{{ notes[i]!.includes(n) ? n : '' }}</small></span
            >
          </button>
        </div>
        <div class="sudoku-pad" role="group" aria-label="填写数字">
          <button
            v-for="n in 9"
            :key="n"
            class="game-button"
            :aria-label="`填写 ${n}`"
            :disabled="won || !!puzzle.puzzle[selected]"
            @click="enter(n)"
          >
            {{ n }}
          </button>
        </div>
        <div class="game-actions sudoku-actions">
          <button
            class="game-button"
            :aria-pressed="noteMode"
            title="记录候选数字，不会填入正式答案"
            @click="noteMode = !noteMode"
          >
            <Pencil :size="16" aria-hidden="true" />笔记
          </button>
          <button
            class="game-button"
            :disabled="won || !!puzzle.puzzle[selected]"
            @click="enter(0)"
          >
            <Eraser :size="16" aria-hidden="true" />擦除
          </button>
          <button class="game-button" :disabled="won" @click="hint">
            <Lightbulb :size="16" aria-hidden="true" />提示一格
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
