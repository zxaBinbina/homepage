<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Github, Menu, X } from 'lucide-vue-next'
import { profile } from '../content'
import ThemeToggle from './ThemeToggle.vue'
import MusicDialog from './MusicDialog.vue'
import NeteaseIcon from './NeteaseIcon.vue'
const props = withDefaults(defineProps<{ home?: boolean; active?: string }>(), {
  home: false,
  active: 'projects',
})
const asset = (name: string) => `${import.meta.env.BASE_URL}images/${name}`
const menuOpen = ref(false)
const musicTrigger = ref<HTMLButtonElement>()
const musicOpen = ref(false)
const musicPlaying = ref(false)
const musicTrack = ref('')
const nav = [
  { id: 'home', label: '首页' },
  { id: 'about', label: '关于' },
  { id: 'projects', label: '项目' },
  { id: 'world', label: '悠哉世界' },
]
function navHref(id: string) {
  return id === 'projects' ? '/project/' : `${props.home ? '' : '/'}#${id}`
}
function isActive(id: string) {
  return props.active === id && (id !== 'projects' || !props.home)
}
function openMusic() {
  menuOpen.value = false
}
function onKey(event: KeyboardEvent) {
  if (event.key === 'Escape') menuOpen.value = false
}
onMounted(() => document.addEventListener('keydown', onKey))
onBeforeUnmount(() => document.removeEventListener('keydown', onKey))
</script>
<template>
  <header class="header">
    <a :href="home ? '#home' : '/'" class="brand" @click="menuOpen = false"
      ><img :src="asset('avatar.png')" alt="" width="30" height="30" /><span
        >{{ profile.name }}<span class="brand-dot">.</span></span
      ></a
    >
    <nav class="desktop-nav" aria-label="主导航">
      <a
        v-for="item in nav"
        :key="item.id"
        :href="navHref(item.id)"
        :class="{ active: isActive(item.id) }"
        :aria-current="isActive(item.id) ? (home ? 'location' : 'page') : undefined"
        >{{ item.label }}</a
      >
    </nav>
    <div class="header-actions">
      <ThemeToggle />
      <button
        ref="musicTrigger"
        class="icon-button music-toggle"
        :class="{ 'is-playing': musicPlaying }"
        aria-label="打开网易云音乐播放器"
        aria-haspopup="dialog"
        :aria-expanded="musicOpen"
        aria-controls="music-popover"
        popovertarget="music-popover"
        :title="musicPlaying && musicTrack ? `正在播放：${musicTrack}` : '网易云音乐'"
        @click="openMusic"
      >
        <NeteaseIcon /></button
      ><a
        :href="profile.github"
        target="_blank"
        rel="noopener noreferrer"
        class="icon-button"
        aria-label="GitHub"
        title="GitHub"
        ><Github :size="19" /></a
      ><span class="nav-divider"></span
      ><a :href="navHref('contact')" class="nav-contact">打个招呼</a
      ><button
        class="icon-button mobile-toggle"
        :aria-expanded="menuOpen"
        aria-controls="mobile-nav"
        :aria-label="menuOpen ? '关闭菜单' : '打开菜单'"
        :title="menuOpen ? '关闭菜单' : '打开菜单'"
        @click="menuOpen = !menuOpen"
      >
        <X v-if="menuOpen" :size="21" /><Menu v-else :size="21" />
      </button>
    </div>
    <Transition
      @before-leave="(el) => el.setAttribute('inert', '')"
      @before-enter="(el) => el.removeAttribute('inert')"
      name="mobile-menu"
    >
      <nav
        v-if="menuOpen"
        :inert="!menuOpen"
        id="mobile-nav"
        class="mobile-nav"
        aria-label="移动导航"
      >
        <a
          v-for="item in [...nav, { id: 'contact', label: '联系我' }]"
          :key="item.id"
          :href="navHref(item.id)"
          @click="menuOpen = false"
          >{{ item.label }}</a
        >
      </nav>
    </Transition>
  </header>
  <MusicDialog
    :anchor="musicTrigger"
    @playing="musicPlaying = $event"
    @track="musicTrack = $event"
    @opened="musicOpen = $event"
  />
</template>
