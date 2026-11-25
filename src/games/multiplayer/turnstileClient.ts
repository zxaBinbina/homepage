export type TurnstileApi = {
  render: (element: HTMLElement, options: Record<string, unknown>) => string
  remove: (id: string) => void
  reset: (id: string) => void
}
export const turnstileApi = () => (window as Window & { turnstile?: TurnstileApi }).turnstile
let pending: Promise<void> | undefined
export function loadTurnstile() {
  if (turnstileApi()) return Promise.resolve()
  if (pending) return pending
  pending = new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    const timeout = setTimeout(() => {
      script.remove()
      reject(new Error('安全验证加载超时，请重试。'))
    }, 12000)
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
    script.async = true
    script.onload = () => {
      clearTimeout(timeout)
      resolve()
    }
    script.onerror = () => {
      clearTimeout(timeout)
      script.remove()
      reject(new Error('安全验证暂时无法加载，请重试。'))
    }
    document.head.append(script)
  }).catch((error) => {
    pending = undefined
    throw error
  })
  return pending
}
