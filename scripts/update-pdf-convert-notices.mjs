import { readFile, writeFile, readdir } from 'node:fs/promises'
import { resolve } from 'node:path'

const seen = new Set()
const sections = [
  'PDF 转 Word / Excel / PowerPoint / Markdown\n\n' +
    'pdf2md analysis pipeline (MIT)\nhttps://github.com/opendocsg/pdf2md\n' +
    (await readFile('third_party/pdf-convert/LICENSE', 'utf8')),
]
async function visit(name, parent = resolve('node_modules')) {
  if (name.startsWith('@types/')) return
  let folder = resolve(parent, name)
  let pkg
  try {
    pkg = JSON.parse(await readFile(resolve(folder, 'package.json'), 'utf8'))
  } catch {
    folder = resolve('node_modules', name)
    pkg = JSON.parse(await readFile(resolve(folder, 'package.json'), 'utf8'))
  }
  const key = `${pkg.name}@${pkg.version}`
  if (seen.has(key)) return
  seen.add(key)
  const files = await readdir(folder)
  const license = files.find((file) => /^(?:LICENSE|LICENCE)(?:\.[\w-]+)?$/i.test(file))
  const readme = files.find((file) => /^readme(?:\.md)?$/i.test(file))
  const fallback =
    !license && readme
      ? (await readFile(resolve(folder, readme), 'utf8')).match(
          /(?:^#{1,3}\s*License\b|MIT License)[\s\S]*/im,
        )?.[0]
      : undefined
  if (!license && !fallback) throw new Error(`Missing license file for ${key}`)
  sections.push(
    `${key} (${pkg.license || 'See license'})\n${pkg.repository?.url || pkg.repository || ''}\n\n` +
      (license ? await readFile(resolve(folder, license), 'utf8') : fallback),
  )
  for (const dep of Object.keys(pkg.dependencies || {})) {
    if (pkg.browser?.[dep] === false) continue
    await visit(dep, resolve(folder, 'node_modules'))
  }
}
for (const name of ['docx', 'pptxgenjs']) await visit(name)
sections.push(
  'Shared existing libraries: PDF.js (Apache-2.0), SheetJS (Apache-2.0) and fflate (MIT).\n' +
    'Their notices are distributed in tools-dependencies.txt and jaytools-dependencies.txt.',
)
await writeFile(
  'public/licenses/pdf-convert.txt',
  sections.join('\n\n' + '='.repeat(72) + '\n\n') + '\n',
)
console.log(`PDF conversion notices updated (${seen.size} dependency versions).`)
