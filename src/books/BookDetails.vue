<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, shallowRef } from 'vue'
import { ArrowRight, X } from 'lucide-vue-next'
import BookCover from './BookCover.vue'
import { useBookDialog } from './useBookMotion'
import { bookPath, bookLength, type Book, type ChapterIndex } from './catalog'
import { bookSynopsis, fetchBookJson, positionPath } from './content'
import { readProgress } from './progress'
const dialog = ref<HTMLDialogElement>()
const motion = useBookDialog(dialog)
const book = shallowRef<Book>(),
  index = shallowRef<ChapterIndex>()
const loading = ref(false),
  failed = ref(false)
const synopsis = computed(() => (book.value ? bookSynopsis(book.value, index.value) : []))
const progress = computed(() => (book.value ? readProgress(book.value) : null))
let controller: AbortController | undefined,
  request = 0
async function fetchInfo() {
  if (!book.value) return
  controller?.abort()
  const pending = new AbortController()
  controller = pending
  const token = ++request
  loading.value = true
  failed.value = false
  const timeout = setTimeout(() => pending.abort(), 15000)
  try {
    const data = await fetchBookJson(book.value, 'index', pending.signal)
    if (token === request) index.value = data
  } catch {
    if (token === request) failed.value = true
  } finally {
    clearTimeout(timeout)
    if (token === request) loading.value = false
  }
}
async function open(value: Book) {
  book.value = value
  index.value = undefined
  await nextTick()
  void motion.open()
  void fetchInfo()
}
function close() {
  void motion.close()
}
function cancel() {
  ++request
  controller?.abort()
}
function onClosed() {
  // Native close events are queued; an earlier close must not cancel a reopened dialog.
  if (!dialog.value?.open) cancel()
}
onBeforeUnmount(cancel)
defineExpose({ open })
</script>
<template>
  <dialog
    ref="dialog"
    class="book-details"
    aria-labelledby="book-details-title"
    @close="onClosed"
    @cancel.prevent="close"
    @click="
      (event) => {
        if (event.target === dialog) close()
      }
    "
  >
    <template v-if="book"
      ><button
        type="button"
        class="book-details-close"
        aria-label="关闭书籍详情"
        title="关闭书籍详情"
        @click="close"
      >
        <X :size="21" />
      </button>
      <div class="book-details-scroll">
        <div class="book-details-heading">
          <BookCover :book="book" />
          <div>
            <p class="overline">{{ book.category }}</p>
            <h2 id="book-details-title">{{ book.title }}</h2>
            <p>{{ book.author }}</p>
            <p v-if="book.alias" class="book-details-alias">又名《{{ book.alias }}》</p>
            <span
              >{{ bookLength(book) }} · {{ (book.characterCount / 10000).toFixed(1) }} 万字</span
            >
          </div>
        </div>
        <section class="book-details-synopsis">
          <h3>书籍简介</h3>
          <p v-for="(paragraph, n) in synopsis" :key="n">{{ paragraph }}</p>
          <p v-if="loading" role="status" class="book-details-status">正在载入完整简介…</p>
          <p v-if="failed" class="book-details-status">
            完整简介暂未加载。<button type="button" @click="fetchInfo">重试</button>
          </p>
        </section>
        <p v-if="book.sourceNote" class="book-details-status">{{ book.sourceNote }}</p>
        <a
          v-if="book.coverSource"
          :href="book.coverSource"
          target="_blank"
          rel="noopener noreferrer"
          class="book-details-source"
          >番茄作品页 ↗</a
        >
      </div>
      <footer>
        <div v-if="progress" class="book-details-progress">
          <span>上次读到</span><strong>{{ progress.title }}</strong>
        </div>
        <div class="book-details-actions">
          <a :href="bookPath(book)" class="primary book-read-button" @click="close"
            >{{ progress ? '继续阅读' : '开始阅读' }}<ArrowRight :size="17" /></a
          ><a v-if="progress" :href="positionPath(book, 0, 0)" @click="close">从头开始</a>
        </div>
      </footer></template
    >
  </dialog>
</template>
