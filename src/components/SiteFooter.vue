<script setup lang="ts">
import GovBadge from './GovBadge.vue'
withDefaults(defineProps<{ brandLink?: boolean }>(), { brandLink: true })
</script>
<template>
  <footer class="shell footer">
    <component :is="brandLink ? 'a' : 'span'" class="brand" :href="brandLink ? '/' : undefined"
      >a彬彬a<span class="brand-dot">.</span></component
    >
    <div class="footer-info">
      <p>© {{ new Date().getFullYear() }} zxabinbina · 用代码与热爱构筑</p>
      <a href="https://icp.gov.moe/?keyword=20264016" target="_blank" rel="noopener noreferrer"
        ><GovBadge />萌ICP备20264016号</a
      >
    </div>
  </footer>
</template>
