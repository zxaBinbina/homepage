<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import SiteHeader from './components/SiteHeader.vue'
import ProjectHeader from './rdp/components/ProjectHeader.vue'
import './rdp/style.css'
import { navigateInternalLink } from './router'
import { isProjectPage } from './pages'
const route = useRoute()
const project = computed(() => isProjectPage(route.name))
const personal = computed(() => !project.value)
onMounted(() => document.addEventListener('click', navigateInternalLink))
onBeforeUnmount(() => document.removeEventListener('click', navigateInternalLink))
</script>
<template>
  <a class="skip-link" href="#main">跳至内容</a>
  <div class="app-header-transition" :class="{ 'is-project': project }">
    <Transition name="header-swap">
      <div v-if="personal" class="header-layer" key="personal-header">
        <SiteHeader
          :home="route.name === 'home'"
          :active="
            route.name === 'home' ? 'home' : route.name === 'directory' ? 'projects' : 'tools'
          "
        />
      </div>
      <div v-else class="header-layer" key="project-header">
        <ProjectHeader
          :view="route.name === 'wiki' ? 'wiki' : route.name === 'downloads' ? 'downloads' : 'rdp'"
        />
      </div>
    </Transition>
  </div>
  <RouterView v-slot="{ Component, route: pageRoute }">
    <Transition
      name="page-swap"
      @before-leave="(el) => el.setAttribute('inert', '')"
      @before-enter="(el) => el.removeAttribute('inert')"
    >
      <component :is="Component" :key="isProjectPage(pageRoute.name) ? 'rdp' : pageRoute.name" />
    </Transition>
  </RouterView>
</template>
