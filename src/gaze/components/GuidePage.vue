<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  ChevronDown,
  CircleHelp,
  ExternalLink,
  List,
  Search,
  X,
} from 'lucide-vue-next'
import content from 'virtual:gaze-content'
import { gazeGuides, gazeGuideGroups, gazeGuidePath, gazeGuide, gazeRepoUrl } from '../catalog'
import BlockList from './BlockList.vue'

const props = defineProps<{ guideId: string }>()
const doc = computed(() => content.guides[props.guideId])
const guide = computed(() => gazeGuide(props.guideId)!)
const article = ref<HTMLElement>()
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)')
const desktop = matchMedia('(min-width: 761px)')
const wide = ref(desktop.matches)
const menuOpen = ref(false)
const menuButton = ref<HTMLButtonElement>()
const navVisible = computed(() => wide.value || menuOpen.value)
const query = ref('')
const activeHeading = ref<string>()
const results = computed(() =>
  gazeGuides.filter((item) => {
    const text = content.guides[item.id]?.search ?? ''
    return `${item.title}\n${text}`
      .toLocaleLowerCase()
      .includes(query.value.trim().toLocaleLowerCase())
  }),
)
const neighbors = computed(() => {
  const index = gazeGuides.findIndex((item) => item.id === props.guideId)
  return {
    prev: index > 0 ? gazeGuides[index - 1] : undefined,
    next: index >= 0 && index < gazeGuides.length - 1 ? gazeGuides[index + 1] : undefined,
  }
})
function onWidth() {
  wide.value = desktop.matches
}
function closeMenu(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  if (query.value) query.value = ''
  else if (menuOpen.value) {
    menuOpen.value = false
    menuButton.value?.focus()
  }
}
let headings: HTMLElement[] = []
function updateHeading() {
  if (!headings.length) return
  let current = headings[0]
  for (const heading of headings) if (heading.getBoundingClientRect().top <= 150) current = heading
  activeHeading.value = current?.id
}
onMounted(() => {
  headings = Array.from(
    article.value?.querySelectorAll<HTMLElement>('[id].gaze-doc-heading, [id].gaze-sub-heading') ||
      [],
  )
  activeHeading.value = doc.value?.outline[0]?.id
  updateHeading()
  window.addEventListener('scroll', updateHeading, { passive: true })
  desktop.addEventListener('change', onWidth)
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateHeading)
  desktop.removeEventListener('change', onWidth)
})
</script>

<template>
  <main v-if="doc && guide" id="main" class="gaze-page shell">
    <div class="gaze-doc-title">
      <div class="gaze-breadcrumb">
        <BookOpen :size="15" /> Gaze <span>/</span> 文档 <span>/</span>
        {{ gazeGuideGroups.find((group) => group.id === guide.group)?.label }}
      </div>
      <div class="gaze-title-row">
        <div>
          <h1>{{ doc.title }}</h1>
          <p class="gaze-lead">{{ guide.description }}</p>
        </div>
        <a
          class="gaze-source"
          :href="`${gazeRepoUrl}/blob/main/docs/src/guide/${guide.id}.md`"
          target="_blank"
          rel="noopener noreferrer"
          >在 GitHub 查看原文 <ExternalLink :size="14"
        /></a>
      </div>
    </div>
    <div class="gaze-doc-layout">
      <aside class="gaze-sidebar" @keydown="closeMenu">
        <button
          ref="menuButton"
          class="gaze-mobile-nav"
          :aria-expanded="navVisible"
          aria-controls="gaze-directory"
          @click="menuOpen = !menuOpen"
        >
          <List :size="17" />文档目录<ChevronDown :size="16" :class="{ rotated: menuOpen }" />
        </button>
        <div id="gaze-directory" v-show="navVisible" :inert="!navVisible">
          <label class="gaze-search"
            ><Search :size="15" /><input
              v-model="query"
              type="search"
              placeholder="搜索文档内容…"
              aria-label="搜索文档" /><button
              v-if="query"
              aria-label="清空搜索"
              @click="query = ''"
            >
              <X :size="14" /></button
          ></label>
          <p v-if="query" class="gaze-search-count" role="status">
            {{
              results.length
                ? `找到 ${results.length} 篇相关文档`
                : '没有找到相关内容，换个关键词试试。'
            }}
          </p>
          <nav aria-label="Gaze 文档目录">
            <template v-if="query">
              <div class="gaze-nav-group">
                <p>搜索结果</p>
                <a
                  v-for="item in results"
                  :key="item.id"
                  :href="gazeGuidePath(item.id)"
                  :aria-current="item.id === guide.id ? 'page' : undefined"
                  @click="menuOpen = false"
                  >{{ item.title }}</a
                >
              </div>
            </template>
            <template v-else>
              <div v-for="group in gazeGuideGroups" :key="group.id" class="gaze-nav-group">
                <p>{{ group.label }}</p>
                <a
                  v-for="item in gazeGuides.filter((entry) => entry.group === group.id)"
                  :key="item.id"
                  :href="gazeGuidePath(item.id)"
                  :aria-current="item.id === guide.id ? 'page' : undefined"
                  @click="menuOpen = false"
                  >{{ item.title }}</a
                >
              </div>
            </template>
          </nav>
        </div>
      </aside>
      <article ref="article" class="gaze-doc">
        <BlockList :blocks="doc.intro" />
        <section v-for="section in doc.sections" :key="section.id" class="gaze-doc-section">
          <p class="gaze-doc-section-kicker">
            {{ gazeGuideGroups.find((group) => group.id === guide.group)?.label }}
          </p>
          <h2 :id="section.id" class="gaze-doc-heading" tabindex="-1">{{ section.title }}</h2>
          <BlockList :blocks="section.blocks" />
        </section>
        <nav class="gaze-doc-nav" aria-label="文档翻页">
          <a v-if="neighbors.prev" :href="gazeGuidePath(neighbors.prev.id)">
            <span><ArrowLeft :size="14" />上一篇</span><b>{{ neighbors.prev.title }}</b>
          </a>
          <a v-if="neighbors.next" :href="gazeGuidePath(neighbors.next.id)" class="next">
            <span>下一篇<ArrowRight :size="14" /></span><b>{{ neighbors.next.title }}</b>
          </a>
        </nav>
        <div class="gaze-doc-bottom">
          <CircleHelp :size="21" />
          <div>
            <b>没有解决你的问题？</b>
            <p>到 GitHub 提交问题，附上复现步骤与脱敏后的错误信息。</p>
          </div>
          <a :href="`${gazeRepoUrl}/issues`" target="_blank" rel="noopener noreferrer"
            >反馈问题 <ArrowRight :size="16"
          /></a>
        </div>
      </article>
    </div>
  </main>
</template>

<style scoped>
.gaze-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}
.gaze-source {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  font-size: 12px;
  color: var(--muted);
  padding-block: 12px;
  flex-shrink: 0;
}
.gaze-source:hover {
  color: var(--blue);
}
@media (max-width: 760px) {
  .gaze-title-row {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
