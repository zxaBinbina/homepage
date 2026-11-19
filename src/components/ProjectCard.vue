<script setup lang="ts">
import { ArrowUpRight, Globe2, ScanFace, ShieldCheck } from 'lucide-vue-next'
import type { projects } from '../content'

withDefaults(
  defineProps<{
    project: (typeof projects)[number]
    heading?: 'h2' | 'h3'
  }>(),
  { heading: 'h3' },
)

const icons = { globe: Globe2, scan: ScanFace, shield: ShieldCheck }
const asset = (name: string) => `/images/${name}`
</script>

<template>
  <a
    :href="project.url"
    :target="project.url.startsWith('/') ? undefined : '_blank'"
    rel="noopener noreferrer"
    class="project-card"
    :class="[`project-${project.id}`, { 'project-youzai': project.icon === 'youzai' }]"
    :aria-label="`${project.title}，${project.role}，${project.link}${project.url.startsWith('/') ? '' : '（在新标签页打开）'}`"
    :aria-describedby="`project-desc-${project.id}`"
  >
    <div class="project-top">
      <div class="project-icon">
        <img
          v-if="project.icon === 'youzai' || project.id === 'gaze'"
          :src="asset(project.icon === 'youzai' ? 'logocircle.webp' : project.image)"
          alt=""
          width="32"
          height="32"
          loading="lazy"
        />
        <component
          v-else
          :is="icons[project.icon as keyof typeof icons]"
          :size="26"
          :stroke-width="1.5"
        />
      </div>
      <span>{{ project.number }} <ArrowUpRight :size="20" /></span>
    </div>
    <div v-if="project.id === 'core'" class="voxel-art" aria-hidden="true">
      <img :src="asset(project.image)" alt="" loading="lazy" />
    </div>
    <div v-if="project.id === 'web'" class="browser-art" aria-hidden="true">
      <div><i></i><i></i><i></i><span>mcyzw.top</span></div>
      <img :src="asset(project.image)" alt="" loading="lazy" />
    </div>
    <div
      v-if="project.icon === 'youzai' && !['core', 'web'].includes(project.id)"
      class="project-logo-art"
      aria-hidden="true"
    >
      <img :src="asset('logocircle.webp')" alt="" width="160" height="160" loading="lazy" />
    </div>
    <div v-if="project.id === 'rdp'" class="project-logo-art rdp-logo-art" aria-hidden="true">
      <img :src="asset(project.image)" alt="" width="512" height="394" loading="lazy" />
    </div>
    <div v-if="project.id === 'gaze'" class="project-logo-art gaze-logo-art" aria-hidden="true">
      <img :src="asset(project.image)" alt="" width="128" height="128" loading="lazy" />
    </div>
    <div class="project-content">
      <!-- UI-FIX P1-1 / P1-6 · 项目名上移到图下第一行，角色短句降为标题下辅助行；
           整卡链接改为简短可读名 + aria-describedby 指向描述。 -->
      <component :is="heading">{{ project.title }}</component>
      <span class="project-role">{{ project.role }} <span>·</span> {{ project.subtitle }}</span>
      <p :id="`project-desc-${project.id}`">{{ project.description }}</p>
      <div class="project-bottom">
        <div class="tags">
          <span v-for="tag in project.tags" :key="tag">{{ tag }}</span>
        </div>
        <span class="project-link">{{ project.link }} <ArrowUpRight :size="14" /></span>
      </div>
    </div>
  </a>
</template>
