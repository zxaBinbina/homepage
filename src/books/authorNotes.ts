import reviewed from './author-notes.json'

export type NoteRange = readonly [from: number, to: number]
type ReviewedBook = {
  revision: string
  ranges: number[][]
  inline: number[][]
}
const annotations: Record<string, ReviewedBook> = reviewed
type BookVersion = { id: string; revision: string }

export function authorNoteRanges(book: BookVersion, chapter: number): NoteRange[] {
  const entry = annotations[book.id]
  if (entry?.revision !== book.revision) return []
  return entry.ranges
    .filter(([number]) => number === chapter)
    .map(([, from, to]) => [from!, to!] as const)
}

export function inlineNoteRanges(
  book: BookVersion,
  chapter: number,
  paragraph: number,
): NoteRange[] {
  const entry = annotations[book.id]
  if (entry?.revision !== book.revision) return []
  return entry.inline
    .filter(([number, position]) => number === chapter && position === paragraph)
    .map(([, , from, to]) => [from!, to!] as const)
}

export function readingBlocks(paragraphs: string[], notes: NoteRange[]) {
  const blocks: {
    note: boolean
    from: number
    paragraphs: { number: number; text: string }[]
  }[] = []
  function add(from: number, to: number, note: boolean) {
    if (from === to) return
    blocks.push({
      note,
      from,
      paragraphs: paragraphs
        .slice(from, to)
        .map((text, offset) => ({ number: from + offset, text })),
    })
  }
  let cursor = 0
  for (const [from, to] of notes) {
    // A stale or malformed annotation must never hide another passage.
    if (
      !Number.isInteger(from) ||
      !Number.isInteger(to) ||
      from < cursor ||
      to <= from ||
      to > paragraphs.length
    )
      continue
    add(cursor, from, false)
    add(from, to, true)
    cursor = to
  }
  add(cursor, paragraphs.length, false)
  return blocks
}

export function inlineParts(text: string, notes: NoteRange[]) {
  const parts: { text: string; note: boolean }[] = []
  let cursor = 0
  for (const [from, to] of notes) {
    if (
      !Number.isInteger(from) ||
      !Number.isInteger(to) ||
      from < cursor ||
      to <= from ||
      to > text.length
    )
      continue
    if (from > cursor) parts.push({ text: text.slice(cursor, from), note: false })
    parts.push({ text: text.slice(from, to), note: true })
    cursor = to
  }
  if (cursor < text.length) parts.push({ text: text.slice(cursor), note: false })
  return parts
}

export function highlightText(text: string, query: string) {
  if (!query) return [{ text, match: false }]
  const needle = query.toLocaleLowerCase(),
    lower = text.toLocaleLowerCase(),
    parts: { text: string; match: boolean }[] = []
  let offset = 0,
    at = lower.indexOf(needle)
  while (at >= 0) {
    if (at > offset) parts.push({ text: text.slice(offset, at), match: false })
    parts.push({ text: text.slice(at, at + needle.length), match: true })
    offset = at + needle.length
    at = lower.indexOf(needle, offset)
  }
  if (offset < text.length) parts.push({ text: text.slice(offset), match: false })
  return parts
}
