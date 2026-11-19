import { analyzePages, numericCell, toMarkdown } from './analyze'
import type { AnalyzedPage } from './analyze'
import type { ConvertOptions, ConvertOutput, PdfPageData } from './types'
import { presentationSize, slideFrame, slideText } from './presentation'

const wordMime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
const excelMime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
const pptMime = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'

async function exportWord(pages: AnalyzedPage[], options: ConvertOptions) {
  const D = await import('docx')
  const paragraph = (text: string, level = 0, list = false) =>
    new D.Paragraph({
      children: [new D.TextRun({ text: list ? text.replace(/^[-•–]\s*/, '') : text })],
      heading: level
        ? [
            D.HeadingLevel.HEADING_1,
            D.HeadingLevel.HEADING_2,
            D.HeadingLevel.HEADING_3,
            D.HeadingLevel.HEADING_4,
            D.HeadingLevel.HEADING_5,
            D.HeadingLevel.HEADING_6,
          ][level - 1]
        : undefined,
      bullet: list && /^[-•–]\s/.test(text) ? { level: 0 } : undefined,
      spacing: { after: 120 },
    })
  const children: (InstanceType<typeof D.Paragraph> | InstanceType<typeof D.Table>)[] = []
  for (const [index, page] of pages.entries()) {
    if (options.pageBreaks && index > 0)
      children.push(new D.Paragraph({ children: [new D.PageBreak()] }))
    for (const block of page.blocks) {
      if (block.kind === 'text') children.push(paragraph(block.text, block.level, block.list))
      else
        children.push(
          new D.Table({
            width: { size: 100, type: D.WidthType.PERCENTAGE },
            rows: block.rows.map(
              (row, i) =>
                new D.TableRow({
                  tableHeader: i === 0,
                  children: row.map((text) => new D.TableCell({ children: [paragraph(text)] })),
                }),
            ),
          }),
        )
    }
  }
  const doc = new D.Document({
    title: 'PDF 转 Word',
    styles: {
      default: { document: { run: { font: 'Microsoft YaHei', size: 24, color: '222222' } } },
    },
    sections: [{ children }],
  })
  return new Uint8Array(await (await D.Packer.toBlob(doc)).arrayBuffer())
}

async function exportWordImages(pages: PdfPageData[]) {
  const D = await import('docx')
  const doc = new D.Document({
    sections: pages.map((page) => ({
      properties: {
        page: {
          size: { width: Math.round(page.width * 20), height: Math.round(page.height * 20) },
          margin: { top: 200, bottom: 200, left: 0, right: 0 },
        },
      },
      children: [
        new D.Paragraph({
          spacing: { before: 0, after: 0 },
          children: [
            new D.ImageRun({
              type: 'jpg',
              data: Uint8Array.from(atob(page.image!.split(',')[1]!), (c) => c.charCodeAt(0)),
              transformation: {
                width: (page.width * 96) / 72,
                height: ((page.height - 24) * 96) / 72,
              },
              altText: {
                title: `PDF 第 ${page.index + 1} 页`,
                description: '整页图片，文字不可编辑',
                name: `Page ${page.index + 1}`,
              },
            }),
          ],
        }),
      ],
    })),
  })
  return new Uint8Array(await (await D.Packer.toBlob(doc)).arrayBuffer())
}

async function exportExcel(pages: AnalyzedPage[], options: ConvertOptions) {
  const X = await import('xlsx')
  const workbook = X.utils.book_new()
  let combined: (string | number)[][] = []
  for (const page of pages) {
    const rows: (string | number)[][] = []
    for (const block of page.blocks) {
      if (block.kind === 'table') {
        if (rows.length) rows.push([])
        rows.push(...block.rows.map((row) => row.map((cell) => numericCell(cell, options.numbers))))
      } else if (options.excelScope === 'all') rows.push([block.text])
    }
    if (!rows.length) continue
    if (options.excelSheets === 'single') {
      if (combined.length) combined.push([])
      combined.push([`第 ${page.index + 1} 页`], ...rows)
    } else addSheet(rows, `第${page.index + 1}页`)
  }
  if (combined.length) addSheet(combined, 'PDF 内容')
  if (!workbook.SheetNames.length)
    throw new Error('没有识别到表格。可将导出内容改为「全部文字」后重试。')
  function addSheet(rows: (string | number)[][], name: string) {
    // aoa_to_sheet stores strings as literal text, including formula-like input.
    const sheet = X.utils.aoa_to_sheet(rows)
    const count = Math.max(...rows.map((row) => row.length))
    sheet['!cols'] = Array.from({ length: count }, (_, i) => ({
      wch: Math.min(60, Math.max(12, ...rows.map((row) => String(row[i] ?? '').length + 2))),
    }))
    X.utils.book_append_sheet(workbook, sheet, name)
  }
  // SheetJS emits Calibri as the default font. Name a CJK-capable font in the
  // actual workbook so both native Office and the browser engine display Chinese.
  const { unzipSync, zipSync, strFromU8, strToU8 } = await import('fflate')
  const archive = unzipSync(new Uint8Array(X.write(workbook, { type: 'array', bookType: 'xlsx' })))
  const styles = archive['xl/styles.xml']!
  archive['xl/styles.xml'] = strToU8(
    strFromU8(styles)
      .replace('<name val="Calibri"/>', '<name val="Microsoft YaHei"/>')
      .replace('<scheme val="minor"/>', ''),
  )
  return zipSync(archive)
}

async function exportPowerPoint(pages: PdfPageData[], options: ConvertOptions) {
  const { default: PptxGenJS } = await import('pptxgenjs')
  const deck = new PptxGenJS()
  const { width, height } = presentationSize(pages[0]!)
  deck.defineLayout({ name: 'PDF', width, height })
  deck.layout = 'PDF'
  deck.author = 'a彬彬a'
  deck.subject = options.mode === 'image' ? '每页 PDF 作为图片' : 'PDF 文字层，可编辑'
  for (const page of pages) {
    const slide = deck.addSlide()
    slide.background = { color: 'FFFFFF' }
    const { x, y, w, h } = slideFrame(page, { width, height })
    if (options.mode === 'image')
      slide.addImage({
        data: page.image!,
        x,
        y,
        w,
        h,
        altText: `PDF 第 ${page.index + 1} 页`,
      })
    else
      for (const item of page.items) {
        if (!item.text.trim()) continue
        const { text, ...box } = slideText(item, page, { width, height })
        slide.addText(text, {
          ...box,
          margin: 0,
          breakLine: false,
          fit: 'shrink',
          color: '222222',
          valign: 'top',
        })
      }
  }
  const output = await deck.write({ outputType: 'arraybuffer' })
  return new Uint8Array(output as ArrayBuffer)
}

export async function convertPages(
  pages: PdfPageData[],
  options: ConvertOptions,
): Promise<ConvertOutput> {
  const stats = {
    pages: pages.length,
    textPages: pages.filter((page) => page.items.some((item) => item.text.trim())).length,
    tables: 0,
  }
  if (options.mode !== 'image' && !stats.textPages)
    throw new Error(
      '这份 PDF 没有可提取的文字层。扫描件可用 Word 或 PowerPoint 的「整页图片」模式；文字转换需要先进行 OCR。',
    )
  const analyzed = options.mode === 'image' ? [] : analyzePages(pages)
  stats.tables = analyzed.reduce(
    (sum, page) => sum + page.blocks.filter((b) => b.kind === 'table').length,
    0,
  )
  const markdown = options.mode === 'image' ? '' : toMarkdown(analyzed, options.pageBreaks)
  let bytes: Uint8Array, extension: string, mime: string
  if (options.target === 'markdown') {
    bytes = new TextEncoder().encode(markdown)
    extension = 'md'
    mime = 'text/markdown;charset=utf-8'
  } else if (options.target === 'word') {
    bytes =
      options.mode === 'image' ? await exportWordImages(pages) : await exportWord(analyzed, options)
    extension = 'docx'
    mime = wordMime
  } else if (options.target === 'excel') {
    bytes = await exportExcel(analyzed, options)
    extension = 'xlsx'
    mime = excelMime
  } else {
    bytes = await exportPowerPoint(pages, options)
    extension = 'pptx'
    mime = pptMime
  }
  if (bytes.byteLength > 80 * 1024 * 1024)
    throw new Error('结果超过 80 MB，请减少转换页数或降低图片清晰度。')
  return {
    bytes,
    extension,
    mime,
    preview: options.target === 'markdown' ? markdown.slice(0, 50000) : '',
    stats,
  }
}
