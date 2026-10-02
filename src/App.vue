<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import {
  ArrowUpRight,
  ArrowRight,
  ArrowDown,
  Github,
  MonitorPlay,
  Code2,
  Blocks,
  Globe2,
  ScanFace,
  ShieldCheck,
  Copy,
  Check,
  Menu,
  X,
  Heart,
  Mountain,
  Sparkles,
  Sun,
  Moon,
} from 'lucide-vue-next'
import { profile, projects } from './content'
import MusicDialog from './components/MusicDialog.vue'
import NeteaseIcon from './components/NeteaseIcon.vue'

const asset = (name: string) => `${import.meta.env.BASE_URL}images/${name}`
const menuOpen = ref(false)
const musicTrigger = ref<HTMLButtonElement>()
const musicOpen = ref(false)
const musicPlaying = ref(false)
const musicTrack = ref('')
function openMusic() {
  menuOpen.value = false
}
const active = ref('home')
const light = ref(false)
const copied = ref(false)
const copyMessage = ref('')
const nav = [
  { id: 'home', label: '首页' },
  { id: 'about', label: '关于' },
  { id: 'projects', label: '项目' },
  { id: 'world', label: '悠哉世界' },
]
const icons = { blocks: Blocks, globe: Globe2, scan: ScanFace, shield: ShieldCheck }
let observer: IntersectionObserver | undefined
let revealObserver: IntersectionObserver | undefined
let timer: ReturnType<typeof setTimeout> | undefined
function toggleTheme() {
  light.value = !light.value
  document.documentElement.dataset.theme = light.value ? 'light' : 'dark'
  try {
    localStorage.setItem('homepage-theme', light.value ? 'light' : 'dark')
  } catch {
    /* storage may be unavailable */
  }
}
async function copyAddress() {
  try {
    await navigator.clipboard.writeText(profile.address)
    copied.value = true
    copyMessage.value = '服务器地址已复制'
  } catch {
    copyMessage.value = `请手动复制：${profile.address}`
  }
  clearTimeout(timer)
  timer = setTimeout(() => {
    copied.value = false
    copyMessage.value = ''
  }, 3500)
}
function onKey(event: KeyboardEvent) {
  if (event.key === 'Escape') menuOpen.value = false
}
onMounted(() => {
  try {
    light.value = localStorage.getItem('homepage-theme') === 'light'
  } catch {
    /* keep default */
  }
  document.documentElement.dataset.theme = light.value ? 'light' : 'dark'
  if ('IntersectionObserver' in window) {
    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) if (entry.isIntersecting) active.value = entry.target.id
      },
      { rootMargin: '-15% 0px -55% 0px', threshold: 0 },
    )
    document.querySelectorAll('main > section[id]').forEach((el) => observer?.observe(el))
  }
  if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    revealObserver = new IntersectionObserver(
      (entries) =>
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
            revealObserver?.unobserve(entry.target)
          }
        }),
      { threshold: 0.08 },
    )
    document.querySelectorAll('.reveal').forEach((el) => {
      el.classList.add('will-reveal')
      revealObserver?.observe(el)
    })
  }
  document.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  observer?.disconnect()
  revealObserver?.disconnect()
  clearTimeout(timer)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <a class="skip-link" href="#main">跳至内容</a>
  <header class="header">
    <a href="#home" class="brand" @click="menuOpen = false"
      ><img :src="asset('avatar.png')" alt="" width="30" height="30" /><span
        >{{ profile.name }}<span class="brand-dot">.</span></span
      ></a
    >
    <nav class="desktop-nav" aria-label="主导航">
      <a
        v-for="item in nav"
        :key="item.id"
        :href="`#${item.id}`"
        :class="{ active: active === item.id }"
        :aria-current="active === item.id ? 'location' : undefined"
        >{{ item.label }}</a
      >
    </nav>
    <div class="header-actions">
      <button
        class="icon-button theme-toggle"
        @click="toggleTheme"
        :aria-label="light ? '切换深色主题' : '切换浅色主题'"
        :title="light ? '切换深色主题' : '切换浅色主题'"
      >
        <Moon v-if="light" :size="17" /><Sun v-else :size="17" /></button
      ><button
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
      ><span class="nav-divider"></span><a href="#contact" class="nav-contact">打个招呼</a
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
          :href="`#${item.id}`"
          @click="menuOpen = false"
          >{{ item.label }}</a
        >
      </nav>
    </Transition>
  </header>

  <main id="main">
    <section id="home" class="hero">
      <div class="hero-glow"></div>
      <div class="shell hero-top">
        <div class="eyebrow">
          <span class="status-dot"></span> HELLO, WORLD. I'M Z X A B I N B I N A
        </div>
        <h1>在代码与方块之间，<br /><span>创造一点不一样。</span></h1>
        <p class="hero-description">
          你好，我是 <strong>a彬彬a</strong>。一名开发者，也是方块世界的构筑者。<br
            class="desktop-break"
          />写代码，做有趣的东西，把热爱慢慢变成现实。
        </p>
        <div class="hero-buttons">
          <a class="button primary" href="#projects">看看我的作品</a
          ><a class="button secondary" href="#world"><Blocks :size="18" /> 来悠哉世界坐坐</a>
        </div>
        <div class="hero-notes">
          <span><Code2 :size="14" /> Developer</span><i></i
          ><span><Blocks :size="14" /> Minecraft enthusiast</span><i></i><span>始终保持好奇</span>
        </div>
      </div>
      <div class="shell landscape-wrap">
        <div class="landscape">
          <img
            :src="asset('world.webp')"
            :srcset="`${asset('world-small.webp')} 960w, ${asset('world.webp')} 2048w`"
            sizes="(max-width: 800px) 100vw, 1200px"
            alt="蓝天下，Minecraft 世界中的胡桃和芙宁娜方块雕像"
            width="2048"
            height="1086"
            fetchpriority="high"
          />
          <div class="landscape-shade"></div>
          <div class="image-label">
            <span class="mini-cross">+</span> A LITTLE WORLD, BUILT WITH LOVE
          </div>
          <div class="landscape-bottom">
            <div>
              <span class="overline">不止是方块，更是热爱</span>
              <p>每一个世界，都从一个想法开始。</p>
            </div>
            <a href="#world" class="round-link" aria-label="了解悠哉世界"
              ><ArrowDown :size="24" aria-hidden="true"
            /></a>
          </div>
        </div>
        <div class="image-caption">
          <span>MY WORLD, ONE BLOCK AT A TIME.</span
          ><span>01 / PERSONAL SPACE</span>
        </div>
      </div>
    </section>

    <section id="about" class="shell about-section reveal">
      <div class="section-label"><span>01 / ABOUT ME</span><span class="line"></span></div>
      <div class="about-grid">
        <div>
          <div class="profile-line">
            <img
              :src="asset('avatar.png')"
              alt="a彬彬a 的 GitHub 头像"
              width="64"
              height="64"
              loading="lazy"
            />
            <div>
              <h2>很高兴，在这里遇见你。</h2>
              <span>@{{ profile.handle }}</span>
            </div>
          </div>
          <p class="about-copy">
            从一个网页，到一个完整的方块世界。<br />我喜欢把脑海里的想法，做成真正能用、能玩的东西。
          </p>
          <p class="muted">
            这里收集着我参与开发的项目，也放着我对 Minecraft
            的热爱。你可以随意逛逛，看看代码，或者来悠哉世界一起创造。
          </p>
          <a class="text-link" :href="profile.github" target="_blank" rel="noopener noreferrer"
            >在 GitHub 认识我 <ArrowUpRight :size="16"
          /></a>
        </div>
        <div class="about-aside">
          <span class="overline">WHAT I ENJOY</span>
          <div>
            <Code2 />
            <p>把想法写成代码<small>Web · 工具 · 开源</small></p>
            <span>01</span>
          </div>
          <div>
            <Mountain />
            <p>把方块搭成世界<small>Minecraft · 模组 · 社区</small></p>
            <span>02</span>
          </div>
          <div>
            <Sparkles />
            <p>把日常变得更好<small>探索 · 打磨 · 持续创造</small></p>
            <span>03</span>
          </div>
        </div>
      </div>
    </section>

    <section id="projects" class="projects-section">
      <div class="shell">
        <div class="section-label reveal">
          <span>02 / SELECTED PROJECTS</span><span class="line"></span>
        </div>
        <div class="section-heading reveal">
          <div>
            <h2>想法，正在发生。</h2>
            <p>一些我参与开发的项目，从方块世界延伸到日常生活。</p>
          </div>
          <a
            class="text-link"
            :href="`${profile.github}?tab=repositories`"
            target="_blank"
            rel="noopener noreferrer"
            >更多 GitHub 项目 <ArrowUpRight :size="16"
          /></a>
        </div>
        <div class="project-grid">
          <a
            v-for="(project, index) in projects"
            :key="project.id"
            :href="project.url"
            target="_blank"
            rel="noopener noreferrer"
            class="project-card reveal"
            :style="{ '--reveal-delay': `${(index % 2) * 90}ms` }"
            :class="`project-${project.id}`"
            ><div class="project-top">
              <div class="project-icon">
                <component
                  :is="icons[project.icon as keyof typeof icons]"
                  :size="26"
                  :stroke-width="1.5"
                />
              </div>
              <span>{{ project.number }} <ArrowUpRight :size="20" /></span>
            </div>
            <div v-if="project.id === 'core'" class="voxel-art" aria-hidden="true">
              <img :src="asset('youzaiworld-core.png')" alt="" loading="lazy" />
            </div>
            <div v-if="project.id === 'web'" class="browser-art" aria-hidden="true">
              <div><i></i><i></i><i></i><span>mcyzw.top</span></div>
              <img :src="asset('youzaiworld-web.webp')" alt="" loading="lazy" />
            </div>
            <div class="project-content">
              <span class="project-role">开发者 <span>·</span> {{ project.subtitle }}</span>
              <h3>{{ project.title }}</h3>
              <p>{{ project.description }}</p>
              <div class="project-bottom">
                <div class="tags">
                  <span v-for="tag in project.tags" :key="tag">{{ tag }}</span>
                </div>
                <span class="project-link">{{ project.link }} <ArrowUpRight :size="14" /></span>
              </div></div
          ></a>
        </div>
      </div>
    </section>

    <section id="world" class="shell world-section">
      <div class="section-label reveal">
        <span>03 / YOUZAI WORLD</span><span class="line"></span
        ><span class="warm-text">给热爱留一个地方</span>
      </div>
      <div class="world-heading reveal">
        <img
          :src="asset('logocircle.webp')"
          alt="悠哉世界 Logo"
          width="58"
          height="58"
          loading="lazy"
        /><span>MINECRAFT JAVA SERVER</span>
        <h2>欢迎来到，<span>悠哉世界。</span></h2>
        <p>放慢一点，建造一点。<br />在方块组成的天地里，找到属于自己的小小日常。</p>
      </div>
      <div class="world-card reveal">
        <img
          class="world-image"
          :src="asset('show_1.webp')"
          alt="悠哉世界 Minecraft 服务器景观"
          loading="lazy"
          width="1200"
          height="675"
        />
        <div class="world-overlay"></div>
        <div class="world-card-content">
          <span class="world-badge"><Blocks :size="14" /> Youzai World</span>
          <h3>一个世界，<br />无数种可能。</h3>
          <p>
            探索、建造、冒险，或只是和伙伴一起看一场日落。<br />我在这里写代码，也和你一起创造故事。
          </p>
          <div class="world-actions">
            <a
              class="button white-button"
              :href="profile.server"
              target="_blank"
              rel="noopener noreferrer"
              >探索服务器官网 <ArrowUpRight :size="17" /></a
            ><button class="address-button" @click="copyAddress">
              <span><small>服务器地址</small>{{ profile.address }}</span
              ><Check v-if="copied" :size="18" /><Copy v-else :size="18" />
            </button>
          </div>
        </div>
      </div>
      <div class="world-features reveal">
        <div>
          <Mountain :size="22" />
          <h3>自由探索</h3>
          <p>采集、建造与冒险，享受生存的乐趣。</p>
        </div>
        <div>
          <Blocks :size="22" />
          <h3>用心开发</h3>
          <p>自研核心模组，打磨属于悠哉的体验。</p>
        </div>
        <div>
          <Heart :size="22" />
          <h3>纯粹热爱</h3>
          <p>公益运营，没有 VIP 特权，一起悠哉。</p>
        </div>
      </div>
      <a
        class="world-guide text-link"
        :href="`${profile.server}/tutorials/quick_play_guide`"
        target="_blank"
        rel="noopener noreferrer"
        >第一次来？看看快速游玩指南 <ArrowRight :size="16"
      /></a>
    </section>

    <section id="contact" class="contact-section">
      <div class="shell reveal">
        <span class="overline">LET'S MAKE SOMETHING GOOD.</span>
        <h2>有趣的想法，<br />从一句「你好」开始。</h2>
        <p>聊聊项目、交换想法，或只是打个招呼。<br />很期待听到你的声音。</p>
        <a class="email-link" :href="`mailto:${profile.email}`">{{ profile.email }}</a>
        <div class="contact-links">
          <a :href="profile.github" target="_blank" rel="noopener noreferrer"
            ><Github :size="19" /> GitHub <ArrowUpRight :size="14" /></a
          ><a :href="profile.bilibili" target="_blank" rel="noopener noreferrer"
            ><MonitorPlay :size="19" /> Bilibili <ArrowUpRight :size="14"
          /></a>
        </div>
      </div>
      <div class="contact-watermark" aria-hidden="true">keep creating.</div>
    </section>
  </main>
  <MusicDialog
    :anchor="musicTrigger"
    @playing="musicPlaying = $event"
    @track="musicTrack = $event"
    @opened="musicOpen = $event"
  />
  <footer class="shell footer">
    <a class="brand" href="#home">a彬彬a<span class="brand-dot">.</span></a>
    <div class="footer-info">
      <p>© {{ new Date().getFullYear() }} zxabinbina · 用代码与热爱构筑</p>
      <a href="https://icp.gov.moe/?keyword=20264016" target="_blank" rel="noopener noreferrer"
        >萌ICP备20264016号</a
      >
    </div>
    <a href="#home">回到顶部</a>
  </footer>
  <Transition name="toast"
    ><div v-if="copyMessage" role="status" class="toast-message">
      <Check :size="17" />{{ copyMessage }}
    </div></Transition
  >
</template>
