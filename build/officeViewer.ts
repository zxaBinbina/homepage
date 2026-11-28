import { createHash } from 'node:crypto'
import { cpSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { extname, join, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'
import { createReadStream } from 'node:fs'
import { createServer } from 'node:http'
import type { Plugin } from 'vite'

const prefix = '/office-viewer/v0.2.0/'
const vendor = resolve('third_party/office-wasm')
const mime: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.otf': 'font/otf',
  '.wasm': 'application/wasm',
  '.gz': 'application/gzip',
}

export function officeViewerAssets(siteUrl: string): Plugin {
  const manifest = JSON.parse(readFileSync(join(vendor, 'manifest.json'), 'utf8')) as {
    runtime: { file: string; sha256: string }[]
  }
  const sha = (buffer: Buffer) => createHash('sha256').update(buffer).digest('hex')
  const key = sha(Buffer.from(JSON.stringify(manifest.runtime))).slice(0, 16)
  const runtime = resolve('.cache/office-wasm', key)
  if (!statSync(join(runtime, 'x2t-info.json'), { throwIfNoEntry: false })) {
    const parts = manifest.runtime.map((part) => {
      const data = readFileSync(join(vendor, part.file))
      if (sha(data) !== part.sha256)
        throw new Error(`Office runtime checksum mismatch: ${part.file}`)
      return data
    })
    mkdirSync(runtime, { recursive: true })
    const extracted = spawnSync('tar', ['-xzf', '-', '-C', runtime], {
      input: Buffer.concat(parts),
    })
    if (extracted.status !== 0)
      throw new Error(`Office runtime extraction failed: ${extracted.stderr}`)
  }
  // The AGPL viewer is a separate program. Vite only serves/copies its files;
  // the host app imports the independently licensed Apache SDK.
  function overlay(from: string, to: string) {
    for (const entry of readdirSync(from, { withFileTypes: true })) {
      const target = join(to, entry.name)
      const source = join(from, entry.name)
      if (entry.isDirectory()) {
        mkdirSync(target, { recursive: true })
        overlay(source, target)
      } else if (
        !statSync(target, { throwIfNoEntry: false }) ||
        !readFileSync(source).equals(readFileSync(target))
      )
        cpSync(source, target)
    }
  }
  overlay(join(vendor, 'viewer'), runtime)
  for (const file of ['LICENSE', 'NOTICE.md']) cpSync(join(vendor, file), join(runtime, file))
  cpSync(join(vendor, 'font-licenses'), join(runtime, 'font-licenses'), { recursive: true })
  const sourceDir = join(runtime, 'source')
  mkdirSync(sourceDir, { recursive: true })
  cpSync(join(vendor, 'viewer-source.tar.gz'), join(sourceDir, 'viewer-source.tar.gz'))
  const source = spawnSync('tar', [
    '-czf',
    '-',
    '-C',
    vendor,
    'viewer',
    'prepare.py',
    'manifest.json',
    'README.md',
    'LICENSE',
    'NOTICE.md',
    'font-licenses',
  ])
  if (source.status !== 0) throw new Error(`Office source packaging failed: ${source.stderr}`)
  writeFileSync(join(sourceDir, 'modified-source.tar.gz'), source.stdout)
  const sourceHtml = readFileSync(join(vendor, 'source.html'))
  const sourceIndex = join(sourceDir, 'index.html')
  if (
    !statSync(sourceIndex, { throwIfNoEntry: false }) ||
    !sourceHtml.equals(readFileSync(sourceIndex))
  )
    writeFileSync(sourceIndex, sourceHtml)

  const ancestors = `'self' ${new URL(siteUrl).origin} https://homepage.zxabinbina.workers.dev http://127.0.0.1:* http://localhost:*`
  const csp = `default-src 'self' blob: data:; script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; connect-src 'self' blob:; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; font-src 'self' data: blob:; worker-src 'self' blob:; frame-src 'self' blob:; frame-ancestors ${ancestors}; object-src 'none'; base-uri 'none'; form-action 'none'`
  const headers = `${prefix}*\n  Content-Security-Policy: ${csp}\n  Referrer-Policy: no-referrer\n  X-Content-Type-Options: nosniff\n  Cache-Control: public, max-age=31536000, immutable\n${prefix}wasm/prebuilt/x2t.wasm.br\n  Content-Type: application/wasm\n  Content-Encoding: br\n/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n`
  function middleware(
    request: import('node:http').IncomingMessage,
    response: import('node:http').ServerResponse,
    next: () => void,
  ) {
    const path = new URL(request.url || '/', 'http://localhost').pathname
    if (!path.startsWith(prefix)) return next()
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      response.writeHead(405, { Allow: 'GET, HEAD' }).end()
      return
    }
    let rel: string
    try {
      rel = decodeURIComponent(path.slice(prefix.length)) || 'index.html'
    } catch {
      response.writeHead(400).end()
      return
    }
    if (rel.endsWith('/')) rel += 'index.html'
    const file = resolve(runtime, rel)
    if (!file.startsWith(runtime + '/') || !statSync(file, { throwIfNoEntry: false })?.isFile()) {
      response.writeHead(404).end()
      return
    }
    response.setHeader('Content-Security-Policy', csp)
    response.setHeader('Referrer-Policy', 'no-referrer')
    response.setHeader('X-Content-Type-Options', 'nosniff')
    response.setHeader('Cache-Control', 'no-cache')
    response.setHeader(
      'Content-Type',
      file.endsWith('.wasm.br')
        ? 'application/wasm'
        : mime[extname(file)] || 'application/octet-stream',
    )
    if (file.endsWith('.wasm.br')) response.setHeader('Content-Encoding', 'br')
    if (request.method === 'HEAD') response.end()
    else createReadStream(file).pipe(response)
  }
  // Fedora commonly resolves localhost only to ::1. Serve the same viewer on the
  // other loopback address so the independent origin works without another command.
  function localViewer(main: import('vite').ViteDevServer['httpServer']) {
    if (!main) return
    main.once('listening', () => {
      const address = main.address()
      if (!address || typeof address === 'string') return
      const host =
        address.address === '127.0.0.1' ? '::1' : address.address === '::1' ? '127.0.0.1' : null
      if (!host) return
      const local = createServer((req, res) =>
        middleware(req, res, () => {
          res.writeHead(404).end()
        }),
      )
      local.on('error', (error) => console.error('Office loopback viewer:', error.message))
      local.listen(address.port, host)
      main.once('close', () => local.close())
    })
  }
  return {
    name: 'office-viewer-assets',
    configureServer(server) {
      server.middlewares.use(middleware)
      localViewer(server.httpServer)
    },
    configurePreviewServer(server) {
      server.middlewares.use(middleware)
      localViewer(server.httpServer)
    },
    generateBundle() {
      this.emitFile({ type: 'asset', fileName: '_headers', source: headers })
    },
    writeBundle(options) {
      const output = resolve(options.dir || 'dist', prefix.slice(1))
      cpSync(runtime, output, { recursive: true })
      function verify(dir: string) {
        for (const entry of readdirSync(dir, { withFileTypes: true })) {
          const file = join(dir, entry.name)
          if (entry.isDirectory()) verify(file)
          else if (statSync(file).size > 25 * 1024 * 1024)
            throw new Error(`Asset exceeds Cloudflare Workers static asset limit: ${file}`)
        }
      }
      verify(output)
    },
  }
}
