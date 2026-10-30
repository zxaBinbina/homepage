// Refresh notices for the dependencies used by the imported Web Tools.
import { existsSync, readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve, join } from 'node:path'
const roots = [
  'exifreader',
  'fast-xml-parser',
  'fflate',
  'highlight.js',
  'html-to-image',
  'ini',
  'javascript-obfuscator',
  'nzh',
  'pdfjs-dist',
  'pinyin-pro',
  'rehype-parse',
  'rehype-remark',
  'remark-gfm',
  'remark-stringify',
  'svgo',
  'togscc',
  'toml',
  'unified',
]
const seen = new Map()
function visit(name, from = resolve('.')) {
  let current = from
  let dir
  while (true) {
    const candidate = join(current, 'node_modules', name)
    if (existsSync(join(candidate, 'package.json'))) {
      dir = candidate
      break
    }
    const parent = dirname(current)
    if (parent === current) return
    current = parent
  }
  const pkg = JSON.parse(readFileSync(join(dir, 'package.json'), 'utf8'))
  const key = `${pkg.name}@${pkg.version}`
  if (seen.has(key)) return
  seen.set(key, { pkg, dir })
  for (const dependency of Object.keys(pkg.dependencies || {})) visit(dependency, dir)
}
roots.forEach((name) => visit(name))
const missing = []
const sections = [
  'Web Tools runtime dependency notices. Generated from package-lock.json and installed package licenses.\nExifReader is MPL-2.0; unmodified corresponding source is provided at /licenses/exifreader-source.tar.gz.\nPDF.js is Apache-2.0; its bundled fonts and WebAssembly libraries include their own notices under /tool-assets/pdfjs/.\n',
]
for (const [key, { pkg, dir }] of [...seen].sort(([a], [b]) => a.localeCompare(b))) {
  const names = readdirSync(dir).filter((name) =>
    /^(licen[sc]e|copying|notice)([.-]|$)/i.test(name),
  )
  const texts = names.map((name) => readFileSync(join(dir, name), 'utf8'))
  if (pkg.name === 'javascript-obfuscator') {
    texts.push(readFileSync(join(dir, 'dist/index.browser.js.LICENSE.txt'), 'utf8'))
  }
  if (!texts.length) {
    const supplemental = resolve(
      'third_party/jaywcjlove-tools/dependency-licenses',
      pkg.name.replaceAll('/', '__') + '.txt',
    )
    if (existsSync(supplemental)) texts.push(readFileSync(supplemental, 'utf8'))
    else
      missing.push({
        name: pkg.name,
        version: pkg.version,
        repository: pkg.repository,
        license: pkg.license,
      })
  }
  sections.push(
    `${key}\nLicense: ${typeof pkg.license === 'string' ? pkg.license : JSON.stringify(pkg.license)}\nSource: ${typeof pkg.repository === 'string' ? pkg.repository : pkg.repository?.url || pkg.homepage || ''}\n\n${texts.join('\n\n')}`,
  )
}
if (missing.length) {
  console.error(JSON.stringify(missing, null, 2))
  process.exitCode = 1
} else {
  writeFileSync(
    'public/licenses/jaytools-dependencies.txt',
    sections.join('\n\n' + '='.repeat(72) + '\n\n') + '\n',
  )
  console.log(`${seen.size} package notices written.`)
}
