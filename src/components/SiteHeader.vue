<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Github, Menu, Rocket, X } from 'lucide-vue-next'
import { profile } from '../content'
import ColorPalettePicker from './ColorPalettePicker.vue'
import ThemeToggle from './ThemeToggle.vue'
import MusicDialog from './MusicDialog.vue'
import NeteaseIcon from './NeteaseIcon.vue'
const props = withDefaults(
  defineProps<{
    home?: boolean
    myriad?: boolean
    active?: 'home' | 'projects' | 'tools' | 'games' | 'books' | 'myriad' | null
  }>(),
  {
    home: false,
    active: 'home',
  },
)
const asset = (name: string) => `/images/${name}`
const menuOpen = ref(false)
const menuToggle = ref<HTMLButtonElement>()
const mobileNav = ref<HTMLElement>()
const musicTrigger = ref<HTMLButtonElement>()
const musicOpen = ref(false)
const musicPlaying = ref(false)
const musicTrack = ref('')
/* UI-FIX P0-4 · 站内核心栏目在前，聚合入口「万象导航」置末并由 CSS 弱化。 */
const nav = [
  { id: 'home', label: '首页' },
  { id: 'projects', label: '项目' },
  { id: 'tools', label: '工具' },
  { id: 'games', label: '游戏' },
  { id: 'books', label: '书架' },
  { id: 'world', label: '悠哉世界' },
  { id: 'myriad', label: '万象导航' },
]
/* UI-FIX P0-4 · 移动菜单补回「关于」，保持与首屏编号栏目的对应。 */
const mobileItems = [
  nav[0],
  { id: 'about', label: '关于' },
  ...nav.slice(1),
  { id: 'contact', label: '联系我' },
]
function navHref(id: string) {
  if (id === 'home') return '/'
  /* UI-FIX P0-4 · 「悠哉世界」统一指向站内介绍区块，官网入口留在该区块内。 */
  if (id === 'world') return '/#world'
  if (id === 'tools') return '/tool'
  if (id === 'games') return '/game'
  if (id === 'books') return '/book'
  if (id === 'myriad') return '/myriad'
  return id === 'projects' ? '/project' : `${props.home ? '' : '/'}#${id}`
}
function isActive(id: string) {
  return id === props.active
}
function openMusic() {
  menuOpen.value = false
}
/* UI-FIX P2-4 · 打开菜单后把焦点送入首项，便于键盘与读屏继续操作。 */
function toggleMenu() {
  menuOpen.value = !menuOpen.value
  if (menuOpen.value) {
    nextTick(() => mobileNav.value?.querySelector<HTMLAnchorElement>('a')?.focus())
  }
}
/* UI-FIX P2-4 · 点击菜单与开关以外的区域时收起菜单。 */
function onPointerDown(event: PointerEvent) {
  if (!menuOpen.value || !(event.target instanceof Node)) return
  if (menuToggle.value?.contains(event.target) || mobileNav.value?.contains(event.target)) return
  menuOpen.value = false
}
function onKey(event: KeyboardEvent) {
  if (event.key === 'Escape' && menuOpen.value) {
    menuOpen.value = false
    menuToggle.value?.focus()
  }
}
onMounted(() => {
  document.addEventListener('keydown', onKey)
  document.addEventListener('pointerdown', onPointerDown)
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKey)
  document.removeEventListener('pointerdown', onPointerDown)
})
</script>
<template>
  <header class="header">
    <a href="/" class="brand" :aria-label="`${profile.name}的首页`" @click="menuOpen = false"
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
        :aria-current="isActive(item.id) ? 'page' : undefined"
        >{{ item.label }}</a
      >
    </nav>
    <div class="header-actions">
      <a
        class="nav-travel"
        href="https://travel.moe/go.html?travel=on"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="异次元之旅（在新标签页打开）"
        title="去萌友的星球逛逛（在新标签页打开）"
        @click="menuOpen = false"
      >
        <span class="nav-travel-icon" aria-hidden="true"><Rocket :size="16" /></span>
        <span class="nav-travel-label">异次元之旅</span>
      </a>
      <ColorPalettePicker />
      <ThemeToggle />
      <button
        v-if="!myriad"
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
        ref="menuToggle"
        class="icon-button mobile-toggle"
        :aria-expanded="menuOpen"
        aria-controls="mobile-nav"
        :aria-label="menuOpen ? '关闭菜单' : '打开菜单'"
        :title="menuOpen ? '关闭菜单' : '打开菜单'"
        @click="toggleMenu"
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
        ref="mobileNav"
        :inert="!menuOpen"
        id="mobile-nav"
        class="mobile-nav"
        aria-label="移动导航"
      >
        <!-- UI-FIX P0-4 · 移动菜单补回「关于」；打开时焦点由脚本送入首项。 -->
        <a
          v-for="item in mobileItems"
          :key="item.id"
          :href="navHref(item.id)"
          :aria-current="isActive(item.id) ? 'page' : undefined"
          @click="menuOpen = false"
          >{{ item.label }}</a
        >
      </nav>
    </Transition>
  </header>
  <MusicDialog
    :anchor="musicTrigger"
    :suspended="myriad"
    @playing="musicPlaying = $event"
    @track="musicTrack = $event"
    @opened="musicOpen = $event"
  />
</template>
