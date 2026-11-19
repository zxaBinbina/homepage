<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import OfficePreview from '../office/OfficePreview.vue'
import type { ConvertOutput } from './types'

const props = defineProps<{ result: ConvertOutput; name: string }>()
const markdown = computed(() => props.result.preview)
const markdownMode = ref('reading')
watch(
  () => props.result,
  () => {
    markdownMode.value = 'reading'
  },
)
const readingHtml = computed(() => {
  if (!markdown.value) return ''
  const html = marked.parse(markdown.value, { gfm: true, async: false })
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'h1',
      'h2',
      'h3',
      'h4',
      'h5',
      'h6',
      'p',
      'strong',
      'em',
      'del',
      'ul',
      'ol',
      'li',
      'blockquote',
      'pre',
      'code',
      'table',
      'thead',
      'tbody',
      'tr',
      'th',
      'td',
      'br',
      'hr',
    ],
    ALLOWED_ATTR: ['start'],
    ALLOW_DATA_ATTR: false,
    ALLOW_ARIA_ATTR: false,
  })
})
</script>

<template>
  <section class="pdfconv-visual-preview" aria-label="转换结果预览">
    <template v-if="result.extension !== 'md'">
      <h3 class="pdfconv-preview-title">Office 文件预览</h3>
      <OfficePreview :bytes="result.bytes" :name="name" />
    </template>
    <template v-else>
      <h3 class="pdfconv-preview-title">Markdown 预览</h3>
      <div class="pdfconv-preview-controls">
        <label class="jay-field"
          >Markdown 显示方式<select v-model="markdownMode" class="field">
            <option value="reading">阅读预览</option>
            <option value="source">Markdown 源码</option>
          </select></label
        >
      </div>
      <article
        v-if="markdownMode === 'reading'"
        class="pdfconv-reading"
        tabindex="0"
        aria-label="Markdown 阅读预览，可滚动查看"
        v-html="readingHtml"
      ></article>
      <label v-else class="jay-field"
        >Markdown 源码（最多 5 万字符，下载与复制包含完整内容）<textarea
          class="field pdfconv-preview"
          readonly
          :value="markdown"
          spellcheck="false"
        ></textarea>
      </label>
    </template>
  </section>
</template>
