import { cwd } from 'node:process'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import ejs from 'ejs'
import { createSiteMeta } from './site.config'
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

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, cwd(), 'SITE_')
  const site = createSiteMeta(env.SITE_URL)
  return {
    plugins: [
      {
        name: 'local-music-lyrics',
        configureServer(server) {
          server.middlewares.use('/api/music/lyrics', lyricsMiddleware)
        },
        configurePreviewServer(server) {
          server.middlewares.use('/api/music/lyrics', lyricsMiddleware)
        },
      },
      {
        name: 'site-sharing-template',
        transformIndexHtml: {
          order: 'pre',
          handler: (html) => ejs.render(html, { site }),
        },
      },
      vue(),
    ],
    base: './',
  }
})
