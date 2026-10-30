import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { dirname } from 'node:path'
import { build } from 'esbuild'
import { parse } from '@vue/compiler-sfc'

// Execute the actual imported tool functions, without mounting the UI.
async function tool(name) {
  const file = `src/tools/freemium/pages/tools/${name}.vue`
  const { descriptor } = parse(await readFile(file, 'utf8'))
  const code = descriptor.scriptSetup.content.replace(/^import .*from ['"].*\.vue['"]\s*$/gm, '')
  const names = ['transform', 'options'].filter((name) =>
    new RegExp(`(?:function|const) ${name}\\b`).test(code),
  )
  const result = await build({
    stdin: { contents: `${code}\nexport { ${names.join(',')} }`, resolveDir: dirname(file) },
    bundle: true,
    format: 'esm',
    platform: 'browser',
    write: false,
  })
  const m = await import(
    `data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString('base64')}`
  )
  const defaults = Object.fromEntries((m.options || []).map((o) => [o.key, o.default]))
  return (input, options = {}) => m.transform(input, { ...defaults, ...options })
}
const manifest = JSON.parse(await readFile('third_party/freemium/upstream.json', 'utf8'))
assert.equal(manifest.tools.length, 41)
const catalogBuild = await build({
  entryPoints: ['src/tools/catalog.ts'],
  bundle: true,
  format: 'esm',
  write: false,
})
const { toolIds, toolCatalog } = await import(
  `data:text/javascript;base64,${Buffer.from(catalogBuild.outputFiles[0].text).toString('base64')}`
)
assert.deepEqual(
  toolIds,
  manifest.tools.map((t) => t.id),
  'Every upstream tool must be present',
)
for (const { id, file } of manifest.tools) {
  assert.equal(toolCatalog[id].path, `/tools/${id}`)
  assert.ok((await readFile(`src/tools/freemium/pages/tools/${file}`, 'utf8')).length > 100)
}
const json = await tool('JsonFormatter')
assert.equal(
  json('{"b":2,"a":{"z":1,"b":2}}', { sortKeys: true }),
  JSON.stringify({ a: { b: 2, z: 1 }, b: 2 }, null, 2),
)
assert.equal(json('{"a": [1, true, null]}', { mode: 'minify' }), '{"a":[1,true,null]}')
assert.throws(() => json('{bad}'))
const b64 = await tool('Base64String')
const text = '中文 🌍 + / \n\t'
for (const urlSafe of [false, true])
  assert.equal(b64(b64(text, { urlSafe }), { mode: 'decode', urlSafe }), text)
assert.throws(() => b64('%%%%', { mode: 'decode' }))
const url = await tool('UrlEncode')
assert.equal(url(url(text), { mode: 'decode' }), text)
assert.throws(() => url('%QQ', { mode: 'decode' }))
const hex = await tool('HexAscii')
assert.equal(hex(hex(text), { mode: 'decode' }), text)
assert.throws(() => hex('a', { mode: 'decode' }))
const escape = await tool('BackslashEscape')
assert.equal(escape(escape(text), { mode: 'unescape' }), text)
const yaml = await tool('JsonToYaml')
const fromYaml = await tool('YamlToJson')
assert.deepEqual(JSON.parse(fromYaml(yaml('{"name":"中文","ok":true,"items":[1,2]}'))), {
  name: '中文',
  ok: true,
  items: [1, 2],
})
assert.throws(() => fromYaml('a: 1\n---\nb: 2'))
const csv = await tool('JsonToCsv')
const fromCsv = await tool('CsvToJson')
const data = [{ name: 'a,b', note: '含"引号"\n和换行', count: 2 }]
assert.deepEqual(JSON.parse(await fromCsv(await csv(JSON.stringify(data)))), data)
const php = await tool('PhpJson')
const encoded = php(JSON.stringify({ text, n: 12, yes: true, empty: null }), { mode: 'serialize' })
assert.deepEqual(JSON.parse(php(encoded, { mode: 'unserialize' })), {
  text,
  n: 12,
  yes: true,
  empty: null,
})
const code = await tool('JsonToCode')
for (const lang of ['typescript', 'go', 'swift', 'kotlin', 'rust'])
  assert.match(code('{"id":1,"name":"Ada","active":true}', { lang }), /Root/)
const curl = await tool('CurlToCode')
const generated = curl(
  'curl https://example.com/api -X POST -H "Content-Type: application/json" -d \'{"ok":true}\'',
)
assert.match(generated, /POST/)
assert.match(generated, /Content-Type/)
assert.match(generated, /example.com/)
assert.throws(() => curl('echo hello'))
const js = await tool('JsBeautify')
for (const source of [
  'return /ab+c/i.test("abbc")',
  'const n = 8 / 2; return n',
  'return `hello ${1 + 2}`',
  'return "a  b"',
]) {
  const minified = js(source, { mode: 'minify' })
  assert.equal(
    Function(minified)(),
    Function(source)(),
    `JavaScript minification must preserve behavior: ${source}`,
  )
}
console.log(
  '41 tools match the upstream inventory; JSON, UTF-8/Base64, URL, hex, escapes, YAML, CSV, PHP, type/code generation and JavaScript checks passed.',
)
