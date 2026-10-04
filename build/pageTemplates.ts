import type { Plugin } from 'vite'
import type { IncomingMessage, ServerResponse } from 'node:http'
import ejs from 'ejs'
import { createSiteMeta } from '../site.config'
import { pages, pageForPath, knownPageForPath, pageFile, type PageName } from '../src/pages'

/** All URLs share index.html; page content lives in Vue single-file components. */
export function pageTemplates(baseUrl: string | undefined, build: boolean): Plugin {
  function redirectLegacyUrl(request: IncomingMessage, response: ServerResponse, next: () => void) {
    const url = new URL(request.url || '/', 'http://localhost')
    const page = knownPageForPath(url.pathname)
    if (
      (request.method === 'GET' || request.method === 'HEAD') &&
      page &&
      url.pathname !== pages[page]
    ) {
      response.writeHead(301, { Location: `${pages[page]}${url.search}` })
      response.end()
    } else next()
  }
  function render(html: string, page: PageName) {
    return ejs.render(html, { site: createSiteMeta(baseUrl, page), page })
  }
  return {
    name: 'vue-page-templates',
    configureServer(server) {
      server.middlewares.use(redirectLegacyUrl)
    },
    configurePreviewServer(server) {
      server.middlewares.use(redirectLegacyUrl)
    },
    transformIndexHtml: {
      order: 'pre',
      handler(html, context) {
        // Vite resolves the shared entry/assets first; render metadata for every URL below.
        return build
          ? html
          : render(html, pageForPath(context.originalUrl?.split('?')[0] || context.path))
      },
    },
    generateBundle: {
      order: 'post',
      handler(_options, bundle) {
        const entry = bundle['index.html']
        if (!entry || entry.type !== 'asset' || typeof entry.source !== 'string') {
          throw new Error('Missing shared HTML entry')
        }
        const template = entry.source
        for (const page of Object.keys(pages) as PageName[]) {
          const fileName = pageFile(page)
          const prefix = '../'.repeat(fileName.split('/').length - 1) || './'
          const html = render(template, page).replace(/(src|href)="\.\//g, `$1="${prefix}`)
          if (page === 'home') entry.source = html
          else this.emitFile({ type: 'asset', fileName, source: html })
        }
        const redirects = ['/index.html / 301']
        for (const path of Object.values(pages)) {
          if (path === '/') continue
          for (const suffix of ['/', '/index.html', '.html'])
            redirects.push(`${path}${suffix} ${path} 301`)
        }
        this.emitFile({
          type: 'asset',
          fileName: '_redirects',
          source: `${redirects.join('\n')}\n`,
        })
      },
    },
  }
}
