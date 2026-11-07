import { readFontSize } from './progress'

export interface ReaderSettings {
  fontSize: number
  font: 'sans' | 'serif'
  lineHeight: number
  paragraphGap: number
  width: number
  theme: 'site' | 'paper' | 'green' | 'night'
  mode: 'scroll' | 'pages'
}
export const defaultSettings: ReaderSettings = {
  fontSize: 20,
  font: 'sans',
  lineHeight: 1.9,
  paragraphGap: 1,
  width: 760,
  theme: 'site',
  mode: 'scroll',
}
export function readSettings(): ReaderSettings {
  const fallback = { ...defaultSettings, fontSize: readFontSize() }
  try {
    const value = JSON.parse(localStorage.getItem('homepage-reader-settings') || 'null')
    if (!value || typeof value !== 'object') return fallback
    return {
      fontSize:
        Number.isInteger(value.fontSize) && value.fontSize >= 16 && value.fontSize <= 32
          ? value.fontSize
          : fallback.fontSize,
      font: value.font === 'serif' ? 'serif' : 'sans',
      lineHeight: [1.6, 1.9, 2.2].includes(value.lineHeight) ? value.lineHeight : 1.9,
      paragraphGap: [0.5, 1, 1.5].includes(value.paragraphGap) ? value.paragraphGap : 1,
      width: [640, 760, 900].includes(value.width) ? value.width : 760,
      theme: ['site', 'paper', 'green', 'night'].includes(value.theme) ? value.theme : 'site',
      mode: value.mode === 'pages' ? 'pages' : 'scroll',
    }
  } catch {
    return fallback
  }
}
export function writeSettings(settings: ReaderSettings) {
  try {
    localStorage.setItem('homepage-reader-settings', JSON.stringify(settings))
    return true
  } catch {
    return false
  }
}
