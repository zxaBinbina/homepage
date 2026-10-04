<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import SiteHeader from './components/SiteHeader.vue'
import ProjectHeader from './rdp/components/ProjectHeader.vue'
import './rdp/style.css'
import { navigateInternalLink } from './router'
const route = useRoute()
const personal = computed(() => route.name === 'home' || route.name === 'directory')
const project = computed(
  () => route.name === 'rdp' || route.name === 'wiki' || route.name === 'downloads',
)
onMounted(() => document.addEventListener('click', navigateInternalLink))
onBeforeUnmount(() => document.removeEventListener('click', navigateInternalLink))
</script>
<template>
  <a class="skip-link" href="#main">跳至内容</a>
  <div class="app-header-transition" :class="{ 'is-project': project }">
    <Transition name="header-swap">
      <div v-if="personal" class="header-layer" key="personal-header">
        <SiteHeader :home="route.name === 'home'" />
      </div>
      <div v-else class="header-layer" key="project-header">
        <ProjectHeader
          :view="route.name === 'wiki' ? 'wiki' : route.name === 'downloads' ? 'downloads' : 'rdp'"
        />
      </div>
    </Transition>
  </div>
  <RouterView />
</template>
