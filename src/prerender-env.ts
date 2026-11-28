/**
 * 构建期预渲染环境桩。仅由 src/prerender.ts 在 Node 中引入，不会进入客户端构建。
 *
 * 大量组件在 setup 顶层读取 matchMedia / document.hidden 等浏览器 API（仅作初始化
 * 判断用），逐个为 SSR 改写客户端组件侵入性过大；这里为这些 API 提供惰性实现，
 * 让预渲染只输出静态正文，不改变浏览器中的任何行为。
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Stub = Record<string, any>

const noop = (): void => {}

const mediaQuery = (): Stub => ({
  matches: false,
  media: '',
  onchange: null,
  addEventListener: noop,
  removeEventListener: noop,
  addListener: noop,
  removeListener: noop,
  dispatchEvent: () => false,
})

const classListStub = {
  add: noop,
  remove: noop,
  toggle: () => false,
  contains: () => false,
  replace: () => false,
  item: () => null,
  toString: () => '',
}

const elementStub = (tag = 'div'): Stub => ({
  tagName: String(tag).toUpperCase(),
  dataset: {},
  style: { setProperty: noop, removeProperty: noop, getPropertyValue: () => '' },
  classList: classListStub,
  children: [],
  hidden: false,
  textContent: '',
  innerHTML: '',
  offsetWidth: 0,
  offsetHeight: 0,
  appendChild: noop,
  removeChild: noop,
  setAttribute: noop,
  getAttribute: () => null,
  hasAttribute: () => false,
  removeAttribute: noop,
  closest: () => null,
  contains: () => false,
  querySelector: () => null,
  querySelectorAll: () => [],
  addEventListener: noop,
  removeEventListener: noop,
  getBoundingClientRect: () => ({
    x: 0,
    y: 0,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    width: 0,
    height: 0,
  }),
  focus: noop,
})

const storageStub = {
  getItem: () => null,
  setItem: noop,
  removeItem: noop,
  clear: noop,
  key: () => null,
  length: 0,
}

const documentStub: Stub = {
  hidden: false,
  visibilityState: 'visible',
  title: '',
  cookie: '',
  activeElement: null,
  documentElement: elementStub('html'),
  body: elementStub('body'),
  head: elementStub('head'),
  querySelector: () => null,
  querySelectorAll: () => [],
  getElementById: () => null,
  createElement: (tag?: string) => elementStub(tag),
  addEventListener: noop,
  removeEventListener: noop,
}

const locationStub = {
  href: 'https://localhost/',
  origin: 'https://localhost',
  protocol: 'https:',
  host: 'localhost',
  hostname: 'localhost',
  port: '',
  pathname: '/',
  search: '',
  hash: '',
}

const windowStub: Stub = {
  document: null as unknown as Stub,
  location: locationStub,
  history: {
    state: null,
    scrollRestoration: 'auto',
    pushState: noop,
    replaceState: noop,
    go: noop,
    back: noop,
    forward: noop,
  },
  navigator: { userAgent: 'build-time-prerender', language: 'zh-CN' },
  visualViewport: null,
  innerWidth: 1280,
  innerHeight: 800,
  localStorage: storageStub,
  sessionStorage: storageStub,
  matchMedia: mediaQuery,
  getComputedStyle: () => ({ length: 0, getPropertyValue: () => '' }),
  requestAnimationFrame: (callback: (time: number) => void) => setTimeout(() => callback(0), 0),
  cancelAnimationFrame: (id: number) => clearTimeout(id),
  addEventListener: noop,
  removeEventListener: noop,
  dispatchEvent: () => true,
  classList: classListStub,
}
windowStub.document = documentStub

class IntersectionObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
  takeRecords(): unknown[] {
    return []
  }
}

class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

const globals = globalThis as unknown as Stub
if (!globals.window) {
  globals.window = windowStub
  globals.document = documentStub
  globals.matchMedia = mediaQuery
  globals.localStorage = storageStub
  globals.sessionStorage = storageStub
  globals.location = locationStub
  globals.history = windowStub.history
  globals.getComputedStyle = windowStub.getComputedStyle
  globals.requestAnimationFrame = windowStub.requestAnimationFrame
  globals.cancelAnimationFrame = windowStub.cancelAnimationFrame
  globals.IntersectionObserver ??= IntersectionObserverStub
  globals.ResizeObserver ??= ResizeObserverStub
}
