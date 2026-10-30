import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { build } from 'esbuild'
import vm from 'node:vm'

async function moduleAt(path) {
  const result = await build({
    entryPoints: [path],
    bundle: true,
    format: 'esm',
    platform: 'node',
    write: false,
  })
  return import(
    `data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString('base64')}`
  )
}
const manifest = JSON.parse(await readFile('third_party/jaywcjlove-tools/upstream.json', 'utf8'))
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex')
const archive = 'third_party/jaywcjlove-tools/' + manifest.archive
assert.equal(hash(await readFile(archive)), manifest.archiveSha256)
const prefix = execFileSync('tar', ['-tzf', archive], { encoding: 'utf8' })
  .split('\n')[0]
  .replace(/\/$/, '')
const source = (path) => execFileSync('tar', ['-xOzf', archive, `${prefix}/${path}`])
const routes = [
  ...source(manifest.inventorySource)
    .toString()
    .matchAll(/path: '([^']+)'/g),
]
  .map((m) => m[1])
  .filter((p) => !['/', '*', 'home'].includes(p))
assert.deepEqual(
  manifest.tools.map((t) => t.upstreamId),
  routes,
)
assert.equal(hash(source(manifest.inventorySource)), manifest.inventorySha256)
assert.equal(routes.length, 31)
const { toolIds, toolCatalog } = await moduleAt('src/tools/catalog.ts')
assert.equal(toolIds.length, 56)
assert.equal(manifest.tools.filter((t) => t.status === 'added').length, 15)
assert.equal(manifest.tools.filter((t) => t.status === 'duplicate').length, 16)
assert.equal(new Set(toolIds.map((id) => toolCatalog[id].path)).size, toolIds.length)
for (const tool of manifest.tools) {
  assert.equal(hash(source(tool.source)), tool.sha256)
  if (tool.status === 'added') {
    assert.ok(toolIds.includes(tool.id))
    assert.ok((await readFile(tool.component, 'utf8')).length > 100)
  } else assert.ok(tool.existingTools.every((id) => toolIds.includes(id)))
}
const ini = (await import('../src/tools/jaytools/json-ini.js')).transform
assert.deepEqual(
  JSON.parse(ini(ini('{"site":{"name":"中文","ok":true,"roles":["a","b"]}}'), { mode: 'decode' })),
  { site: { name: '中文', ok: true, roles: ['a', 'b'] } },
)
assert.throws(() => ini('null'))
const xml = (await import('../src/tools/jaytools/json-xml.js')).transform
const object = { root: { '@_name': '中文', '#text': 'hello', child: [1, 2] } }
assert.deepEqual(JSON.parse(xml(xml(JSON.stringify(object)), { mode: 'decode' })), object)
assert.throws(() => xml('<a><b></a>', { mode: 'decode' }))
assert.throws(() => xml('<!DOCTYPE a [<!ENTITY x "x">]><a>&x;</a>', { mode: 'decode' }))
const toml = (await import('../src/tools/jaytools/toml.js')).transform
assert.deepEqual(JSON.parse(toml('[site]\nname="中文"\nports=[80,443]')), {
  site: { name: '中文', ports: [80, 443] },
})
assert.throws(() => toml('a=['))
const markdown = (await import('../src/tools/jaytools/html-markdown.js')).transform
assert.match(markdown('<h2>中文</h2><p><strong>内容</strong></p>'), /## 中文[\s\S]*\*\*内容\*\*/)
assert.match(markdown('<table><tr><th>A</th></tr><tr><td>B</td></tr></table>'), /\| A \|/)
assert.doesNotMatch(markdown('<script>throw new Error("x")</script><p>text</p>'), /throw new Error/)
const rmb = (await import('../src/tools/jaytools/rmb.js')).transform
assert.match(rmb('1001.01'), /壹仟零壹元零壹分/)
assert.match(rmb('9007199254740993.01'), /玖佰玖拾叁元零壹分/)
assert.throws(() => rmb('1.234'))
const convert = (await moduleAt('src/tools/jaytools/chinese-convert.js')).transform
assert.equal(convert('汉字与中文 🌍'), '漢字與中文 🌍')
assert.equal(convert('漢字與中文 🌍', { mode: 'simplified' }), '汉字与中文 🌍')
const pinyin = await import('../src/tools/jaytools/pinyin.js')
assert.match(pinyin.transform('中国'), /zhōng guó/)
assert.equal(pinyin.transform('中国', { style: 'first' }), 'z g')
const { compress } = await import('../src/tools/jaytools/svg.js')
const svg = compress(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><title>保留</title><!--删--><rect width="10" height="10" fill="#ffffff"/></svg>',
)
assert.match(svg, /viewBox="0 0 10 10"/)
assert.match(svg, /<title>保留<\/title>/)
assert.doesNotMatch(svg, /<!--/)
assert.throws(() => compress('invalid'))
const badges = await moduleAt('src/tools/jaytools/badges.js')
assert.equal(
  new URL(badges.changeStyle('https://flat.badgen.net/npm/v/vue', 'badgen', 'classic')).hostname,
  'badgen.net',
)
assert.ok(
  badges
    .generateBadges('team/image', 'docker', 'shields')
    .some((b) => b.url.includes('/team/image')),
)
assert.ok(
  badges
    .generateBadges('@vue/compiler-sfc', 'npm', 'shields')
    .some((b) => b.url.includes('%40vue/compiler-sfc')),
)
assert.throws(() => badges.generateBadges('x?bad', 'github'))
assert.ok(badges.customBadge({ label: 'a-b', content: '中 文', color: '#fff' }).includes('a--b'))
const { default: obfuscator } = await import('javascript-obfuscator')
const { defaultOption } = await moduleAt('src/tools/jaytools/obfuscator-options.ts')
const obfuscated = obfuscator
  .obfuscate('globalThis.answer = (a => a + "中文")(42)', { ...defaultOption, seed: 42 })
  .getObfuscatedCode()
const context = {}
vm.runInNewContext(obfuscated, context, { timeout: 1000 })
assert.equal(context.answer, '42中文')
console.log(
  '31 upstream pages accounted for: 15 additions, 16 duplicates; 56 unique routes. Conversion, invalid input, SVG preservation, badge URLs and obfuscation checks passed.',
)
