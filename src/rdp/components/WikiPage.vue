<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount, watch } from 'vue'
import {
  ArrowDown,
  ArrowRight,
  BookOpen,
  ChevronDown,
  Code2,
  ExternalLink,
  List,
  Search,
  Server,
  ShieldCheck,
  Wrench,
  X,
} from 'lucide-vue-next'
import content from 'virtual:rdp-wiki'
import agentPrompt from '../../../docs/rdp-agent-deploy.md?raw'
import WikiCodeBlock from './WikiCodeBlock.vue'
import '../wiki.css'
const article = ref<HTMLElement>()
const toc = ref<HTMLElement>()
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)')
const agentOpen = ref(false)
const query = ref('')
const active = ref(content.sections[0]?.id)
const menuOpen = ref(false)
const menuButton = ref<HTMLButtonElement>()
const desktop = matchMedia('(min-width: 761px)')
const wide = ref(desktop.matches)
const tocVisible = computed(() => wide.value || menuOpen.value)
const groups = ['开始部署', '使用与维护', '了解项目']
const results = computed(() =>
  content.sections.filter((section) =>
    section.search.toLocaleLowerCase().includes(query.value.trim().toLocaleLowerCase()),
  ),
)
function keepActiveVisible() {
  const container = toc.value
  if (!wide.value || !container) return
  const link = container.querySelector<HTMLElement>('a[aria-current="location"]')
  if (!link) return
  const bounds = container.getBoundingClientRect()
  const item = link.getBoundingClientRect()
  if (item.top >= bounds.top + 16 && item.bottom <= bounds.bottom - 16) return
  // Scroll only the directory; scrollIntoView would also move the document.
  container.scrollTo({
    top: container.scrollTop + item.top - bounds.top - (container.clientHeight - item.height) / 2,
    behavior: reducedMotion.matches ? 'instant' : 'smooth',
  })
}
watch([active, wide, results], keepActiveVisible, { flush: 'post' })
let headings: HTMLElement[] = []
function updateSection() {
  let current = headings[0]
  const threshold = (menuButton.value?.getBoundingClientRect().bottom || 0) > 110 ? 185 : 160
  for (const heading of headings)
    if (heading.getBoundingClientRect().top <= threshold) current = heading
  active.value = current?.id
}
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
onMounted(() => {
  headings = Array.from(article.value?.querySelectorAll<HTMLElement>('.wiki-section-heading') || [])
  updateSection()
  window.addEventListener('scroll', updateSection, { passive: true })
  desktop.addEventListener('change', onWidth)
  window.addEventListener('resize', keepActiveVisible)
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateSection)
  desktop.removeEventListener('change', onWidth)
  window.removeEventListener('resize', keepActiveVisible)
})
</script>
<template>
  <main id="main" class="rdp-page shell wiki-page">
    <div class="rdp-wiki-title">
      <div class="wiki-breadcrumb"><BookOpen :size="15" /> RDP Access Auth <span>/</span> WIKI</div>
      <div class="wiki-title-row">
        <div>
          <h1>部署与使用<span>指南。</span></h1>
          <p class="rdp-lead">从第一条命令，到一次安心的远程连接。</p>
        </div>
        <a
          class="wiki-source"
          href="https://github.com/zxaBinbina/rdp-access-auth/blob/main/readme.md"
          >在 GitHub 查看文档 <ExternalLink :size="14"
        /></a>
      </div>
      <div class="wiki-start-grid">
        <a href="#section-3" @click="menuOpen = false"
          ><Server :size="21" />
          <div><b>部署前准备</b><span>Linux、域名与远程桌面</span></div>
          <ArrowRight :size="17"
        /></a>
        <a href="#deployment" @click="menuOpen = false"
          ><Code2 :size="21" />
          <div><b>六步完成部署</b><span>直接从源码开始，无需发行版</span></div>
          <ArrowRight :size="17"
        /></a>
        <a href="#section-11" @click="menuOpen = false"
          ><Wrench :size="21" />
          <div><b>遇到连接问题</b><span>日常维护与常见故障排查</span></div>
          <ArrowRight :size="17"
        /></a>
      </div>
    </div>
    <div class="rdp-wiki-layout">
      <aside ref="toc" class="rdp-toc" @keydown="closeMenu">
        <button
          ref="menuButton"
          class="wiki-mobile-toc"
          :aria-expanded="tocVisible"
          aria-controls="wiki-directory"
          @click="menuOpen = !menuOpen"
        >
          <List :size="17" />文档目录<ChevronDown :size="16" :class="{ rotated: menuOpen }" />
        </button>
        <div id="wiki-directory" v-show="tocVisible" :inert="!tocVisible">
          <label class="wiki-search"
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
          <p v-if="query" class="wiki-search-count" role="status">
            {{
              results.length
                ? `找到 ${results.length} 个相关章节`
                : '没有找到相关内容，试试“域名”或“密码”。'
            }}
          </p>
          <nav aria-label="Wiki 目录">
            <div v-for="group in groups" :key="group" class="wiki-nav-group">
              <template v-if="results.some((section) => section.group === group)"
                ><p>{{ group }}</p>
                <a
                  v-for="section in results.filter((section) => section.group === group)"
                  :key="section.id"
                  :href="`#${section.id}`"
                  :aria-current="active === section.id ? 'location' : undefined"
                  :class="{ 'wiki-step-link': section.step }"
                  @click="menuOpen = false"
                  ><span v-if="section.step" class="wiki-nav-number">{{ section.step }}</span
                  >{{ section.step ? section.title.replace(/^\d+\. /, '') : section.title }}</a
                ></template
              >
            </div>
          </nav>
        </div>
      </aside>
      <article ref="article" class="rdp-doc">
        <div class="wiki-intro-note">
          <ShieldCheck :size="20" />
          <div>
            <b>在自己的主机上，搭建认证入口。</b>
            <p>按顺序完成准备与六步部署。文中的域名、端口和隧道 ID 均为示例，请替换为自己的值。</p>
          </div>
        </div>
        <details
          class="wiki-agent"
          :open="agentOpen"
          @toggle="agentOpen = ($event.target as HTMLDetailsElement).open"
        >
          <summary>
            <Code2 :size="20" /><span
              ><b>交给 Agent 部署</b
              ><small>复制提示词，填写环境参数，让你的部署助手接着做。</small></span
            ><ChevronDown :size="18" />
          </summary>
          <div class="wiki-agent-body">
            <p>
              适用于有终端操作能力的 Agent 工具。先替换尖括号中的参数，密码与 Token
              在服务器终端安全填写。
            </p>
            <WikiCodeBlock :code="agentPrompt" language="text" copy-label="复制部署提示词" />
          </div>
        </details>
        <section
          v-for="section in content.sections"
          :key="section.id"
          class="wiki-section"
          :class="{ 'wiki-deploy-step': section.step }"
        >
          <header class="wiki-section-header">
            <span v-if="section.step" class="wiki-step-number">{{
              section.step.padStart(2, '0')
            }}</span>
            <div>
              <p class="wiki-section-kicker">
                {{ section.step ? `部署步骤 ${section.step} · 共 6 步` : section.group }}
              </p>
              <h2 :id="section.id" class="wiki-section-heading" tabindex="-1">
                {{ section.step ? section.title.replace(/^\d+\. /, '') : section.title }}
              </h2>
            </div>
          </header>
          <template v-for="(block, index) in section.blocks" :key="index">
            <div v-if="block.type === 'html'" class="wiki-prose" v-html="block.html"></div>
            <WikiCodeBlock
              v-else-if="block.type === 'code'"
              :code="block.code"
              :language="block.language"
            />
            <div v-else class="wiki-architecture">
              <div>
                <b>网页认证</b>
                <p>浏览器 → Cloudflare Tunnel</p>
                <ArrowDown :size="16" />
                <p>本机认证服务 → SakuraFrp 授权 API</p>
              </div>
              <div>
                <b>远程连接</b>
                <p>RDP 客户端 → SakuraFrp TCP 准入</p>
                <ArrowDown :size="16" />
                <p>现有远程桌面服务</p>
              </div>
            </div>
          </template>
        </section>
        <div class="wiki-bottom">
          <BookOpen :size="21" />
          <div>
            <b>文档没能解决你的问题？</b>
            <p>带上复现步骤与脱敏后的错误信息，到仓库反馈。</p>
          </div>
          <a href="https://github.com/zxaBinbina/rdp-access-auth/issues"
            >反馈问题 <ArrowRight :size="16"
          /></a>
        </div>
      </article>
    </div>
  </main>
</template>
