import { cwd } from 'node:process'
import { resolve } from 'node:path'
import { compileGazeContent } from './build/gazeContent'
import { compileRdpWiki } from './build/rdpWiki'
import { gazeGuideIds } from './src/gaze/catalog'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { pageTemplates } from './build/pageTemplates'
import { toolAssets } from './build/toolAssets'
import { xcpdfAssets } from './build/xcpdf'
import { officeViewerAssets } from './build/officeViewer'
import { siteContent } from './site.config'
import { lyricsResponse } from './server/lyrics'
import { sptlReleaseResponse } from './server/sptlRelease'
import type { IncomingMessage, ServerResponse } from 'node:http'

async function lyricsMiddleware(request: IncomingMessage, response: ServerResponse) {
  if (request.method !== 'GET') {
    response.writeHead(405, { Allow: 'GET' })
    response.end()
    return
  }
  const result = await lyricsResponse(new URL(request.url || '/', 'http://localhost'))
  response.writeHead(result.status, Object.fromEntries(result.headers))
  response.end(await result.text())
}

async function experienceMiddleware(request: IncomingMessage, response: ServerResponse) {
  response.writeHead(503, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
  })
  response.end(JSON.stringify({ error: 'experience storage unavailable in local preview' }))
}

async function sptlReleaseMiddleware(request: IncomingMessage, response: ServerResponse) {
  const result = await sptlReleaseResponse(
    new Request('http://localhost/api/projects/SPTL/release', {
      method: request.method,
    }),
  )
  response.writeHead(result.status, Object.fromEntries(result.headers))
  response.end(await result.text())
}

export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, cwd(), 'SITE_')
  return {
    define: { 'import.meta.env.SITE_URL': JSON.stringify(env.SITE_URL || siteContent.url) },
    worker: { format: 'es' },
    server: {
      proxy: { '/api/games/rooms': { target: 'http://127.0.0.1:8788', ws: true } },
    },
    preview: {
      proxy: { '/api/games/rooms': { target: 'http://127.0.0.1:8788', ws: true } },
    },
    plugins: [
      {
        name: 'rdp-wiki-content',
        resolveId(id) {
          if (id === 'virtual:rdp-wiki') return '\0virtual:rdp-wiki'
        },
        load(id) {
          if (id !== '\0virtual:rdp-wiki') return
          const path = resolve('docs/rdp-access-auth.md')
          this.addWatchFile(path)
          return `export default ${JSON.stringify(compileRdpWiki(path))}`
        },
      },
      {
        name: 'gaze-content',
        resolveId(id) {
          if (id === 'virtual:gaze-content') return '\0virtual:gaze-content'
        },
        load(id) {
          if (id !== '\0virtual:gaze-content') return
          const contentDir = resolve('src/gaze/content')
          this.addWatchFile(resolve(contentDir, 'anchors.json'))
          for (const guideId of gazeGuideIds)
            this.addWatchFile(resolve(contentDir, 'guide', `${guideId}.md`))
          return `export default ${JSON.stringify(compileGazeContent(contentDir))}`
        },
      },
      {
        name: 'local-music-lyrics',
        configureServer(server) {
          server.middlewares.use('/api/music/lyrics', lyricsMiddleware)
          server.middlewares.use('/api/games/experience', experienceMiddleware)
          server.middlewares.use('/api/projects/SPTL/release', sptlReleaseMiddleware)
        },
        configurePreviewServer(server) {
          server.middlewares.use('/api/music/lyrics', lyricsMiddleware)
          server.middlewares.use('/api/games/experience', experienceMiddleware)
          server.middlewares.use('/api/projects/SPTL/release', sptlReleaseMiddleware)
        },
      },
      pageTemplates(env.SITE_URL, command === 'build'),
      toolAssets(),
      xcpdfAssets(),
      officeViewerAssets(env.SITE_URL || siteContent.url),
      vue(),
    ],
    base: './',
  }
})
