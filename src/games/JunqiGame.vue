<script setup lang="ts">
import { computed, inject, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  ArrowLeftRight,
  Bot,
  Flag,
  Play,
  RotateCcw,
  Shield,
  Shuffle,
  Undo2,
  UserRound,
  X,
} from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import GameResult from './GameResult.vue'
import { gameFullscreenKey } from './fullscreen'
import { useGameMotion } from './useGameMotion'
import {
  battle,
  camps,
  headquarters,
  location,
  moveJunqi,
  newJunqi,
  rankNames,
  rows,
  cols,
  chooseJunqi,
  canMove,
  rail,
  neighbors,
  swapJunqiSetup,
  type JPiece,
  type JState,
} from './junqi'

type MoveRecord = { from: number; to: number; side: number; summary: string }
type Snapshot = { state: JState; last: MoveRecord | null; records: MoveRecord[] }
const game = ref<JState>(newJunqi())
const history = ref<Snapshot[]>([])
const arranging = ref(true)
const thinking = ref(false)
const moving = ref(false)
const lastMove = ref<MoveRecord | null>(null)
const records = ref<MoveRecord[]>([])
const notice = ref('交换两枚我方棋子，布置好后开始对局。')
const boardElement = ref<HTMLElement>()
const flightElement = ref<HTMLElement>()
const flight = ref<{ piece: JPiece; to: number } | null>(null)
const focusAt = ref(30)
const horizontal = ref(false)
const fullscreen = inject(gameFullscreenKey)!
const motion = useGameMotion()
let timer: ReturnType<typeof setTimeout> | undefined
let revision = 0
const selected = computed(() => game.value.selected)
const selectedPiece = computed(() =>
  selected.value === null ? null : game.value.board[selected.value],
)
const canAct = computed(
  () =>
    !game.value.finished &&
    !thinking.value &&
    !moving.value &&
    (arranging.value || game.value.turn === 1),
)
const status = computed(() =>
  game.value.finished
    ? '本局结束'
    : arranging.value
      ? '布置你的阵型'
      : thinking.value
        ? '电脑正在思考'
        : moving.value
          ? '行棋中'
          : '轮到你行棋',
)
const outcome = computed(() => {
  if (!game.value.finished) return ''
  const captured = !game.value.board.some(
    (piece) => piece?.flag && piece.side === -game.value.finished,
  )
  return game.value.finished === 1
    ? captured
      ? '你夺得军旗，获胜！'
      : '对方无棋可走，你赢了！'
    : captured
      ? '电脑夺得军旗，再来一局吧。'
      : '你已无棋可走，再来一局吧。'
})
const remaining = (side: number) => game.value.board.filter((piece) => piece?.side === side).length
const targets = computed(() => {
  const result = new Set<number>()
  if (selected.value === null || !canAct.value) return result
  for (let at = 0; at < rows * cols; at++)
    if (
      arranging.value
        ? swapJunqiSetup(game.value, selected.value, at)
        : canMove(game.value, selected.value, at)
    )
      result.add(at)
  return result
})
function pieceName(piece: JPiece) {
  return rankNames[piece.rank] ?? '棋子'
}
const pieceDetail = computed(() => {
  const piece = selectedPiece.value
  if (!piece)
    return arranging.value
      ? '先选一枚我方棋子，再点另一枚交换位置。'
      : '选择我方棋子，查看可走的位置。'
  if (arranging.value)
    return piece.flag
      ? '军旗留在大本营，只能与另一座大本营的棋子交换。'
      : piece.mine
        ? '地雷只能布置在后两排。'
        : piece.bomb
          ? '炸弹不能布置在最前排。'
          : '普通棋子可交换位置；军旗、地雷和炸弹的位置有各自限制。'
  if (piece.flag) return '军旗不能移动，守好它才能继续作战。'
  if (piece.mine) return '地雷不能移动；对方只有工兵能安全排雷。'
  if (selected.value !== null && headquarters.has(selected.value))
    return '棋子进入大本营后不能再移动。'
  if (piece.bomb) return '炸弹与对方棋子相遇时，双方一起移除。'
  if (piece.rank === 1) return '工兵能排地雷，也能沿畅通的铁路转弯。'
  return '公路走一步，铁路沿畅通的直线长走；行营里的棋子不会被攻击。'
})

// Station coordinates share one map with both the SVG and the interactive grid.
const mapWidth = computed(() => (horizontal.value ? 800 : 500))
const mapHeight = computed(() => (horizontal.value ? 500 : 800))
function point(at: number) {
  const r = Math.floor(at / cols),
    x = 50 + (at % cols) * 100,
    y = 30 + r * 60 + (r >= 6 ? 80 : 0)
  return horizontal.value ? { x: y, y: x } : { x, y }
}
function pathFor(from: number, to: number) {
  const a = point(from),
    b = point(to)
  return `M${a.x} ${a.y}L${b.x} ${b.y}`
}
const roadEdges = Array.from({ length: rows * cols }, (_, at) =>
  neighbors(at)
    .filter((to) => to > at)
    .map((to) => [at, to] as const),
).flat()
const diagonals = Array.from(camps).flatMap((at) =>
  [-6, -4, 4, 6]
    .filter((d) => {
      const to = at + d
      return to >= 0 && to < rows * cols && Math.abs((to % cols) - (at % cols)) === 1
    })
    .map((d) => [at, at + d] as const),
)
const roadPath = computed(() =>
  [...roadEdges, ...diagonals].map(([a, b]) => pathFor(a, b)).join(''),
)
const railPath = computed(() =>
  roadEdges
    .filter(([a, b]) => rail(a) && rail(b))
    .map(([a, b]) => pathFor(a, b))
    .join(''),
)
function gridPosition(at: number) {
  const r = Math.floor(at / cols) + 1 + (at >= 30 ? 1 : 0),
    c = (at % cols) + 1
  return { gridColumn: horizontal.value ? r : c, gridRow: horizontal.value ? c : r }
}
const flightStyle = computed(() => {
  if (!flight.value) return {}
  const p = point(flight.value.to)
  return {
    left: `${(p.x / mapWidth.value) * 100}%`,
    top: `${(p.y / mapHeight.value) * 100}%`,
    width: horizontal.value ? '6.75%' : '16.8%',
    height: horizontal.value ? '12.4%' : fullscreen.active.value ? '6.9%' : '5.25%',
  }
})
function updateOrientation() {
  const next = fullscreen.active.value && window.innerWidth >= 560 && window.innerHeight <= 600
  motion.cancel()
  horizontal.value = next
}
watch(fullscreen.active, updateOrientation, { flush: 'post' })
onMounted(() => {
  updateOrientation()
  window.addEventListener('resize', updateOrientation)
})
function stop() {
  clearTimeout(timer)
  timer = undefined
}
function resetMotion() {
  revision++
  stop()
  motion.cancel()
  moving.value = false
  thinking.value = false
  flight.value = null
}
function restart() {
  resetMotion()
  game.value = newJunqi()
  history.value = []
  arranging.value = true
  lastMove.value = null
  records.value = []
  focusAt.value = 30
  notice.value = '交换两枚我方棋子，布置好后开始对局。'
}
function start() {
  if (!arranging.value) return
  arranging.value = false
  game.value = { ...game.value, selected: null }
  notice.value = '你先行棋，点击棋子查看可走的位置。'
}
function clearSelection() {
  game.value = { ...game.value, selected: null }
}
async function commitMove(from: number, to: number) {
  const next = moveJunqi(game.value, from, to)
  if (!next) return
  const before = game.value,
    piece = before.board[from]!,
    defender = before.board[to]
  if (piece.side === 1)
    history.value.push({
      state: { ...before, selected: null },
      last: lastMove.value,
      records: [...records.value],
    })
  const token = ++revision
  const source = boardElement.value
    ?.querySelector<HTMLElement>(`[data-at="${from}"]`)
    ?.getBoundingClientRect()
  const target = boardElement.value
    ?.querySelector<HTMLElement>(`[data-at="${to}"]`)
    ?.getBoundingClientRect()
  const result = defender ? battle(piece, defender) : 'win'
  const effect = !defender
    ? '行棋'
    : result === 'win'
      ? `吃掉${pieceName(defender)}`
      : result === 'both'
        ? '双方同归于尽'
        : `${pieceName(piece)}被吃掉`
  lastMove.value = {
    from,
    to,
    side: piece.side,
    summary: `${piece.side === 1 ? '你' : '电脑'} · ${pieceName(piece)} · ${effect}`,
  }
  records.value = [...records.value.slice(-2), lastMove.value]
  game.value = next
  moving.value = true
  flight.value = { piece, to }
  await nextTick()
  if (token !== revision) return
  const scale = fullscreen.scale.value || 1
  const dx = source && target ? (source.left - target.left) / scale : 0
  const dy = source && target ? (source.top - target.top) / scale : 0
  await motion.settle([
    motion.animate(
      flightElement.value,
      [
        { transform: `translate(${dx}px, ${dy}px) translate(-50%, -50%)`, opacity: 1 },
        { transform: 'translate(-50%, -50%)', opacity: result === 'win' ? 1 : 0 },
      ],
      { duration: 260 },
    ),
  ])
  if (token !== revision) return
  flight.value = null
  moving.value = false
  notice.value = outcome.value || lastMove.value!.summary
  scheduleComputer()
}
function scheduleComputer() {
  stop()
  if (game.value.finished || game.value.turn !== -1 || arranging.value) return
  thinking.value = true
  timer = setTimeout(() => {
    timer = undefined
    const move = chooseJunqi(game.value)
    thinking.value = false
    if (move) void commitMove(move[0], move[1])
  }, 500)
}
function act(at: number) {
  if (!canAct.value) return
  if (selected.value === at) {
    clearSelection()
    return
  }
  const piece = game.value.board[at]
  if (arranging.value && selected.value !== null && piece?.side === 1) {
    const next = swapJunqiSetup(game.value, selected.value, at)
    if (next) {
      game.value = next
      notice.value = '棋子已交换，继续布阵或开始对局。'
    } else notice.value = '这两枚棋子的位置不符合布阵要求，请选择高亮的位置。'
    return
  }
  if (piece?.side === 1) {
    game.value = { ...game.value, selected: at }
    return
  }
  if (selected.value !== null && targets.value.has(at)) void commitMove(selected.value, at)
}
function undo() {
  if (!history.value.length) return
  resetMotion()
  const previous = history.value.pop()!
  game.value = previous.state
  lastMove.value = previous.last
  records.value = previous.records
  notice.value = '已撤回你与电脑的一轮行棋。'
}
function label(at: number) {
  const piece = game.value.board[at]
  const terrain = camps.has(at) ? '行营，安全区' : headquarters.has(at) ? '大本营' : '兵站'
  return `${location(at)}，${piece ? `${piece.side === 1 ? '我方' : '电脑'}${pieceName(piece)}，` : ''}${terrain}${targets.value.has(at) ? (arranging.value ? '，可交换' : piece ? '，可攻击' : '，可移动') : ''}`
}
async function boardKey(event: KeyboardEvent) {
  const at = Number((event.target as HTMLElement).closest<HTMLElement>('[data-at]')?.dataset.at)
  if (
    !Number.isFinite(at) ||
    !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)
  )
    return
  event.preventDefault()
  let next = at
  if (event.key === 'Home') next = 0
  else if (event.key === 'End') next = 59
  else {
    const delta = horizontal.value
      ? { ArrowLeft: -5, ArrowRight: 5, ArrowUp: -1, ArrowDown: 1 }
      : { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -5, ArrowDown: 5 }
    next += delta[event.key as keyof typeof delta]
    if (Math.abs(next - at) === 1 && Math.floor(next / 5) !== Math.floor(at / 5)) next = at
    next = Math.max(0, Math.min(59, next))
  }
  focusAt.value = next
  await nextTick()
  boardElement.value
    ?.querySelector<HTMLButtonElement>(`[data-at="${next}"]`)
    ?.focus({ preventScroll: true })
}
onBeforeUnmount(() => {
  resetMotion()
  window.removeEventListener('resize', updateOrientation)
})
</script>

<template>
  <div class="game-layout junqi-layout">
    <section
      class="game-surface junqi-surface"
      aria-label="军旗对局"
      :aria-busy="moving || thinking"
    >
      <div class="game-toolbar junqi-toolbar">
        <div class="junqi-heading">
          <span class="junqi-game-mark"><Flag :size="22" aria-hidden="true" /></span>
          <div>
            <span class="junqi-phase">{{ arranging ? '明棋布阵' : '双人明棋' }}</span
            ><strong role="status">{{ status }}</strong>
          </div>
        </div>
        <div class="game-actions">
          <button v-if="arranging" class="game-button junqi-primary" @click="start">
            <Play :size="16" aria-hidden="true" />开始对局</button
          ><button v-else class="game-button" :disabled="!history.length" @click="undo">
            <Undo2 :size="16" aria-hidden="true" />悔棋
          </button>
          <div class="game-restart-actions">
            <button class="game-button" @click="restart">
              <RotateCcw :size="16" aria-hidden="true" />重新开始</button
            ><GameFullscreenButton />
          </div>
        </div>
      </div>
      <div class="junqi-match">
        <div class="junqi-board-column">
          <div
            class="junqi-player junqi-opponent"
            :class="{ 'is-current': !arranging && game.turn === -1 && !game.finished }"
          >
            <span class="junqi-avatar"><Bot :size="22" aria-hidden="true" /></span>
            <div>
              <strong>电脑</strong
              ><span>{{
                arranging
                  ? '对方阵型已就位'
                  : thinking
                    ? '正在思考'
                    : game.finished
                      ? '本局结束'
                      : '与你对弈'
              }}</span>
            </div>
            <span class="junqi-player-count"
              ><strong>{{ remaining(-1) }}</strong> 枚</span
            >
          </div>
          <div class="junqi-board-frame">
            <div
              ref="boardElement"
              class="junqi-board"
              :class="{ 'is-horizontal': horizontal }"
              role="group"
              aria-label="军旗棋盘"
              aria-describedby="junqi-board-help"
              @keydown="boardKey"
              @keydown.esc="clearSelection"
            >
              <svg
                class="junqi-roads"
                :viewBox="`0 0 ${mapWidth} ${mapHeight}`"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <path class="junqi-road" :d="roadPath" />
                <path class="junqi-rail-under" :d="railPath" />
                <path class="junqi-rail" :d="railPath" />
                <g
                  v-for="at in rows * cols"
                  :key="at - 1"
                  :transform="`translate(${point(at - 1).x} ${point(at - 1).y})`"
                  class="junqi-station"
                  :class="{ 'is-camp': camps.has(at - 1), 'is-base': headquarters.has(at - 1) }"
                >
                  <ellipse
                    v-if="camps.has(at - 1)"
                    :rx="horizontal ? 25 : 40"
                    :ry="horizontal ? 38 : 22"
                  />
                  <rect
                    v-else
                    :x="horizontal ? -25 : -40"
                    :y="horizontal ? -35 : -20"
                    :width="horizontal ? 50 : 80"
                    :height="horizontal ? 70 : 40"
                    :rx="headquarters.has(at - 1) ? 8 : 4"
                  />
                </g>
                <text
                  class="junqi-boundary"
                  :x="horizontal ? 400 : 250"
                  :y="horizontal ? 250 : 400"
                  text-anchor="middle"
                  dominant-baseline="middle"
                >
                  {{ horizontal ? '山界' : '山 界' }}
                </text>
              </svg>
              <button
                v-for="at in rows * cols"
                :key="at - 1"
                class="junqi-cell"
                :class="{
                  'is-camp': camps.has(at - 1),
                  'is-base': headquarters.has(at - 1),
                  'is-selected': selected === at - 1,
                  'is-target': targets.has(at - 1),
                  'is-last-from': lastMove?.from === at - 1,
                  'is-last-to': lastMove?.to === at - 1,
                }"
                :style="gridPosition(at - 1)"
                :data-at="at - 1"
                :aria-label="label(at - 1)"
                :aria-pressed="selected === at - 1"
                :tabindex="at - 1 === focusAt ? 0 : -1"
                :disabled="!canAct"
                @click="act(at - 1)"
                @focus="focusAt = at - 1"
              >
                <span
                  v-if="game.board[at - 1]"
                  class="junqi-piece"
                  :class="[
                    game.board[at - 1]!.side === 1 ? 'is-self' : 'is-enemy',
                    { 'is-in-flight': flight?.piece.id === game.board[at - 1]!.id },
                  ]"
                  :data-piece-id="game.board[at - 1]!.id"
                  ><b>{{ pieceName(game.board[at - 1]!) }}</b
                  ><small>{{ game.board[at - 1]!.side === 1 ? '我方' : '电脑' }}</small></span
                >
                <span v-else-if="camps.has(at - 1)" class="junqi-terrain" aria-hidden="true"
                  >行营</span
                ><Flag
                  v-else-if="headquarters.has(at - 1)"
                  class="junqi-terrain"
                  :size="16"
                  aria-hidden="true"
                />
                <span v-if="targets.has(at - 1)" class="junqi-target" aria-hidden="true"
                  ><ArrowLeftRight v-if="arranging" :size="14" /><span
                    v-else-if="!game.board[at - 1]"
                    >●</span
                  ></span
                >
              </button>
              <span
                v-if="flight"
                ref="flightElement"
                class="junqi-piece junqi-flight"
                :class="flight.piece.side === 1 ? 'is-self' : 'is-enemy'"
                :style="flightStyle"
                aria-hidden="true"
                ><b>{{ pieceName(flight.piece) }}</b
                ><small>{{ flight.piece.side === 1 ? '我方' : '电脑' }}</small></span
              >
              <GameResult
                v-if="game.finished && !moving"
                :message="outcome"
                :tone="game.finished === 1 ? 'success' : 'ended'"
                ><button class="game-button junqi-primary" @click="restart">
                  再来一局
                </button></GameResult
              >
            </div>
          </div>
          <div
            class="junqi-player junqi-self"
            :class="{ 'is-current': !arranging && game.turn === 1 && !game.finished }"
          >
            <span class="junqi-avatar"><UserRound :size="22" aria-hidden="true" /></span>
            <div>
              <strong>你</strong
              ><span>{{
                arranging ? '先把阵型布置好' : game.finished ? '本局结束' : '守好军旗，稳步推进'
              }}</span>
            </div>
            <span class="junqi-player-count"
              ><strong>{{ remaining(1) }}</strong> 枚</span
            >
          </div>
        </div>
        <aside class="junqi-sidebar" aria-label="战局与行棋提示">
          <section class="junqi-info-panel junqi-command">
            <p class="overline">{{ arranging ? '准备出发' : '行棋指引' }}</p>
            <div class="junqi-selection-heading">
              <Shield :size="20" aria-hidden="true" />
              <h2>
                {{
                  selectedPiece ? pieceName(selectedPiece) : arranging ? '排兵布阵' : '选一枚棋子'
                }}
              </h2>
              <button
                v-if="selected !== null"
                class="junqi-deselect"
                aria-label="取消选择"
                @click="clearSelection"
              >
                <X :size="16" aria-hidden="true" />
              </button>
            </div>
            <p>{{ pieceDetail }}</p>
            <span v-if="selectedPiece" class="junqi-target-count">{{
              targets.size
                ? `${targets.size} 处可${arranging ? '交换' : '行走'}`
                : arranging
                  ? '选另一枚棋子调整位置'
                  : '这枚棋子当前无法移动'
            }}</span>
            <div v-if="arranging" class="junqi-setup-actions">
              <button class="game-button" @click="restart">
                <Shuffle :size="16" aria-hidden="true" />随机布阵
              </button>
            </div>
          </section>
          <section class="junqi-info-panel junqi-map-key">
            <p class="overline">看懂棋盘</p>
            <ul>
              <li>
                <span class="junqi-key-road" aria-hidden="true"></span>
                <div><strong>公路</strong><span>沿连线行走一步</span></div>
              </li>
              <li>
                <span class="junqi-key-rail" aria-hidden="true"></span>
                <div><strong>铁路</strong><span>直线长走，工兵可转弯</span></div>
              </li>
              <li>
                <span class="junqi-key-camp" aria-hidden="true"></span>
                <div><strong>行营</strong><span>营内棋子不会被攻击</span></div>
              </li>
              <li>
                <span class="junqi-key-base" aria-hidden="true"><Flag :size="12" /></span>
                <div><strong>大本营</strong><span>军旗驻地，入营后不能移动</span></div>
              </li>
            </ul>
          </section>
          <section v-if="records.length" class="junqi-info-panel junqi-recent">
            <p class="overline">最近行棋</p>
            <ol>
              <li v-for="(record, i) in [...records].reverse()" :key="i">
                <span>{{ record.side === 1 ? '你' : '电脑' }}</span>
                <p>{{ record.summary.split(' · ').slice(1).join(' · ') }}</p>
              </li>
            </ol>
          </section>
        </aside>
      </div>
      <p id="junqi-board-help" class="sr-only">
        方向键移动焦点，回车或空格选择棋子与落点，Escape 取消选择。布阵阶段可交换两枚我方棋子。
      </p>
      <p class="sr-only" role="status">{{ notice }}</p>
    </section>
  </div>
</template>
