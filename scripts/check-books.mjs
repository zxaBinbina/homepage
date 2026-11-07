import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import ts from 'typescript'
import { parseBook, organizeChapters, chapterMigration } from './book-parser.mjs'

const fixture = new TextEncoder().encode(
  '书名：测试\r\n简介\r\n第 1 章 来信\r\n====\r\n正文甲\r\n第二节课是草药课。\r\n第二章 魔杖\r\n正文乙\r\n第2章 番外\r\n正文丙\r\n第 3章 结尾\r\n第三章 结尾\r\n正文丁',
)
const parsed = parseBook(fixture)
assert.deepEqual(
  parsed.chapters.map((c) => c.number),
  [1, 2, 2, 3],
)
assert.deepEqual(
  parsed.chapters.map((c) => c.paragraphs),
  [['正文甲', '第二节课是草药课。'], ['正文乙'], ['正文丙'], ['正文丁']],
)
assert.equal(parsed.diagnostics.collapsedHeadings, 1)
assert.deepEqual(parsed.diagnostics.repeated, [2])
assert.throws(() => parseBook(new TextEncoder().encode('没有章节')))
const broken = parseBook(new Uint8Array([...new TextEncoder().encode('第1章 测试\n正文\0'), 0xff]))
assert.match(broken.chapters[0].paragraphs[0], /〔原文此处损坏〕/)
assert.equal(broken.diagnostics.controls, 1)
const groupedFixture = parseBook(
  new TextEncoder().encode(
    '第1章 开场\n正文一\n番外之来信\n番外内容\n第3章 结局\n正文二\n完本感言！\n谢谢读者\n第1章 续篇\n后续故事',
  ),
)
const organized = organizeChapters(groupedFixture, { extraFromChapter: 3 })
assert.deepEqual(
  organized.map((c) => [c.group, c.number, c.parentChapter, c.appendix, c.name]),
  [
    ['main', 1, null, false, '开场'],
    ['extra', null, 0, false, '番外之来信'],
    ['main', 2, null, false, '结局'],
    ['notes', null, 2, false, '完本感言！'],
    ['extra', null, null, true, '番外 · 续篇'],
  ],
)
const skits = organizeChapters(
  parseBook(
    new TextEncoder().encode(
      '第1章 开场\n正文一\n小剧场\n花絮一\n小剧场：来信\n花絮二\n第2章 结局\n正文二\n小剧场\n花絮三',
    ),
  ),
)
assert.deepEqual(
  skits.map((c) => [c.number, c.parentChapter, c.appendix]),
  [
    [1, null, false],
    [null, 0, false],
    [null, 0, false],
    [2, null, false],
    [null, 3, false],
  ],
)
assert.deepEqual(chapterMigration({ chapters: groupedFixture.chapters }, organized)[0], [
  { chapter: 0, from: 0, offset: 0 },
  { chapter: 1, from: 1, offset: -2 },
])
const legacyGrouped = {
  chapters: [organized[0], organized[2], organized[1], organized[4], organized[3]],
}
assert.deepEqual(chapterMigration(legacyGrouped, organized), [
  [{ chapter: 0, from: 0, offset: 0 }],
  [{ chapter: 2, from: 0, offset: 0 }],
  [{ chapter: 1, from: 0, offset: 0 }],
  [{ chapter: 4, from: 0, offset: 0 }],
  [{ chapter: 3, from: 0, offset: 0 }],
])
// Reassembling each original chapter proves that extracting a heading lost no text.
for (const [number, original] of groupedFixture.chapters.entries()) {
  const reconstructed = []
  for (const section of organized
    .filter((c) => c.sourceChapter === number)
    .sort((a, b) => a.sourceParagraph - b.sourceParagraph)) {
    if (section.sourceParagraph) reconstructed.push(section.originalTitle)
    reconstructed.push(...section.paragraphs)
  }
  assert.deepEqual(reconstructed, original.paragraphs)
}

const books = JSON.parse(await readFile('src/books/library.json', 'utf8'))
assert.equal(new Set(books.map((b) => b.id)).size, books.length)
let sections = 0
for (const book of books) {
  const base = `public/books/${book.id}/${book.revision}`
  const index = JSON.parse(await readFile(`${base}-index.json`, 'utf8'))
  assert.equal(index.chapters.length, book.chapterCount)
  const counts = { main: 0, extra: 0, notes: 0 }
  let numbered = 0
  for (const [position, chapter] of index.chapters.entries()) {
    counts[chapter.group]++
    if (chapter.parentChapter !== null) {
      assert.ok(chapter.parentChapter < position)
      const parent = index.chapters[chapter.parentChapter]
      assert.equal(parent.sourceChapter, chapter.sourceChapter)
      assert.equal(parent.parentChapter, null)
      assert.equal(chapter.appendix, false)
      assert.equal(chapter.number, null)
      assert.equal(chapter.title, `第${parent.number}章附篇 · ${chapter.name}`)
    } else if (chapter.appendix) {
      assert.equal(chapter.number, null)
      assert.equal(chapter.title, chapter.name)
    } else {
      assert.equal(chapter.number, ++numbered)
      assert.equal(chapter.title, `第${chapter.number}章 ${chapter.name}`)
    }
    const previous = index.chapters[position - 1]
    assert.ok(
      !previous ||
        chapter.sourceChapter > previous.sourceChapter ||
        (chapter.sourceChapter === previous.sourceChapter &&
          chapter.sourceParagraph > previous.sourceParagraph),
      `${book.id}: chapter ${chapter.number} must remain in source order`,
    )
    assert.equal(typeof chapter.originalTitle, 'string')
  }
  assert.equal(numbered, book.numberedChapterCount)
  assert.equal(index.chapters.filter((c) => c.appendix).length, book.appendixCount)
  assert.deepEqual(counts, book.groups)
  let characters = 0
  const content = []
  for (let part = 0; part < Math.ceil(book.chapterCount / book.chunkSize); part++) {
    const chunk = JSON.parse(await readFile(`${base}-${part}.json`, 'utf8'))
    content.push(...chunk)
  }
  assert.equal(content.length, book.chapterCount)
  for (const [i, paragraphs] of content.entries()) {
    assert.equal(paragraphs.length, index.chapters[i].paragraphs)
    assert.ok(paragraphs.every((p) => typeof p === 'string' && p.length && !p.includes('\0')))
    characters += paragraphs.join('').length
  }
  assert.equal(characters, book.characterCount)
  sections += content.length
}

// Storage validation is tested without a browser; browser checks cover restoring actual positions.
const compiled = ts.transpileModule(await readFile('src/books/progress.ts', 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.ESNext },
}).outputText
const progressModule = `data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`
const { readProgress, writeProgress, readFontSize, migratePosition } = await import(progressModule)
const store = new Map()
globalThis.localStorage = {
  getItem: (key) => store.get(key) || null,
  setItem: (key, value) => store.set(key, value),
}
const book = books[0]
const good = {
  version: 1,
  revision: book.revision,
  chapter: 3,
  title: '第四章',
  paragraph: 12,
  offset: 0.25,
  fraction: 0.3,
  updatedAt: Date.now(),
}
const migrationIndex = {
  chapters: [
    { title: '第1章 开场', paragraphs: 1 },
    { title: '第1章附篇 · 番外之来信', paragraphs: 10 },
  ],
  migrations: {
    old: [
      [
        { chapter: 0, from: 0, offset: 0 },
        { chapter: 1, from: 5, offset: -6 },
      ],
    ],
  },
}
const migrated = migratePosition(book, migrationIndex, {
  ...good,
  revision: 'old',
  chapter: 0,
  paragraph: 8,
})
assert.equal(migrated.chapter, 1)
assert.equal(migrated.paragraph, 2)
assert.equal(migrated.title, '第1章附篇 · 番外之来信')
assert.equal(writeProgress(book, good), true)
assert.deepEqual(readProgress(book), good)
assert.equal(readProgress(books[1]), null)
for (const change of [
  { version: 2 },
  { chapter: -1 },
  { chapter: book.chapterCount },
  { paragraph: -1 },
  { offset: 2 },
  { fraction: -1 },
  { updatedAt: null },
]) {
  writeProgress(book, { ...good, ...change })
  assert.equal(readProgress(book), null)
}
store.set(`homepage-reading:${book.id}`, '{broken')
assert.equal(readProgress(book), null)
assert.equal(readFontSize(), 20)
async function importStorageModule(file) {
  const source = await readFile(`src/books/${file}.ts`, 'utf8')
  const compiled = ts
    .transpileModule(source, {
      compilerOptions: { module: ts.ModuleKind.ESNext },
    })
    .outputText.replace("'./progress'", JSON.stringify(progressModule))
  return import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`)
}
const { readSettings, writeSettings, defaultSettings } = await importStorageModule('readerSettings')
const { readBookmarks, writeBookmarks } = await importStorageModule('bookmarks')
assert.deepEqual(readSettings(), defaultSettings)
store.set('homepage-reader-font-size', '24')
assert.equal(readSettings().fontSize, 24)
const customSettings = {
  ...defaultSettings,
  fontSize: 32,
  mode: 'pages',
  theme: 'night',
  width: 900,
}
assert.equal(writeSettings(customSettings), true)
assert.deepEqual(readSettings(), customSettings)
store.set(
  'homepage-reader-settings',
  JSON.stringify({ fontSize: 200, mode: 'invalid', width: -1, paragraphGap: null }),
)
assert.deepEqual(readSettings(), { ...defaultSettings, fontSize: 24 })
store.set('homepage-reader-settings', '{broken')
assert.equal(readSettings().fontSize, 24)
const bookmark = { ...good, id: 'bookmark-1', excerpt: '正文片段' }
assert.equal(writeBookmarks(book, [bookmark]), true)
assert.deepEqual(readBookmarks(book), [bookmark])
assert.deepEqual(readBookmarks(books[1]), [])
for (const patch of [
  { version: 9 },
  { chapter: -1 },
  { chapter: book.chapterCount },
  { paragraph: -1 },
  { offset: 2 },
  { updatedAt: null },
  { excerpt: 12 },
]) {
  writeBookmarks(book, [{ ...bookmark, ...patch }, bookmark])
  assert.deepEqual(readBookmarks(book), [bookmark])
}
writeBookmarks(
  book,
  Array.from({ length: 600 }, (_, i) => ({ ...bookmark, id: String(i) })),
)
assert.equal(readBookmarks(book).length, 500)
store.set(`homepage-bookmarks:${book.id}`, '{broken')
assert.deepEqual(readBookmarks(book), [])
globalThis.localStorage = {
  getItem() {
    throw new Error('blocked')
  },
  setItem() {
    throw new Error('quota')
  },
}
assert.equal(readProgress(book), null)
assert.equal(writeProgress(book, good), false)
assert.equal(readFontSize(), 20)
assert.deepEqual(readSettings(), defaultSettings)
assert.equal(writeSettings(customSettings), false)
assert.deepEqual(readBookmarks(book), [])
assert.equal(writeBookmarks(book, [bookmark]), false)
console.log(
  `${books.length} books / ${sections} sections: parser edge cases, all chapter chunks, corruption markers and progress/bookmark isolation and settings validation passed.`,
)
