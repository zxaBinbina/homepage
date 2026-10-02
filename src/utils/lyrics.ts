export interface LyricLine {
  time: number
  text: string
  translation?: string
}

export function parseLrc(source: string): LyricLine[] {
  const offset = Number(source.match(/\[offset:([+-]?\d+)\]/i)?.[1] || 0) / 1000
  const lines: LyricLine[] = []
  for (const raw of source.split(/\r?\n/)) {
    const timestamps = [...raw.matchAll(/\[(\d+):(\d{1,2}(?:\.\d+)?)\]/g)]
    const text = raw.replace(/\[[^\]]*\]/g, '').trim()
    if (!text) continue
    for (const match of timestamps) {
      lines.push({ time: Math.max(0, Number(match[1]) * 60 + Number(match[2]) - offset), text })
    }
  }
  return lines.sort((a, b) => a.time - b.time)
}

export function mergeLyrics(original: string, translation: string): LyricLine[] {
  const translated = new Map(
    parseLrc(translation).map((line) => [Math.round(line.time * 100), line.text]),
  )
  return parseLrc(original).map((line) => ({
    ...line,
    translation: translated.get(Math.round(line.time * 100)),
  }))
}
