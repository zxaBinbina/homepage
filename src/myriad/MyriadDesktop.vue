<script setup lang="ts">
import { MyriadApp, type MyriadPlatform } from '@zxabinbina/myriad-ui'
import { createLocalStorageAdapter } from '@zxabinbina/myriad-core'
import '@zxabinbina/myriad-ui/style.css'
import { watch } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'

const emit = defineEmits<{ ready: [] }>()
const router = useRouter()
const theme = useTheme()
const platform: MyriadPlatform = {
  kind: 'web',
  guest: true,
  embedded: true,
  version: '0.1.0',
  repoUrl: 'https://github.com/zxaBinbina/myriad',
  storage: createLocalStorageAdapter('homepage.myriad.visitor.'),
  publicApiBase: import.meta.env.VITE_MYRIAD_PUBLIC_API || 'https://myriad.zxabinbina.cc.cd',
  navigate(url) {
    void router.push(url.pathname + url.search + url.hash)
  },
  theme: {
    get: () => ({ palette: theme.palette.value, theme: theme.mode.value }),
    set(value) {
      if (value.palette !== theme.palette.value) theme.setPalette(value.palette)
      if (value.theme !== theme.mode.value) theme.setThemeMode(value.theme)
    },
    subscribe: (listener) => watch([theme.palette, theme.mode], listener),
  },
}
</script>

<template>
  <MyriadApp :platform="platform" @ready="emit('ready')" />
</template>
