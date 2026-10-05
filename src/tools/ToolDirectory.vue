<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  ArrowUpRight,
  Braces,
  Clock3,
  Fingerprint,
  Link2,
  ScanText,
  Search,
  TextCursorInput,
  X,
} from 'lucide-vue-next'
import SiteFooter from '../components/SiteFooter.vue'
import { pages } from '../pages'
import { toolCatalog, toolIds } from './catalog'

const icons = {
  json: Braces,
  base64: ScanText,
  url: Link2,
  timestamp: Clock3,
  uuid: Fingerprint,
  text: TextCursorInput,
}
const query = ref('')
const category = ref('全部')
const categories = ['全部', '开发', '编码', '文本']
const matches = computed(() =>
  toolIds.filter((id) => {
    const tool = toolCatalog[id]
    return (
      (category.value === '全部' || tool.category === category.value) &&
      `${tool.name} ${tool.description} ${tool.keywords}`
        .toLowerCase()
        .includes(query.value.trim().toLowerCase())
    )
  }),
)
function reset() {
  query.value = ''
  category.value = '全部'
}
</script>

<template>
  <div>
    <main id="main" class="directory-main shell tools-directory">
      <section class="directory-intro directory-entry">
        <p class="overline">TOOLBOX / {{ String(toolIds.length).padStart(2, '0') }}</p>
        <h1>小工具，<span class="tools-accent">让事情简单一点。</span></h1>
        <p>把开发和日常里重复的小事，交给顺手的网页工具。<br />不用安装，打开就能用。</p>
      </section>
      <div class="directory-toolbar">
        <div class="tool-filters" role="group" aria-label="工具分类">
          <button
            v-for="item in categories"
            :key="item"
            type="button"
            :aria-pressed="category === item"
            @click="category = item"
          >
            {{ item }}
          </button>
        </div>
        <div class="directory-search">
          <Search :size="17" aria-hidden="true" />
          <input
            v-model="query"
            type="search"
            aria-label="搜索工具"
            placeholder="搜索工具，例如 JSON、时间戳"
            @keydown.esc="query = ''"
          />
          <button v-if="query" type="button" aria-label="清空搜索" @click="query = ''">
            <X :size="16" />
          </button>
        </div>
      </div>
      <p class="tools-count" role="status">
        {{
          query || category !== '全部'
            ? `找到 ${matches.length} 个工具`
            : `全部 ${toolIds.length} 个工具`
        }}
      </p>
      <div v-if="matches.length" class="tools-grid">
        <a v-for="id in matches" :key="id" :href="pages[id]" class="tool-card">
          <div class="tool-card-top">
            <span class="tool-icon"
              ><component :is="icons[id]" :size="24" aria-hidden="true"
            /></span>
            <span class="overline">{{ toolCatalog[id].label }}</span>
          </div>
          <h2>{{ toolCatalog[id].name }}</h2>
          <p>{{ toolCatalog[id].description }}</p>
          <div class="tool-card-bottom">
            <span>{{ toolCatalog[id].category }}</span
            ><span>打开工具 <ArrowUpRight :size="16" aria-hidden="true" /></span>
          </div>
        </a>
      </div>
      <div v-else class="directory-empty">
        <h2>暂时没有匹配的工具</h2>
        <p>试试其他关键词，或回到全部工具。</p>
        <button type="button" @click="reset">查看全部工具</button>
      </div>
      <p class="tools-note">从代码到日常，收集一些用得上的小帮手。</p>
    </main>
    <SiteFooter />
  </div>
</template>
