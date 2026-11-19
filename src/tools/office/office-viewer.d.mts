export class OfficeViewer {
  constructor(
    container: HTMLElement,
    options: { url: string; title?: string; timeoutMs?: number; params?: Record<string, string> },
  )
  ready: Promise<unknown>
  iframe: HTMLIFrameElement | null
  on(event: string, callback: (data: { phase?: string; error?: unknown }) => void): () => void
  open(document: {
    name: string
    data: Uint8Array
    mode: 'desktop' | 'embedded'
    timeoutMs: number
  }): Promise<unknown>
  call(method: string, params?: Record<string, unknown>): Promise<unknown>
  destroy(): void
}
