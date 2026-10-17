<script setup lang="ts">
import { MoveRight, ShieldCheck } from 'lucide-vue-next'
import CodeBlock from './CodeBlock.vue'
import ScanDemo from './ScanDemo.vue'
import { gazeRepoUrl } from '../catalog'

const features = [
  {
    no: '01 / QUICK SETUP',
    title: '快速上手',
    details: '安装 Gaze、启动守护进程、录入人脸，并在终端里先试一次认证。',
    link: '/projects/gaze/guide/getting-started',
    linkText: '开始设置',
  },
  {
    no: '02 / DESKTOP LOGIN',
    title: '桌面登录',
    details:
      '为 GNOME、KDE Plasma 或 Hyprland 的 hyprlock 设置面部解锁，也可以搭配 SDDM 等基于 PAM 的登录管理器。',
    link: '/projects/gaze/guide/gnome',
    linkText: '配置桌面认证',
  },
  {
    no: '03 / PAM',
    title: 'PAM 集成',
    details: '在 sudo 和其他通过 PAM 认证的程序里，使用你的脸。',
    link: '/projects/gaze/guide/pam',
    linkText: '阅读 PAM 指南',
  },
  {
    no: '04 / CLI & GUI',
    title: 'CLI 与 GUI 工具',
    details: '在终端或 GTK 应用里增删人脸、测试识别、修改设置。',
    link: '/projects/gaze/guide/cli',
    linkText: '查看 CLI',
  },
  {
    no: '05 / LOCAL-FIRST',
    title: '本地优先',
    details:
      '面部模板留在你的机器上：守护进程在本地完成识别，通过 DBus 与 CLI、GUI 和 PAM 模块通信。',
    link: '/projects/gaze/guide/how-it-works',
    linkText: '工作原理',
  },
  {
    no: '06 / TROUBLESHOOTING',
    title: '故障排查',
    details: '解决摄像头选择、守护进程启动、DBus 权限、PAM 锁定与模型问题。',
    link: '/projects/gaze/guide/troubleshooting',
    linkText: '排查问题',
  },
]

const pipeline = [
  '摄像头',
  'SCRFD 人脸检测',
  '对齐',
  'ArcFace 特征向量',
  '比对',
  'MiniFASNet-V2 活体检测',
]

const forks = [
  {
    no: '01 / 中文提示',
    title: '认证提示中文化',
    details: 'PAM 认证过程的提示信息全面中文化，终端与锁屏上的交互更亲切。',
  },
  {
    no: '02 / KRDP 免打扰',
    title: '远程桌面不误触',
    details: 'KDE 远程桌面（KRDP）连接建立时跳过本机人脸扫描，远程会话不再触发认证弹窗。',
  },
  {
    no: '03 / 画面冻结修复',
    title: 'KRDP 6.7.5 修复',
    details: '补齐帧暂停/恢复确认与帧编号回绕处理，修复 Windows App 连接约 4 秒后画面冻结的问题。',
  },
  {
    no: '04 / 合并 RPM',
    title: '单包安装',
    details:
      '守护进程、CLI、GUI、KDE 集成、PAM 模块与 KRDP 修复合并为一个 RPM，面向 Fedora 44 x86_64。',
  },
]
</script>

<template>
  <main id="main" class="gaze-page">
    <section class="gaze-hero shell">
      <div class="gaze-hero-copy">
        <p class="gaze-eyebrow">OPEN SOURCE / LINUX FACIAL AUTHENTICATION</p>
        <h1>刷个脸，<br />解锁 <span>Linux。</span></h1>
        <p class="gaze-lead">
          Gaze 把面部识别认证带到 Linux：设备端本地识别、PAM 集成，<br />覆盖登录、锁屏、sudo
          与桌面管理。
        </p>
        <div class="gaze-actions">
          <a class="gaze-button primary" href="/projects/gaze/guide/getting-started"
            >快速开始 <MoveRight :size="16" /></a
          ><a class="gaze-button" href="/projects/gaze/guide/installation">安装指南</a
          ><a class="gaze-button" :href="gazeRepoUrl" target="_blank" rel="noopener noreferrer"
            >GitHub ↗</a
          >
        </div>
        <p class="gaze-caption">支持 Debian / Ubuntu / Fedora / openSUSE / Arch / Manjaro</p>
      </div>
      <ScanDemo class="gaze-hero-demo" />
    </section>
    <section class="gaze-section shell gaze-reveal">
      <p class="gaze-eyebrow">INSTALL / 中文版下载</p>
      <h2>一个安装包，装好一切。</h2>
      <CodeBlock code="sudo dnf install ./gaze-*.rpm" language="bash" copy-label="复制安装命令" />
      <p class="gaze-caption">
        从
        <a
          class="gaze-text-link"
          href="https://github.com/zxaBinbina/gaze-zh/releases"
          target="_blank"
          rel="noopener noreferrer"
          style="margin-top: 0"
          >GitHub Releases</a
        >
        下载中文版合并 RPM（Fedora 44 x86_64，含中文提示与 KRDP 修复）；其他发行版走官方渠道，细节见
        <a class="gaze-text-link" href="/projects/gaze/guide/installation" style="margin-top: 0"
          >安装指南 →</a
        >
      </p>
    </section>
    <section class="gaze-section shell gaze-reveal" id="features">
      <p class="gaze-eyebrow">01 / FEATURES</p>
      <h2>它能做什么</h2>
      <div class="gaze-grid">
        <a
          v-for="feature in features"
          :key="feature.no"
          :href="feature.link"
          class="gaze-card gaze-reveal"
          ><article>
            <span class="gaze-card-icon">{{ feature.no }}</span>
            <h3>{{ feature.title }}</h3>
            <p>{{ feature.details }}</p>
            <span class="gaze-card-link">{{ feature.linkText }} →</span>
          </article></a
        >
      </div>
    </section>
    <section class="gaze-section shell gaze-split gaze-reveal">
      <div>
        <p class="gaze-eyebrow">02 / SECURITY</p>
        <h2>安全与<span>活体检测。</span></h2>
        <p class="gaze-lead">
          Gaze 在本地进行活体检测，并支持红外（IR）摄像头，帮助抵御照片与视频欺骗。
        </p>
        <div class="gaze-note">
          <ShieldCheck :size="17" style="vertical-align: -3px" />
          <b>高安全环境的建议</b>
          <p>在涉密或高安全环境中使用 Gaze 时，请保留原有的系统认证方式作为回退。</p>
        </div>
      </div>
      <div>
        <p class="gaze-eyebrow">HOW IT WORKS</p>
        <h2>识别链路</h2>
        <div class="gaze-pipeline">
          <template v-for="(item, index) in pipeline" :key="item">
            <span>{{ item }}</span
            ><MoveRight v-if="index < pipeline.length - 1" :size="14" />
          </template>
        </div>
        <p class="gaze-caption">一切发生在本机：面部数据不会被发送到任何地方。</p>
      </div>
    </section>
    <section class="gaze-section shell gaze-reveal" id="fork">
      <p class="gaze-eyebrow">03 / 中文分支</p>
      <h2>这个中文版本，<span>多做了一点。</span></h2>
      <p class="gaze-lead">
        本站对应的源码分支在官方 Gaze 的基础上，为中文用户修了几件日常的小事。
      </p>
      <div class="gaze-fork-grid">
        <article v-for="item in forks" :key="item.no" class="gaze-card gaze-reveal">
          <span class="gaze-card-icon">{{ item.no }}</span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.details }}</p>
        </article>
      </div>
      <a class="gaze-text-link" :href="gazeRepoUrl" target="_blank" rel="noopener noreferrer"
        >查看分支仓库与修复说明 ↗</a
      >
    </section>
    <section class="gaze-section shell gaze-reveal">
      <div class="gaze-deploy-card">
        <div>
          <p class="gaze-eyebrow">04 / GET STARTED</p>
          <h2>从快速开始，<br />十分钟跑起来。</h2>
          <p>
            安装、录入人脸、测试认证，再按桌面环境配置锁屏与 sudo。<br />
            全部 21 篇中文指南，从第一条命令到故障排查。
          </p>
        </div>
        <a class="gaze-button primary" href="/projects/gaze/guide/getting-started"
          >阅读快速开始 →</a
        >
      </div>
    </section>
  </main>
</template>
