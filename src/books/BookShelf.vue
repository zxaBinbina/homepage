<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ArrowRight, BookOpen, Grid2X2, List, Search, X } from 'lucide-vue-next'
import SiteFooter from '../components/SiteFooter.vue'
import SegmentedControl from '../components/SegmentedControl.vue'
import BookCover from './BookCover.vue'
import BookDetails from './BookDetails.vue'
import { books, bookPath, bookLength, type Book } from './catalog'
import { readProgress, progressPercent, type ReadingProgress } from './progress'
const query = ref(''),
  status = ref('all'),
  sort = ref('collection'),
  view = ref<'cards' | 'list'>('cards')
const details = ref<InstanceType<typeof BookDetails>>()
const progress = ref<Record<string, ReadingProgress | null>>({})
const filters = [
  { value: 'all', label: '全部' },
  { value: 'reading', label: '在读' },
  { value: 'unread', label: '未读' },
  { value: 'finished', label: '已读' },
]
function refreshProgress() {
  progress.value = Object.fromEntries(books.map((book) => [book.id, readProgress(book)]))
}
function readingStatus(book: Book) {
  const value = progress.value[book.id]
  return !value ? 'unread' : progressPercent(book, value) >= 100 ? 'finished' : 'reading'
}
refreshProgress()
onMounted(() => window.addEventListener('storage', refreshProgress))
onBeforeUnmount(() => window.removeEventListener('storage', refreshProgress))
const matches = computed(() => {
  const term = query.value.trim().toLocaleLowerCase()
  const matches = books.filter(
    (book) =>
      [book.title, book.alias, book.author, book.category]
        .join(' ')
        .toLocaleLowerCase()
        .includes(term) &&
      (status.value === 'all' || readingStatus(book) === status.value),
  )
  if (sort.value === 'recent')
    return matches.sort(
      (a, b) => (progress.value[b.id]?.updatedAt || 0) - (progress.value[a.id]?.updatedAt || 0),
    )
  if (sort.value === 'title') return matches.sort((a, b) => a.title.localeCompare(b.title, 'zh-CN'))
  return matches
})
const latest = computed(
  () =>
    books
      .filter((book) => progress.value[book.id])
      .sort((a, b) => progress.value[b.id]!.updatedAt - progress.value[a.id]!.updatedAt)[0],
)
function reset() {
  query.value = ''
  status.value = 'all'
}
</script>
<template>
  <div class="library-route">
    <main id="main" class="shell library-main">
      <header class="library-heading">
        <div>
          <p class="overline">A SMALL LIBRARY</p>
          <h1>
            我的书架<span>{{ books.length }} 本</span>
          </h1>
          <p>读过的故事，和你分享。挑一本，慢慢看。</p>
        </div>
        <span class="library-local"><BookOpen :size="16" />你的阅读进度，留在这个浏览器里。</span>
      </header>
      <section v-if="latest" class="library-continue" aria-label="最近阅读">
        <BookCover :book="latest" />
        <div>
          <p class="overline">CONTINUE READING</p>
          <h2>{{ latest.title }}</h2>
          <p>{{ progress[latest.id]!.title }}</p>
          <span>已读 {{ progressPercent(latest, progress[latest.id]!) }}%</span>
        </div>
        <a :href="bookPath(latest)" class="primary book-read-button"
          >继续阅读<ArrowRight :size="17"
        /></a>
      </section>
      <div class="library-toolbar">
        <SegmentedControl v-model="status" :options="filters" label="阅读状态" />
        <div class="directory-search">
          <Search :size="17" aria-hidden="true" /><input
            v-model="query"
            type="search"
            aria-label="搜索小说"
            placeholder="搜索书名、作者或别名"
            @keydown.esc="query = ''"
          /><button
            v-if="query"
            type="button"
            aria-label="清空搜索"
            title="清空搜索"
            @click="query = ''"
          >
            <X :size="16" />
          </button>
        </div>
      </div>
      <div class="library-list-heading">
        <p role="status">
          {{
            query.trim() || status !== 'all'
              ? `找到 ${matches.length} 本小说`
              : `全部 ${books.length} 本小说`
          }}
        </p>
        <div>
          <label
            ><span class="sr-only">书架排序</span
            ><select v-model="sort" aria-label="书架排序">
              <option value="collection">书架顺序</option>
              <option value="recent">最近阅读</option>
              <option value="title">书名顺序</option>
            </select></label
          >
          <div class="library-view" role="group" aria-label="书架布局">
            <button
              type="button"
              aria-label="卡片视图"
              title="卡片视图"
              :aria-pressed="view === 'cards'"
              @click="view = 'cards'"
            >
              <Grid2X2 :size="17" /></button
            ><button
              type="button"
              aria-label="列表视图"
              title="列表视图"
              :aria-pressed="view === 'list'"
              @click="view = 'list'"
            >
              <List :size="18" />
            </button>
          </div>
        </div>
      </div>
      <div v-if="matches.length" class="library-grid" :class="{ 'is-list': view === 'list' }">
        <article v-for="book in matches" :key="book.id" class="book-card">
          <div class="book-card-cover">
            <BookCover :book="book" :number="books.indexOf(book) + 1" />
          </div>
          <div class="book-card-info">
            <p class="book-category">
              {{ book.category
              }}<span :title="bookLength(book)">{{ book.numberedChapterCount }} 章</span>
            </p>
            <h2>
              <button
                class="book-card-details"
                type="button"
                :aria-label="`查看《${book.title}》的详情`"
                aria-haspopup="dialog"
                @click="details?.open(book)"
              >
                {{ book.title }}
              </button>
            </h2>
            <p class="book-author">{{ book.author }}</p>
            <p class="book-description">{{ book.description }}</p>
            <p v-if="book.alias" class="book-alias">又名《{{ book.alias }}》</p>
            <div class="book-card-bottom">
              <div v-if="progress[book.id]" class="book-card-progress">
                <span class="book-progress-track" aria-hidden="true"
                  ><i :style="{ width: `${progressPercent(book, progress[book.id]!)}%` }"></i></span
                ><span>{{ progressPercent(book, progress[book.id]!) }}%</span>
              </div>
              <a :href="bookPath(book)"
                >{{ progress[book.id] ? '继续阅读' : '开始阅读' }}<ArrowRight :size="16"
              /></a>
            </div>
          </div>
        </article>
      </div>
      <div v-else class="directory-empty">
        <h2>这里暂时还没有书</h2>
        <p>换个关键词，或看看书架上的其他故事。</p>
        <button type="button" @click="reset">查看全部小说</button>
      </div>
      <p class="library-footnote">
        收录章节以当前文本为准。阅读进度、书签与设置仅保存在当前浏览器。
      </p>
    </main>
    <SiteFooter /><BookDetails ref="details" />
  </div>
</template>
