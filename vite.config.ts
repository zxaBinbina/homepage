import { cwd } from 'node:process'
import { resolve } from 'node:path'
import { compileRdpWiki } from './build/rdpWiki'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { pageTemplates } from './build/pageTemplates'
import { siteContent } from './site.config'
import { lyricsResponse } from './server/lyrics'
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

export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, cwd(), 'SITE_')
  return {
    define: { 'import.meta.env.SITE_URL': JSON.stringify(env.SITE_URL || siteContent.url) },
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
        name: 'local-music-lyrics',
        configureServer(server) {
          server.middlewares.use('/api/music/lyrics', lyricsMiddleware)
          server.middlewares.use('/api/games/experience', experienceMiddleware)
        },
        configurePreviewServer(server) {
          server.middlewares.use('/api/music/lyrics', lyricsMiddleware)
          server.middlewares.use('/api/games/experience', experienceMiddleware)
        },
      },
      pageTemplates(env.SITE_URL, command === 'build'),
      vue(),
    ],
    base: './',
  }
})
