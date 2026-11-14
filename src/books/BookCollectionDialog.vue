<script setup lang="ts">
import { nextTick, ref, shallowRef } from 'vue'
import { ArrowRight, X } from 'lucide-vue-next'
import BookCover from './BookCover.vue'
import { bookLength, bookPath, type BookCollection } from './catalog'
import { progressPercent, type ReadingProgress } from './progress'
import { useBookDialog } from './useBookMotion'

defineProps<{ progress: Record<string, ReadingProgress | null> }>()
const dialog = ref<HTMLDialogElement>()
const collection = shallowRef<BookCollection>()
const motion = useBookDialog(dialog)
async function open(value: BookCollection) {
  collection.value = value
  await nextTick()
  void motion.open()
}
const close = () => void motion.close()
defineExpose({ open })
</script>

<template>
  <dialog
    ref="dialog"
    class="book-details book-collection-dialog"
    aria-labelledby="book-collection-title"
    @cancel.prevent="close"
    @click="
      (event) => {
        if (event.target === dialog) close()
      }
    "
  >
    <template v-if="collection">
      <button
        class="book-details-close"
        type="button"
        aria-label="关闭分册选择"
        title="关闭分册选择"
        @click="close"
      >
        <X :size="21" />
      </button>
      <div class="book-details-scroll">
        <div class="book-details-heading">
          <BookCover :book="collection" />
          <div>
            <p class="overline">{{ collection.volumes.length }} 册组合</p>
            <h2 id="book-collection-title">{{ collection.title }}</h2>
            <p>作者：{{ collection.author }}</p>
            <p>译者：{{ collection.translator }}</p>
            <span>按原著顺序排列 · 每册独立保存进度</span>
          </div>
        </div>
        <p class="book-collection-intro">{{ collection.description }}</p>
        <h3 class="book-collection-label">选择一册开始阅读</h3>
        <ol class="book-volume-list" aria-label="分册列表">
          <li v-for="(book, number) in collection.volumes" :key="book.id">
            <a :href="bookPath(book)" class="book-volume" @click="close">
              <BookCover :book="book" :number="number + 1" />
              <div class="book-volume-info">
                <span class="book-volume-number">第 {{ number + 1 }} 册</span>
                <h4>{{ book.title }}</h4>
                <p>{{ bookLength(book) }} · {{ (book.characterCount / 10000).toFixed(1) }} 万字</p>
                <p class="book-volume-description">{{ book.description }}</p>
                <p v-if="progress[book.id]" class="book-volume-progress">
                  已读 {{ progressPercent(book, progress[book.id]!) }}% ·
                  {{ progress[book.id]!.title }}
                </p>
              </div>
              <span class="book-volume-action"
                >{{ progress[book.id] ? '继续阅读' : '开始阅读'
                }}<ArrowRight :size="16" aria-hidden="true"
              /></span>
            </a>
          </li>
        </ol>
      </div>
    </template>
  </dialog>
</template>
