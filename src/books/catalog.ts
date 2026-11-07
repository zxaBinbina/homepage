import library from './library.json'

export const books = library
export type Book = (typeof books)[number]
export type BookPageName = `book.${string}`
export const bookPath = (book: Book) => `/books/${book.id}`
export const bookPage = (book: Book): BookPageName => `book.${book.id}`
export function isBookPage(page: unknown): page is BookPageName {
  return typeof page === 'string' && books.some((book) => bookPage(book) === page)
}
export const bookForPage = (page: string) => books.find((book) => bookPage(book) === page)!
export const chapterPath = (book: Book, chapter: number) =>
  `${bookPath(book)}?chapter=${chapter + 1}`
export const bookAsset = (book: Book, part: string | number) =>
  `/books/${book.id}/${book.revision}-${part}.json`

export interface ChapterIndex {
  preface: string[]
  migrations?: Record<string, { chapter: number; from: number; offset: number }[][]>
  chapters: {
    title: string
    name: string
    originalTitle: string
    number: number | null
    parentChapter: number | null
    appendix: boolean
    group: 'main' | 'extra' | 'notes'
    sourceChapter: number
    sourceParagraph: number
    paragraphs: number
  }[]
}

export function bookLength(book: Book) {
  const supplements = book.chapterCount - book.numberedChapterCount - book.appendixCount
  return `${book.numberedChapterCount} 章${book.appendixCount ? ` · ${book.appendixCount} 篇番外` : ''}${supplements ? ` · ${supplements} 篇附篇` : ''}`
}
