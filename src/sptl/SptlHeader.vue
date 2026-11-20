<script setup lang="ts">
import { Github } from 'lucide-vue-next'
import ThemePanel from '../components/ThemePanel.vue'
import { sptlProject } from './content'
</script>

<template>
  <header class="sptl-header shell">
    <a class="sptl-brand" href="/projects/SPTL" aria-label="SPTL 官网首页">
      <img src="/images/sptl.png" alt="" width="38" height="38" />
      <span>SPTL</span>
    </a>
    <nav aria-label="SPTL 导航">
      <a class="sptl-install-link" href="/projects/SPTL#install">安装指南</a>
      <div class="sptl-nav-tools">
        <ThemePanel />
        <a
          class="icon-button"
          :href="sptlProject.repository"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="SPTL GitHub 仓库（在新标签页打开）"
          title="GitHub 仓库"
        >
          <Github :size="19" aria-hidden="true" />
        </a>
      </div>
    </nav>
  </header>
</template>

<style scoped>
.sptl-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-xl);
  min-height: 64px;
  border: 1px solid var(--border);
  border-radius: var(--radius-shell);
  background: var(--glass);
  backdrop-filter: blur(24px) saturate(150%);
  box-shadow: 0 8px 24px var(--shadow);
}
.sptl-brand,
nav,
.sptl-nav-tools {
  display: flex;
  align-items: center;
}
.sptl-brand {
  gap: var(--space-sm);
  font-size: var(--text-lg);
  font-weight: 650;
}
.sptl-brand img {
  flex-shrink: 0;
}
nav {
  gap: var(--space-lg);
  font-size: var(--text-sm);
}
nav > a {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
}
.sptl-nav-tools {
  gap: var(--space-xs);
}
@media (max-width: 760px) {
  .sptl-header {
    padding: var(--space-xs) var(--space-md);
    backdrop-filter: blur(16px) saturate(140%);
  }
  nav {
    gap: var(--space-sm);
  }
  .sptl-brand {
    gap: var(--space-xs);
  }
  .sptl-brand img {
    width: 32px;
    height: 32px;
  }
}
@media (max-width: 360px) {
  .sptl-header {
    padding-inline: var(--space-sm);
    gap: var(--space-xs);
  }
  nav {
    gap: var(--space-xs);
  }
  .sptl-install-link {
    font-size: var(--text-xs);
  }
}
</style>
