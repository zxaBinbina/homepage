import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { build } from 'esbuild'

const manifest = JSON.parse(await readFile('third_party/xcpdf/upstream.json', 'utf8'))
const source = await readFile('third_party/xcpdf/upstream.html', 'utf8')
assert.equal(createHash('sha256').update(source).digest('hex'), manifest.sha256)
assert.match(
  await readFile('public/licenses/xcpdf.txt', 'utf8'),
  /MIT License[\s\S]*Copyright \(c\) 2026 wallechfox/,
)
const bundle = async (path) => {
  const result = await build({
    entryPoints: [path],
    bundle: true,
    platform: 'node',
    format: 'esm',
    write: false,
  })
  return import(
    `data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString('base64')}`
  )
}
const { toolCatalog } = await bundle('src/tools/catalog.ts')
const { xcpdfDocument, decodeXcpdfBody } = await bundle('build/xcpdf.ts')
const decoder = [...source.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)]
  .map((m) => m[1])
  .find((s) => /var K=\[\d+,/.test(s))
const originalPanels = [
  ...decodeXcpdfBody(decoder).matchAll(/class="tool-card[^>]*data-target="([^"]+)"/g),
].map((m) => m[1])
assert.equal(originalPanels.length, 43)
assert.deepEqual([...new Set(manifest.tools.map((t) => t.panel))].sort(), originalPanels.sort())
for (const item of manifest.tools) {
  assert.equal(toolCatalog[item.id].panel, item.panel)
  assert.equal(toolCatalog[item.id].path, `/tools/${item.id}`)
}
const runtime = xcpdfDocument()
assert.match(runtime, /connect-src 'none'/)
assert.match(runtime, /form-action 'none'/)
assert.match(runtime, /Copyright 2022 Mozilla Foundation/)
assert.match(runtime, /xcpdf:init/)
assert.equal(Object.keys(toolCatalog).length, 101)
console.log(
  '43 XCPDF tools match the unchanged MIT archive; routes, source license and network-isolated runtime passed.',
)
