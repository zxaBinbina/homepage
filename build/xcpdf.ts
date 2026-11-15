import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import type { Plugin } from 'vite'
import { xcpdfUiColors, xcpdfUiValue } from './xcpdfUiTheme'

const sourcePath = 'third_party/xcpdf/upstream.html'
const runtimePath = '/tool-assets/xcpdf/runtime.html'

export function decodeXcpdfBody(script: string): string {
  const array = (name: string) =>
    JSON.parse(script.match(new RegExp(`var ${name}=(\\[.*?\\]);`, 's'))![1])
  const key: number[] = array('K')
  const order: number[] = array('O')
  const parts: string[] = array('S')
  const buffers: Buffer[] = []
  parts.forEach((part, i) => (buffers[order[i]] = Buffer.from(part, 'base64')))
  const body = Buffer.concat(buffers)
  for (let i = 0; i < body.length; i++) body[i] ^= key[i % key.length]!
  return body.toString('utf8')
}

export function xcpdfDocument(): string {
  const source = readFileSync(sourcePath, 'utf8')
  const manifest = JSON.parse(readFileSync('third_party/xcpdf/upstream.json', 'utf8'))
  if (createHash('sha256').update(source).digest('hex') !== manifest.sha256)
    throw new Error('XCPDF archive differs from the pinned MIT release')
  const scripts = [...source.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(
    (match) => match[1]!,
  )
  const decoder = scripts.findIndex(
    (script) => /var K=\[\d+,/.test(script) && script.includes('var O='),
  )
  if (decoder < 0) throw new Error('XCPDF body decoder missing')
  const body = decodeXcpdfBody(scripts[decoder]!)
  let css = source.match(/<style>([\s\S]*?)<\/style>/)![1]!
  // Change the upstream UI palette at its declarations. PDF canvases and color swatches
  // keep their document colors; the source archive remains byte-for-byte unchanged.
  css = css.replace(/:root\s*\{[^}]*\}/, '')
  css = css.replace(/([\w-]+)\s*:\s*([^;{}]+)(?=[;}])/g, (declaration, property, value) =>
    /color|background|border|shadow|outline|fill|stroke/.test(property)
      ? `${property}: ${xcpdfUiValue(value, property, xcpdfUiColors)}`
      : declaration,
  )
  css = css.replace(/var\(--shadow\)/g, 'var(--xcpdf-shadow)')
  const bridge = readFileSync('src/tools/xcpdf/bridge.js', 'utf8')
  const overrides = readFileSync('src/tools/xcpdf/frame.css', 'utf8')
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline' blob: data:; style-src 'unsafe-inline'; img-src data: blob:; font-src data: blob:; worker-src blob: data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>XCPDF V7.3 · MIT · 相声的技术备忘录</title><style>${css}\n${overrides}</style></head>
<body>${body}<script>
const xcpdfUiColors = ${JSON.stringify(xcpdfUiColors)};
const xcpdfUiValue = ${xcpdfUiValue.toString()};
${bridge}</script>
${scripts
  .filter((_, i) => i !== decoder)
  .map((script) => `<script>${script}</script>`)
  .join('\n')}
</body></html>`
}

export function xcpdfAssets(): Plugin {
  let html: string
  return {
    name: 'xcpdf-mit-runtime',
    buildStart() {
      for (const file of [sourcePath, 'src/tools/xcpdf/bridge.js', 'src/tools/xcpdf/frame.css'])
        this.addWatchFile(resolve(file))
      html = xcpdfDocument()
    },
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        if (request.url?.split('?')[0] !== runtimePath) return next()
        response.setHeader('Content-Type', 'text/html; charset=utf-8')
        response.end(xcpdfDocument())
      })
    },
    generateBundle() {
      this.emitFile({ type: 'asset', fileName: runtimePath.slice(1), source: html })
    },
  }
}
