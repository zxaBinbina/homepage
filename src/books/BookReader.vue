<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { watch } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowDownUp,
  Bookmark as BookmarkIcon,
  BookmarkPlus,
  Check,
  ChevronLeft,
  ChevronRight,
  Info,
  List,
  Maximize2,
  Minimize2,
  Minus,
  Plus,
  RotateCcw,
  Search,
  Settings2,
  Trash2,
  X,
} from 'lucide-vue-next'
import SegmentedControl from '../components/SegmentedControl.vue'
import CollapsePanel from '../components/CollapsePanel.vue'
import BookCover from './BookCover.vue'
import { useReaderFocus } from './useReaderFocus'
import { useBookDialog, useBookFade } from './useBookMotion'
import { books, bookLength, chapterPath, type ChapterIndex } from './catalog'
import { readProgress, writeProgress, migratePosition, type ReadingProgress } from './progress'
import {
  beginReaderNavigation,
  readerHistoryEntry,
  rememberReaderPosition,
  recalledReaderPosition,
} from './readingNavigation'
import { defaultSettings, readSettings, writeSettings, type ReaderSettings } from './readerSettings'
import { readBookmarks, writeBookmarks, type Bookmark } from './bookmarks'
import { bookSynopsis, fetchBookJson, positionPath, searchBook, type SearchResult } from './content'

const props = defineProps<{ id: string }>()
const book = books.find((entry) => entry.id === props.id)!
const route = useRoute(),
  router = useRouter()
const settings = ref(readSettings())
const index = shallowRef<ChapterIndex>()
const paragraphs = shallowRef<string[]>([])
const chapter = ref(0),
  chapterFraction = ref(0)
const loading = ref(true),
  error = ref(false),
  storageFailed = ref(false)
const reader = ref<HTMLElement>(),
  viewport = ref<HTMLElement>(),
  article = ref<HTMLElement>(),
  heading = ref<HTMLElement>()
const panel = ref<HTMLDialogElement>(),
  panelSearch = ref<HTMLInputElement>(),
  panelList = ref<HTMLElement>(),
  focusExit = ref<HTMLButtonElement>(),
  focusButton = ref<HTMLButtonElement>()
type Panel = 'toc' | 'bookmarks' | 'search' | 'info' | 'settings'
const panelTab = ref<Panel>('toc'),
  panelOpen = ref(false)
const panelTabs = [
  { value: 'toc', label: '目录' },
  { value: 'bookmarks', label: '书签' },
  { value: 'search', label: '搜索' },
  { value: 'info', label: '简介' },
] as const
const currentEntry = computed(() => index.value?.chapters[chapter.value])
const parentEntry = computed(() => {
  const parent = currentEntry.value?.parentChapter
  return parent != null ? index.value?.chapters[parent] : undefined
})
const currentChapterNumber = computed(
  () => parentEntry.value?.number ?? currentEntry.value?.number ?? 1,
)
const expandedChapters = ref(new Set<number>())
const searchCollapsedChapters = ref(new Set<number>())
const appendixEntries = computed(() =>
  (index.value?.chapters || [])
    .map((entry, index) => ({ ...entry, index }))
    .filter((entry) => entry.appendix),
)
const currentAppendixNumber = computed(
  () => appendixEntries.value.findIndex((entry) => entry.index === chapter.value) + 1,
)
const chapterQuery = ref(''),
  reverse = ref(false),
  jumpNumber = ref(1)
const bookmarks = ref(readBookmarks(book))
const searchQuery = ref(''),
  searchResults = shallowRef<SearchResult[]>([])
const searching = ref(false),
  searchDone = ref(false),
  searchFailed = ref(false),
  searchedParts = ref(0),
  highlight = ref('')
const notice = ref('')
const pageNumber = ref(0),
  pageCount = ref(1),
  pageWidth = ref(720)
const title = computed(() => index.value?.chapters[chapter.value]?.title || '正在打开故事…')
const synopsis = computed(() => bookSynopsis(book, index.value))
const percent = computed(() =>
  Math.min(100, ((chapter.value + chapterFraction.value) / book.chapterCount) * 100),
)
const chapterMatches = computed(() => {
  const query = chapterQuery.value.trim().toLocaleLowerCase()
  const entries = (index.value?.chapters || []).map((entry, index) => ({ ...entry, index }))
  const children = new Map<number, typeof entries>()
  for (const entry of entries) {
    if (entry.parentChapter === null) continue
    const siblings = children.get(entry.parentChapter) || []
    siblings.push(entry)
    children.set(entry.parentChapter, siblings)
  }
  const matches = (entry: (typeof entries)[number]) =>
    `${entry.number ?? ''} ${entry.title} ${entry.originalTitle}`
      .toLocaleLowerCase()
      .includes(query)
  const roots = entries
    .filter((entry) => entry.parentChapter === null && !entry.appendix)
    .flatMap((entry) => {
      const attached = children.get(entry.index) || []
      const matchingChildren = attached.filter(matches)
      return matches(entry) || matchingChildren.length
        ? [
            {
              ...entry,
              appendixGroup: false,
              children: matches(entry) ? attached : matchingChildren,
            },
          ]
        : []
    })
  const appendices = appendixEntries.value.filter(
    (entry) => matches(entry) || '番外'.includes(query),
  )
  if (appendices.length)
    roots.push({
      ...appendices[0]!,
      index: -1,
      number: null,
      title: '番外',
      name: '番外',
      appendixGroup: true,
      children: appendices,
    })
  return reverse.value ? roots.reverse() : roots
})
function branchOpen(chapter: number) {
  return chapterQuery.value.trim()
    ? !searchCollapsedChapters.value.has(chapter)
    : expandedChapters.value.has(chapter)
}
function toggleBranch(chapter: number) {
  const state = chapterQuery.value.trim() ? searchCollapsedChapters.value : expandedChapters.value
  if (state.has(chapter)) state.delete(chapter)
  else state.add(chapter)
}
watch(chapterQuery, () => searchCollapsedChapters.value.clear())
const appearance = computed(() => ({
  '--reader-width': `${settings.value.width}px`,
  '--reader-font-size': `${settings.value.fontSize}px`,
  '--reader-line-height': settings.value.lineHeight,
  '--reader-paragraph-gap': `${settings.value.paragraphGap}em`,
  '--reader-column-width': `${pageWidth.value}px`,
}))
const currentBookmark = computed(() =>
  bookmarks.value.some((item) => item.chapter === chapter.value),
)
type Position = Pick<ReadingProgress, 'paragraph' | 'offset'>
const GAP = 48
const chunks = new Map<number, string[][]>()
let controller: AbortController | undefined, searchController: AbortController | undefined
let request = 0,
  searchRequest = 0,
  layoutRequest = 0
let ready = false,
  firstOpen = true,
  disposed = false,
  openLastPage = false
let saveTimer: ReturnType<typeof setTimeout> | undefined,
  noticeTimer: ReturnType<typeof setTimeout> | undefined,
  resizeTimer: ReturnType<typeof setTimeout> | undefined
let finishNavigation: (() => void) | undefined
let cleaningAnchorPath: string | undefined
let historyEntry = ''
let layoutAnchor: Position | null = null,
  panelAnchor: ReadingProgress | null = null,
  lastPosition: ReadingProgress | null = null
let swipe: { x: number; y: number; time: number; id: number } | null = null

const panelMotion = useBookDialog(panel, true)
const fadeContent = useBookFade()
const { focused, exitVisible, toggleFocus, pointerMove, pointerLeave, pointerUp, reveal, release } =
  useReaderFocus({
    exitButton: focusExit,
    enterButton: focusButton,
    capture: () => {
      clearTimeout(resizeTimer)
      const anchor = capturePosition() || layoutAnchor || lastPosition
      ready = false
      return anchor
    },
    restore: async (anchor) => {
      await measureLayout()
      if (disposed || loading.value || error.value) return
      restorePosition(anchor)
      ready = true
      savePosition()
      fadeContent(article.value)
    },
    notice: message,
  })

function message(text: string) {
  notice.value = text
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => {
    notice.value = ''
  }, 2800)
}
function readingLine() {
  return focused.value ? 32 : 88
}
function capturePosition(): ReadingProgress | null {
  if (!ready || !article.value || !paragraphs.value.length) return null
  const nodes = Array.from(article.value.querySelectorAll<HTMLElement>('[data-paragraph]'))
  let paragraph = 0,
    offset = 0,
    endVisible = false
  if (settings.value.mode === 'pages' && viewport.value) {
    const bounds = viewport.value.getBoundingClientRect()
    outer: for (const [n, node] of nodes.entries()) {
      const rects = Array.from(node.getClientRects())
      for (const [part, rect] of rects.entries())
        if (rect.right > bounds.left + 2 && rect.left < bounds.right - 2) {
          paragraph = n
          offset = part / rects.length
          break outer
        }
    }
    endVisible = pageNumber.value === pageCount.value - 1
  } else {
    const line = readingLine()
    paragraph = nodes.findIndex((node) => node.getBoundingClientRect().bottom > line)
    if (paragraph < 0) paragraph = nodes.length - 1
    const rect = nodes[paragraph].getBoundingClientRect()
    offset = Math.max(0, Math.min(1, (line - rect.top) / Math.max(1, rect.height)))
    endVisible =
      nodes[nodes.length - 1].getBoundingClientRect().bottom <=
      innerHeight - (focused.value ? 28 : 76)
  }
  return {
    version: 1,
    revision: book.revision,
    chapter: chapter.value,
    title: title.value,
    paragraph,
    offset,
    fraction: endVisible ? 1 : (paragraph + offset) / nodes.length,
    updatedAt: Date.now(),
  }
}
function savePosition() {
  clearTimeout(saveTimer)
  const position = capturePosition()
  if (!position) return
  lastPosition = position
  rememberReaderPosition(historyEntry, book.id, position)
  chapterFraction.value = position.fraction
  storageFailed.value = !writeProgress(book, position)
}
function scheduleSave() {
  clearTimeout(saveTimer)
  saveTimer = setTimeout(savePosition, 180)
}
function onVisibility() {
  if (document.hidden) savePosition()
}
function setPage(number: number) {
  pageNumber.value = Math.max(0, Math.min(pageCount.value - 1, number))
  viewport.value?.scrollTo({
    left: pageNumber.value * (pageWidth.value + GAP),
    behavior: 'instant',
  })
}
async function measureLayout() {
  await nextTick()
  if (!viewport.value) return
  pageWidth.value = viewport.value.clientWidth
  await nextTick()
  await new Promise<void>((resolve) =>
    requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
  )
  if (disposed) return
  pageCount.value =
    settings.value.mode === 'pages' && article.value
      ? Math.max(1, Math.ceil((article.value.scrollWidth + GAP - 1) / (pageWidth.value + GAP)))
      : 1
}
function restorePosition(position: Position | null) {
  const node =
    position &&
    article.value?.querySelector<HTMLElement>(
      `[data-paragraph="${Math.min(position.paragraph, paragraphs.value.length - 1)}"]`,
    )
  if (settings.value.mode === 'pages') {
    window.scrollTo({ top: 0, behavior: 'instant' })
    if (node && viewport.value && (position.paragraph || position.offset)) {
      const rects = Array.from(node.getClientRects())
      const rect = rects[Math.min(rects.length - 1, Math.floor(position.offset * rects.length))]
      const x = rect.left - viewport.value.getBoundingClientRect().left + viewport.value.scrollLeft
      setPage(Math.floor((x + 2) / (pageWidth.value + GAP)))
    } else setPage(0)
  } else {
    viewport.value?.scrollTo({ left: 0, behavior: 'instant' })
    if (node && (position.paragraph || position.offset)) {
      const rect = node.getBoundingClientRect()
      window.scrollTo({
        top: Math.max(0, scrollY + rect.top + rect.height * position.offset - readingLine()),
        behavior: 'instant',
      })
    } else window.scrollTo({ top: 0, behavior: 'instant' })
  }
}
async function loadChapter() {
  historyEntry = readerHistoryEntry()
  finishNavigation?.()
  const finish = beginReaderNavigation(route.fullPath)
  finishNavigation = finish
  const token = ++request
  controller?.abort()
  const pending = new AbortController()
  controller = pending
  const timeout = setTimeout(() => pending.abort(), 15000)
  ready = false
  loading.value = true
  error.value = false
  const saved = readProgress(book, true),
    raw = route.query.chapter
  const requested = typeof raw === 'string' && /^\d+$/.test(raw) ? Number(raw) - 1 : -1
  let target =
    raw == null
      ? saved?.chapter || 0
      : requested >= 0 && requested < book.chapterCount
        ? requested
        : 0
  const anchorNumber =
    typeof route.query.paragraph === 'string' && /^\d+$/.test(route.query.paragraph)
      ? Number(route.query.paragraph) - 1
      : -1
  const anchorOffset = Number(route.query.offset || 0)
  let restore =
    anchorNumber >= 0
      ? {
          paragraph: anchorNumber,
          offset: Number.isFinite(anchorOffset) ? Math.max(0, Math.min(1, anchorOffset)) : 0,
        }
      : recalledReaderPosition(historyEntry, book.id, target) ||
        (firstOpen && saved?.chapter === target ? saved : null)
  const moveFocus = !firstOpen
  try {
    const contents: ChapterIndex =
      index.value || (await fetchBookJson(book, 'index', pending.signal))
    if (!Array.isArray(contents.chapters) || contents.chapters.length !== book.chapterCount)
      throw new Error('目录不可用')
    if (saved && firstOpen && anchorNumber < 0 && (raw == null || target === saved.chapter)) {
      const migrated = migratePosition(book, contents, saved)
      target = migrated.chapter
      restore = migrated
    }
    if (bookmarks.value.some((item) => item.revision !== book.revision)) {
      bookmarks.value = bookmarks.value.map((item) => migratePosition(book, contents, item))
      writeBookmarks(book, bookmarks.value)
    }
    const part = Math.floor(target / book.chunkSize)
    const chunk: string[][] = chunks.get(part) || (await fetchBookJson(book, part, pending.signal))
    const text = chunk[target % book.chunkSize]
    if (!Array.isArray(text) || !text.length || text.some((line) => typeof line !== 'string'))
      throw new Error('正文不可用')
    if (token !== request || disposed) return
    chunks.set(part, chunk)
    if (chunks.size > 2) chunks.delete(chunks.keys().next().value!)
    index.value = contents
    chapter.value = target
    jumpNumber.value = currentChapterNumber.value
    if (currentEntry.value?.parentChapter != null)
      expandedChapters.value.add(currentEntry.value.parentChapter)
    if (currentEntry.value?.appendix) expandedChapters.value.add(-1)
    paragraphs.value = text
    loading.value = false
    await measureLayout()
    await Promise.allSettled(
      (reader.value?.getAnimations() || []).map((animation) => animation.finished),
    )
    if (token !== request || disposed) return
    restorePosition(restore)
    if (openLastPage && settings.value.mode === 'pages') setPage(pageCount.value - 1)
    openLastPage = false
    if (moveFocus)
      (anchorNumber >= 0
        ? article.value?.querySelector<HTMLElement>(
            `[data-paragraph="${Math.min(anchorNumber, text.length - 1)}"]`,
          )
        : heading.value
      )?.focus({ preventScroll: true })
    ready = true
    firstOpen = false
    layoutAnchor = null
    savePosition()
    fadeContent(article.value)
    // A bookmark/search link is a one-time destination. Subsequent reloads resume
    // the new reading position instead of jumping back to the original result.
    if (anchorNumber >= 0) {
      const query = { ...route.query }
      delete query.paragraph
      delete query.offset
      cleaningAnchorPath = router.resolve({ path: route.path, query }).fullPath
      await router.replace({ path: route.path, query })
    }
  } catch {
    if (token === request && !disposed) {
      error.value = true
      loading.value = false
    }
  } finally {
    clearTimeout(timeout)
    finish()
  }
}
async function updateSettings(patch: Partial<ReaderSettings>) {
  const token = ++layoutRequest
  layoutAnchor = capturePosition() || layoutAnchor || lastPosition
  ready = false
  settings.value = { ...settings.value, ...patch }
  if (!writeSettings(settings.value)) message('浏览器未允许保存阅读设置')
  await measureLayout()
  if (token !== layoutRequest || disposed || loading.value || error.value) return
  restorePosition(layoutAnchor)
  ready = true
  layoutAnchor = null
  savePosition()
}
function beginSwipe(event: PointerEvent) {
  if (settings.value.mode !== 'pages' || event.pointerType === 'mouse' || !event.isPrimary) return
  swipe = { x: event.clientX, y: event.clientY, time: performance.now(), id: event.pointerId }
}
function endSwipe(event: PointerEvent) {
  const start = swipe
  swipe = null
  if (!start || start.id !== event.pointerId || !window.getSelection()?.isCollapsed) return
  const dx = event.clientX - start.x,
    dy = event.clientY - start.y
  if (
    Math.abs(dx) >= 48 &&
    Math.abs(dx) > Math.abs(dy) * 1.4 &&
    performance.now() - start.time < 900
  )
    turnPage(dx < 0 ? 1 : -1)
}
function turnPage(direction: number) {
  if (!ready) return
  const next = pageNumber.value + direction
  if (settings.value.mode === 'pages' && next >= 0 && next < pageCount.value) {
    setPage(next)
    fadeContent(article.value)
    savePosition()
    return
  }
  const nextChapter = chapter.value + direction
  if (nextChapter < 0 || nextChapter >= book.chapterCount) {
    message(direction < 0 ? '已经是全书开头' : '已读到这份文本的结尾')
    return
  }
  openLastPage = direction < 0 && settings.value.mode === 'pages'
  void router.push(chapterPath(book, nextChapter))
}
function chapterStart() {
  restorePosition(null)
  savePosition()
  heading.value?.focus({ preventScroll: true })
}
function onKey(event: KeyboardEvent) {
  if (
    panelOpen.value ||
    event.altKey ||
    event.ctrlKey ||
    event.metaKey ||
    (event.target instanceof HTMLElement &&
      event.target.closest('input,textarea,select,[contenteditable="true"],.seg'))
  )
    return
  if (event.key === 'Escape' && focused.value) {
    event.preventDefault()
    void toggleFocus()
  }
  if (
    ['ArrowLeft', 'ArrowRight'].includes(event.key) ||
    (settings.value.mode === 'pages' && ['PageUp', 'PageDown', ' '].includes(event.key))
  ) {
    if (
      event.target instanceof HTMLElement &&
      event.target.closest('button,a') &&
      event.key === ' '
    )
      return
    event.preventDefault()
    turnPage(['ArrowLeft', 'PageUp'].includes(event.key) || event.shiftKey ? -1 : 1)
  }
}
function stopSearch() {
  ++searchRequest
  searchController?.abort()
  searching.value = false
}
async function runSearch() {
  stopSearch()
  const query = searchQuery.value.trim()
  if (!query || !index.value) return
  const token = ++searchRequest,
    pending = new AbortController()
  searchController = pending
  searching.value = true
  searchFailed.value = false
  searchDone.value = false
  searchResults.value = []
  searchedParts.value = 0
  const timeout = setTimeout(() => pending.abort(), 45000)
  try {
    const results = await searchBook(book, query, pending.signal, (loaded) => {
      if (token === searchRequest) searchedParts.value = loaded
    })
    if (token !== searchRequest || disposed) return
    searchResults.value = results
    searchDone.value = true
    highlight.value = query
  } catch {
    if (token === searchRequest && !disposed) searchFailed.value = true
  } finally {
    clearTimeout(timeout)
    if (token === searchRequest) searching.value = false
  }
}
function setPanel(tab: Panel) {
  if (panelTab.value === 'search' && tab !== 'search') stopSearch()
  panelTab.value = tab
  void focusPanel().then(() =>
    fadeContent(panel.value?.querySelector<HTMLElement>('.reader-panel-scroll') || undefined),
  )
}
let tocFocusRequest = 0
async function focusPanel() {
  const token = ++tocFocusRequest
  if (panelTab.value === 'toc' && currentEntry.value?.parentChapter != null) {
    expandedChapters.value.add(currentEntry.value.parentChapter)
    searchCollapsedChapters.value.delete(currentEntry.value.parentChapter)
  }
  if (panelTab.value === 'toc' && currentEntry.value?.appendix) {
    expandedChapters.value.add(-1)
    searchCollapsedChapters.value.delete(-1)
  }
  await nextTick()
  panelSearch.value?.focus({ preventScroll: true })
  if (panelTab.value === 'toc') {
    await Promise.allSettled(
      (panelList.value?.getAnimations({ subtree: true }) || []).map(
        (animation) => animation.finished,
      ),
    )
    if (token !== tocFocusRequest || !panelOpen.value || panelTab.value !== 'toc') return
    const list = panelList.value
    const current = list?.querySelector<HTMLElement>('[aria-current]')
    if (current && list) {
      const row = current.closest<HTMLElement>('.reader-toc-row') || current
      list.scrollTop +=
        row.getBoundingClientRect().top -
        list.getBoundingClientRect().top -
        (list.clientHeight - row.offsetHeight) / 2
    }
  }
}
async function openPanel(tab: Panel) {
  panelAnchor = capturePosition()
  panelTab.value = tab
  if (tab === 'toc') jumpNumber.value = currentChapterNumber.value
  panelOpen.value = true
  void panelMotion.open()
  await focusPanel()
}
function closePanel() {
  stopSearch()
  return panelMotion.close()
}
function panelClosed() {
  panelOpen.value = false
  stopSearch()
}
function addBookmark() {
  const position = panelOpen.value ? panelAnchor : capturePosition()
  if (!position) return
  if (
    bookmarks.value.some(
      (item) => item.chapter === position.chapter && item.paragraph === position.paragraph,
    )
  ) {
    message('这个位置已经有书签了')
    return
  }
  if (bookmarks.value.length >= 500) {
    message('这本书已保存 500 个书签，请先整理一些')
    return
  }
  const bookmark: Bookmark = {
    ...position,
    id: crypto.randomUUID(),
    excerpt: (paragraphs.value[position.paragraph] || '').slice(0, 90),
  }
  const next = [bookmark, ...bookmarks.value]
  if (writeBookmarks(book, next)) {
    bookmarks.value = next
    message('已为当前位置添加书签')
  } else message('浏览器未允许保存书签')
}
function removeBookmark(id: string) {
  const next = bookmarks.value.filter((item) => item.id !== id)
  if (writeBookmarks(book, next)) bookmarks.value = next
  else message('书签未能删除，请稍后重试')
}
function jumpChapter() {
  const number = Number(jumpNumber.value)
  const target = index.value?.chapters.findIndex((entry) => entry.number === number) ?? -1
  if (!Number.isInteger(number) || target < 0) {
    message(`请输入 1–${book.numberedChapterCount} 的章节序号`)
    return
  }
  if (target === chapter.value) void closePanel().then(chapterStart)
  else {
    void closePanel()
    void router.push(chapterPath(book, target))
  }
}
function selectChapter(event: MouseEvent, number: number) {
  if (event.button || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return
  if (number === chapter.value && ready) {
    event.preventDefault()
    void closePanel().then(chapterStart)
  } else void closePanel()
}
function highlighted(text: string) {
  if (!highlight.value) return [{ text, match: false }]
  const needle = highlight.value.toLocaleLowerCase(),
    lower = text.toLocaleLowerCase(),
    parts: { text: string; match: boolean }[] = []
  let offset = 0,
    at = lower.indexOf(needle)
  while (at >= 0) {
    if (at > offset) parts.push({ text: text.slice(offset, at), match: false })
    parts.push({ text: text.slice(at, at + needle.length), match: true })
    offset = at + needle.length
    at = lower.indexOf(needle, offset)
  }
  if (offset < text.length) parts.push({ text: text.slice(offset), match: false })
  return parts
}
function onResize() {
  clearTimeout(resizeTimer)
  const anchor = lastPosition
  resizeTimer = setTimeout(async () => {
    if (!ready) return
    ready = false
    await measureLayout()
    if (disposed) return
    restorePosition(anchor)
    ready = true
    savePosition()
  }, 120)
}
function onStorage() {
  bookmarks.value = readBookmarks(book)
}
const routeKey = () =>
  JSON.stringify([route.query.chapter, route.query.paragraph, route.query.offset])
onBeforeRouteUpdate((to, from) => {
  if (to.fullPath === cleaningAnchorPath) return
  if (
    JSON.stringify([to.query.chapter, to.query.paragraph, to.query.offset]) !==
    JSON.stringify([from.query.chapter, from.query.paragraph, from.query.offset])
  ) {
    savePosition()
    ready = false
    void panelMotion.close(true)
  }
})
onBeforeRouteLeave(() => {
  savePosition()
  ready = false
  void panelMotion.close(true)
  stopSearch()
  release()
})
watch(
  routeKey,
  () => {
    if (route.fullPath === cleaningAnchorPath) {
      cleaningAnchorPath = undefined
      return
    }
    void loadChapter()
  },
  { immediate: true },
)
watch(searchQuery, () => {
  stopSearch()
  searchDone.value = false
  searchResults.value = []
})
onMounted(() => {
  window.addEventListener('scroll', scheduleSave, { passive: true })
  window.addEventListener('pagehide', savePosition)
  window.addEventListener('resize', onResize)
  window.addEventListener('storage', onStorage)
  document.addEventListener('visibilitychange', onVisibility)
})
onBeforeUnmount(() => {
  savePosition()
  finishNavigation?.()
  disposed = true
  ++request
  ++layoutRequest
  controller?.abort()
  stopSearch()
  clearTimeout(saveTimer)
  clearTimeout(noticeTimer)
  clearTimeout(resizeTimer)
  window.removeEventListener('scroll', scheduleSave)
  window.removeEventListener('pagehide', savePosition)
  window.removeEventListener('resize', onResize)
  window.removeEventListener('storage', onStorage)
  document.removeEventListener('visibilitychange', onVisibility)
})
</script>

<template>
  <div
    ref="reader"
    class="reader-root"
    :class="{ 'is-paged': settings.mode === 'pages', 'is-focused': focused }"
    :data-reading-theme="settings.theme"
    :data-reading-font="settings.font"
    :style="appearance"
    @keydown="onKey"
    @pointermove="pointerMove"
    @pointerleave="pointerLeave"
    @pointerup="pointerUp"
  >
    <header class="reader-topbar" :inert="focused">
      <a href="/book" class="reader-back reader-control" aria-label="返回书架" title="返回书架"
        ><ChevronLeft :size="20" /><span>书架</span></a
      >
      <div class="reader-identity">
        <strong>{{ book.title }}</strong
        ><span>{{ book.author }}</span>
      </div>
      <div class="reader-top-actions">
        <button
          class="reader-control reader-mobile-tools"
          type="button"
          aria-label="阅读工具"
          title="阅读工具"
          @click="openPanel('toc')"
        >
          <List :size="20" />
        </button>
        <button
          class="reader-control reader-info-button"
          type="button"
          aria-label="书籍简介"
          title="书籍简介"
          @click="openPanel('info')"
        >
          <Info :size="19" />
        </button>
        <button
          class="reader-control reader-add-bookmark"
          type="button"
          aria-label="为当前位置添加书签"
          title="为当前位置添加书签"
          :disabled="loading || error"
          @click="addBookmark"
        >
          <BookmarkPlus :size="19" />
        </button>
        <button
          class="reader-control reader-settings-button"
          type="button"
          aria-label="阅读设置"
          title="阅读设置"
          @click="openPanel('settings')"
        >
          <Settings2 :size="19" />
        </button>
        <button
          ref="focusButton"
          class="reader-control reader-focus-button"
          type="button"
          aria-label="专注阅读"
          title="专注阅读"
          :disabled="loading || error"
          @click="toggleFocus"
        >
          <Maximize2 :size="18" />
        </button>
      </div>
    </header>
    <button
      v-if="focused"
      ref="focusExit"
      class="reader-focus-exit reader-control"
      :class="{ 'is-visible': exitVisible }"
      @focus="reveal"
      type="button"
      title="退出专注模式（Esc）"
      @click="toggleFocus"
    >
      <Minimize2 :size="17" />退出专注
    </button>
    <nav class="reader-rail" aria-label="阅读工具" title="阅读工具" :inert="focused">
      <button
        class="reader-control reader-directory-button"
        type="button"
        aria-label="章节目录"
        title="章节目录"
        @click="openPanel('toc')"
      >
        <List :size="21" /><span>目录</span>
      </button>
      <button
        class="reader-control"
        type="button"
        aria-label="全文搜索"
        title="全文搜索"
        @click="openPanel('search')"
      >
        <Search :size="20" /><span>搜索</span>
      </button>
      <button
        class="reader-control"
        type="button"
        aria-label="我的书签"
        title="我的书签"
        @click="openPanel('bookmarks')"
      >
        <BookmarkIcon :size="20" :class="{ 'has-bookmark': currentBookmark }" /><span>书签</span>
      </button>
      <button
        class="reader-control reader-start-button"
        type="button"
        aria-label="回到本章开头"
        title="回到本章开头"
        @click="chapterStart"
      >
        <ArrowUp :size="20" /><span>章首</span>
      </button>
    </nav>
    <main id="main" class="reader-main" tabindex="-1">
      <div v-if="loading || error" class="reader-state" :aria-busy="loading" role="status">
        <span class="reader-state-symbol"><BookCover :book="book" /></span>
        <h1>{{ error ? '这一章暂时没能打开' : '正在打开书页…' }}</h1>
        <p>{{ error ? '检查一下网络，再试一次。' : book.title }}</p>
        <button v-if="error" type="button" class="reader-primary" @click="loadChapter">
          重新加载</button
        ><a v-if="error" href="/book">返回书架</a>
      </div>
      <div v-else class="reader-flow">
        <div
          ref="viewport"
          class="reader-viewport"
          @pointerdown="beginSwipe"
          @pointerup="endSwipe"
          @pointercancel="swipe = null"
        >
          <article ref="article" class="reader-text-layout" aria-labelledby="chapter-title">
            <header class="reader-chapter-heading">
              <p>
                {{ book.title }}
                <span v-if="currentEntry"
                  >·
                  {{
                    currentEntry.appendix
                      ? `番外 ${currentAppendixNumber} / ${book.appendixCount} 篇`
                      : `${currentChapterNumber} / ${book.numberedChapterCount} 章${parentEntry ? ' · 附篇' : ''}`
                  }}</span
                >
              </p>
              <a
                v-if="parentEntry && currentEntry?.parentChapter != null"
                class="reader-parent-chapter"
                :href="chapterPath(book, currentEntry.parentChapter)"
                >返回所属章节 · {{ parentEntry.title }}</a
              >
              <h1 id="chapter-title" ref="heading" tabindex="-1">
                {{ parentEntry ? currentEntry?.name : title }}
              </h1>
              <span class="reader-chapter-divider" aria-hidden="true"></span>
            </header>
            <p
              v-for="(paragraph, number) in paragraphs"
              :key="`${chapter}-${number}`"
              class="reader-paragraph"
              :data-paragraph="number"
              tabindex="-1"
            >
              <template v-for="(part, n) in highlighted(paragraph)" :key="n"
                ><mark v-if="part.match">{{ part.text }}</mark
                ><template v-else>{{ part.text }}</template></template
              >
            </p>
            <p v-if="chapter === book.chapterCount - 1" class="reader-end">
              已读到这份文本的最后一章。<br /><span>回到书架，再遇见一个故事。</span>
            </p>
          </article>
        </div>
        <nav v-if="settings.mode === 'scroll'" class="reader-chapter-nav" aria-label="章节导航">
          <a v-if="chapter > 0" :href="chapterPath(book, chapter - 1)"
            ><ArrowLeft :size="18" />上一章</a
          ><span v-else>全书开头</span><button type="button" @click="openPanel('toc')">目录</button
          ><a v-if="chapter < book.chapterCount - 1" :href="chapterPath(book, chapter + 1)"
            >下一章<ArrowRight :size="18" /></a
          ><a v-else href="/book">返回书架<ArrowRight :size="18" /></a>
        </nav>
      </div>
    </main>
    <footer class="reader-statusbar" :inert="focused">
      <button
        class="reader-control reader-turn-prev"
        type="button"
        :aria-label="settings.mode === 'pages' ? '上一页' : '上一章'"
        :title="settings.mode === 'pages' ? '上一页（←）' : '上一章（←）'"
        :disabled="
          loading || error || (chapter === 0 && (settings.mode === 'scroll' || pageNumber === 0))
        "
        @click="turnPage(-1)"
      >
        <ChevronLeft :size="20" /><span>{{ settings.mode === 'pages' ? '上一页' : '上一章' }}</span>
      </button>
      <button
        class="reader-position"
        type="button"
        aria-label="打开章节目录"
        title="打开章节目录"
        @click="openPanel('toc')"
      >
        <span>{{ title }}</span
        ><small
          >{{ settings.mode === 'pages' ? `本章 ${pageNumber + 1} / ${pageCount} 页 · ` : ''
          }}{{ percent.toFixed(1) }}%</small
        ><span class="reader-progress-line" aria-hidden="true"
          ><i :style="{ width: `${percent}%` }"></i
        ></span>
      </button>
      <button
        class="reader-control reader-turn-next"
        type="button"
        :aria-label="settings.mode === 'pages' ? '下一页' : '下一章'"
        :title="settings.mode === 'pages' ? '下一页（→）' : '下一章（→）'"
        :disabled="
          loading ||
          error ||
          (chapter === book.chapterCount - 1 &&
            (settings.mode === 'scroll' || pageNumber === pageCount - 1))
        "
        @click="turnPage(1)"
      >
        <span>{{ settings.mode === 'pages' ? '下一页' : '下一章' }}</span
        ><ChevronRight :size="20" />
      </button>
    </footer>
    <p v-if="storageFailed" class="reader-storage-warning" role="status">
      浏览器未允许保存进度，请记下当前章节。
    </p>
    <p v-if="notice" class="reader-notice" role="status">{{ notice }}</p>
    <dialog
      ref="panel"
      class="reader-panel"
      :class="{ 'is-settings': panelTab === 'settings' }"
      aria-labelledby="reader-panel-title"
      @close="panelClosed"
      @cancel.prevent="closePanel"
      @click="
        (event) => {
          if (event.target === panel) closePanel()
        }
      "
    >
      <div class="reader-panel-inner">
        <header class="reader-panel-heading">
          <div>
            <p>{{ panelTab === 'settings' ? 'MAKE IT YOURS' : 'IN THIS BOOK' }}</p>
            <h2 id="reader-panel-title">{{ panelTab === 'settings' ? '阅读设置' : book.title }}</h2>
          </div>
          <button
            class="reader-control"
            type="button"
            aria-label="关闭阅读面板"
            title="关闭阅读面板"
            @click="closePanel"
          >
            <X :size="20" />
          </button>
        </header>
        <SegmentedControl
          v-if="panelTab !== 'settings'"
          :model-value="panelTab"
          :options="panelTabs"
          label="阅读面板"
          @update:model-value="setPanel"
        />
        <template v-if="panelTab === 'toc'">
          <div class="reader-panel-search">
            <Search :size="17" /><input
              ref="panelSearch"
              v-model="chapterQuery"
              type="search"
              aria-label="搜索章节"
              placeholder="搜索章节名称或序号"
            />
          </div>
          <div class="reader-toc-toolbar">
            <span>{{ bookLength(book) }}</span
            ><button type="button" @click="reverse = !reverse">
              <ArrowDownUp :size="15" />{{ reverse ? '倒序' : '正序' }}
            </button>
          </div>
          <nav ref="panelList" class="reader-panel-scroll reader-toc" aria-label="小说目录">
            <ul class="reader-toc-tree">
              <li v-for="entry in chapterMatches" :key="entry.index" class="reader-toc-entry">
                <div class="reader-toc-row" :class="{ 'is-current': entry.index === chapter }">
                  <button
                    v-if="entry.appendixGroup"
                    type="button"
                    class="reader-toc-main reader-toc-toggle"
                    :aria-expanded="branchOpen(entry.index)"
                    :aria-controls="`reader-branch-${entry.index}`"
                    :title="`${branchOpen(entry.index) ? '收起' : '展开'}番外`"
                    @click="toggleBranch(entry.index)"
                  >
                    <span class="reader-toc-name"
                      >{{ entry.name }}<small>{{ entry.children.length }} 篇</small></span
                    >
                    <ChevronRight
                      :size="16"
                      class="reader-toc-chevron"
                      :class="{ 'is-open': branchOpen(entry.index) }"
                      aria-hidden="true"
                    />
                  </button>
                  <a
                    v-else
                    class="reader-toc-main"
                    :href="chapterPath(book, entry.index)"
                    :aria-current="entry.index === chapter ? 'location' : undefined"
                    @click="selectChapter($event, entry.index)"
                  >
                    <span class="reader-toc-number">{{
                      String(entry.number).padStart(2, '0')
                    }}</span>
                    <span class="reader-toc-name"
                      >{{ entry.name
                      }}<small v-if="entry.children.length"
                        >{{ entry.children.length }} 篇附篇</small
                      ></span
                    >
                  </a>
                  <button
                    v-if="entry.children.length && !entry.appendixGroup"
                    type="button"
                    class="reader-toc-toggle reader-toc-expand"
                    :aria-expanded="branchOpen(entry.index)"
                    :aria-controls="`reader-branch-${entry.index}`"
                    :aria-label="`${branchOpen(entry.index) ? '收起' : '展开'}《${entry.title}》的附篇`"
                    :title="`${branchOpen(entry.index) ? '收起' : '展开'}《${entry.title}》的附篇`"
                    @click="toggleBranch(entry.index)"
                  >
                    <ChevronRight
                      :size="16"
                      class="reader-toc-chevron"
                      :class="{ 'is-open': branchOpen(entry.index) }"
                      aria-hidden="true"
                    />
                  </button>
                </div>
                <CollapsePanel
                  v-if="entry.children.length"
                  :id="`reader-branch-${entry.index}`"
                  :open="branchOpen(entry.index)"
                  lazy
                >
                  <ul class="reader-toc-children">
                    <li v-for="child in entry.children" :key="child.index">
                      <a
                        class="reader-toc-child"
                        :href="chapterPath(book, child.index)"
                        :aria-current="child.index === chapter ? 'location' : undefined"
                        @click="selectChapter($event, child.index)"
                        >{{ child.name }}</a
                      >
                    </li>
                  </ul>
                </CollapsePanel>
              </li>
            </ul>
            <p v-if="!chapterMatches.length" class="reader-panel-empty">没有找到对应章节。</p>
          </nav>
          <form class="reader-jump" @submit.prevent="jumpChapter">
            <label for="reader-jump">跳至第</label
            ><input
              id="reader-jump"
              v-model="jumpNumber"
              type="number"
              min="1"
              :max="book.numberedChapterCount"
            /><span>章</span><button class="reader-primary" type="submit">跳转</button>
          </form>
        </template>
        <template v-else-if="panelTab === 'bookmarks'">
          <div class="reader-bookmark-toolbar">
            <span>{{ bookmarks.length }} 个书签</span
            ><button type="button" @click="addBookmark"><Plus :size="16" />添加当前位置</button>
          </div>
          <div class="reader-panel-scroll">
            <div v-if="!bookmarks.length" class="reader-panel-empty">
              <BookmarkIcon :size="36" :stroke-width="1" />
              <h3>把想再看的地方留下来</h3>
              <p>添加书签后，可以随时回到这一段。</p>
            </div>
            <article v-for="mark in bookmarks" :key="mark.id" class="reader-bookmark">
              <a
                :href="
                  positionPath(
                    book,
                    mark.chapter,
                    mark.revision === book.revision ? mark.paragraph : 0,
                    mark.revision === book.revision ? mark.offset : 0,
                  )
                "
                @click="closePanel"
                ><strong>{{ mark.title }}</strong>
                <p>{{ mark.excerpt }}</p>
                <small>{{ new Date(mark.updatedAt).toLocaleDateString('zh-CN') }}</small></a
              ><button
                class="reader-control"
                type="button"
                :aria-label="`删除书签：${mark.title}`"
                title="删除书签"
                @click="removeBookmark(mark.id)"
              >
                <Trash2 :size="16" />
              </button>
            </article>
          </div>
        </template>
        <template v-else-if="panelTab === 'search'">
          <form class="reader-full-search" @submit.prevent="runSearch">
            <div class="reader-panel-search">
              <Search :size="17" /><input
                ref="panelSearch"
                v-model="searchQuery"
                type="search"
                aria-label="搜索小说正文"
                placeholder="输入关键词，搜索整本书"
                maxlength="100"
              />
            </div>
            <button
              class="reader-primary"
              type="submit"
              :disabled="!searchQuery.trim() || searching || !index"
            >
              搜索
            </button>
          </form>
          <div v-if="searching" class="reader-search-state" role="status">
            <span
              >正在搜索 {{ searchedParts }} /
              {{ Math.ceil(book.chapterCount / book.chunkSize) }} 批正文</span
            ><button type="button" @click="stopSearch">取消</button>
          </div>
          <p v-else-if="searchFailed" class="reader-search-state" role="status">
            搜索未完成，请检查网络后重试。
          </p>
          <p v-else-if="searchDone" class="reader-search-state" role="status">
            {{
              searchResults.length >= 200
                ? '显示前 200 条结果，试试更具体的关键词。'
                : `找到 ${searchResults.length} 个段落`
            }}
          </p>
          <div class="reader-panel-scroll reader-search-results">
            <div v-if="!searchDone && !searching && !searchFailed" class="reader-panel-empty">
              <Search :size="36" :stroke-width="1" />
              <h3>找回故事里的某句话</h3>
              <p>搜索在当前浏览器内进行。首次搜索会载入这本书的全部正文。</p>
            </div>
            <a
              v-for="result in searchResults"
              :key="`${result.chapter}-${result.paragraph}`"
              :href="positionPath(book, result.chapter, result.paragraph)"
              @click="closePanel"
              ><strong>{{ index?.chapters[result.chapter]?.title }}</strong>
              <p>
                <template v-for="(part, n) in highlighted(result.excerpt)" :key="n"
                  ><mark v-if="part.match">{{ part.text }}</mark
                  ><template v-else>{{ part.text }}</template></template
                >
              </p></a
            >
          </div>
        </template>
        <section v-else-if="panelTab === 'info'" class="reader-panel-scroll reader-book-info">
          <div class="reader-info-cover">
            <BookCover :book="book" />
            <div>
              <h3>{{ book.title }}</h3>
              <p>{{ book.author }}</p>
              <span>{{ book.category }} · {{ bookLength(book) }}</span>
              <p v-if="book.alias">又名《{{ book.alias }}》</p>
            </div>
          </div>
          <h3>书籍简介</h3>
          <div class="reader-synopsis">
            <p v-for="(paragraph, n) in synopsis" :key="n">{{ paragraph }}</p>
          </div>
          <p v-if="book.sourceNote" class="reader-source-note">{{ book.sourceNote }}</p>
          <a
            v-if="book.coverSource"
            :href="book.coverSource"
            target="_blank"
            rel="noopener noreferrer"
            class="reader-source-link"
            >在番茄查看这本书 ↗</a
          >
          <p class="reader-info-note">
            章节以本地收录文本为准。进度、书签和设置保存在当前浏览器，清除浏览器数据后会消失。
          </p>
        </section>
        <div v-else class="reader-panel-scroll reader-settings">
          <section>
            <h3>阅读方式</h3>
            <SegmentedControl
              :model-value="settings.mode"
              :options="[
                { value: 'scroll', label: '上下滚动' },
                { value: 'pages', label: '左右翻页' },
              ]"
              label="阅读方式"
              @update:model-value="(mode) => updateSettings({ mode })"
            />
          </section>
          <section>
            <h3>纸张颜色</h3>
            <div class="reader-paper-options">
              <button
                v-for="option in [
                  { value: 'site', label: '跟随网站' },
                  { value: 'paper', label: '米白' },
                  { value: 'green', label: '浅绿' },
                  { value: 'night', label: '夜读' },
                ] as const"
                :key="option.value"
                type="button"
                :data-paper="option.value"
                :aria-pressed="settings.theme === option.value"
                @click="updateSettings({ theme: option.value })"
              >
                <span aria-hidden="true">Aa</span>{{ option.label
                }}<Check v-if="settings.theme === option.value" :size="12" />
              </button>
            </div>
          </section>
          <section>
            <h3>字体</h3>
            <SegmentedControl
              :model-value="settings.font"
              :options="[
                { value: 'sans', label: '黑体' },
                { value: 'serif', label: '宋体' },
              ]"
              label="正文字体"
              @update:model-value="(font) => updateSettings({ font })"
            />
          </section>
          <section>
            <div class="reader-setting-label">
              <h3>字号</h3>
              <output>{{ settings.fontSize }} px</output>
            </div>
            <div class="reader-font-adjust">
              <button
                class="reader-control"
                type="button"
                aria-label="缩小字号"
                title="缩小字号"
                :disabled="settings.fontSize <= 16"
                @click="updateSettings({ fontSize: settings.fontSize - 2 })"
              >
                <Minus :size="18" /></button
              ><input
                type="range"
                aria-label="正文字号"
                min="16"
                max="32"
                step="2"
                :value="settings.fontSize"
                @input="
                  updateSettings({ fontSize: Number(($event.target as HTMLInputElement).value) })
                "
              /><button
                class="reader-control"
                type="button"
                aria-label="放大字号"
                title="放大字号"
                :disabled="settings.fontSize >= 32"
                @click="updateSettings({ fontSize: settings.fontSize + 2 })"
              >
                <Plus :size="18" />
              </button>
            </div>
          </section>
          <section>
            <h3>行距</h3>
            <SegmentedControl
              :model-value="settings.lineHeight"
              :options="[
                { value: 1.6, label: '紧凑' },
                { value: 1.9, label: '适中' },
                { value: 2.2, label: '宽松' },
              ]"
              label="正文行距"
              @update:model-value="(lineHeight) => updateSettings({ lineHeight })"
            />
          </section>
          <section>
            <h3>段落间距</h3>
            <SegmentedControl
              :model-value="settings.paragraphGap"
              :options="[
                { value: 0.5, label: '紧凑' },
                { value: 1, label: '适中' },
                { value: 1.5, label: '宽松' },
              ]"
              label="段落间距"
              @update:model-value="(paragraphGap) => updateSettings({ paragraphGap })"
            />
          </section>
          <section>
            <h3>正文宽度</h3>
            <SegmentedControl
              :model-value="settings.width"
              :options="[
                { value: 640, label: '窄' },
                { value: 760, label: '适中' },
                { value: 900, label: '宽' },
              ]"
              label="正文宽度"
              @update:model-value="(width) => updateSettings({ width })"
            />
          </section>
          <p class="reader-settings-help">
            左右方向键切换{{ settings.mode === 'pages' ? '书页' : '章节' }}，Esc
            退出专注模式。左右翻页时也可以滑动屏幕，或用空格、Page Up / Down 翻页。设置会自动保存。
          </p>
          <button
            class="reader-reset"
            type="button"
            @click="updateSettings({ ...defaultSettings })"
          >
            <RotateCcw :size="16" />恢复默认设置
          </button>
        </div>
      </div>
    </dialog>
  </div>
</template>
