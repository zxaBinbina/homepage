import { ref, onMounted, onBeforeUnmount } from 'vue'

export type ColorPalette = 'fufu-blue' | 'hutao-red'

const browserTheme = matchMedia('(prefers-color-scheme: light)')
let manualTheme: 'light' | 'dark' | undefined
let initialPalette: ColorPalette = 'fufu-blue'
try {
  const savedTheme = localStorage.getItem('homepage-theme')
  if (savedTheme === 'light' || savedTheme === 'dark') manualTheme = savedTheme
  if (localStorage.getItem('homepage-palette') === 'hutao-red') initialPalette = 'hutao-red'
} catch {
  /* Keep the browser preference and default palette when storage is unavailable. */
}

const light = ref(manualTheme ? manualTheme === 'light' : browserTheme.matches)
const palette = ref<ColorPalette>(initialPalette)
let subscribers = 0

function themeColor() {
  if (palette.value === 'hutao-red') return light.value ? '#fcf0e1' : '#3a1b19'
  return light.value ? '#f4f6fa' : '#141521'
}

function applyTheme() {
  document.documentElement.dataset.theme = light.value ? 'light' : 'dark'
  document.documentElement.dataset.palette = palette.value
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', themeColor())
}

function followBrowserTheme() {
  if (manualTheme) return
  light.value = browserTheme.matches
  applyTheme()
}

function toggleTheme() {
  light.value = !light.value
  manualTheme = light.value ? 'light' : 'dark'
  applyTheme()
  try {
    localStorage.setItem('homepage-theme', manualTheme)
  } catch {
    /* Theme remains usable. */
  }
}

function setPalette(nextPalette: ColorPalette) {
  palette.value = nextPalette
  applyTheme()
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
    applyTheme()
    if (!subscribed) {
      subscribed = true
      if (subscribers++ === 0) browserTheme.addEventListener('change', followBrowserTheme)
    }
  })
  onBeforeUnmount(() => {
    if (subscribed) {
      subscribed = false
      if (--subscribers === 0) browserTheme.removeEventListener('change', followBrowserTheme)
    }
  })
  return { light, palette, toggleTheme, setPalette }
}
