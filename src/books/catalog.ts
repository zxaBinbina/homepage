import library from './library.json'
import collectionMetadata from './collections.json'

export const books = library
export type Book = (typeof books)[number]
export type BookCollection = Omit<(typeof collectionMetadata)[number], 'volumes'> & {
  volumes: Book[]
}
export type ShelfEntry = Book | BookCollection
export function isCollection(entry: ShelfEntry): entry is BookCollection {
  return 'volumes' in entry
}
export const bookCollections: BookCollection[] = collectionMetadata.map((collection) => ({
  ...collection,
  volumes: collection.volumes.map((id) => {
    const book = books.find((book) => book.id === id)
    if (!book) throw new Error(`组合《${collection.title}》的分册不存在：${id}`)
    return book
  }),
}))
const collectionForBook = new Map(
  bookCollections.flatMap((collection) =>
    collection.volumes.map((book) => [book.id, collection] as const),
  ),
)
export const shelfEntries = books.flatMap<ShelfEntry>((book) => {
  const collection = collectionForBook.get(book.id)
  return collection ? (collection.volumes[0] === book ? [collection] : []) : [book]
})
export const entryBooks = (entry: ShelfEntry): Book[] =>
  isCollection(entry) ? entry.volumes : [entry]
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
  synopsis?: string[]
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
