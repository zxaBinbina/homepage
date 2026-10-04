import { nextTick } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { knownPageForPath, pages, type PageName } from './pages'
import { createSiteMeta } from '../site.config'

const components = {
  home: () => import('./HomePage.vue'),
  directory: () => import('./ProjectDirectory.vue'),
  rdp: () => import('./rdp/App.vue'),
  wiki: () => import('./rdp/App.vue'),
}

function hashTarget(hash: string) {
  try {
    return document.getElementById(decodeURIComponent(hash.slice(1)))
  } catch {
    return null
  }
}

function focusContent(element: HTMLElement | null) {
  if (!element) return
  if (!element.hasAttribute('tabindex')) element.tabIndex = -1
  element.focus({ preventScroll: true })
}

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    ...(Object.keys(pages) as PageName[]).map((name) => ({
      name,
      path: pages[name],
      alias:
        name === 'home' ? ['/index.html'] : [`${pages[name]}/index.html`, `${pages[name]}.html`],
      component: components[name],
      props: name === 'rdp' || name === 'wiki' ? { wiki: name === 'wiki' } : undefined,
    })),
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  async scrollBehavior(to, from, savedPosition) {
    await nextTick()
    const changedPage = to.name !== from.name
    if (changedPage && from.matched.length) focusContent(document.querySelector('main'))
    if (savedPosition) return { ...savedPosition, behavior: 'instant' }
    const target = hashTarget(to.hash)
    if (target) {
      focusContent(target)
      const padding = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0
      const margin = parseFloat(getComputedStyle(target).scrollMarginTop) || 0
      return {
        el: target,
        top: padding + margin,
        behavior:
          changedPage || matchMedia('(prefers-reduced-motion: reduce)').matches
            ? 'instant'
            : 'smooth',
      }
    }
    if (changedPage || !to.hash) return { top: 0, left: 0, behavior: 'instant' }
    return false
  },
})

router.beforeEach((to) => {
  const page = knownPageForPath(to.path)
  if (page && to.path !== pages[page]) {
    return { path: pages[page], query: to.query, hash: to.hash, replace: true }
  }
})

router.afterEach((to, _from, failure) => {
  if (failure) return
  const page = to.name as PageName
  const meta = createSiteMeta(import.meta.env.SITE_URL, page)
  const project = page === 'rdp' || page === 'wiki'
  document.title = meta.title
  document.body.classList.toggle('rdp-site', project)
  const values = {
    'meta[name="description"]': meta.description,
    'meta[property="og:title"]': meta.title,
    'meta[property="og:description"]': meta.description,
    'meta[property="og:url"]': meta.url,
    'meta[property="og:image"]': meta.image,
    'meta[property="og:image:secure_url"]': meta.image,
    'meta[property="og:image:alt"]': meta.imageAlt,
    'meta[itemprop="name"]': meta.title,
    'meta[itemprop="image"]': meta.image,
  }
  for (const [selector, value] of Object.entries(values)) {
    document.querySelector(selector)?.setAttribute('content', value)
  }
  document.querySelector('link[rel="canonical"]')?.setAttribute('href', meta.url)
  const favicon = document.querySelector('link[rel="icon"]')
  favicon?.setAttribute('href', project ? '/images/rdp-access-auth.png' : '/favicon.svg')
  favicon?.setAttribute('type', project ? 'image/png' : 'image/svg+xml')
})

/** Enhance regular links, including rendered Wiki content, without changing native link gestures. */
export function navigateInternalLink(event: MouseEvent) {
  if (
    event.defaultPrevented ||
    event.button !== 0 ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey
  )
    return
  const link =
    event.target instanceof Element ? event.target.closest<HTMLAnchorElement>('a[href]') : null
  if (!link || link.hasAttribute('download') || (link.target && link.target !== '_self')) return
  const url = new URL(link.href)
  const page = knownPageForPath(url.pathname)
  if (url.origin !== location.origin || !page) return
  event.preventDefault()
  void router.push(`${pages[page]}${url.search}${url.hash}`).catch(() => {
    // A stale or unavailable lazy chunk can still be opened as a complete server-rendered shell.
    location.assign(url.href)
  })
}
