<script setup lang="ts">
import { computed } from 'vue'
import { ArrowUpRight, Database, Server, ShieldCheck } from 'lucide-vue-next'
import type { Project } from '../content'

const props = withDefaults(
  defineProps<{
    project: Project
    heading?: 'h2' | 'h3'
  }>(),
  { heading: 'h3' },
)

const icons = { database: Database, server: Server, shield: ShieldCheck }
const youzaiLogo = { file: 'logocircle.webp', width: 800, height: 800 }
const art = computed(
  () => props.project.image ?? (props.project.icon === 'youzai' ? youzaiLogo : undefined),
)
const badgeImage = computed(() => (props.project.icon === 'youzai' ? youzaiLogo : art.value))
const badgeIcon = computed(() => {
  const icon = props.project.icon
  return icon && icon !== 'youzai' ? icons[icon] : undefined
})
const asset = (name: string) => `/images/${name}`
</script>

<template>
  <a
    :href="project.url"
    :target="project.url.startsWith('/') ? undefined : '_blank'"
    rel="noopener noreferrer"
    class="project-card"
    :class="`project-${project.id}`"
    :aria-label="`${project.title}，${project.role}，${project.link}${project.url.startsWith('/') ? '' : '（在新标签页打开）'}`"
    :aria-describedby="`project-desc-${project.id}`"
  >
    <div class="project-top">
      <div class="project-icon" aria-hidden="true">
        <component v-if="badgeIcon" :is="badgeIcon" :size="26" :stroke-width="1.5" />
        <img
          v-else-if="badgeImage"
          :src="asset(badgeImage.file)"
          alt=""
          width="32"
          height="32"
          loading="lazy"
          decoding="async"
        />
      </div>
      <span>{{ project.number }} <ArrowUpRight :size="20" /></span>
    </div>
    <div v-if="project.id === 'core' && art" class="voxel-art" aria-hidden="true">
      <img
        :src="asset(art.file)"
        alt=""
        :width="art.width"
        :height="art.height"
        loading="lazy"
        decoding="async"
      />
    </div>
    <div v-else-if="project.id === 'web' && art" class="browser-art" aria-hidden="true">
      <div><i></i><i></i><i></i><span>mcyzw.top</span></div>
      <img
        :src="asset(art.file)"
        alt=""
        :width="art.width"
        :height="art.height"
        loading="lazy"
        decoding="async"
      />
    </div>
    <div
      v-else
      class="project-logo-art"
      :class="{ 'project-logo-art--large': project.icon === 'youzai' || project.id === 'rdp' }"
      aria-hidden="true"
    >
      <img
        v-if="art"
        :src="asset(art.file)"
        alt=""
        :width="art.width"
        :height="art.height"
        loading="lazy"
        decoding="async"
      />
      <component v-else-if="badgeIcon" :is="badgeIcon" :size="128" :stroke-width="1.25" />
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
