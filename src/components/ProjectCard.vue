<script setup lang="ts">
import { ArrowUpRight, Blocks, Globe2, ScanFace, ShieldCheck } from 'lucide-vue-next'
import type { projects } from '../content'

withDefaults(
  defineProps<{
    project: (typeof projects)[number]
    heading?: 'h2' | 'h3'
  }>(),
  { heading: 'h3' },
)

const icons = { blocks: Blocks, globe: Globe2, scan: ScanFace, shield: ShieldCheck }
const asset = (name: string) => `/images/${name}`
</script>

<template>
  <a
    :href="project.url"
    :target="project.url.startsWith('/') ? undefined : '_blank'"
    rel="noopener noreferrer"
    class="project-card"
    :class="`project-${project.id}`"
  >
    <div class="project-top">
      <div class="project-icon">
        <img
          v-if="project.id === 'gaze'"
          :src="asset(project.image)"
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
    <div v-if="project.id === 'rdp'" class="project-logo-art rdp-logo-art" aria-hidden="true">
      <img :src="asset(project.image)" alt="" width="512" height="394" loading="lazy" />
    </div>
    <div v-if="project.id === 'gaze'" class="project-logo-art gaze-logo-art" aria-hidden="true">
      <img :src="asset(project.image)" alt="" width="128" height="128" loading="lazy" />
    </div>
    <div class="project-content">
      <span class="project-role">开发者 <span>·</span> {{ project.subtitle }}</span>
      <component :is="heading">{{ project.title }}</component>
      <p>{{ project.description }}</p>
      <div class="project-bottom">
        <div class="tags">
          <span v-for="tag in project.tags" :key="tag">{{ tag }}</span>
        </div>
        <span class="project-link">{{ project.link }} <ArrowUpRight :size="14" /></span>
      </div>
    </div>
  </a>
</template>
