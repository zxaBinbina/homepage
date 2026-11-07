<script setup lang="ts">
import { ref } from 'vue'
import { BookOpen, Sparkles } from 'lucide-vue-next'
import type { Book } from './catalog'
defineProps<{ book: Book; number?: number }>()
const failed = ref(false)
</script>

<template>
  <div
    class="book-cover"
    :class="`book-cover-${book.category === '悬疑探险' ? 'warm' : book.category === '方块冒险' ? 'world' : 'magic'}`"
    aria-hidden="true"
  >
    <img
      v-if="book.cover && !failed"
      :src="book.cover"
      alt=""
      width="240"
      height="320"
      loading="lazy"
      decoding="async"
      @error="failed = true"
    />
    <div v-else class="book-cover-type">
      <span class="book-cover-label"
        >{{ book.category }} <span>{{ String(number || 1).padStart(2, '0') }}</span></span
      >
      <Sparkles class="book-cover-mark" :size="48" :stroke-width="0.8" />
      <strong>{{ book.title }}</strong>
      <span class="book-cover-author">{{ book.author }}</span>
      <BookOpen class="book-cover-sign" :size="20" :stroke-width="1.3" />
    </div>
  </div>
</template>
