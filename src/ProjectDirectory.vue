<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount, type ObjectDirective } from 'vue'
import { ArrowUpRight, Search, X } from 'lucide-vue-next'
import ProjectCard from './components/ProjectCard.vue'
import { profile, projects, projectCatalog } from './content'
import SiteFooter from './components/SiteFooter.vue'

const motion = matchMedia('(prefers-reduced-motion: reduce)')
const animations = new Map<Element, Animation>()
const revealObserver: IntersectionObserver | undefined =
  'IntersectionObserver' in window && 'animate' in Element.prototype
    ? new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (!entry.isIntersecting) continue
            revealObserver?.unobserve(entry.target)
            const animation = animations.get(entry.target)
            if (motion.matches) animation?.cancel()
            else animation?.play()
          }
        },
        { threshold: 0.08 },
      )
    : undefined

// Vue mounts new cards after filtering, so each new result is observed as well.
const vReveal: ObjectDirective<HTMLElement> = {
  mounted(element) {
    if (!revealObserver || motion.matches) return
    const style = getComputedStyle(element)
    // Hold the first animation frame before paint, including while waiting for the observer.
    const animation = element.animate(
      [
        { opacity: 0, translate: '0 20px' },
        { opacity: 1, translate: '0 0' },
      ],
      {
        duration: 650,
        delay: parseFloat(style.getPropertyValue('--reveal-delay')) || 0,
        easing: style.getPropertyValue('--motion-ease').trim(),
        fill: 'backwards',
      },
    )
    animation.pause()
    animation.currentTime = 0
    animations.set(element, animation)
    animation.finished.catch(() => {}).finally(() => animations.delete(element))
    revealObserver.observe(element)
  },
  unmounted(element) {
    revealObserver?.unobserve(element)
    animations.get(element)?.cancel()
    animations.delete(element)
  },
}
function stopAnimations() {
  for (const animation of animations.values()) animation.cancel()
  animations.clear()
}
onMounted(() => motion.addEventListener('change', stopAnimations))
onBeforeUnmount(() => {
  revealObserver?.disconnect()
  stopAnimations()
  motion.removeEventListener('change', stopAnimations)
})

const query = ref('')
const matches = computed(() => {
  const term = query.value.trim().toLocaleLowerCase()
  return projects.filter((project) =>
    [project.title, project.description, project.repository, project.role, ...project.tags]
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
      <h1>做出来，<span>也分享出来。</span></h1>
      <p>
        从方块世界到日常工具，看看我和悠哉世界团队已公开的项目。<br />在这里了解它们的用途，找到官网、源码与使用入口。
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
          placeholder="搜索项目、账号或技术栈"
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
        v-reveal
        :project="project"
        heading="h2"
        class="reveal"
        :style="{ '--reveal-delay': `${(index % 2) * 90}ms` }"
      />
    </div>
    <div v-else v-reveal class="directory-empty">
      <h2>暂时没有匹配的项目</h2>
      <p>换个名称或技术关键词试试。</p>
      <button type="button" @click="query = ''">查看全部项目</button>
    </div>
    <p v-reveal class="directory-more">
      项目来自
      <a :href="`${profile.github}?tab=repositories`" target="_blank" rel="noopener noreferrer"
        >个人 GitHub <ArrowUpRight :size="14"
      /></a>
      与
      <a
        :href="`${projectCatalog.organization}/repositories`"
        target="_blank"
        rel="noopener noreferrer"
        >悠哉世界团队 <ArrowUpRight :size="14" /></a
      >。
    </p>
  </main>
  <SiteFooter />
</template>
