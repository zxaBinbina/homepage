<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import { pageForPath } from './pages'
const page = pageForPath(location.pathname)
const ProjectDirectory = defineAsyncComponent(() => import('./ProjectDirectory.vue'))
const HomePage = defineAsyncComponent(() => import('./HomePage.vue'))
const ProjectPage = defineAsyncComponent(() => import('./rdp/App.vue'))
</script>
<template>
  <HomePage v-if="page === 'home'" />
  <ProjectDirectory v-else-if="page === 'directory'" />
  <ProjectPage v-else :wiki="page === 'wiki'" />
</template>
