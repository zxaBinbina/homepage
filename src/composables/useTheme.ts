import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { finishThemeTransition, transitionTheme } from '../utils/themeTransition'

export type ColorPalette = 'fufu-blue' | 'hutao-red'
export type ThemeMode = 'dark' | 'light' | 'auto'

const browserTheme = matchMedia('(prefers-color-scheme: light)')
let initialMode: ThemeMode = 'auto'
let initialPalette: ColorPalette = 'fufu-blue'
try {
  const savedTheme = localStorage.getItem('homepage-theme')
  if (savedTheme === 'light' || savedTheme === 'dark') initialMode = savedTheme
  if (localStorage.getItem('homepage-palette') === 'hutao-red') initialPalette = 'hutao-red'
} catch {
  /* Keep the browser preference and default palette when storage is unavailable. */
}

const mode = ref<ThemeMode>(initialMode)
const systemLight = ref(browserTheme.matches)
const light = computed(() => (mode.value === 'auto' ? systemLight.value : mode.value === 'light'))
const nextModes = { dark: 'light', light: 'auto', auto: 'dark' } as const
const nextMode = computed(() => nextModes[mode.value])
const palette = ref<ColorPalette>(initialPalette)
let subscribers = 0

function themeColor() {
  if (palette.value === 'hutao-red') return light.value ? '#fcf0e1' : '#3a1b19'
  return light.value ? '#f4f6fa' : '#141521'
}

function applyTheme(animate = false) {
  const root = document.documentElement
  const theme = light.value ? 'light' : 'dark'
  const changed = root.dataset.theme !== theme || root.dataset.palette !== palette.value
  const update = () => {
    root.dataset.theme = theme
    root.dataset.themeMode = mode.value
    root.dataset.palette = palette.value
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', themeColor())
  }
  if (animate && changed) transitionTheme(update)
  else update()
}

function followBrowserTheme() {
  systemLight.value = browserTheme.matches
  if (mode.value === 'auto') applyTheme(true)
}

function setThemeMode(next: ThemeMode) {
  systemLight.value = browserTheme.matches
  mode.value = next
  applyTheme(true)
  try {
    localStorage.setItem('homepage-theme', next)
  } catch {
    /* Theme remains usable. */
  }
}

function cycleTheme() {
  setThemeMode(nextMode.value)
}

function setPalette(nextPalette: ColorPalette) {
  palette.value = nextPalette
  applyTheme(true)
  try {
    localStorage.setItem('homepage-palette', nextPalette)
  } catch {
    /* Palette remains usable. */
  }
}

/** Shared by the homepage and project pages; matches the first-paint HTML initialization. */
export function useTheme() {
  let subscribed = false
  onMounted(() => {
    systemLight.value = browserTheme.matches
    applyTheme()
    if (!subscribed) {
      subscribed = true
      if (subscribers++ === 0) browserTheme.addEventListener('change', followBrowserTheme)
    }
  })
  onBeforeUnmount(() => {
    if (subscribed) {
      subscribed = false
      if (--subscribers === 0) {
        browserTheme.removeEventListener('change', followBrowserTheme)
        finishThemeTransition()
      }
    }
  })
  return { mode, light, nextMode, palette, cycleTheme, setThemeMode, setPalette }
}
