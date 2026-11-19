import assert from 'node:assert/strict'
import { readFile, mkdir } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
import { build } from 'esbuild'
import { unzipSync, strFromU8 } from 'fflate'
import * as PDF from 'pdfjs-dist/legacy/build/pdf.mjs'
import * as X from 'xlsx'

const manifest = JSON.parse(await readFile('third_party/pdf-convert/upstream.json', 'utf8'))
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex')
const archive = 'third_party/pdf-convert/' + manifest.archive
assert.equal(hash(await readFile(archive)), manifest.archiveSha256)
for (const item of manifest.files) {
  assert.equal(hash(execFileSync('tar', ['-xOzf', archive, item.source])), item.sha256)
  assert.ok((await readFile(item.adapted, 'utf8')).includes('opendocsg/pdf2md'))
}
const notices = await readFile('public/licenses/pdf-convert.txt', 'utf8')
assert.match(notices, /Copyright \(c\) 2020 Johannes Zillmann/)
assert.match(notices, /Copyright \(c\) 2013 Julian Gruber/)
await mkdir('artifacts/pdf-convert', { recursive: true })
const engineFile = resolve('artifacts/pdf-convert/engine-check.mjs')
await build({
  entryPoints: ['src/tools/pdfconvert/export.ts'],
  bundle: true,
  platform: 'node',
  format: 'esm',
  packages: 'external',
  outfile: engineFile,
})
const { convertPages } = await import(pathToFileURL(engineFile).href)
const analysis = await build({
  entryPoints: ['src/tools/pdfconvert/analyze.ts'],
  bundle: true,
  format: 'esm',
  write: false,
})
const { analyzePages, numericCell, toMarkdown } = await import(
  'data:text/javascript;base64,' + Buffer.from(analysis.outputFiles[0].text).toString('base64')
)
const task = PDF.getDocument({
  data: new Uint8Array(await readFile('scripts/fixtures/pdf-convert.pdf')),
  fontExtraProperties: true,
  verbosity: 0,
  cMapUrl: resolve('node_modules/pdfjs-dist/cmaps') + '/',
  cMapPacked: true,
  standardFontDataUrl: resolve('node_modules/pdfjs-dist/standard_fonts') + '/',
})
const doc = await task.promise
const pages = []
try {
  for (let number = 1; number <= doc.numPages; number++) {
    const page = await doc.getPage(number),
      viewport = page.getViewport({ scale: 1 })
    const content = await page.getTextContent()
    await page.getOperatorList()
    const items = content.items
      .filter((t) => 'str' in t)
      .map((t) => {
        const tx = PDF.Util.transform(viewport.transform, t.transform),
          height = Math.hypot(tx[2], tx[3])
        return {
          x: tx[4],
          y: tx[5] - height * 0.8,
          width: t.width,
          height,
          text: t.str,
          font: t.fontName,
        }
      })
    const fonts = Object.fromEntries(
      items.map((t) => [t.font, { name: page.commonObjs.get(t.font)?.name || '' }]),
    )
    pages.push({ index: number - 1, width: viewport.width, height: viewport.height, items, fonts })
  }
} finally {
  await task.destroy()
}
const opts = {
  target: 'markdown',
  mode: 'text',
  pageBreaks: true,
  excelScope: 'tables',
  excelSheets: 'pages',
  numbers: false,
}
const md = await convertPages(pages, opts)
assert.equal(md.stats.tables, 2)
assert.match(strFromU8(md.bytes), /^# 季度销售报告/m)
assert.match(strFromU8(md.bytes), /较长段落在页面内自动换行/)
assert.match(strFromU8(md.bytes), /\| 华东 \| 1,200 \|/)
assert.match(strFromU8(md.bytes), /1\. 编号列表第一项/)
assert.match(strFromU8(md.bytes), /Second Page Title/)
assert.doesNotMatch(strFromU8(md.bytes), /[\u2e80-\u2fff]/)
const word = unzipSync((await convertPages(pages, { ...opts, target: 'word' })).bytes)
assert.match(strFromU8(word['word/document.xml']), /季度销售报告/)
assert.equal((strFromU8(word['word/document.xml']).match(/<w:tbl>/g) || []).length, 2)
const excel = X.read((await convertPages(pages, { ...opts, target: 'excel', numbers: true })).bytes)
assert.equal(excel.SheetNames.length, 2)
assert.deepEqual(X.utils.sheet_to_json(excel.Sheets[excel.SheetNames[0]], { header: 1 })[1], [
  '华东',
  1200,
  1350,
  1480,
  4030,
])
for (const value of ['00123', '9007199254740993', '123456789012345.67', '2026-11-19', '=1+1'])
  assert.equal(numericCell(value, true), value)
assert.equal(numericCell('1,200.50', true), 1200.5)
assert.equal(numericCell('1200', false), '1200')

const synthetic = {
  index: 0,
  width: 600,
  height: 800,
  fonts: { normal: { name: 'Arial' } },
  items: [
    { x: 40, y: 40, width: 250, height: 24, text: '重复标题', font: 'normal' },
    { x: 40, y: 90, width: 250, height: 12, text: '中文段落。', font: 'normal' },
    { x: 40, y: 120, width: 250, height: 12, text: '- 中文列表', font: 'normal' },
    { x: 40, y: 150, width: 250, height: 12, text: '1. Numbered list', font: 'normal' },
  ],
}
const repeated = toMarkdown(analyzePages([synthetic, synthetic, synthetic]), false)
assert.equal((repeated.match(/重复标题/g) || []).length, 3, 'Repeated content must remain present')
assert.match(repeated, /- 中文列表/)
await assert.rejects(convertPages([synthetic], { ...opts, target: 'excel' }), /没有识别到表格/)
const allText = X.read(
  (await convertPages([synthetic], { ...opts, target: 'excel', excelScope: 'all' })).bytes,
)
assert.match(
  JSON.stringify(X.utils.sheet_to_json(allText.Sheets[allText.SheetNames[0]], { header: 1 })),
  /中文段落/,
)
await assert.rejects(convertPages([{ ...synthetic, items: [] }], opts), /没有可提取的文字层/)
console.log(
  'PDF conversion checks passed: pinned source, Chinese paragraphs, headings, lists, two tables, real DOCX/XLSX, numeric identifiers, repeated text and missing text layer.',
)
