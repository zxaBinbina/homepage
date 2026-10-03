/** One route table for Vue page selection and generated sharing documents. */
export const pages = {
  home: '/',
  directory: '/project/',
  rdp: '/projects/rdp-access-auth/',
  wiki: '/projects/rdp-access-auth/wiki/',
} as const
export type PageName = keyof typeof pages
export function pageForPath(path: string): PageName {
  const normalized = `${path.replace(/\/index\.html$/, '').replace(/\/$/, '')}/`
  return (Object.keys(pages) as PageName[]).find((name) => pages[name] === normalized) ?? 'home'
}
