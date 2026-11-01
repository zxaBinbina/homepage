import { cleanJsonl, type CleaningMode } from './cleaner'

self.onmessage = ({ data }: MessageEvent<{ input: string; mode: CleaningMode }>) => {
  try {
    self.postMessage({ result: cleanJsonl(data.input, data.mode) })
  } catch (error) {
    self.postMessage({ error: error instanceof Error ? error.message : '处理失败，请重试。' })
  }
}
