<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { rankName, suits } from './solitaire'

const props = defineProps<{ origins: { x: number; y: number }[] }>()
const emit = defineEmits<{ finished: [] }>()
const canvas = ref<HTMLCanvasElement>()
let frame = 0
let observer: ResizeObserver | undefined
let stop = () => {}
onMounted(() => {
  const element = canvas.value!
  const context = element.getContext('2d')
  if (!context) {
    emit('finished')
    return
  }
  const preference = matchMedia('(prefers-reduced-motion: reduce)')
  if (preference.matches) {
    emit('finished')
    return
  }
  let width = 0,
    height = 0,
    finished = false,
    last = performance.now()
  const start = last
  const particles: {
    suit: number
    rank: number
    x: number
    y: number
    vx: number
    vy: number
    angle: number
    spin: number
    flip: number
    delay: number
  }[] = []
  function resize() {
    const bounds = element.getBoundingClientRect()
    width = bounds.width
    height = bounds.height
    const ratio = Math.min(devicePixelRatio || 1, 2)
    element.width = Math.round(width * ratio)
    element.height = Math.round(height * ratio)
    context!.setTransform(ratio, 0, 0, ratio, 0, 0)
  }
  resize()
  observer = new ResizeObserver(resize)
  observer.observe(element)
  const cardWidth = Math.min(74, width / 7),
    cardHeight = cardWidth * 1.4
  for (let rank = 13; rank >= 1; rank--)
    for (let suit = 0; suit < 4; suit++) {
      const origin = props.origins[suit] ?? { x: (width * (suit + 1)) / 5, y: 25 }
      particles.push({
        suit,
        rank,
        x: Math.max(cardWidth / 2, Math.min(width - cardWidth / 2, origin.x)),
        y: origin.y + cardHeight / 2,
        vx: (suit % 2 ? -1 : 1) * (75 + Math.random() * 115),
        vy: -160 - Math.random() * 160,
        angle: 0,
        spin: (Math.random() - 0.5) * 5,
        flip: 0,
        delay: (13 - rank) * 155 + suit * 65,
      })
    }
  stop = () => {
    if (finished) return
    finished = true
    cancelAnimationFrame(frame)
    emit('finished')
  }
  function visibility() {
    if (document.hidden) stop()
  }
  function reduced() {
    if (preference.matches) stop()
  }
  preference.addEventListener('change', reduced)
  document.addEventListener('visibilitychange', visibility)
  const cleanup = stop
  stop = () => {
    cleanup()
    preference.removeEventListener('change', reduced)
    document.removeEventListener('visibilitychange', visibility)
  }
  function draw(time: number) {
    if (finished) return
    if (time - start > 5600) {
      stop()
      return
    }
    const dt = Math.min((time - last) / 1000, 0.035)
    last = time
    // Fade the transparent previous frame to leave a short Windows-style card trail.
    context!.save()
    context!.globalCompositeOperation = 'destination-out'
    context!.fillStyle = 'rgba(0,0,0,.35)'
    context!.fillRect(0, 0, width, height)
    context!.restore()
    const style = getComputedStyle(element)
    const paper = style.getPropertyValue('--game-card-paper').trim()
    const ink = style.getPropertyValue('--game-card-ink').trim()
    const red = style.getPropertyValue('--game-card-red').trim()
    const back = style.getPropertyValue('--game-card-back').trim()
    for (const card of particles) {
      if (time - start < card.delay) continue
      card.vy += 640 * dt
      card.x += card.vx * dt
      card.y += card.vy * dt
      card.angle += card.spin * dt
      card.flip += 5 * dt
      const floor = height - cardHeight / 2 - 8
      if (card.y > floor && card.vy > 0) {
        card.y = floor
        card.vy = -Math.max(170, card.vy * 0.72)
      }
      if (card.x < cardWidth / 2 || card.x > width - cardWidth / 2) {
        card.x = Math.max(cardWidth / 2, Math.min(width - cardWidth / 2, card.x))
        card.vx *= -1
      }
      context!.save()
      context!.translate(card.x, card.y)
      context!.rotate(card.angle)
      const face = Math.cos(card.flip)
      context!.scale(Math.max(0.06, Math.abs(face)), 1)
      context!.beginPath()
      context!.roundRect(-cardWidth / 2, -cardHeight / 2, cardWidth, cardHeight, 6)
      context!.fillStyle = face > 0 ? paper : back
      context!.shadowColor = '#0004'
      context!.shadowBlur = 6
      context!.fill()
      context!.shadowBlur = 0
      context!.strokeStyle = style.getPropertyValue('--game-card-back-border').trim()
      context!.lineWidth = 1
      context!.stroke()
      context!.fillStyle = face > 0 && card.suit % 2 ? red : ink
      context!.textAlign = 'center'
      context!.textBaseline = 'middle'
      context!.font = `${cardWidth * 0.5}px sans-serif`
      context!.fillText(face > 0 ? suits[card.suit]! : '✦', 0, 6)
      if (face > 0) {
        context!.textAlign = 'left'
        context!.font = `bold ${cardWidth * 0.22}px sans-serif`
        context!.fillText(
          `${rankName(card.rank)}${suits[card.suit]}`,
          -cardWidth / 2 + 5,
          -cardHeight / 2 + 13,
        )
      }
      context!.restore()
    }
    frame = requestAnimationFrame(draw)
  }
  frame = requestAnimationFrame(draw)
})
onBeforeUnmount(() => {
  stop()
  cancelAnimationFrame(frame)
  observer?.disconnect()
})
</script>

<template><canvas ref="canvas" class="solitaire-celebration" aria-hidden="true"></canvas></template>
