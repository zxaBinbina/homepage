<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import SiteHeader from './components/SiteHeader.vue'
import { navigateInternalLink } from './router'
const route = useRoute()
const personal = computed(() => route.name === 'home' || route.name === 'directory')
onMounted(() => document.addEventListener('click', navigateInternalLink))
onBeforeUnmount(() => document.removeEventListener('click', navigateInternalLink))
</script>
<template>
  <a class="skip-link" href="#main">跳至内容</a>
  <SiteHeader v-if="personal" :home="route.name === 'home'" />
  <RouterView />
</template>
