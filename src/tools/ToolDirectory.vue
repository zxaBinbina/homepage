<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowUpRight, Search, X } from 'lucide-vue-next'
import SiteFooter from '../components/SiteFooter.vue'
import AppIcon from './freemium/components/AppIcon.vue'
import { toolCatalog, toolIds } from './catalog'
const query = ref('')
const category = ref('全部')
const categories = ['全部', ...new Set(toolIds.map((id) => toolCatalog[id].category))]
const matches = computed(() =>
  toolIds.filter((id) => {
    const tool = toolCatalog[id]
    return (
      (category.value === '全部' || tool.category === category.value) &&
      query.value
        .trim()
        .toLowerCase()
        .split(/\s+/)
        .every((word) =>
          `${tool.name} ${tool.description} ${tool.keywords}`.toLowerCase().includes(word),
        )
    )
  }),
)
function reset() {
  query.value = ''
  category.value = '全部'
}
function leave(element: Element) {
  const el = element as HTMLElement
  const { offsetLeft, offsetTop, offsetWidth, offsetHeight } = el
  Object.assign(el.style, {
    left: `${offsetLeft}px`,
    top: `${offsetTop}px`,
    width: `${offsetWidth}px`,
    height: `${offsetHeight}px`,
  })
  el.inert = true
}
function enter(element: Element) {
  const el = element as HTMLElement
  for (const key of ['left', 'top', 'width', 'height']) el.style.removeProperty(key)
  el.inert = false
}
</script>
<template>
  <div class="tool-route">
    <main id="main" class="directory-main shell tools-directory">
      <section class="directory-intro directory-entry">
        <p class="overline">TOOLBOX / {{ toolIds.length }}</p>
        <h1>小工具，<span class="tools-accent">让事情简单一点。</span></h1>
        <p>从整理代码到转换文件，把重复的小事交给顺手的工具。<br />不用安装，打开就能用。</p>
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
          <Search :size="17" aria-hidden="true" /><input
            v-model="query"
            type="search"
            aria-label="搜索工具"
            placeholder="搜索工具，例如 JSON、二维码"
            @keydown.esc="query = ''"
          /><button v-if="query" type="button" aria-label="清空搜索" @click="query = ''">
            <X :size="16" aria-hidden="true" />
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
      <TransitionGroup
        tag="div"
        class="tools-grid"
        name="tool-list"
        appear
        @before-leave="leave"
        @before-enter="enter"
        @enter-cancelled="enter"
      >
        <a
          v-for="(id, index) in matches"
          :key="id"
          :href="toolCatalog[id].path"
          class="tool-card"
          :style="{ '--tool-delay': `${Math.min(index, 8) * 24}ms` }"
        >
          <div class="tool-card-top">
            <span class="tool-icon"><AppIcon :name="toolCatalog[id].icon" :size="24" /></span
            ><span class="overline">{{ String(toolIds.indexOf(id) + 1).padStart(2, '0') }}</span>
          </div>
          <h2>{{ toolCatalog[id].name }}</h2>
          <p>{{ toolCatalog[id].description }}</p>
          <div class="tool-card-bottom">
            <span>{{ toolCatalog[id].category }}</span
            ><span>打开工具 <ArrowUpRight :size="16" aria-hidden="true" /></span>
          </div>
        </a>
      </TransitionGroup>
      <Transition name="tool-empty"
        ><div v-if="!matches.length" class="directory-empty">
          <h2>暂时没有匹配的工具</h2>
          <p>试试其他关键词，或回到全部工具。</p>
          <button type="button" @click="reset">查看全部工具</button>
        </div></Transition
      >
      <p class="tools-note">在浏览器内处理，让灵感少一点等待。</p>
      <p class="tools-credit">
        源自
        <a
          href="https://github.com/incentius-foss/freemium"
          target="_blank"
          rel="noopener noreferrer"
          >Freemium</a
        >
        ·
        <a href="/licenses/freemium.txt" target="_blank" rel="noopener noreferrer">MIT 开源许可</a>
      </p>
    </main>
    <SiteFooter />
  </div>
</template>
