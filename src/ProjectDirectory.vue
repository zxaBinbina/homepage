<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowUpRight, Search, X } from 'lucide-vue-next'
import ProjectCard from './components/ProjectCard.vue'
import { profile, projects } from './content'
import SiteFooter from './components/SiteFooter.vue'
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
  <main id="main" class="directory-main shell">
    <section class="directory-intro directory-entry">
      <p class="overline">PROJECTS / {{ projects.length.toString().padStart(2, '0') }}</p>
      <h1>做出来，也分享出来。</h1>
      <p>
        从方块世界到日常工具，看看我已公开的项目。<br />在这里了解它们的用途，找到官网、源码与使用入口。
      </p>
    </section>
    <div class="directory-toolbar directory-entry">
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
    <div v-if="matches.length" class="project-grid directory-project-grid">
      <ProjectCard
        v-for="(project, index) in matches"
        :key="project.id"
        :project="project"
        heading="h2"
        class="reveal"
        :style="{ '--reveal-delay': `${(index % 2) * 90}ms` }"
      />
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
  <SiteFooter />
</template>
