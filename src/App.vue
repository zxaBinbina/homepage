<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import SiteHeader from './components/SiteHeader.vue'
import ProjectHeader from './rdp/components/ProjectHeader.vue'
import GazeHeader from './gaze/components/GazeHeader.vue'
import AnimatedCursor from './components/AnimatedCursor.vue'
import './rdp/style.css'
import { navigateInternalLink } from './router'
import { isProjectPage, isGazePage } from './pages'
import { isGameId } from './games/catalog'
import { isToolId } from './tools/catalog'
import { isBookPage } from './books/catalog'
const route = useRoute()
const myriad = computed(() => route.name === 'myriad')
const header = ref<HTMLElement>()
const revealed = ref(false)
watch(myriad, () => {
  revealed.value = false
})
function onPointer(event: PointerEvent) {
  if (!myriad.value) return
  const bounds = header.value?.getBoundingClientRect()
  revealed.value =
    event.clientY <= 24 || (revealed.value && !!bounds && event.clientY <= bounds.bottom + 16)
}
onMounted(() => document.addEventListener('pointermove', onPointer, { passive: true }))
onBeforeUnmount(() => document.removeEventListener('pointermove', onPointer))
const project = computed(() => isProjectPage(route.name))
const gaze = computed(() => isGazePage(route.name))
const reading = computed(() => isBookPage(route.name))
// 主页、目录、工具、游戏与书架共用导航；Gaze 与 RDP 子站各用项目导航。
const activeNav = computed(() =>
  myriad.value
    ? 'myriad'
    : route.name === 'home'
      ? 'home'
      : route.name === 'directory'
        ? 'projects'
        : route.name === 'bookshelf' || isBookPage(route.name)
          ? 'books'
          : route.name === 'games' || isGameId(route.name)
            ? 'games'
            : route.name === 'tools' || isToolId(route.name)
              ? 'tools'
              : null,
)
onMounted(() => document.addEventListener('click', navigateInternalLink))
onBeforeUnmount(() => document.removeEventListener('click', navigateInternalLink))
</script>
<template>
  <AnimatedCursor />
  <a class="skip-link" href="#main">跳至内容</a>
  <div
    ref="header"
    class="app-header-transition"
    :class="{
      'is-project': project || gaze,
      'is-reader': reading,
      'is-myriad': myriad,
      'is-revealed': revealed,
    }"
  >
    <Transition name="header-swap">
      <div v-if="!project && !gaze" class="header-layer" key="unified-header">
        <SiteHeader :home="route.name === 'home'" :active="activeNav" :myriad="myriad" />
      </div>
      <div v-else-if="gaze" class="header-layer" key="gaze-header">
        <GazeHeader :view="route.name === 'gaze' ? 'home' : 'guide'" />
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
      <component
        :is="Component"
        :key="
          isProjectPage(pageRoute.name)
            ? 'rdp'
            : isGazePage(pageRoute.name)
              ? 'gaze'
              : pageRoute.name
        "
      />
    </Transition>
  </RouterView>
</template>
