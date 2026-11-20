<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import {
  ArrowDown,
  ArrowDownToLine,
  AudioLines,
  Check,
  ChevronDown,
  Copy,
  LayoutPanelTop,
  Palette,
  Settings2,
  SlidersHorizontal,
  Type,
} from 'lucide-vue-next'
import AnimatedDetails from '../components/AnimatedDetails.vue'
import SiteFooter from '../components/SiteFooter.vue'
import TaskbarDemo from './TaskbarDemo.vue'
import { features, settingGroups, sptlProject } from './content'
import './style.css'

const icons = {
  lyrics: Type,
  sync: AudioLines,
  playback: SlidersHorizontal,
  panel: LayoutPanelTop,
  theme: Palette,
  settings: Settings2,
}
const copied = ref(false)
const copyMessage = ref('')
const installCommand = `cd SPTL-${sptlProject.version}\npython3 tools/install.py`
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
          <a class="sptl-button" :href="sptlProject.source" download
            >下载源码包 <ArrowDownToLine :size="17" aria-hidden="true"
          /></a>
        </div>
        <div class="sptl-tags"><span>KDE Plasma</span><span>SPlayer Next</span></div>
        <p class="sptl-caption">v{{ sptlProject.version }} · Linux 桌面 · 用户级安装</p>
      </div>
      <TaskbarDemo />
    </section>
    <section class="sptl-section shell sptl-reveal" id="features">
      <p class="sptl-eyebrow">01 / EVERYDAY LISTENING</p>
      <h2>小小一块，<span>刚好够用。</span></h2>
      <p class="sptl-section-lead">看歌词、换歌曲、找回当前播放进度，都留在熟悉的桌面里。</p>
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
        </article>
      </div>
    </section>
    <section class="sptl-section shell sptl-reveal" id="install">
      <div class="sptl-section-heading">
        <div>
          <p class="sptl-eyebrow">02 / GET STARTED</p>
          <h2>装好，<span>就开始听。</span></h2>
        </div>
        <a class="sptl-text-link" :href="sptlProject.source" download
          >完整源码包 v{{ sptlProject.version }} <ArrowDownToLine :size="16" aria-hidden="true"
        /></a>
      </div>
      <p class="sptl-section-lead">
        当前提供源码安装。下载包包含 SPlayer 插件、小组件、辅助服务和安装脚本。
      </p>
      <ul class="sptl-requirements" aria-label="安装要求">
        <li>Python 3.10+</li>
        <li>Plasma 6 / Qt 6，或 Plasma 5.27 / Qt 5.15</li>
        <li>SPlayer Next 插件 API 4+</li>
        <li>systemd 用户会话</li>
      </ul>
      <ol class="sptl-install-steps">
        <li>
          <span class="sptl-step-number">01</span>
          <div>
            <h3>下载并解压源码包</h3>
            <p>把源码包解压到方便保存的位置，在解压目录的上一级打开终端。</p>
          </div>
        </li>
        <li>
          <span class="sptl-step-number">02</span>
          <div>
            <h3>运行用户级安装</h3>
            <p>在 KDE 桌面会话里运行以下命令。安装脚本会构建插件与小组件，并启动歌词辅助服务。</p>
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
          </div>
        </li>
        <li>
          <span class="sptl-step-number">03</span>
          <div>
            <h3>在 SPlayer Next 中导入插件</h3>
            <p>
              打开「设置 → 插件管理 → 本地导入」，选择
              <code>~/.local/share/sptl/zxaBinbina.sptl.js</code
              >，启用插件并允许网络与播放控制权限。使用自定义 XDG
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
            面向 KDE Plasma 5.27 / Qt 5.15 与 Plasma 6 / Qt 6 的横向任务栏。当前已在 Plasma 6
            实机验证；Plasma 5 安装包已生成，仍需实机验收。
          </p></AnimatedDetails
        >
        <AnimatedDetails
          ><template #summary
            >需要一直开着 SPlayer Next 吗？<ChevronDown :size="18" aria-hidden="true"
          /></template>
          <p>
            显示同步歌词需要 SPlayer Next 正在运行且 SPTL
            插件已启用。播放器关闭后可收起为图标或隐藏；收起图标也可以设置为点击启动播放器。
          </p></AnimatedDetails
        >
        <AnimatedDetails
          ><template #summary
            >更新后，小组件怎么还是原来的样子？<ChevronDown :size="18" aria-hidden="true"
          /></template>
          <p>
            Plasma 可能缓存旧的小组件代码。在项目目录运行
            <code>python3 tools/install.py --reload-plasma</code>
            更新并重载桌面外壳，任务栏会短暂重载，应用窗口保留；也可以普通更新后注销再登录。更新插件后，在
            SPlayer Next 中重新导入同 ID 插件。
          </p></AnimatedDetails
        >
        <AnimatedDetails
          ><template #summary
            >AppImage 播放器无法从图标打开怎么办？<ChevronDown :size="18" aria-hidden="true"
          /></template>
          <p>
            安装时使用
            <code>--splayer-command '/path/to/SPlayer-Next.AppImage'</code>
            指定启动入口。自定义播放器数据目录可以通过
            <code>--splayer-config</code> 指定，详细用法见源码包中的 <code>docs/install.md</code>。
          </p></AnimatedDetails
        >
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
          <a class="sptl-button primary" :href="sptlProject.source" download
            >下载源码包 <ArrowDownToLine :size="17" aria-hidden="true"
          /></a>
        </div>
      </div>
    </section>
  </main>
  <SiteFooter :brand-link="false" />
</template>
