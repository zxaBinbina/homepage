import { nextTick } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { isProjectPage, knownPageForPath, pages, type PageName } from './pages'
import { isToolId } from './tools/catalog'
import { createSiteMeta, createStructuredData, serializeStructuredData } from '../site.config'

const components = {
  home: () => import('./HomePage.vue'),
  directory: () => import('./ProjectDirectory.vue'),
  tools: () => import('./tools/ToolDirectory.vue'),
  json: () => import('./tools/ToolPage.vue'),
  base64: () => import('./tools/ToolPage.vue'),
  url: () => import('./tools/ToolPage.vue'),
  timestamp: () => import('./tools/ToolPage.vue'),
  uuid: () => import('./tools/ToolPage.vue'),
  text: () => import('./tools/ToolPage.vue'),
  rdp: () => import('./rdp/App.vue'),
  wiki: () => import('./rdp/App.vue'),
  downloads: () => import('./rdp/App.vue'),
}

function hashTarget(hash: string) {
  try {
    return document.getElementById(decodeURIComponent(hash.slice(1)))
  } catch {
    return null
  }
}

async function waitForHashTarget(hash: string) {
  for (let frame = 0; frame < 60; frame += 1) {
    const target = hashTarget(hash)
    if (target) {
      await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
      const current = hashTarget(hash) || target
      const page = current.closest<HTMLElement>('.rdp-page')
      if (
        !page ||
        (!page.classList.contains('rdp-content-enter-from') &&
          !page.classList.contains('rdp-content-enter-active'))
      )
        return current
      continue
    }
    await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
  }
  return null
}

function focusContent(element: HTMLElement | null) {
  if (!element) return
  if (!element.hasAttribute('tabindex')) element.tabIndex = -1
  element.focus({ preventScroll: true })
}

async function waitForMain() {
  // An out-in transition can temporarily leave only the outgoing main in the DOM.
  for (let frame = 0; frame < 60; frame += 1) {
    const main = Array.from(document.querySelectorAll('main')).find(
      (element) => !element.closest('.page-swap-leave-active, .rdp-content-leave-active'),
    )
    if (main) return main
    await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
  }
  return null
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
      props: isProjectPage(name) ? { view: name } : isToolId(name) ? { id: name } : undefined,
    })),
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  async scrollBehavior(to, from, savedPosition) {
    await nextTick()
    const changedPage = to.name !== from.name
    if (changedPage && from.matched.length) {
      const main = await waitForMain()
      if (router.currentRoute.value.fullPath !== to.fullPath) return false
      focusContent(main)
    }
    if (savedPosition) return { ...savedPosition, behavior: 'instant' }
    const target = to.hash ? await waitForHashTarget(to.hash) : null
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
  const project = isProjectPage(page)
  document.title = meta.title
  const structuredData = document.getElementById('site-structured-data')
  if (structuredData)
    structuredData.textContent = serializeStructuredData(
      createStructuredData(import.meta.env.SITE_URL, page),
    )
  document.body.classList.toggle('rdp-site', project)
  const values = {
    'meta[name="description"]': meta.description,
    'meta[property="og:title"]': meta.title,
    'meta[property="og:description"]': meta.description,
    'meta[property="og:url"]': meta.url,
    'meta[property="og:image"]': meta.image,
    'meta[property="og:image:secure_url"]': meta.image,
    'meta[property="og:image:alt"]': meta.imageAlt,
    'meta[property="og:image:type"]': meta.imageType,
    'meta[property="og:image:width"]': String(meta.imageWidth),
    'meta[property="og:image:height"]': String(meta.imageHeight),
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
