<script setup lang="ts">
import { computed, inject, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { ArrowUpRight, RotateCcw } from 'lucide-vue-next'
import GameFullscreenButton from './GameFullscreenButton.vue'
import GameResult from './GameResult.vue'
import { gameFullscreenKey } from './fullscreen'
import { useGameMotion } from './useGameMotion'
import { JUMP_CHARGE_MS, jumpPower, landJump, newJump } from './jump'

const game = ref(newJump()),
  phase = ref<'ready' | 'charging' | 'jumping'>('ready'),
  power = ref(0)
const actor = ref<SVGGElement>(),
  world = ref<SVGGElement>()
const motion = useGameMotion(),
  fullscreen = inject(gameFullscreenKey)
const camera = computed(() => game.value.current.x - 140)
const platforms = computed(() =>
  [game.value.previous, game.value.current, game.value.next].filter((p) => p !== null),
)
const label = computed(() =>
  game.value.status === 'lost'
    ? '本局结束'
    : phase.value === 'charging'
      ? '松开跳跃'
      : phase.value === 'jumping'
        ? '跳跃中'
        : '按住蓄力',
)
let version = 0,
  frame = 0,
  startedAt = 0
let input:
  { kind: 'pointer'; id: number; element: HTMLElement } | { kind: 'keyboard'; key: string } | null =
  null

function clearInput() {
  const previous = input
  input = null
  cancelAnimationFrame(frame)
  frame = 0
  if (previous?.kind === 'pointer' && previous.element.hasPointerCapture(previous.id))
    previous.element.releasePointerCapture(previous.id)
}
function cancelCharge() {
  clearInput()
  if (phase.value === 'charging') {
    phase.value = 'ready'
    power.value = 0
  }
}
function updatePower() {
  if (phase.value !== 'charging') return
  power.value = jumpPower(performance.now() - startedAt)
  if (power.value < 1) frame = requestAnimationFrame(updatePower)
}
function begin() {
  startedAt = performance.now()
  power.value = 0
  phase.value = 'charging'
  frame = requestAnimationFrame(updatePower)
}
function pointerDown(event: PointerEvent) {
  if (
    !event.isPrimary ||
    event.button !== 0 ||
    input ||
    phase.value !== 'ready' ||
    game.value.status !== 'playing'
  )
    return
  if ((event.target as Element).closest('.game-result')) return
  event.preventDefault()
  const element = event.currentTarget as HTMLElement
  element.focus({ preventScroll: true })
  input = { kind: 'pointer', id: event.pointerId, element }
  element.setPointerCapture(event.pointerId)
  begin()
}
function pointerUp(event: PointerEvent) {
  if (input?.kind !== 'pointer' || input.id !== event.pointerId) return
  const elapsed = performance.now() - startedAt
  clearInput()
  void jump(elapsed)
}
function pointerCancel(event: PointerEvent) {
  if (input?.kind === 'pointer' && input.id === event.pointerId) cancelCharge()
}
function onKeyDown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    cancelCharge()
    return
  }
  if (
    event.altKey ||
    event.ctrlKey ||
    event.metaKey ||
    ![' ', 'Enter'].includes(event.key) ||
    (event.target as Element).closest('.game-result')
  )
    return
  event.preventDefault()
  if (event.repeat || input || phase.value !== 'ready' || game.value.status !== 'playing') return
  input = { kind: 'keyboard', key: event.key }
  begin()
}
function onKeyUp(event: KeyboardEvent) {
  if (input?.kind !== 'keyboard' || input.key !== event.key) return
  event.preventDefault()
  const elapsed = performance.now() - startedAt
  clearInput()
  void jump(elapsed)
}
function onBlur() {
  if (input?.kind === 'keyboard') cancelCharge()
}
async function jump(milliseconds: number) {
  if (phase.value !== 'charging' || game.value.status !== 'playing') return
  phase.value = 'jumping'
  power.value = 0
  const current = ++version,
    before = game.value,
    after = landJump(before, milliseconds)
  const falling = after.status === 'lost'
  const frames: Keyframe[] = Array.from({ length: 9 }, (_, i) => {
    const t = i / 8
    return {
      offset: t * (falling ? 0.75 : 1),
      transform: `translate(${before.x + (after.x - before.x) * t}px, ${272 - Math.sin(Math.PI * t) * (70 + jumpPower(milliseconds) * 65)}px)`,
      opacity: 1,
    }
  })
  if (falling)
    frames.push({
      offset: 1,
      transform: `translate(${after.x}px, 440px) rotate(25deg)`,
      opacity: 0,
    })
  await motion.settle([
    motion.animate(actor.value, frames, {
      duration: falling ? 650 : 480,
      easing: 'linear',
      fill: 'both',
    }),
  ])
  if (current !== version) return
  const previousCamera = camera.value
  game.value = after
  await nextTick()
  if (current !== version) return
  if (after.score > before.score) {
    await motion.settle([
      motion.animate(
        world.value,
        [
          { transform: `translate(${-previousCamera}px, 0px)` },
          { transform: `translate(${-camera.value}px, 0px)` },
        ],
        { duration: 280, fill: 'both' },
      ),
      motion.animate(
        actor.value?.querySelector('.jump-figure'),
        [{ transform: 'scale(1.16, .78)' }, { transform: 'scale(1, 1)' }],
        { duration: 200 },
      ),
    ])
  }
  if (current !== version) return
  phase.value = 'ready'
}
function restart() {
  version++
  cancelCharge()
  motion.cancel()
  game.value = newJump()
  phase.value = 'ready'
  power.value = 0
}
function away() {
  cancelCharge()
  motion.finish()
}
function visibility() {
  if (document.hidden) away()
}
window.addEventListener('blur', away)
window.addEventListener('resize', cancelCharge)
document.addEventListener('visibilitychange', visibility)
if (fullscreen) watch(fullscreen.active, cancelCharge)
onBeforeUnmount(() => {
  version++
  clearInput()
  window.removeEventListener('blur', away)
  window.removeEventListener('resize', cancelCharge)
  document.removeEventListener('visibilitychange', visibility)
})
</script>

<template>
  <div class="game-layout">
    <section
      class="game-surface jump-surface"
      aria-label="跳一跳游戏"
      :aria-busy="phase === 'jumping'"
    >
      <div class="game-toolbar">
        <div class="game-stats">
          <div>
            <span>本局得分</span><strong>{{ game.score }}</strong>
          </div>
          <div>
            <span>当前方块</span><strong>{{ game.current.id + 1 }}</strong>
          </div>
        </div>
        <div class="game-actions">
          <div class="game-restart-actions">
            <button class="game-button" @click="restart">
              <RotateCcw :size="16" aria-hidden="true" />重新开始</button
            ><GameFullscreenButton />
          </div>
        </div>
      </div>
      <div
        class="jump-stage"
        tabindex="0"
        role="group"
        aria-label="跳一跳场景，按住蓄力，松开跳跃；也可按住空格或回车"
        :data-phase="phase"
        @pointerdown="pointerDown"
        @pointerup="pointerUp"
        @pointercancel="pointerCancel"
        @lostpointercapture="pointerCancel"
        @contextmenu.prevent
        @keydown="onKeyDown"
        @keyup="onKeyUp"
        @blur="onBlur"
      >
        <svg viewBox="0 0 600 400" aria-hidden="true">
          <path class="jump-horizon" d="M0 324H600" />
          <g ref="world" :style="{ transform: `translate(${-camera}px, 0px)` }">
            <g
              v-for="platform in platforms"
              :key="platform.id"
              class="jump-platform"
              :class="{ 'is-next': platform.id === game.next.id }"
              :data-platform="platform.id"
            >
              <ellipse
                class="jump-shadow"
                :cx="platform.x + 6"
                cy="345"
                :rx="platform.width * 0.62"
                ry="10"
              />
              <path
                class="jump-block-side"
                :d="`M${platform.x + platform.width / 2} 280 l12 -14 v56 l-12 14z`"
              />
              <rect
                class="jump-block-front"
                :x="platform.x - platform.width / 2"
                y="278"
                :width="platform.width"
                height="58"
                rx="5"
              />
              <path
                class="jump-block-top"
                :d="`M${platform.x - platform.width / 2} 280 l12 -14 h${platform.width} l-12 14z`"
              />
              <path
                v-if="platform.id === game.next.id"
                class="jump-target-mark"
                :d="`M${platform.x - 10} 273h20 M${platform.x} 269v8`"
              />
              <text :x="platform.x" y="365" text-anchor="middle">
                {{
                  platform.id === game.next.id
                    ? '下一块'
                    : platform.id === game.current.id
                      ? '脚下这一块'
                      : ''
                }}
              </text>
            </g>
            <g
              ref="actor"
              class="jump-actor"
              :style="{
                transform: `translate(${game.x}px, 272px)`,
                opacity: game.status === 'lost' ? 0 : 1,
              }"
            >
              <g
                class="jump-figure"
                :style="{
                  transform: motion.reduced.value
                    ? undefined
                    : `scale(${1 + power * 0.2}, ${1 - power * 0.25})`,
                }"
              >
                <rect class="jump-body" x="-12" y="-36" width="24" height="36" rx="9" />
                <circle class="jump-head" cx="0" cy="-48" r="14" />
                <circle class="jump-eye" cx="5" cy="-51" r="2" />
              </g>
            </g>
          </g>
        </svg>
        <GameResult
          v-if="game.status === 'lost' && phase !== 'jumping'"
          :message="`差一点就站稳了。本局 ${game.score} 分，再来一次吧。`"
          tone="ended"
        />
      </div>
      <div class="jump-charge">
        <div class="jump-power-label">
          <span>{{ label }}</span
          ><span>{{ Math.round(power * 100) }}%</span>
        </div>
        <div
          class="jump-power-track"
          role="meter"
          aria-label="蓄力"
          :aria-valuenow="Math.round(power * 100)"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <span :style="{ transform: `scaleX(${power})` }"></span>
        </div>
        <button
          class="game-button jump-hold"
          :aria-disabled="phase === 'jumping' || game.status === 'lost'"
          @pointerdown="pointerDown"
          @pointerup="pointerUp"
          @pointercancel="pointerCancel"
          @lostpointercapture="pointerCancel"
          @contextmenu.prevent
          @keydown="onKeyDown"
          @keyup="onKeyUp"
          @blur="onBlur"
        >
          <ArrowUpRight :size="18" aria-hidden="true" />{{ label }}
        </button>
      </div>
    </section>
  </div>
</template>
