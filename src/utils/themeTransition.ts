const duration = 1000
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)')
let colorProperties: string[] | undefined
let active: Animation | undefined

function registerColors(root: HTMLElement) {
  if (colorProperties) return colorProperties
  const style = getComputedStyle(root)
  const candidates = Array.from(style).filter(
    (name) => name.startsWith('--') && CSS.supports('color', style.getPropertyValue(name)),
  )
  colorProperties = candidates.filter((name) => {
    try {
      CSS.registerProperty({ name, syntax: '<color>', inherits: true, initialValue: 'transparent' })
      return true
    } catch (error) {
      // A development hot reload may have already registered the same color token.
      return error instanceof DOMException && error.name === 'InvalidModificationError'
    }
  })
  return colorProperties
}

function colors(root: HTMLElement, properties: string[]) {
  const style = getComputedStyle(root)
  return Object.fromEntries(properties.map((name) => [name, style.getPropertyValue(name).trim()]))
}

export function finishThemeTransition() {
  if (active) {
    active.onfinish = null
    active.cancel()
    active = undefined
  }
  reducedMotion.removeEventListener('change', onMotionChange)
  document.removeEventListener('visibilitychange', onVisibilityChange)
}

function onMotionChange() {
  if (reducedMotion.matches) finishThemeTransition()
}

function onVisibilityChange() {
  if (document.hidden) finishThemeTransition()
}

/** Interpolate shared colors, including gradient stops, without touching component motion. */
export function transitionTheme(update: () => void) {
  const root = document.documentElement
  if (
    reducedMotion.matches ||
    document.hidden ||
    typeof CSS.registerProperty !== 'function' ||
    typeof root.animate !== 'function'
  ) {
    finishThemeTransition()
    update()
    return
  }

  const properties = registerColors(root)
  // Capture the currently displayed colors before cancelling an unfinished transition.
  const before = colors(root, properties)
  finishThemeTransition()
  update()
  const after = colors(root, properties)
  const changed = properties.filter((name) => before[name] !== after[name])
  if (!changed.length) return

  active = root.animate(
    [
      Object.fromEntries(changed.map((name) => [name, before[name]])),
      Object.fromEntries(changed.map((name) => [name, after[name]])),
    ],
    { duration, easing: 'ease-in-out' },
  )
  active.id = 'theme-colors'
  active.onfinish = finishThemeTransition
  reducedMotion.addEventListener('change', onMotionChange)
  document.addEventListener('visibilitychange', onVisibilityChange)
}
