<script setup>
// Adapted from jaywcjlove/tools packages/standard-chinese-characters (MIT).
import { computed, ref, watch } from 'vue'
import characters from 'togscc'
import ToolPage from '../freemium/components/ToolPage.vue'
import { copyText } from '../freemium/composables/clipboard'
const query = ref('')
const level = ref('all')
const page = ref(1)
const entries = Object.entries(characters).map(([char, value], index) => ({
  char,
  pinyin: [].concat(value).join(' / '),
  index: index + 1,
}))
const matches = computed(() =>
  entries.filter((item) => {
    const inLevel =
      level.value === 'all' ||
      (level.value === '1'
        ? item.index <= 3500
        : level.value === '2'
          ? item.index > 3500 && item.index <= 6500
          : item.index > 6500)
    const term = query.value.trim().toLowerCase()
    return (
      inLevel &&
      (!term ||
        term.includes(item.char) ||
        item.pinyin.toLowerCase().includes(term) ||
        String(item.index) === term)
    )
  }),
)
const pages = computed(() => Math.max(1, Math.ceil(matches.value.length / 120)))
const visible = computed(() => matches.value.slice((page.value - 1) * 120, page.value * 120))
watch([query, level], () => {
  page.value = 1
})
</script>
<template>
  <ToolPage>
    <template #options>
      <label class="jay-field"
        >查找汉字或拼音<input
          v-model="query"
          class="field"
          type="search"
          placeholder="输入汉字、声调拼音或序号"
      /></label>
      <label class="jay-field"
        >字表级别<select v-model="level" class="field">
          <option value="all">全部 8105 字</option>
          <option value="1">一级 · 3500 字</option>
          <option value="2">二级 · 3000 字</option>
          <option value="3">三级 · 1605 字</option>
        </select></label
      >
    </template>
    <p class="jay-note" role="status">找到 {{ matches.length }} 个汉字，点击可复制。</p>
    <Transition name="jay-panel" mode="out-in" @before-leave="(el) => (el.inert = true)">
      <div :key="`${query}:${level}:${page}`" class="jay-characters">
        <button
          v-for="item in visible"
          :key="item.char"
          type="button"
          :aria-label="`复制 ${item.char}，${item.pinyin}`"
          @click="copyText(item.char)"
        >
          <span>{{ item.pinyin }}</span
          ><strong>{{ item.char }}</strong
          ><small>{{ item.index }}</small>
        </button>
        <p v-if="!visible.length">暂时没有找到，试试单个汉字或其他拼音。</p>
      </div>
    </Transition>
    <div class="jay-actions">
      <button class="btn" :disabled="page <= 1" @click="page--">上一页</button
      ><span aria-live="polite">{{ page }} / {{ pages }}</span
      ><button class="btn" :disabled="page >= pages" @click="page++">下一页</button>
    </div>
  </ToolPage>
</template>
