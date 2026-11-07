import type { Book } from './catalog'
import type { ReadingProgress } from './progress'

export interface Bookmark extends ReadingProgress {
  id: string
  excerpt: string
}
const key = (book: Book) => `homepage-bookmarks:${book.id}`
export function readBookmarks(book: Book): Bookmark[] {
  try {
    const value = JSON.parse(localStorage.getItem(key(book)) || '[]')
    if (!Array.isArray(value)) return []
    return value
      .filter(
        (item) =>
          item &&
          typeof item.id === 'string' &&
          typeof item.title === 'string' &&
          typeof item.excerpt === 'string' &&
          item.version === 1 &&
          typeof item.revision === 'string' &&
          Number.isInteger(item.chapter) &&
          item.chapter >= 0 &&
          item.chapter < book.chapterCount &&
          Number.isInteger(item.paragraph) &&
          item.paragraph >= 0 &&
          Number.isFinite(item.offset) &&
          item.offset >= 0 &&
          item.offset <= 1 &&
          Number.isFinite(item.updatedAt) &&
          item.updatedAt >= 0,
      )
      .slice(0, 500)
  } catch {
    return []
  }
}
export function writeBookmarks(book: Book, bookmarks: Bookmark[]) {
  try {
    localStorage.setItem(key(book), JSON.stringify(bookmarks))
    return true
  } catch {
    return false
  }
}
