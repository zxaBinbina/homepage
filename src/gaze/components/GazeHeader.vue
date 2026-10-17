<script setup lang="ts">
import { Github } from 'lucide-vue-next'
import ThemeToggle from '../../components/ThemeToggle.vue'
defineProps<{ view: 'home' | 'guide' }>()
</script>
<template>
  <header class="gaze-header shell">
    <a class="gaze-brand" href="/projects/gaze"
      ><img class="gaze-mark" src="/images/gaze.svg" alt="" width="38" height="38" />
      <span>Gaze <b>中文</b></span></a
    >
    <nav aria-label="Gaze 导航">
      <a href="/projects/gaze" :aria-current="view === 'home' ? 'page' : undefined">首页</a
      ><a
        href="/projects/gaze/guide/getting-started"
        :aria-current="view === 'guide' ? 'page' : undefined"
        >使用指南</a
      >
      <div class="gaze-nav-tools">
        <ThemeToggle class="gaze-theme" />
        <a
          class="icon-button"
          href="https://github.com/zxaBinbina/gaze-zh"
          aria-label="GitHub 仓库"
          title="GitHub 仓库"
          target="_blank"
          rel="noopener noreferrer"
          ><Github :size="19" aria-hidden="true"
        /></a>
      </div>
    </nav>
  </header>
</template>
