<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import content from 'virtual:rdp-wiki'
const article = ref<HTMLElement>()
const active = ref(content.toc[0]?.id)
let headings: HTMLElement[] = []
function updateSection() {
  let current = headings[0]
  for (const heading of headings) if (heading.getBoundingClientRect().top <= 160) current = heading
  active.value = current?.id
}
onMounted(() => {
  headings = Array.from(article.value?.querySelectorAll<HTMLElement>('h2, h3, h4') || [])
  // The anchor target becomes available after Vue mounts the Markdown content.
  if (location.hash)
    document.getElementById(location.hash.slice(1))?.scrollIntoView({ behavior: 'instant' })
  updateSection()
  window.addEventListener('scroll', updateSection, { passive: true })
})
onBeforeUnmount(() => window.removeEventListener('scroll', updateSection))
</script>
<template>
  <main id="main" class="rdp-page shell">
    <div class="rdp-wiki-title">
      <p class="rdp-eyebrow">DOCUMENTATION / WIKI</p>
      <h1>把部署的每一步，<span>说清楚。</span></h1>
      <p class="rdp-lead">从环境准备到第一次远程连接，以及之后的维护与排错。</p>
    </div>
    <div class="rdp-wiki-layout">
      <aside class="rdp-toc">
        <nav aria-label="Wiki 目录">
          <p class="rdp-eyebrow">本页目录</p>
          <a
            v-for="item in content.toc"
            :key="item.id"
            :href="`#${item.id}`"
            :aria-current="active === item.id ? 'location' : undefined"
            >{{ item.text }}</a
          >
        </nav>
        <a
          class="rdp-text-link"
          href="https://github.com/zxaBinbina/rdp-access-auth/blob/main/readme.md"
          >查看上游文档 ↗</a
        >
      </aside>
      <article ref="article" class="rdp-doc">
        <div class="rdp-note">
          <b>源码部署，无需生成发行版</b>
          <p>
            以下指南基于项目公开 README 与部署模板整理。域名、端口和隧道 ID
            均为示例；升级前请核对上游变更。官网本身不提供认证服务。
          </p>
        </div>
        <div v-html="content.html"></div>
      </article>
    </div>
  </main>
</template>
