<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  ArrowDown,
  ArrowUp,
  ArrowDownToLine,
  AudioLines,
  Check,
  ChevronDown,
  Copy,
  ExternalLink,
  LayoutPanelTop,
  ListMusic,
  RefreshCw,
  Settings2,
  SlidersHorizontal,
  Type,
} from 'lucide-vue-next'
import AnimatedDetails from '../components/AnimatedDetails.vue'
import SiteFooter from '../components/SiteFooter.vue'
import DesktopRecording from './DesktopRecording.vue'
import ShotImage from './ShotImage.vue'
import {
  distributionLinks,
  features,
  releaseHighlights,
  settingGroups,
  sptlProject,
} from './content'
import { useSptlRelease } from './useSptlRelease'
import './style.css'

const icons = {
  lyrics: Type,
  sync: AudioLines,
  playback: SlidersHorizontal,
  panel: LayoutPanelTop,
  playlist: ListMusic,
  settings: Settings2,
}
const copied = ref(false)
const copyMessage = ref('')
const { release, loading, error, refresh } = useSptlRelease()
const version = computed(() => release.value?.version || sptlProject.version)
const releaseUrl = computed(() => release.value?.url || sptlProject.latest)
const sourceAsset = computed(() =>
  release.value?.assets.find((asset) => asset.name === `sptl-source-${version.value}.tar.gz`),
)
const sourceUrl = computed(() =>
  release.value ? sourceAsset.value?.url || releaseUrl.value : sptlProject.source,
)
const sourceLabel = computed(() =>
  release.value
    ? sourceAsset.value
      ? `完整源码 v${version.value}`
      : '查看发行文件'
    : `本站源码包 v${sptlProject.version}`,
)
const releaseDate = computed(() => {
  const date = release.value?.publishedAt
  return date && Number.isFinite(Date.parse(date))
    ? new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' }).format(new Date(date))
    : ''
})
const installerUrl = new URL(
  sptlProject.installer,
  import.meta.env.SITE_URL || 'https://zxabinbina.cc.cd/',
).href
const installCommand = `curl -fsSL '${installerUrl.replaceAll("'", "'\\''")}' | sh`
let copyTimer: ReturnType<typeof setTimeout> | undefined
async function copyInstall() {
  clearTimeout(copyTimer)
  try {
    await navigator.clipboard.writeText(installCommand)
    copied.value = true
    copyMessage.value = '安装命令已复制'
  } catch {
    copyMessage.value = '复制失败，请选中命令手动复制。'
  }
  copyTimer = setTimeout(() => {
    copied.value = false
    copyMessage.value = ''
  }, 3500)
}
const page = ref<HTMLElement>()
const motion = matchMedia('(prefers-reduced-motion: reduce)')
const animations = new Set<Animation>()
let observer: IntersectionObserver | undefined
function cancelAnimations() {
  animations.forEach((animation) => animation.cancel())
  animations.clear()
}
onMounted(() => {
  if ('IntersectionObserver' in window && 'animate' in Element.prototype) {
    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue
          observer?.unobserve(entry.target)
          if (motion.matches) continue
          const animation = entry.target.animate(
            [
              { opacity: 0, translate: '0 20px' },
              { opacity: 1, translate: '0 0' },
            ],
            {
              duration: 650,
              easing: getComputedStyle(entry.target).getPropertyValue('--motion-ease').trim(),
            },
          )
          animations.add(animation)
          animation.finished.catch(() => {}).finally(() => animations.delete(animation))
        }
      },
      { threshold: 0.08 },
    )
    page.value?.querySelectorAll('.sptl-reveal').forEach((element) => observer?.observe(element))
  }
  motion.addEventListener('change', cancelAnimations)
})
onBeforeUnmount(() => {
  clearTimeout(copyTimer)
  observer?.disconnect()
  cancelAnimations()
  motion.removeEventListener('change', cancelAnimations)
})
</script>

<template>
  <main ref="page" id="main" class="sptl-page">
    <section class="sptl-hero shell">
      <div class="sptl-hero-copy">
        <p class="sptl-eyebrow">SPTL / SPLAYER TASKBAR LYRICS</p>
        <h1>让歌词，<br /><span>留在任务栏。</span></h1>
        <p class="sptl-lead">
          为 SPlayer Next 打造的 KDE Plasma
          小组件。同步歌词、专辑封面与播放控制，听歌时少切一次窗口。
        </p>
        <div class="sptl-actions">
          <a class="sptl-button primary" href="/projects/SPTL#install"
            >开始安装 <ArrowDown :size="17" aria-hidden="true"
          /></a>
          <a class="sptl-button" :href="releaseUrl" target="_blank" rel="noopener noreferrer"
            >查看正式版 <ExternalLink :size="17" aria-hidden="true"
          /></a>
        </div>
        <div class="sptl-tags"><span>KDE Plasma</span><span>SPlayer Next</span></div>
        <p class="sptl-caption">
          {{ release ? 'v' + version + ' 正式版' : '已核对 v' + sptlProject.version }} · Linux 桌面
          · 用户级安装
        </p>
      </div>
      <DesktopRecording />
    </section>
    <section class="sptl-section shell sptl-reveal" id="features">
      <p class="sptl-eyebrow">01 / EVERYDAY LISTENING</p>
      <h2>小小一块，<span>刚好够用。</span></h2>
      <p class="sptl-section-lead">看歌词、换歌曲、找回当前播放进度，都留在熟悉的桌面里。</p>
      <p class="sptl-photo-intro">
        下面都是本机小组件的实际画面。深浅两套实拍随页面明暗模式切换，任务栏图片可左右查看，点击可打开原图。
      </p>
      <div class="sptl-feature-grid">
        <article v-for="feature in features" :key="feature.label" class="sptl-feature sptl-reveal">
          <div class="sptl-feature-top">
            <component
              :is="icons[feature.icon]"
              :size="24"
              :stroke-width="1.5"
              aria-hidden="true"
            /><span>{{ feature.label }}</span>
          </div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
          <div class="sptl-photo-stack" :class="{ 'is-comparison': feature.icon === 'settings' }">
            <ShotImage v-for="shot in feature.shots" :key="shot.src" :shot="shot" />
          </div>
          <a v-if="feature.icon === 'sync'" class="sptl-text-link" href="/projects/SPTL#recording"
            >看首屏实拍视频 <ArrowUp :size="16" aria-hidden="true"
          /></a>
        </article>
      </div>
    </section>
    <section
      class="sptl-section shell sptl-reveal sptl-release"
      id="release"
      aria-labelledby="sptl-release-title"
    >
      <div>
        <p class="sptl-eyebrow">LATEST RELEASE / v{{ version }}</p>
        <h2 id="sptl-release-title">这一版，<span>更顺手。</span></h2>
        <p class="sptl-release-status" role="status" :aria-busy="loading">
          <template v-if="loading">正在读取 GitHub 最新正式版…</template>
          <template v-else-if="error"
            >暂时无法读取最新版本，当前显示{{ release ? '上次同步的' : '已核对的' }} v{{
              version
            }}。安装脚本仍会读取 GitHub 最新版。</template
          >
          <template v-else
            >已同步 GitHub 最新正式版<span v-if="releaseDate"> · {{ releaseDate }}</span></template
          >
        </p>
        <button
          class="sptl-text-link"
          type="button"
          :disabled="loading"
          @click="refresh"
          aria-label="刷新最新版本"
        >
          <RefreshCw :size="16" aria-hidden="true" />刷新版本
        </button>
      </div>
      <div>
        <ul v-if="version === sptlProject.version" class="sptl-release-highlights">
          <li v-for="highlight in releaseHighlights" :key="highlight">{{ highlight }}</li>
        </ul>
        <p v-else-if="release?.body" class="sptl-release-notes">{{ release.body }}</p>
        <p v-else class="sptl-release-notes">最新版本已发布，详细更新请查看 GitHub 发行说明。</p>
        <a class="sptl-text-link" :href="releaseUrl" target="_blank" rel="noopener noreferrer"
          >完整发行说明 <ExternalLink :size="16" aria-hidden="true"
        /></a>
        <div v-if="release?.assets.length" class="sptl-release-assets" aria-label="最新发行文件">
          <a
            v-for="asset in release.assets"
            :key="asset.name"
            class="sptl-text-link"
            :href="asset.url"
            target="_blank"
            rel="noopener noreferrer"
            ><ArrowDownToLine :size="14" aria-hidden="true" />{{ asset.name }}</a
          >
        </div>
      </div>
    </section>
    <section class="sptl-section shell sptl-reveal" id="install">
      <div class="sptl-section-heading">
        <div>
          <p class="sptl-eyebrow">02 / GET STARTED</p>
          <h2>装好，<span>就开始听。</span></h2>
        </div>
        <a class="sptl-text-link" :href="sourceUrl" :download="!release ? '' : undefined"
          >{{ sourceLabel }} <ArrowDownToLine :size="16" aria-hidden="true"
        /></a>
      </div>
      <p class="sptl-section-lead">
        一条命令，自动下载 GitHub
        最新正式版，校验后安装插件文件、小组件与辅助服务。已有安装会更新，并保留共享设置与自定义播放器路径。
      </p>
      <div class="sptl-download-grid" aria-label="正式版下载入口">
        <article
          v-for="distribution in distributionLinks"
          :key="distribution.title"
          class="sptl-download"
        >
          <h3>
            <a
              class="sptl-text-link"
              :href="distribution.url === sptlProject.latest ? releaseUrl : distribution.url"
              target="_blank"
              rel="noopener noreferrer"
              >{{ distribution.title }} <ExternalLink :size="16" aria-hidden="true"
            /></a>
          </h3>
          <p>{{ distribution.description }}</p>
        </article>
      </div>
      <ul class="sptl-requirements" aria-label="安装要求">
        <li>Python 3.10+ 与 curl</li>
        <li>Plasma 6 / Qt 6，或 Plasma 5.27 / Qt 5.15</li>
        <li>SPlayer Next 插件 API 5+</li>
        <li>systemd 用户会话</li>
        <li>收藏需要 gdbus 与 SPlayer 托盘入口</li>
      </ul>
      <ol class="sptl-install-steps">
        <li>
          <span class="sptl-step-number">01</span>
          <div>
            <h3>准备桌面环境</h3>
            <p>安装 SPlayer Next，并在 KDE 桌面会话中打开终端。确认 Python 与 curl 已安装。</p>
          </div>
        </li>
        <li>
          <span class="sptl-step-number">02</span>
          <div>
            <h3>一键安装或更新</h3>
            <p>
              运行以下命令。脚本自动下载并校验最新源码，安装组件并启动辅助服务。更新已有组件时会短暂重载正在运行的
              Plasma 面板，应用窗口保留。
            </p>
            <div class="sptl-code">
              <div class="sptl-code-toolbar">
                <span>TERMINAL · 无需 sudo</span
                ><button
                  type="button"
                  @click="copyInstall"
                  :aria-label="copied ? '安装命令已复制' : '复制安装命令'"
                >
                  <Check v-if="copied" :size="16" aria-hidden="true" /><Copy
                    v-else
                    :size="16"
                    aria-hidden="true"
                  />{{ copied ? '已复制' : '复制' }}
                </button>
              </div>
              <pre tabindex="0" aria-label="安装命令"><code>{{ installCommand }}</code></pre>
            </div>
            <p class="sptl-copy-status" role="status">{{ copyMessage }}</p>
            <a class="sptl-text-link" :href="sptlProject.installer" download
              >下载安装脚本 <ArrowDownToLine :size="16" aria-hidden="true"
            /></a>
          </div>
        </li>
        <li>
          <span class="sptl-step-number">03</span>
          <div>
            <h3>在 SPlayer Next 中导入插件</h3>
            <p>
              打开「设置 → 插件管理 → 本地导入」，选择
              <code>~/.local/share/sptl/zxaBinbina.sptl.js</code>，启用插件并允许
              <code>network</code>、<code>control</code>、<code>api</code>
              三项权限。更新后重新导入同 ID 插件。使用自定义 XDG
              数据目录时，以安装脚本输出的路径为准。
            </p>
          </div>
        </li>
        <li>
          <span class="sptl-step-number">04</span>
          <div>
            <h3>把 SPTL 加入任务栏</h3>
            <p>
              在顶部或底部的横向 Plasma 面板添加「SPTL — SPlayer
              任务栏歌词」。开始播放歌曲，歌词就会跟着出现。
            </p>
          </div>
        </li>
      </ol>
    </section>
    <section class="sptl-section shell sptl-settings-section sptl-reveal" id="settings">
      <div>
        <p class="sptl-eyebrow">03 / MAKE IT YOURS</p>
        <h2>喜欢的样子，<br /><span>自己调。</span></h2>
        <p class="sptl-lead">
          右键 SPTL → 配置。修改后点击「应用」或「确定」，所有 SPTL 小组件共用这套设置。
        </p>
        <p class="sptl-caption">
          基准字号以 42 像素组件高度为参照；任务栏高度变化时，文字和封面自动适配。
        </p>
      </div>
      <div class="sptl-setting-groups">
        <article v-for="(group, index) in settingGroups" :key="group.title">
          <span>{{ String(index + 1).padStart(2, '0') }}</span>
          <div>
            <h3>{{ group.title }}</h3>
            <p>{{ group.description }}</p>
          </div>
        </article>
      </div>
    </section>
    <section class="sptl-section shell sptl-reveal" id="faq">
      <p class="sptl-eyebrow">04 / GOOD TO KNOW</p>
      <h2>开始之前，<span>再聊几句。</span></h2>
      <div class="sptl-faq">
        <AnimatedDetails
          ><template #summary
            >支持哪些桌面版本？<ChevronDown :size="18" aria-hidden="true"
          /></template>
          <p>
            支持 KDE Plasma 5.27 / Qt 5.15 与 Plasma 6 / Qt 6 的顶部或底部横向任务栏。
            正式版提供两种安装包，脚本自动检测当前桌面；切换 Plasma 主版本后重新运行安装命令。
          </p></AnimatedDetails
        >
        <AnimatedDetails
          ><template #summary
            >需要一直开着 SPlayer Next 吗？<ChevronDown :size="18" aria-hidden="true"
          /></template>
          <p>
            显示同步歌词需要 SPlayer Next 正在运行且 SPTL
            插件已启用。播放器关闭后可收起为图标或隐藏；点击图标可打开播放器，也可设置为启动后播放「我喜欢的音乐」。自动播放需要在
            SPlayer 中登录网易云音乐。
          </p></AnimatedDetails
        >
        <AnimatedDetails
          ><template #summary
            >更新后，小组件怎么还是原来的样子？<ChevronDown :size="18" aria-hidden="true"
          /></template>
          <p>
            再次运行一键安装命令即可更新。脚本在检测到已有组件且 Plasma
            用户服务正在运行时自动重载面板，清除旧代码缓存；否则更新后注销再登录。更新后还需在
            SPlayer 中重新导入同 ID 插件。
          </p></AnimatedDetails
        >
        <AnimatedDetails
          ><template #summary
            >AppImage 播放器无法从图标打开怎么办？<ChevronDown :size="18" aria-hidden="true"
          /></template>
          <p>
            下载官网的安装脚本后运行
            <code>sh install.sh --splayer-command '/path/to/SPlayer-Next.AppImage'</code>
            指定启动入口。自定义播放器数据目录使用
            <code>--splayer-config</code>；以后更新会保留这些参数。使用
            <code>sh install.sh --help</code> 查看选项，<code>--dry-run</code> 只检查最新版本，<code
              >--no-reload-plasma</code
            >
            可关闭自动面板重载。
          </p></AnimatedDetails
        >
        <AnimatedDetails
          ><template #summary
            >从 KDE Store 安装后，还需要做什么？<ChevronDown :size="18" aria-hidden="true"
          /></template>
          <p>
            KDE Store 只提供小组件，仍需运行一键安装脚本安装辅助服务与 SPlayer
            插件文件，再在播放器中导入插件。SPlayer 插件市场投稿仍在等待维护者审核，可在
            <a
              class="sptl-text-link"
              :href="sptlProject.pluginSubmission"
              target="_blank"
              rel="noopener noreferrer"
              >投稿页面 <ExternalLink :size="14" aria-hidden="true" /></a
            >查看进展。
          </p>
        </AnimatedDetails>
        <AnimatedDetails
          ><template #summary
            >私人 FM 和收藏怎么用？<ChevronDown :size="18" aria-hidden="true"
          /></template>
          <p>
            私人 FM 播放时，上一首替换为「不喜欢」，弹窗隐藏播放模式。收藏复用 SPlayer 的 Linux
            托盘菜单，需要 gdbus 和可用的托盘入口；悬停收藏按钮可在「交互与离线」设置中关闭。
          </p>
        </AnimatedDetails>
        <AnimatedDetails
          ><template #summary
            >没有逐字歌词或翻译时会怎样？<ChevronDown :size="18" aria-hidden="true"
          /></template>
          <p>
            逐字高亮取决于歌曲提供的歌词时间信息；只有逐行文本时按行显示。缺少辅助歌词时会回退到下一句，缺少封面时显示占位图。
          </p></AnimatedDetails
        >
      </div>
    </section>
    <section class="sptl-section shell sptl-reveal">
      <div class="sptl-closing">
        <div>
          <p class="sptl-eyebrow">OPEN SOURCE / MADE BY a彬彬a</p>
          <h2>给日常听歌，<br /><span>留一个小角落。</span></h2>
          <p>欢迎反馈使用体验，也欢迎一起完善。</p>
        </div>
        <div class="sptl-closing-links">
          <a class="sptl-button primary" href="/projects/SPTL#install"
            >一键安装 <ArrowDown :size="17" aria-hidden="true"
          /></a>
        </div>
      </div>
    </section>
  </main>
  <SiteFooter :brand-link="false" />
</template>
