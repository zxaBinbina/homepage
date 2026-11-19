import type { PdfPageData } from './types'

interface SlideText {
  text: string
  x: number
  y: number
  w: number
  h: number
  fontFace: string
  fontSize: number
  bold: boolean
  italic: boolean
}

export interface PresentationSize {
  width: number
  height: number
}

// All coordinates used by the PPTX writer are in inches.
export function presentationSize(page: PdfPageData): PresentationSize {
  return { width: Math.min(40, page.width / 72), height: Math.min(40, page.height / 72) }
}
export function slideFrame(page: PdfPageData, size: PresentationSize) {
  const ratio = Math.min(size.width / page.width, size.height / page.height)
  return {
    x: (size.width - page.width * ratio) / 2,
    y: (size.height - page.height * ratio) / 2,
    w: page.width * ratio,
    h: page.height * ratio,
    ratio,
  }
}
export function slideText(
  item: PdfPageData['items'][number],
  page: PdfPageData,
  size: PresentationSize,
): SlideText {
  const { x, y, ratio } = slideFrame(page, size)
  const font = page.fonts[item.font]?.name || ''
  return {
    text: item.text,
    x: x + item.x * ratio,
    y: y + item.y * ratio,
    w: Math.max(item.width * ratio + 0.03, 0.08),
    h: Math.max(item.height * ratio * 1.4, 0.08),
    fontFace: /[\u3400-\u9fff]/.test(item.text)
      ? 'Microsoft YaHei'
      : /serif|times/i.test(font)
        ? 'Times New Roman'
        : 'Arial',
    fontSize: Math.max(2, Math.min(400, item.height * ratio * 72)),
    bold: /bold/i.test(font),
    italic: /italic|oblique/i.test(font),
  }
}
