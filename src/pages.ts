/** One route table for Vue page selection and generated sharing documents. */
export const pages = {
  home: '/',
  directory: '/project',
  tools: '/tool',
  json: '/tools/json',
  base64: '/tools/base64',
  url: '/tools/url',
  timestamp: '/tools/timestamp',
  uuid: '/tools/uuid',
  text: '/tools/text',
  radix: '/tools/radix',
  hash: '/tools/hash',
  jwt: '/tools/jwt',
  password: '/tools/password',
  html: '/tools/html',
  color: '/tools/color',
  rdp: '/projects/rdp-access-auth',
  wiki: '/projects/rdp-access-auth/wiki',
  downloads: '/projects/rdp-access-auth/downloads',
} as const
export type PageName = keyof typeof pages
export function isProjectPage(page: unknown) {
  return page === 'rdp' || page === 'wiki' || page === 'downloads'
}
export function knownPageForPath(path: string): PageName | undefined {
  const normalized =
    path
      .replace(/\/index\.html$/, '')
      .replace(/\.html$/, '')
      .replace(/\/+$/, '') || '/'
  return (Object.keys(pages) as PageName[]).find((name) => pages[name] === normalized)
}
export function pageFile(page: PageName): string {
  return page === 'home' ? 'index.html' : `${pages[page].slice(1)}.html`
}
export function pageForPath(path: string): PageName {
  return knownPageForPath(path) ?? 'home'
}
