import { convertPages } from './export'
import type { ConvertOptions, PdfPageData } from './types'

self.onmessage = async (event: MessageEvent<{ pages: PdfPageData[]; options: ConvertOptions }>) => {
  try {
    const result = await convertPages(event.data.pages, event.data.options)
    self.postMessage({ result }, { transfer: [result.bytes.buffer] })
  } catch (error) {
    self.postMessage({
      error: error instanceof Error ? error.message : '转换失败，请检查文件后重试。',
    })
  }
}
