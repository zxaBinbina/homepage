import { ref, onMounted, onBeforeUnmount } from 'vue'

/** Shared by the homepage and project pages; matches the first-paint HTML initialization. */
export function useTheme() {
  const browserTheme = matchMedia('(prefers-color-scheme: light)')
  let manualTheme: 'light' | 'dark' | undefined
  try {
    const saved = localStorage.getItem('homepage-theme')
    if (saved === 'light' || saved === 'dark') manualTheme = saved
  } catch {
    /* Follow the browser when storage is unavailable. */
  }
  const light = ref(manualTheme ? manualTheme === 'light' : browserTheme.matches)
  function applyTheme() {
    document.documentElement.dataset.theme = light.value ? 'light' : 'dark'
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute('content', light.value ? '#f4f6fa' : '#141521')
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
  onMounted(() => {
    applyTheme()
    browserTheme.addEventListener('change', followBrowserTheme)
  })
  onBeforeUnmount(() => browserTheme.removeEventListener('change', followBrowserTheme))
  return { light, toggleTheme }
}
