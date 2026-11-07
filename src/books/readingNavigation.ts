import type { ReadingProgress } from './progress'

// Keep a paragraph anchor per browser history entry, including column pagination.
// A unique entry ID avoids reusing discarded forward history after a new navigation.
const positions = new Map<string, { book: string; progress: ReadingProgress }>()
export function readerHistoryEntry() {
  const entry: string = history.state?.readerEntry || crypto.randomUUID()
  history.replaceState({ ...history.state, readerEntry: entry }, '')
  return entry
}
export function rememberReaderPosition(entry: string, book: string, progress: ReadingProgress) {
  positions.set(entry, { book, progress })
  if (positions.size > 256) positions.delete(positions.keys().next().value!)
}
export function recalledReaderPosition(entry: string, book: string, chapter: number) {
  const saved = positions.get(entry)
  return saved?.book === book && saved.progress.chapter === chapter ? saved.progress : null
}

// History scroll must wait for the requested chapter to occupy its final layout.
const pending = new Map<string, { promise: Promise<void>; finish: () => void }>()

export function beginReaderNavigation(path: string) {
  pending.get(path)?.finish()
  let resolve!: () => void
  const promise = new Promise<void>((done) => {
    resolve = done
  })
  const task = {
    promise,
    finish() {
      resolve()
      if (pending.get(path) === task) pending.delete(path)
    },
  }
  pending.set(path, task)
  return task.finish
}

export async function waitForReaderNavigation(path: string) {
  await pending.get(path)?.promise
}
