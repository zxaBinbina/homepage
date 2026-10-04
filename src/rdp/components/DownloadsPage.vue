<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  AlertCircle,
  CalendarDays,
  Download,
  ExternalLink,
  FileArchive,
  GitBranch,
  LoaderCircle,
  Package,
  RefreshCw,
} from 'lucide-vue-next'
import '../downloads.css'

type ReleaseAsset = {
  id: number
  name: string
  size: number
  browser_download_url: string
  download_count: number
}

type Release = {
  id: number
  tag_name: string
  name: string
  body: string | null
  html_url: string
  published_at: string | null
  created_at: string
  prerelease: boolean
  draft: boolean
  assets: ReleaseAsset[]
}

const endpoint = 'https://api.github.com/repos/zxaBinbina/rdp-access-auth/releases?per_page=30'
const releases = ref<Release[]>([])
const loading = ref(true)
const error = ref('')
const controller = ref<AbortController>()

const visibleReleases = computed(() => releases.value.filter((release) => !release.draft))

function formatDate(value: string | null) {
  if (!value) return '日期未知'
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' }).format(new Date(value))
}

function formatSize(bytes: number) {
  if (!bytes) return '大小未知'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unit = 0
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024
    unit += 1
  }
  return `${size >= 10 || unit === 0 ? size.toFixed(0) : size.toFixed(1)} ${units[unit]}`
}

function formatDownloads(count: number) {
  return `${count.toLocaleString('zh-CN')} 次下载`
}

function assetIcon(name: string) {
  return /\.(rpm|deb|pkg|msi|exe|appimage)$/i.test(name) ? Package : FileArchive
}

async function loadReleases() {
  controller.value?.abort()
  const request = new AbortController()
  controller.value = request
  loading.value = true
  error.value = ''
  try {
    const response = await fetch(endpoint, {
      headers: { Accept: 'application/vnd.github+json' },
      signal: request.signal,
    })
    if (!response.ok) throw new Error(`GitHub API 返回 ${response.status}`)
    releases.value = (await response.json()) as Release[]
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === 'AbortError') return
    error.value = '暂时无法读取 GitHub Releases，请稍后重试或直接打开发行版页面。'
  } finally {
    if (!request.signal.aborted) loading.value = false
  }
}

onMounted(loadReleases)
onBeforeUnmount(() => controller.value?.abort())
</script>

<template>
  <main id="main" class="rdp-page shell downloads-page">
    <section class="downloads-hero downloads-entry">
      <div>
        <p class="rdp-eyebrow">RDP ACCESS AUTH / RELEASES</p>
        <h1>下载发行版<span>，马上部署。</span></h1>
        <p class="rdp-lead">
          从 GitHub 自动读取所有公开发行版。选择版本后，下载与你的 Linux 发行版和 CPU
          架构匹配的文件。
        </p>
      </div>
      <a
        class="rdp-button"
        href="https://github.com/zxaBinbina/rdp-access-auth/releases"
        target="_blank"
        rel="noopener noreferrer"
        >在 GitHub 查看 <ExternalLink :size="15"
      /></a>
    </section>

    <section class="downloads-toolbar downloads-entry" aria-label="发行版状态">
      <p v-if="!loading && !error" role="status">
        <GitBranch :size="16" />共 {{ visibleReleases.length }} 个发行版
      </p>
    </section>

    <div v-if="loading" class="downloads-state downloads-entry" role="status" aria-live="polite">
      <LoaderCircle :size="24" class="downloads-spinner" />
      <p>正在读取 GitHub Releases…</p>
    </div>

    <div
      v-else-if="error"
      class="downloads-state downloads-entry downloads-state-error"
      role="alert"
    >
      <AlertCircle :size="24" />
      <p>{{ error }}</p>
      <button class="downloads-retry" type="button" @click="loadReleases">
        <RefreshCw :size="15" />重新加载
      </button>
    </div>

    <div v-else-if="!visibleReleases.length" class="downloads-state downloads-entry" role="status">
      <Package :size="24" />
      <p>GitHub 暂时没有可用的公开发行版。</p>
    </div>

    <div v-else class="release-list">
      <article
        v-for="(release, index) in visibleReleases"
        :key="release.id"
        class="release-card reveal"
        :style="{ '--reveal-delay': `${Math.min(index, 5) * 60}ms` }"
      >
        <header class="release-header">
          <div>
            <div class="release-title-line">
              <h2>{{ release.name || release.tag_name }}</h2>
              <span v-if="release.prerelease" class="release-badge">预发布</span>
            </div>
            <p class="release-meta">
              <code>{{ release.tag_name }}</code>
              <span
                ><CalendarDays :size="14" />{{
                  formatDate(release.published_at || release.created_at)
                }}</span
              >
            </p>
          </div>
          <a
            class="release-link"
            :href="release.html_url"
            target="_blank"
            rel="noopener noreferrer"
            :aria-label="`在 GitHub 查看 ${release.tag_name}`"
            title="在 GitHub 查看发行版"
            ><ExternalLink :size="18"
          /></a>
        </header>
        <p v-if="release.body" class="release-description">{{ release.body }}</p>
        <p v-else class="release-description release-description-empty">此发行版没有附加说明。</p>
        <div class="release-assets">
          <div class="release-assets-heading">
            <b>文件</b><span>{{ release.assets.length }} 个资产</span>
          </div>
          <p v-if="!release.assets.length" class="release-assets-empty">此发行版没有上传文件。</p>
          <a
            v-for="asset in release.assets"
            :key="asset.id"
            class="release-asset"
            :href="asset.browser_download_url"
            target="_blank"
            rel="noopener noreferrer"
          >
            <component :is="assetIcon(asset.name)" :size="18" />
            <span class="release-asset-name">{{ asset.name }}</span>
            <span class="release-asset-meta"
              >{{ formatSize(asset.size) }} · {{ formatDownloads(asset.download_count) }}</span
            >
            <Download :size="17" />
          </a>
        </div>
      </article>
    </div>
  </main>
</template>
