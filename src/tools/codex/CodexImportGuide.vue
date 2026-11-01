<script setup lang="ts">
import { computed } from 'vue'
import Segmented from '../freemium/components/ui/Segmented.vue'
import type { ImportPlatform } from './importPlatform'

const platform = defineModel<ImportPlatform>({ required: true })
const options = [
  { value: 'windows', label: 'Windows' },
  { value: 'macos', label: 'macOS' },
  { value: 'linux', label: 'Linux' },
]
const guides = {
  windows: {
    name: 'Windows',
    instructions: '按 Win + E 打开资源管理器，按 Alt + D 选中地址栏，粘贴下方路径后回车。',
    path: '%USERPROFILE%\\.codex\\sessions',
    archivedPath: '%USERPROFILE%\\.codex\\archived_sessions',
    hint: '%USERPROFILE% 表示当前 Windows 用户的主目录，直接输入完整路径即可进入。',
  },
  macos: {
    name: 'macOS',
    instructions: '打开 Finder，按 Command + Shift + G，在「前往文件夹」中粘贴下方路径。',
    path: '~/.codex/sessions',
    archivedPath: '~/.codex/archived_sessions',
    hint: '~ 表示当前用户的主目录；.codex 是隐藏目录，直接输入完整路径即可进入。',
  },
  linux: {
    name: 'Linux',
    instructions: '打开文件管理器，按 Ctrl + L 编辑位置，粘贴下方路径后回车。',
    path: '~/.codex/sessions',
    archivedPath: '~/.codex/archived_sessions',
    hint: '~ 表示当前用户的主目录；.codex 是隐藏目录，直接输入完整路径即可进入。',
  },
}
const guide = computed(() => guides[platform.value])
</script>

<template>
  <section id="codex-import-guide" class="codex-import-guide" aria-labelledby="codex-guide-title">
    <h3 id="codex-guide-title">如何找到并导入对话文件</h3>
    <p>在运行 Codex 的电脑上查找本地对话记录。先等当前回复结束，再选择要清理的文件。</p>
    <Segmented
      v-model="platform"
      :options="options"
      class="codex-import-switcher"
      label="教程适用系统"
    />
    <ol class="codex-import-steps">
      <li>
        <h4>打开对话记录目录</h4>
        <div class="codex-import-platform" aria-live="polite" aria-atomic="true">
          <h4>{{ guide.name }}</h4>
          <p>{{ guide.instructions }}</p>
          <code>{{ guide.path }}</code>
        </div>
        <p>{{ guide.hint }}</p>
      </li>
      <li>
        <h4>找到你要分享的会话</h4>
        <p>
          在目录及其子文件夹中查找 <code>.jsonl</code> 文件，可搜索 <code>*.jsonl</code>，
          再按修改时间定位最近的对话。文件较多时，用文本编辑器查看内容，核对对话文字和项目路径。
        </p>
      </li>
      <li>
        <h4>选择文件，开始清理</h4>
        <p>
          点击旁边的「选择文件」，选中找到的 JSONL 文件；保持默认精确模式或选择其他模式，
          点击「开始清理」。校验通过后可预览结果并下载清理后的文件，原文件不会被覆盖。
        </p>
      </li>
    </ol>
    <div class="codex-import-help">
      <h4>没有找到文件？</h4>
      <ul>
        <li>
          <strong>归档对话：</strong>查看 <code>{{ guide.archivedPath }}</code
          >。
        </li>
        <li>
          <strong>自定义目录：</strong>若设置了环境变量 <code>CODEX_HOME</code>，请在它指向的目录下
          查找 <code>sessions</code> 或 <code>archived_sessions</code>。
        </li>
        <li v-if="platform === 'windows'">
          <strong>WSL：</strong>查找 WSL 内 Linux 用户的目录；可在 WSL 终端进入
          <code>~/.codex/sessions</code> 后运行 <code>explorer.exe .</code>，用 Windows
          资源管理器打开。
        </li>
        <li>
          <strong>SSH、远程开发或容器：</strong>在实际运行 Codex
          的环境中查找记录，复制到当前电脑后再导入。
        </li>
      </ul>
    </div>
    <p class="codex-import-sources">
      位置说明参考 OpenAI 官方文档：
      <a
        href="https://learn.chatgpt.com/docs/reference/troubleshooting"
        target="_blank"
        rel="noopener noreferrer"
        >会话记录位置</a
      >
      ·
      <a
        href="https://learn.chatgpt.com/docs/config-file/environment-variables"
        target="_blank"
        rel="noopener noreferrer"
        >CODEX_HOME 环境变量</a
      >
    </p>
  </section>
</template>
