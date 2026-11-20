import assert from 'node:assert/strict'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { pathToFileURL } from 'node:url'
import { resolve } from 'node:path'
import { build } from 'esbuild'
import { unzipSync, strFromU8 } from 'fflate'
import * as X from 'xlsx'

await mkdir('artifacts/office-editor', { recursive: true })
const output = resolve('artifacts/office-editor/documents-check.mjs')
await build({
  entryPoints: ['src/tools/office/documents.ts'],
  bundle: true,
  format: 'esm',
  platform: 'node',
  packages: 'external',
  outfile: output,
})
const { blankDocument, officeFormat, downloadName } = await import(pathToFileURL(output))
assert.equal(officeFormat('报告.DOCX'), 'docx')
assert.equal(officeFormat('report.pdf'), undefined)
assert.equal(downloadName('合同.docx', 'docx'), '合同.docx')
assert.equal(downloadName('a/b:name.pptx', 'xlsx'), 'a_b_name.xlsx')
assert.equal(downloadName('  ', 'docx'), '未命名文档.docx')
for (const format of ['docx', 'xlsx', 'pptx']) {
  const doc = await blankDocument(format)
  await writeFile(`artifacts/office-editor/blank.${format}`, doc.bytes)
  const files = unzipSync(doc.bytes)
  assert.ok(files['[Content_Types].xml'])
  if (format === 'docx') assert.match(strFromU8(files['word/document.xml']), /<w:body>/)
  if (format === 'xlsx') {
    const workbook = X.read(doc.bytes)
    assert.deepEqual(workbook.SheetNames, ['工作表1'])
    assert.match(strFromU8(files['xl/styles.xml']), /Microsoft YaHei/)
    assert.doesNotMatch(strFromU8(files['xl/styles.xml']), /<scheme val="minor"/)
  }
  if (format === 'pptx') {
    assert.ok(files['ppt/slides/slide1.xml'])
    assert.match(strFromU8(files['ppt/slides/slide1.xml']), /<p:ph[^>]*type="title"/)
  }
}
const source = await readFile('third_party/office-wasm/viewer/viewer.mjs', 'utf8')
assert.match(source, /if \(!doc\.editable\) throw new Error\('document is read-only'\)/)
console.log(
  'Office editing checks passed: three real blank formats, Chinese workbook font, slide placeholders and safe download names.',
)
