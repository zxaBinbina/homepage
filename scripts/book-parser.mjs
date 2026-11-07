const chapterPattern = /^第\s*([0-9零〇一二三四五六七八九十百千万两]+)\s*章\s*(.{0,100})$/u
const separator = /^[=＝]{3,}$/u

export function chapterNumber(value) {
  if (/^\d+$/.test(value)) return Number(value)
  const digits = {
    零: 0,
    〇: 0,
    一: 1,
    二: 2,
    两: 2,
    三: 3,
    四: 4,
    五: 5,
    六: 6,
    七: 7,
    八: 8,
    九: 9,
  }
  const units = { 十: 10, 百: 100, 千: 1000, 万: 10000 }
  let number = 0,
    digit = 0
  for (const character of value) {
    if (character in digits) digit = digits[character]
    else {
      number += (digit || 1) * units[character]
      digit = 0
    }
  }
  return number + digit
}

/** Preserve source order, including gaps and repeated chapter numbers. */
export function parseBook(bytes) {
  const decoded = new TextDecoder('utf-8').decode(bytes)
  const replacements = (decoded.match(/\uFFFD/g) || []).length
  const controls = (decoded.match(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g) || []).length
  const text = decoded
    .replace(/\uFFFD+/g, '〔原文此处损坏〕')
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '')
  const preface = [],
    chapters = []
  let current
  let collapsedHeadings = 0
  for (const raw of text.split(/\r\n?|\n/u)) {
    const line = raw.trim()
    if (!line || separator.test(line)) continue
    const match = chapterPattern.exec(line)
    if (match) {
      const number = chapterNumber(match[1])
      // Some exports put the same Arabic/Chinese heading on adjacent lines.
      if (current && current.number === number && !current.paragraphs.length) {
        collapsedHeadings += 1
        continue
      }
      current = { title: line, number, paragraphs: [] }
      chapters.push(current)
    } else (current ? current.paragraphs : preface).push(line)
  }
  if (!chapters.length || chapters.some((chapter) => !chapter.paragraphs.length))
    throw new Error('无法识别章节，或发现没有正文的章节，请检查源文件')
  const numbers = chapters.map((chapter) => chapter.number)
  const lastNumber = Math.max(...numbers)
  const missing = Array.from({ length: lastNumber }, (_, i) => i + 1).filter(
    (n) => !numbers.includes(n),
  )
  const repeated = [...new Set(numbers.filter((n, i) => numbers.indexOf(n) !== i))]
  return {
    preface,
    chapters,
    diagnostics: {
      replacements,
      controls,
      collapsedHeadings,
      missing,
      repeated,
      lastNumber,
      outOfOrder: numbers.some((n, i) => i > 0 && n < numbers[i - 1]),
    },
  }
}

const extraHeading =
  /^(?:番外(?:之|结局|[\d一二三四五六七八九十（(：:]|$)|小剧场(?:$|[—－：:])|小脑洞$)/u
const noteHeading = /^(?:完本感言|完结感言|作者的话|后记|附记)[！!：:。]?$/u
const groupForTitle = (title) =>
  noteHeading.test(title) ? 'notes' : extraHeading.test(title) ? 'extra' : 'main'

/** Split explicitly headed bonus material; retain provenance for numbering and migration. */
export function organizeChapters(parsed, options = {}) {
  const sections = []
  for (const [sourceChapter, chapter] of parsed.chapters.entries()) {
    const name = chapter.title.replace(chapterPattern, '$2').trim() || '无题'
    const initialGroup =
      options.extraFromChapter && sourceChapter + 1 >= options.extraFromChapter
        ? 'extra'
        : groupForTitle(name)
    let current = {
      name,
      originalTitle: chapter.title,
      group: initialGroup,
      sourceChapter,
      sourceParagraph: 0,
      paragraphs: [],
    }
    for (const [paragraph, text] of chapter.paragraphs.entries()) {
      const group = text.length <= 70 ? groupForTitle(text) : 'main'
      if (group !== 'main') {
        if (current.paragraphs.length) sections.push(current)
        current = {
          name: text,
          originalTitle: text,
          group,
          sourceChapter,
          sourceParagraph: paragraph + 1,
          paragraphs: [],
        }
      } else current.paragraphs.push(text)
    }
    if (current.paragraphs.length) sections.push(current)
  }
  // Keep the flat reading order; unnumbered material belongs to its source chapter.
  const parents = new Map()
  let chapterNumber = 0
  const lastMain = sections.findLastIndex((section) => section.group === 'main')
  return sections.map((section, index) => {
    const appendix =
      lastMain >= 0 &&
      index > lastMain &&
      section.group === 'extra' &&
      !(section.sourceParagraph > 0 && /^小剧场/u.test(section.name))
    const parent = appendix ? undefined : parents.get(section.sourceChapter)
    const number = parent || appendix ? null : ++chapterNumber
    if (!parent && !appendix) parents.set(section.sourceChapter, { index, number })
    const name =
      section.group === 'extra' && !extraHeading.test(section.name)
        ? `番外 · ${section.name}`
        : section.name
    return {
      ...section,
      name,
      number,
      parentChapter: parent?.index ?? null,
      appendix,
      title: appendix
        ? name
        : parent
          ? `第${parent.number}章附篇 · ${name}`
          : `第${number}章 ${name}`,
    }
  })
}

export function chapterMigration(previous, chapters) {
  return previous.chapters.map((old, oldNumber) => {
    const sourceChapter = old.sourceChapter ?? oldNumber
    const sourceParagraph = old.sourceParagraph ?? 0
    const end = Math.min(
      ...previous.chapters
        .filter(
          (entry) =>
            entry.sourceChapter === sourceChapter && entry.sourceParagraph > sourceParagraph,
        )
        .map((entry) => entry.sourceParagraph),
      Infinity,
    )
    return chapters
      .flatMap((chapter, number) =>
        chapter.sourceChapter === sourceChapter &&
        chapter.sourceParagraph >= sourceParagraph &&
        chapter.sourceParagraph < end
          ? [
              {
                chapter: number,
                from: Math.max(
                  0,
                  chapter.sourceParagraph - sourceParagraph - (chapter.sourceParagraph ? 1 : 0),
                ),
                offset: sourceParagraph - chapter.sourceParagraph,
              },
            ]
          : [],
      )
      .sort((a, b) => a.from - b.from)
  })
}
