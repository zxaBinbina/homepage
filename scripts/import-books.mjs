import { readFile, readdir, mkdir, writeFile, stat } from 'node:fs/promises'
import { resolve, join, basename } from 'node:path'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { parseBook, organizeChapters, chapterMigration } from './book-parser.mjs'

const root = fileURLToPath(new URL('../', import.meta.url))
const sources = process.argv.slice(2)
if (!sources.length) throw new Error('用法：node scripts/import-books.mjs <TXT目录或文件> ...')
const overrides = JSON.parse(await readFile(join(root, 'src/books/overrides.json'), 'utf8'))
const files = []
for (const source of sources) {
  const path = resolve(source)
  if ((await stat(path)).isDirectory()) {
    files.push(
      ...(await readdir(path))
        .filter((name) => name.toLowerCase().endsWith('.txt'))
        .map((name) => join(path, name)),
    )
  } else files.push(path)
}
const candidates = [...new Set(files)]
const used = new Set()
const books = [],
  report = []
const chunkSize = 24
const previousBooks = JSON.parse(
  await readFile(join(root, 'src/books/library.json'), 'utf8').catch(() => '[]'),
)
for (const config of overrides) {
  const matches = candidates.filter(
    (path) =>
      basename(path) === config.match + '.txt' ||
      basename(path).startsWith(config.match + ' ') ||
      basename(path).startsWith(config.match + '('),
  )
  if (matches.length !== 1)
    throw new Error(`${config.match}：需要唯一的源文件，找到 ${matches.length} 份`)
  const source = matches[0]
  used.add(source)
  const filename = basename(source)
  const match = /^(.*?)\s+(\S+)\s+(\d+)-(\d+)章\.txt$/u.exec(filename)
  if (!match && !config.author)
    throw new Error(`文件名未提供作者，请在 overrides.json 中补充：${filename}`)
  const [, fullTitle, author, , expectedEnd] = match || [
    null,
    config.match,
    config.author,
    null,
    null,
  ]
  const alias = /\(别名[_：:](.*?)\)/u.exec(fullTitle)?.[1] || config.alias || ''
  const title = config.title || fullTitle.replace(/\(别名[_：:].*?\)/u, '')
  const bytes = await readFile(source)
  const sha256 = createHash('sha256').update(bytes).digest('hex')
  const parsed = parseBook(bytes)
  const { preface, diagnostics } = parsed
  const chapters = organizeChapters(parsed, config)
  const groups = Object.fromEntries(
    ['main', 'extra', 'notes'].map((group) => [
      group,
      chapters.filter((c) => c.group === group).length,
    ]),
  )
  const revision = createHash('sha256')
    .update(JSON.stringify({ preface, chapters, chunkSize }))
    .digest('hex')
    .slice(0, 12)
  const directory = join(root, 'public/books', config.id)
  await mkdir(directory, { recursive: true })
  const writeJson = (name, value) => writeFile(join(directory, name), JSON.stringify(value) + '\n')
  const previous = previousBooks.find((entry) => entry.id === config.id)
  const oldIndex =
    previous &&
    JSON.parse(await readFile(join(directory, `${previous.revision}-index.json`), 'utf8'))
  const migrations = { ...oldIndex?.migrations }
  if (previous && previous.revision !== revision) {
    const migration = chapterMigration(oldIndex, chapters)
    for (const [oldRevision, entries] of Object.entries(migrations)) {
      migrations[oldRevision] = entries
        .map((parts) =>
          parts.flatMap((part) =>
            (migration[part.chapter] || []).map((next) => ({
              chapter: next.chapter,
              from: Math.max(part.from, next.from - part.offset),
              offset: part.offset + next.offset,
            })),
          ),
        )
        .map((parts) => parts.sort((a, b) => a.from - b.from))
    }
    migrations[previous.revision] = migration
  }
  await writeJson(`${revision}-index.json`, {
    preface,
    migrations,
    chapters: chapters.map(({ paragraphs, ...chapter }) => ({
      ...chapter,
      paragraphs: paragraphs.length,
    })),
  })
  for (let start = 0; start < chapters.length; start += chunkSize)
    await writeJson(
      `${revision}-${start / chunkSize}.json`,
      chapters.slice(start, start + chunkSize).map(({ paragraphs }) => paragraphs),
    )
  books.push({
    id: config.id,
    title,
    alias,
    author: config.author || author,
    category: config.category,
    description: config.description,
    cover: config.cover,
    coverSource: config.coverSource,
    chapterCount: chapters.length,
    numberedChapterCount: chapters.filter((chapter) => chapter.number !== null).length,
    appendixCount: chapters.filter((chapter) => chapter.appendix).length,
    groups,
    characterCount: chapters.reduce((sum, c) => sum + c.paragraphs.join('').length, 0),
    revision,
    chunkSize,
    sourceNote: diagnostics.replacements ? '这份文本有一处损坏，已在对应段落标记。' : '',
  })
  report.push({
    id: config.id,
    filename,
    sha256,
    filenameEnd: expectedEnd == null ? null : Number(expectedEnd),
    sourceChapterCount: parsed.chapters.length,
    chapterCount: chapters.length,
    numberedChapterCount: chapters.filter((chapter) => chapter.number !== null).length,
    appendixCount: chapters.filter((chapter) => chapter.appendix).length,
    groups,
    ...diagnostics,
  })
  console.log(
    `${title}：${chapters.length} 节，文件章数标注 ${expectedEnd ?? '无'}，原文最大章号 ${diagnostics.lastNumber}`,
  )
}
for (const path of candidates.filter((path) => !used.has(path)))
  console.log(`未收录（未在 overrides.json 登记）：${basename(path)}`)
await writeFile(join(root, 'src/books/library.json'), JSON.stringify(books, null, 2) + '\n')
await writeFile(join(root, 'src/books/import-report.json'), JSON.stringify(report, null, 2) + '\n')
