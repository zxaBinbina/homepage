import type { Book, ChapterIndex } from './catalog'

export interface ReadingProgress {
  version: 1
  revision: string
  chapter: number
  title: string
  paragraph: number
  offset: number
  fraction: number
  updatedAt: number
}
export const progressKey = (id: string) => `homepage-reading:${id}`
const finite = (value: unknown): value is number =>
  typeof value === 'number' && Number.isFinite(value)

export function readProgress(book: Book, preserveOldPosition = false): ReadingProgress | null {
  try {
    const value = JSON.parse(localStorage.getItem(progressKey(book.id)) || 'null')
    if (
      !value ||
      value.version !== 1 ||
      typeof value.revision !== 'string' ||
      !Number.isInteger(value.chapter) ||
      value.chapter < 0 ||
      value.chapter >= book.chapterCount ||
      typeof value.title !== 'string' ||
      !Number.isInteger(value.paragraph) ||
      value.paragraph < 0 ||
      !finite(value.offset) ||
      value.offset < 0 ||
      value.offset > 1 ||
      !finite(value.fraction) ||
      value.fraction < 0 ||
      value.fraction > 1 ||
      !finite(value.updatedAt) ||
      value.updatedAt < 0
    )
      return null
    return {
      ...value,
      paragraph: preserveOldPosition || value.revision === book.revision ? value.paragraph : 0,
      offset: preserveOldPosition || value.revision === book.revision ? value.offset : 0,
    }
  } catch {
    return null
  }
}

export function migratePosition<T extends ReadingProgress>(
  book: Book,
  index: ChapterIndex,
  value: T,
): T {
  if (value.revision === book.revision) return value
  const parts = index.migrations?.[value.revision]?.[value.chapter] || []
  const target = parts.filter((part) => part.from <= value.paragraph).at(-1)
  const chapter = target?.chapter ?? Math.min(value.chapter, index.chapters.length - 1)
  const entry = index.chapters[chapter]!
  const paragraph = target
    ? Math.min(entry.paragraphs - 1, Math.max(0, value.paragraph + target.offset))
    : 0
  return {
    ...value,
    revision: book.revision,
    chapter,
    title: entry.title,
    paragraph,
    offset: target ? value.offset : 0,
    fraction: paragraph / entry.paragraphs,
  }
}

export function writeProgress(book: Book, progress: ReadingProgress): boolean {
  try {
    localStorage.setItem(progressKey(book.id), JSON.stringify(progress))
    return true
  } catch {
    return false
  }
}

export function readFontSize(): number {
  try {
    const value = Number(localStorage.getItem('homepage-reader-font-size'))
    return Number.isInteger(value) && value >= 16 && value <= 28 ? value : 20
  } catch {
    return 20
  }
}
export function writeFontSize(size: number): boolean {
  try {
    localStorage.setItem('homepage-reader-font-size', String(size))
    return true
  } catch {
    return false
  }
}

export const progressPercent = (book: Book, progress: ReadingProgress) =>
  Math.min(100, Math.floor(((progress.chapter + progress.fraction) / book.chapterCount) * 100))
