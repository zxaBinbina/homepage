import { onBeforeUnmount, onMounted, ref, type Ref } from 'vue'
import {
  moveCard,
  sourceCards,
  type Card,
  type CardSource,
  type CardTarget,
  type SolitaireGame,
} from './solitaire'
import { useGameMotion } from './useGameMotion'

export const cardId = (card: Card) => `${card.suit}-${card.rank}`
export type CardPosition = { x: number; y: number; width: number; height: number; faceUp: boolean }
type Drag = {
  source: CardSource
  cards: Card[]
  x: number
  y: number
  width: number
  height: number
  step: number
}
type Press = {
  id: number
  touch: boolean
  x: number
  y: number
  lastX: number
  lastY: number
  element: HTMLElement
  source: CardSource
  rect: DOMRect
}

export function useSolitaireDrag(options: {
  game: Ref<SolitaireGame>
  surface: Ref<HTMLElement | undefined>
  scroll: Ref<HTMLElement | undefined>
  canStart: () => boolean
  select: (source: CardSource) => void
  drop: (source: CardSource, target: CardTarget, origins: Map<string, CardPosition>) => void
  cancel: (message: string) => void
}) {
  const drag = ref<Drag | null>(null)
  const target = ref<CardTarget | null>(null)
  const ghost = ref<HTMLElement>()
  const motion = useGameMotion()
  let press: Press | null = null
  let hold: ReturnType<typeof setTimeout> | undefined
  let frame = 0,
    generation = 0
  let suppressClick = false
  function stopPress() {
    clearTimeout(hold)
    cancelAnimationFrame(frame)
    const previous = press
    press = null
    if (previous?.element.hasPointerCapture(previous.id))
      previous.element.releasePointerCapture(previous.id)
  }
  function reset() {
    generation++
    stopPress()
    motion.cancel()
    drag.value = null
    target.value = null
  }
  function findTarget(x: number, y: number) {
    const element = document.elementFromPoint(x, y)?.closest<HTMLElement>('[data-drop-kind]')
    if (!element || !options.surface.value?.contains(element)) {
      target.value = null
      return
    }
    const candidate: CardTarget = {
      kind: element.dataset.dropKind as CardTarget['kind'],
      pile: Number(element.dataset.dropPile),
    }
    target.value =
      drag.value && moveCard(options.game.value, drag.value.source, candidate) ? candidate : null
  }
  function autoScroll() {
    if (!press || !drag.value) return
    const scroll = options.scroll.value
    if (scroll) {
      const rect = scroll.getBoundingClientRect()
      if (press.lastY > rect.top && press.lastY < rect.bottom) {
        const left = Math.max(0, rect.left + 38 - press.lastX)
        const right = Math.max(0, press.lastX - rect.right + 38)
        if (left || right) scroll.scrollLeft += Math.max(-12, Math.min(12, (right - left) / 3))
      }
    }
    const viewport = options.surface.value?.closest<HTMLElement>(
      '.is-fullscreen .game-play-content',
    )
    const top = Math.max(
        0,
        (viewport ? viewport.getBoundingClientRect().top + 45 : 85) - press.lastY,
      ),
      bottom = Math.max(0, press.lastY - innerHeight + 65)
    if (top || bottom)
      (viewport || window).scrollBy({
        top: Math.max(-10, Math.min(10, (bottom - top) / 5)),
        behavior: 'instant',
      })
    findTarget(press.lastX, press.lastY)
    frame = requestAnimationFrame(autoScroll)
  }
  function activate() {
    if (!press || !options.canStart()) return
    const cards = sourceCards(options.game.value, press.source)
    if (!cards.length || cards.some((card) => !card.faceUp)) return
    const table = options.scroll.value?.querySelector('.solitaire-table')
    const step = table ? parseFloat(getComputedStyle(table).getPropertyValue('--card-step')) : 34
    drag.value = {
      source: press.source,
      cards,
      x: press.rect.left + press.lastX - press.x,
      y: press.rect.top + press.lastY - press.y,
      width: press.rect.width,
      height: press.rect.height,
      step,
    }
    options.select(press.source)
    frame = requestAnimationFrame(autoScroll)
  }
  function down(event: PointerEvent, source: CardSource) {
    if (event.button !== 0 || !event.isPrimary || !options.canStart() || drag.value) return
    suppressClick = false
    stopPress()
    const element = event.currentTarget as HTMLElement
    press = {
      id: event.pointerId,
      touch: event.pointerType === 'touch',
      x: event.clientX,
      y: event.clientY,
      lastX: event.clientX,
      lastY: event.clientY,
      element,
      source,
      rect: element.getBoundingClientRect(),
    }
    element.setPointerCapture(event.pointerId)
    if (press.touch) hold = setTimeout(activate, 300)
  }
  function move(event: PointerEvent) {
    if (!press || event.pointerId !== press.id) return
    press.lastX = event.clientX
    press.lastY = event.clientY
    const distance = Math.hypot(event.clientX - press.x, event.clientY - press.y)
    if (!drag.value) {
      if (press.touch && distance > 9) {
        stopPress()
        return
      }
      if (!press.touch && distance > 5) activate()
    }
    if (drag.value && press) {
      drag.value.x = press.rect.left + event.clientX - press.x
      drag.value.y = press.rect.top + event.clientY - press.y
      findTarget(event.clientX, event.clientY)
    }
  }
  async function returnHome(message: string) {
    const current = ++generation
    const active = drag.value
    if (!active) return
    target.value = null
    const source = options.surface.value?.querySelector<HTMLElement>(
      `[data-card-id="${cardId(active.cards[0]!)}"]`,
    )
    const rect = source?.getBoundingClientRect()
    if (rect)
      await motion.settle([
        motion.animate(
          ghost.value,
          [
            { transform: 'translate(0,0)' },
            { transform: `translate(${rect.left - active.x}px,${rect.top - active.y}px)` },
          ],
          { duration: 180, fill: 'both' },
        ),
      ])
    if (current !== generation) return
    drag.value = null
    options.cancel(message)
  }
  function up(event: PointerEvent) {
    if (!press || event.pointerId !== press.id) return
    if (!drag.value) {
      stopPress()
      return
    }
    suppressClick = true
    const active = drag.value
    findTarget(event.clientX, event.clientY)
    const destination = target.value
    stopPress()
    if (!destination) {
      void returnHome('这个位置不能放，纸牌已回到原处。')
      return
    }
    const origins = new Map(
      active.cards.map((card, i) => [
        cardId(card),
        {
          x: active.x,
          y: active.y + i * active.step,
          width: active.width,
          height: active.height,
          faceUp: true,
        },
      ]),
    )
    drag.value = null
    target.value = null
    options.drop(active.source, destination, origins)
  }
  function cancel() {
    if (drag.value) suppressClick = true
    stopPress()
    void returnHome('已取消拖动，纸牌回到原处。')
  }
  function pointerCancel(event: PointerEvent) {
    if (press?.id === event.pointerId) cancel()
  }
  function clickCapture(event: MouseEvent) {
    if (suppressClick && event.detail > 0) {
      suppressClick = false
      event.preventDefault()
      event.stopPropagation()
    }
  }
  function newPress() {
    suppressClick = false
  }
  function touchMove(event: TouchEvent) {
    if (drag.value && event.cancelable) event.preventDefault()
  }
  function isOrigin(card: Card) {
    return !!drag.value?.cards.some((item) => cardId(item) === cardId(card))
  }
  function isTarget(kind: CardTarget['kind'], pile: number) {
    return target.value?.kind === kind && target.value.pile === pile
  }
  function interrupted() {
    if (drag.value || press) {
      reset()
      options.cancel('拖动已取消。')
    }
  }
  onMounted(() => {
    window.addEventListener('blur', interrupted)
    window.addEventListener('resize', interrupted)
    document.addEventListener('visibilitychange', interrupted)
  })
  onBeforeUnmount(() => {
    reset()
    window.removeEventListener('blur', interrupted)
    window.removeEventListener('resize', interrupted)
    document.removeEventListener('visibilitychange', interrupted)
  })
  return {
    drag,
    target,
    ghost,
    down,
    move,
    up,
    cancel,
    pointerCancel,
    reset,
    clickCapture,
    newPress,
    touchMove,
    isOrigin,
    isTarget,
  }
}
