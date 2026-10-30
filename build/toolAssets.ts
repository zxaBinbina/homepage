import { readdirSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import type { Plugin } from 'vite'

// Keep PDF fonts, CMaps and image decoders on this origin in both dev and build.
export function toolAssets(): Plugin {
  const assets = new Map<string, string>()
  for (const folder of ['cmaps', 'standard_fonts', 'wasm']) {
    const dir = resolve('node_modules/pdfjs-dist', folder)
    for (const file of readdirSync(dir))
      assets.set(`/tool-assets/pdfjs/${folder}/${file}`, resolve(dir, file))
  }
  return {
    name: 'local-tool-assets',
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        const url = request.url?.split('?')[0] || ''
        const file = assets.get(url)
        if (!file) return next()
        response.setHeader(
          'Content-Type',
          file.endsWith('.wasm') ? 'application/wasm' : 'application/octet-stream',
        )
        response.end(readFileSync(file))
      })
    },
    generateBundle() {
      for (const [url, file] of assets)
        this.emitFile({ type: 'asset', fileName: url.slice(1), source: readFileSync(file) })
    },
  }
}
