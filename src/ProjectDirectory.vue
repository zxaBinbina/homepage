<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowUpRight, Search, X } from 'lucide-vue-next'
import SiteHeader from './components/SiteHeader.vue'
import { profile, projects } from './content'
const query = ref('')
const matches = computed(() => {
  const term = query.value.trim().toLocaleLowerCase()
  return projects.filter((project) =>
    [project.title, project.description, ...project.tags]
      .join(' ')
      .toLocaleLowerCase()
      .includes(term),
  )
})
</script>

<template>
  <a class="skip-link" href="#main">跳至项目列表</a>
  <SiteHeader />
  <main id="main" class="directory-main shell">
    <section class="directory-intro">
      <p class="overline">PROJECTS / {{ projects.length.toString().padStart(2, '0') }}</p>
      <h1>做出来，也分享出来。</h1>
      <p>
        从方块世界到日常工具，看看我已公开的项目。<br />在这里了解它们的用途，找到官网、源码与使用入口。
      </p>
    </section>
    <div class="directory-toolbar">
      <p role="status" aria-live="polite">
        {{ query.trim() ? `找到 ${matches.length} 个项目` : `全部 ${projects.length} 个项目` }}
      </p>
      <div class="directory-search">
        <Search :size="17" aria-hidden="true" />
        <input
          v-model="query"
          type="search"
          aria-label="搜索项目"
          placeholder="搜索项目、用途或技术栈"
          @keydown.esc="query = ''"
        />
        <button v-if="query" type="button" aria-label="清空搜索" @click="query = ''">
          <X :size="16" />
        </button>
      </div>
    </div>
    <div v-if="matches.length" class="directory-grid">
      <a
        v-for="project in matches"
        :key="project.id"
        class="directory-card"
        :href="project.url"
        :target="project.url.startsWith('/') ? undefined : '_blank'"
        rel="noopener noreferrer"
      >
        <div class="directory-card-top">
          <img
            :src="`/images/${project.image}`"
            alt=""
            width="96"
            height="96"
            loading="lazy"
            :class="{ 'directory-pixel': project.id === 'core' }"
          /><span>{{ project.number }} <ArrowUpRight :size="19" /></span>
        </div>
        <p class="directory-subtitle">{{ project.subtitle }}</p>
        <h2>{{ project.title }}</h2>
        <p class="directory-description">{{ project.description }}</p>
        <div class="directory-card-bottom">
          <div class="tags">
            <span v-for="tag in project.tags" :key="tag">{{ tag }}</span>
          </div>
          <span class="directory-visit">{{ project.link }} <ArrowUpRight :size="15" /></span>
        </div>
      </a>
    </div>
    <div v-else class="directory-empty">
      <h2>暂时没有匹配的项目</h2>
      <p>换个名称或技术关键词试试。</p>
      <button type="button" @click="query = ''">查看全部项目</button>
    </div>
    <p class="directory-more">
      更多代码与实验，放在
      <a :href="`${profile.github}?tab=repositories`" target="_blank" rel="noopener noreferrer"
        >GitHub 仓库 <ArrowUpRight :size="14" /></a
      >。
    </p>
  </main>
  <footer class="shell footer">
    <a class="brand" href="/">a彬彬a<span class="brand-dot">.</span></a>
    <div class="footer-info">
      <p>© {{ new Date().getFullYear() }} zxabinbina · 用代码与热爱构筑</p>
      <a href="https://icp.gov.moe/?keyword=20264016" target="_blank" rel="noopener noreferrer"
        >萌ICP备20264016号</a
      >
    </div>
    <a href="#top">回到顶部 ↑</a>
  </footer>
</template>
