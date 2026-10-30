<script setup>
// Adapted from jaywcjlove/tools packages/exif-viewer (MIT).
import { computed, onBeforeUnmount, ref } from 'vue'
import ExifReader from 'exifreader'
import ToolPage from '../freemium/components/ToolPage.vue'
import CodePane from '../freemium/components/CodePane.vue'
const tags = ref(null)
const error = ref('')
const busy = ref(false)
const query = ref('')
const name = ref('')
let version = 0
const json = computed(() => (tags.value ? JSON.stringify(tags.value, null, 2) : ''))
const rows = computed(() =>
  Object.entries(tags.value || {}).filter(([key, value]) =>
    `${key} ${value.description || ''}`.toLowerCase().includes(query.value.toLowerCase()),
  ),
)
async function select(event) {
  const id = ++version
  tags.value = null
  error.value = ''
  busy.value = false
  const file = event.target.files?.[0]
  if (!file) return
  name.value = file.name
  busy.value = true
  try {
    if (file.size > 30 * 1024 * 1024) throw new Error('图片请控制在 30 MB 以内。')
    const result = ExifReader.load(await file.arrayBuffer())
    delete result.MakerNote
    // Thumbnail bytes are omitted from JSON to keep large metadata readable.
    if (result.Thumbnail) delete result.Thumbnail.image
    if (version === id) tags.value = result
  } catch (e) {
    if (version === id) error.value = `无法读取图片信息：${e.message}`
  } finally {
    if (version === id) busy.value = false
  }
}
onBeforeUnmount(() => version++)
</script>
<template>
  <ToolPage>
    <div class="jay-panel">
      <label class="jay-field jay-file"
        >选择图片<input
          type="file"
          accept="image/*,.heic,.heif,.avif"
          class="sr-only"
          aria-label="选择图片"
          @change="select"
        /><span class="jay-file-control" aria-hidden="true"
          ><span class="btn jay-file-choice">选择文件</span
          ><span>{{ name || '未选择图片' }}</span></span
        ></label
      >
      <p class="jay-note">
        支持 JPEG、PNG、WebP、HEIC 等格式。并非每张图片都包含拍摄参数；结果可能包含原文件中的 GPS
        信息。
      </p>
    </div>
    <p v-if="busy" role="status">正在读取图片信息…</p>
    <p v-if="error" class="jay-error" role="alert">{{ error }}</p>
    <Transition name="jay-panel" mode="out-in">
      <div v-if="tags" :key="name" class="split">
        <section class="jay-panel">
          <label class="jay-field"
            >筛选字段<input
              v-model="query"
              type="search"
              class="field"
              placeholder="例如 Date、GPS、Width"
          /></label>
          <dl class="jay-metadata">
            <template v-for="[key, value] in rows" :key="key"
              ><dt>{{ key }}</dt>
              <dd>{{ value.description ?? '—' }}</dd></template
            >
          </dl>
          <p v-if="!rows.length" class="jay-note">没有匹配的元数据。</p>
        </section>
        <CodePane :model-value="json" label="完整元数据" readonly download="metadata.json" />
      </div>
    </Transition>
  </ToolPage>
</template>
