import { nextTick } from 'vue'
import {
  createRouter,
  createWebHistory,
  isNavigationFailure,
  NavigationFailureType,
  type RouteLocationNormalized,
} from 'vue-router'
import { beginPageLoading } from './loading/state'
import { isProjectPage, isGazePage, knownPageForPath, pages, type PageName } from './pages'
import { gazeGuides } from './gaze/catalog'
import { isToolId, toolIds, type ToolId } from './tools/catalog'
import { isGameId } from './games/catalog'
import { isErrorPage } from './errors/catalog'
import { createSiteMeta, createStructuredData, serializeStructuredData } from '../site.config'

const components = {
  home: () => import('./HomePage.vue'),
  directory: () => import('./ProjectDirectory.vue'),
  tools: () => import('./tools/ToolDirectory.vue'),
  ...(Object.fromEntries(toolIds.map((id) => [id, () => import('./tools/ToolPage.vue')])) as Record<
    ToolId,
    () => Promise<typeof import('./tools/ToolPage.vue')>
  >),
  games: () => import('./games/GameDirectory.vue'),
  twenty48: () => import('./games/GamePage.vue'),
  minesweeper: () => import('./games/GamePage.vue'),
  solitaire: () => import('./games/GamePage.vue'),
  tetris: () => import('./games/GamePage.vue'),
  sudoku: () => import('./games/GamePage.vue'),
  xiangqi: () => import('./games/GamePage.vue'),
  gomoku: () => import('./games/GamePage.vue'),
  snake: () => import('./games/GamePage.vue'),
  popstar: () => import('./games/GamePage.vue'),
  huarongdao: () => import('./games/GamePage.vue'),
  jump: () => import('./games/GamePage.vue'),
  chess: () => import('./games/GamePage.vue'),
  go: () => import('./games/GamePage.vue'),
  doudizhu: () => import('./games/GamePage.vue'),
  junqi: () => import('./games/GamePage.vue'),
  rdp: () => import('./rdp/App.vue'),
  wiki: () => import('./rdp/App.vue'),
  downloads: () => import('./rdp/App.vue'),
  gaze: () => import('./gaze/App.vue'),
  ...Object.fromEntries(
    gazeGuides.map((guide) => [`gaze.${guide.id}`, () => import('./gaze/App.vue')]),
  ),
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
      meta: isToolId(name) ? { tool: name } : {},
      alias:
        name === 'home' ? ['/index.html'] : [`${pages[name]}/index.html`, `${pages[name]}.html`],
      component: isErrorPage(name) ? () => import('./errors/ErrorPage.vue') : components[name],
      props: isErrorPage(name)
        ? { error: name }
        : isGazePage(name)
          ? { guide: name === 'gaze' ? null : name.slice(5) }
          : isProjectPage(name)
            ? { view: name }
            : isToolId(name) || isGameId(name)
              ? { id: name }
              : undefined,
    })),
    {
      path: '/:pathMatch(.*)*',
      name: 'unknown',
      component: () => import('./errors/ErrorPage.vue'),
      props: { error: 'error404' },
    },
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

const navigationLoads = new WeakMap<RouteLocationNormalized, ReturnType<typeof beginPageLoading>>()
let pendingNavigation: ReturnType<typeof beginPageLoading> | undefined
router.beforeEach((to, from) => {
  const page = knownPageForPath(to.path)
  if (page && to.path !== pages[page]) {
    return { path: pages[page], query: to.query, hash: to.hash, replace: true }
  }
  if (to.path !== from.path || !from.matched.length) {
    pendingNavigation = beginPageLoading(to.fullPath, true)
    navigationLoads.set(to, pendingNavigation)
  } else {
    // A same-page anchor can also cancel a different route still being downloaded.
    pendingNavigation?.finish()
    pendingNavigation = undefined
  }
})

router.afterEach(async (to, _from, failure) => {
  if (isNavigationFailure(failure, NavigationFailureType.duplicated)) {
    pendingNavigation?.finish()
    pendingNavigation = undefined
    return
  }
  // Let the new view register any nested async content before releasing this task.
  await nextTick()
  const loading = navigationLoads.get(to)
  loading?.finish()
  if (pendingNavigation === loading) pendingNavigation = undefined
})
router.onError((_error, to) => navigationLoads.get(to)?.fail())

router.afterEach((to, _from, failure) => {
  if (failure) return
  const page = to.name === 'unknown' ? 'error404' : (to.name as PageName)
  const meta = createSiteMeta(import.meta.env.SITE_URL, page)
  const project = isProjectPage(page)
  const gaze = isGazePage(page)
  document.title = meta.title
  const structuredData = document.getElementById('site-structured-data')
  if (structuredData)
    structuredData.textContent = serializeStructuredData(
      createStructuredData(import.meta.env.SITE_URL, page),
    )
  document.body.classList.toggle('rdp-site', project)
  const values = {
    'meta[name="robots"]': meta.robots,
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
  favicon?.setAttribute(
    'href',
    project ? '/images/rdp-access-auth.png' : gaze ? '/images/gaze.svg' : '/favicon.svg',
  )
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
    // The loading shell reports failures and offers an explicit full-page retry.
  })
}
