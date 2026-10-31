import type { Plugin } from 'vite'
import type { IncomingMessage, ServerResponse } from 'node:http'
import ejs from 'ejs'
import { readFileSync } from 'node:fs'
import { createSiteMeta, createStructuredData, serializeStructuredData } from '../site.config'
import { pages, pageForPath, knownPageForPath, pageFile, type PageName } from '../src/pages'
import { isErrorPage } from '../src/errors/catalog'

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
    return ejs.render(html, {
      site: createSiteMeta(baseUrl, page),
      structuredData: serializeStructuredData(createStructuredData(baseUrl, page)),
      page,
    })
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
        html = html
          .replace('<%- loadingStyles %>', () =>
            readFileSync(new URL('../src/loading/screen.css', import.meta.url), 'utf8'),
          )
          .replace('<%- loadingScript %>', () =>
            readFileSync(new URL('../src/loading/bootstrap.js', import.meta.url), 'utf8'),
          )
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
        // The critical loading shell can paint while the application CSS is downloading.
        // main.ts waits for these styles before mounting Vue.
        const template = entry.source.replace(
          /<link rel="stylesheet"(?=\s|>)/g,
          '<link rel="stylesheet" data-app-style media="print" onload="this.media=\'all\'"',
        )
        for (const page of Object.keys(pages) as PageName[]) {
          const fileName = pageFile(page)
          // Error documents can be served at arbitrary nested URLs by the host.
          const prefix = isErrorPage(page)
            ? '/'
            : '../'.repeat(fileName.split('/').length - 1) || './'
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
        const escapeXml = (value: string) =>
          value.replace(/[<>&"']/g, (character) => `&#${character.charCodeAt(0)};`)
        const urls = (Object.keys(pages) as PageName[])
          .filter((page) => !isErrorPage(page))
          .map((page) => `  <url><loc>${escapeXml(createSiteMeta(baseUrl, page).url)}</loc></url>`)
        this.emitFile({
          type: 'asset',
          fileName: 'sitemap.xml',
          source: `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join('\n')}\n</urlset>\n`,
        })
        this.emitFile({
          type: 'asset',
          fileName: 'robots.txt',
          source: `User-agent: *\nAllow: /\n\nSitemap: ${new URL('sitemap.xml', createSiteMeta(baseUrl).url).href}\n`,
        })
        // The registered /404 emits 404.html, disabling Cloudflare Pages' implicit SPA fallback.
      },
    },
  }
}
