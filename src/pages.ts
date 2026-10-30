import { toolCatalog, toolIds, type ToolId } from './tools/catalog'
/** One route table for Vue page selection and generated sharing documents. */
import { gazeGuides, gazeGuidePath } from './gaze/catalog'
import { errorPaths } from './errors/catalog'

const gazeGuidePages = Object.fromEntries(
  gazeGuides.map((guide) => [`gaze.${guide.id}`, gazeGuidePath(guide.id)]),
)

const toolPages = Object.fromEntries(toolIds.map((id) => [id, toolCatalog[id].path])) as {
  [Id in ToolId]: `/tools/${Id}`
}

export const pages = {
  home: '/',
  directory: '/project',
  tools: '/tool',
  games: '/game',
  twenty48: '/games/2048',
  minesweeper: '/games/minesweeper',
  solitaire: '/games/solitaire',
  tetris: '/games/tetris',
  sudoku: '/games/sudoku',
  xiangqi: '/games/xiangqi',
  gomoku: '/games/gomoku',
  snake: '/games/snake',
  popstar: '/games/popstar',
  huarongdao: '/games/huarongdao',
  jump: '/games/jump',
  chess: '/games/chess',
  go: '/games/go',
  doudizhu: '/games/doudizhu',
  junqi: '/games/junqi',
  ...toolPages,
  rdp: '/projects/rdp-access-auth',
  wiki: '/projects/rdp-access-auth/wiki',
  downloads: '/projects/rdp-access-auth/downloads',
  gaze: '/projects/gaze',
  ...errorPaths,
  ...gazeGuidePages,
} as const
export type PageName = keyof typeof pages
export function isProjectPage(page: unknown) {
  return page === 'rdp' || page === 'wiki' || page === 'downloads'
}
export function isGazePage(page: unknown): page is PageName {
  return typeof page === 'string' && (page === 'gaze' || page.startsWith('gaze.'))
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
  return knownPageForPath(path) ?? 'error404'
}
