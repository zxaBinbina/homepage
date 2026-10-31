import { onBeforeUnmount, onErrorCaptured, ref } from 'vue'
import { useRoute } from 'vue-router'
import { beginPageLoading } from '../loading/state'

/** Keep delayed feedback active until a page's nested async content is ready. */
export function usePageLoading() {
  const route = useRoute()
  const failed = ref(false)
  let loading: ReturnType<typeof beginPageLoading> | undefined
  function pending() {
    loading ??= beginPageLoading(route.fullPath)
  }
  function resolved() {
    if (failed.value) return
    loading?.finish()
    loading = undefined
  }
  onErrorCaptured(() => {
    failed.value = true
    pending()
    loading?.fail()
    return false
  })
  onBeforeUnmount(() => loading?.finish())
  return { pending, resolved, failed }
}
