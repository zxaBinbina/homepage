<script setup lang="ts">
import { Github } from 'lucide-vue-next'
import ThemeToggle from '../../components/ThemeToggle.vue'
defineProps<{ view: 'rdp' | 'wiki' | 'downloads' }>()
</script>
<template>
  <header class="rdp-header shell">
    <a class="rdp-brand" href="/projects/rdp-access-auth"
      ><img class="rdp-mark" src="/images/rdp-access-auth.png" alt="" width="38" height="38" />
      <span>RDP <b>Access Auth</b></span></a
    >
    <nav aria-label="项目导航">
      <a href="/projects/rdp-access-auth" :aria-current="view === 'rdp' ? 'page' : undefined"
        >概览</a
      ><a href="/projects/rdp-access-auth/wiki" :aria-current="view === 'wiki' ? 'page' : undefined"
        >Wiki</a
      ><a
        href="/projects/rdp-access-auth/downloads"
        :aria-current="view === 'downloads' ? 'page' : undefined"
        >下载</a
      >
      <div class="rdp-nav-tools">
        <ThemeToggle class="rdp-theme" />
        <a
          class="icon-button"
          href="https://github.com/zxaBinbina/rdp-access-auth"
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
