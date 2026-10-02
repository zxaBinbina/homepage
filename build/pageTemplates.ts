import type { Plugin } from 'vite'
import ejs from 'ejs'
import { createSiteMeta } from '../site.config'
import { pages, pageForPath, type PageName } from '../src/pages'

/** All URLs share index.html; page content lives in Vue single-file components. */
export function pageTemplates(baseUrl: string | undefined, build: boolean): Plugin {
  function render(html: string, page: PageName) {
    return ejs.render(html, { site: createSiteMeta(baseUrl, page), page })
  }
  return {
    name: 'vue-page-templates',
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
          const directory = pages[page].slice(1)
          const prefix = '../'.repeat(directory.split('/').filter(Boolean).length) || './'
          const html = render(template, page).replace(/(src|href)="\.\//g, `$1="${prefix}`)
          if (page === 'home') entry.source = html
          else this.emitFile({ type: 'asset', fileName: `${directory}index.html`, source: html })
        }
      },
    },
  }
}
