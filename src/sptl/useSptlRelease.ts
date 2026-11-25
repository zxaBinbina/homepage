import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { SptlRelease } from './release'

export function useSptlRelease() {
  const release = ref<SptlRelease | null>(null)
  const loading = ref(true)
  const error = ref(false)
  let controller: AbortController | undefined

  async function refresh() {
    controller?.abort()
    const request = new AbortController()
    controller = request
    const timeout = setTimeout(() => request.abort(), 28000)
    loading.value = true
    error.value = false
    try {
      const response = await fetch('/api/projects/SPTL/release', { signal: request.signal })
      if (!response.ok) throw new Error('Release unavailable')
      const data = (await response.json()) as SptlRelease
      if (!/^\d+\.\d+\.\d+$/.test(data.version) || !Array.isArray(data.assets))
        throw new Error('Invalid release')
      if (controller === request) release.value = data
    } catch {
      if (controller === request) error.value = true
    } finally {
      clearTimeout(timeout)
      if (controller === request) loading.value = false
    }
  }

  onMounted(refresh)
  onBeforeUnmount(() => {
    controller?.abort()
    controller = undefined
  })
  return { release, loading, error, refresh }
}
