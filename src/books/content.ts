import { bookAsset, type Book, type ChapterIndex } from './catalog'

export async function fetchBookJson(book: Book, part: string | number, signal: AbortSignal) {
  const response = await fetch(bookAsset(book, part), { signal })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}
export function bookSynopsis(book: Book, index?: ChapterIndex) {
  const preface = index?.preface || []
  const start = preface.findIndex((line) => /^简介\s*[:：]$/.test(line))
  return start >= 0 && preface.length > start + 1 ? preface.slice(start + 1) : [book.description]
}
export interface SearchResult {
  chapter: number
  paragraph: number
  excerpt: string
}
export async function searchBook(
  book: Book,
  query: string,
  signal: AbortSignal,
  onProgress: (loaded: number) => void,
) {
  const results: SearchResult[] = []
  const term = query.trim().toLocaleLowerCase()
  if (!term) return results
  const count = Math.ceil(book.chapterCount / book.chunkSize)
  for (let part = 0; part < count; part++) {
    signal.throwIfAborted()
    const chunk: string[][] = await fetchBookJson(book, part, signal)
    for (const [offset, paragraphs] of chunk.entries()) {
      for (const [paragraph, text] of paragraphs.entries()) {
        const at = text.toLocaleLowerCase().indexOf(term)
        if (at < 0) continue
        const start = Math.max(0, at - 24),
          end = Math.min(text.length, at + term.length + 50)
        results.push({
          chapter: part * book.chunkSize + offset,
          paragraph,
          excerpt: `${start ? '…' : ''}${text.slice(start, end)}${end < text.length ? '…' : ''}`,
        })
        if (results.length >= 200) {
          onProgress(part + 1)
          return results
        }
      }
    }
    onProgress(part + 1)
  }
  return results
}
export function positionPath(book: Book, chapter: number, paragraph: number, offset = 0) {
  return `/books/${book.id}?chapter=${chapter + 1}&paragraph=${paragraph + 1}&offset=${offset.toFixed(3)}`
}
