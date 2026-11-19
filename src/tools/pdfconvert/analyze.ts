import TextItem from './pdf2md/models/TextItem.js'
import { makeTransformations, transform } from './pdf2md/util/transformations.js'
import type { PdfPageData, TextBox } from './types'

export interface TextBlock {
  kind: 'text'
  y: number
  text: string
  markdown: string
  level: number
  list: boolean
}
export interface TableBlock {
  kind: 'table'
  y: number
  rows: string[][]
}
export type Block = TextBlock | TableBlock
export interface AnalyzedPage extends PdfPageData {
  blocks: Block[]
}

const cjk = '\\p{Script=Han}\\p{Script=Hiragana}\\p{Script=Katakana}'
const cjkSpace = new RegExp(`(?<=[${cjk}]) +(?=[${cjk}])`, 'gu')
export function normalizeText(text: string) {
  // Chrome's CJK subsets can expose simplified radical glyphs as characters.
  const aliases: Record<string, string> = { '⻓': '长', '⻚': '页', '⻔': '门' }
  return text.replace(
    /[⻓⻚⻔\u2f00-\u2fdf\ufb00-\ufb06]/g,
    (c) => aliases[c] || c.normalize('NFKC'),
  )
}
export function joinText(parts: string[]) {
  return parts
    .map((p) => p.trim())
    .filter(Boolean)
    .join(' ')
    .replace(cjkSpace, '')
}

export function textLines(items: TextBox[]) {
  const lines: TextBox[][] = []
  for (const item of [...items]
    .filter((i) => i.text.trim())
    .sort((a, b) => a.y - b.y || a.x - b.x)) {
    const last = lines.at(-1)
    if (
      last &&
      Math.abs(last[0]!.y - item.y) <= Math.max(2, Math.min(last[0]!.height, item.height) * 0.25)
    )
      last.push(item)
    else lines.push([item])
  }
  return lines.map((line) => line.sort((a, b) => a.x - b.x))
}

// Conservative text alignment detection: at least three rows with matching
// column starts. Bordered and borderless tables use the same text geometry.
export function detectTables(items: TextBox[]) {
  const tables: TableBlock[] = []
  const used = new Set<TextBox>()
  let group: { cells: TextBox[][]; y: number; height: number }[] = []
  const flush = () => {
    if (group.length >= 3) {
      tables.push({
        kind: 'table',
        y: group[0]!.y,
        rows: group.map((row) => row.cells.map((cell) => joinText(cell.map((i) => i.text)))),
      })
      for (const row of group) for (const cell of row.cells) for (const item of cell) used.add(item)
    }
    group = []
  }
  for (const line of textLines(items)) {
    const cells: TextBox[][] = []
    for (const item of line) {
      const cell = cells.at(-1),
        previous = cell?.at(-1)
      if (!previous || item.x - previous.x - previous.width > Math.max(12, item.height * 1.1))
        cells.push([item])
      else cell!.push(item)
    }
    if (cells.length < 2) {
      flush()
      continue
    }
    const y = line[0]!.y,
      height = Math.max(...line.map((i) => i.height))
    const prior = group.at(-1)
    const aligned =
      !prior ||
      (prior.cells.length === cells.length &&
        y - prior.y <= Math.max(height, prior.height) * 4.5 &&
        cells.every(
          (cell, i) => Math.abs(cell[0]!.x - group[0]!.cells[i]![0]!.x) <= Math.max(12, height),
        ))
    if (!aligned) flush()
    group.push({ cells, y, height })
  }
  flush()
  return { tables, used }
}

export function analyzePages(pages: PdfPageData[]): AnalyzedPage[] {
  const tableData = pages.map((page) => detectTables(page.items))
  const fontMap = new Map(pages.flatMap((page) => Object.entries(page.fonts)))
  const source = pages.map((page, index) => ({
    index,
    items: page.items
      .filter((item) => !tableData[index]!.used.has(item))
      .map(
        (item) =>
          new TextItem({
            ...item,
            y: Math.round(page.height - item.y),
            x: Math.round(item.x),
            height: Math.max(1, Math.round(item.height)),
            text: normalizeText(item.text),
          }),
      ),
  }))
  const parsed = transform(source, makeTransformations(fontMap))
  return pages.map((page, index) => {
    const blocks: Block[] = parsed.pages[index].items
      .map(
        (block: {
          type?: { headlineLevel?: number; name?: string }
          items: {
            y: number
            words: { string: string; format?: { startSymbol: string; endSymbol: string } }[]
          }[]
        }): TextBlock => {
          const text = joinText(
            block.items.map((line) => joinText(line.words.map((w) => w.string))),
          )
          const level = block.type?.headlineLevel || 0
          const list = block.type?.name === 'LIST'
          const formatted = joinText(
            block.items.map((line) =>
              joinText(
                line.words.map((w) =>
                  w.format ? `${w.format.startSymbol}${w.string}${w.format.endSymbol}` : w.string,
                ),
              ),
            ),
          )
          return {
            kind: 'text',
            y: page.height - block.items[0]!.y,
            text,
            markdown: level ? `${'#'.repeat(level)} ${text}` : formatted,
            level,
            list,
          }
        },
      )
      .filter((block: TextBlock) => block.text.trim())
    blocks.push(
      ...tableData[index]!.tables.map((table) => ({
        ...table,
        rows: table.rows.map((row) => row.map(normalizeText)),
      })),
    )
    blocks.sort((a, b) => a.y - b.y)
    return { ...page, blocks }
  })
}

export function tableMarkdown(rows: string[][]) {
  const escape = (text: string) =>
    text
      .replace(/\\/g, '\\\\')
      .replace(/\|/g, '\\|')
      .replace(/[\r\n]+/g, ' ')
  return rows
    .map(
      (row, i) =>
        `| ${row.map(escape).join(' | ')} |${i === 0 ? `\n| ${row.map(() => '---').join(' | ')} |` : ''}`,
    )
    .join('\n')
}
export function toMarkdown(pages: AnalyzedPage[], pageBreaks: boolean) {
  return (
    pages
      .map((page) =>
        page.blocks
          .map((block) => (block.kind === 'table' ? tableMarkdown(block.rows) : block.markdown))
          .join('\n\n'),
      )
      .join(pageBreaks ? '\n\n<!-- PAGE_BREAK -->\n\n' : '\n\n')
      .trim() + '\n'
  )
}

// Keep identifiers, leading zeros, dates and unsafe integers as strings.
export function numericCell(value: string, enabled: boolean): string | number {
  if (!enabled || !/^-?(?:0|[1-9]\d*|[1-9]\d{0,2}(?:,\d{3})+)(?:\.\d+)?$/.test(value)) return value
  const plain = value.replaceAll(',', '')
  if (plain.replace(/[-.]/g, '').length > 15) return value
  const number = Number(plain)
  return Number.isFinite(number) && Math.abs(number) <= Number.MAX_SAFE_INTEGER ? number : value
}
