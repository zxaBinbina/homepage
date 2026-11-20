<script setup lang="ts">
import { onBeforeUnmount, ref, shallowRef } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { FileText, Presentation, Table2, Download } from 'lucide-vue-next'
import ToolPage from '../freemium/components/ToolPage.vue'
import OfficeWorkspace from './OfficeWorkspace.vue'
import {
  blankDocument,
  downloadName,
  officeFormat,
  officeMime,
  type OfficeDocument,
  type OfficeFormat,
} from './documents'
import { saveBlob } from '../jaytools/files'

const document = shallowRef<OfficeDocument>()
const workspace = ref<InstanceType<typeof OfficeWorkspace>>()
const filename = ref('')
const input = ref<HTMLInputElement>()
const confirmDialog = ref<HTMLDialogElement>()
const ready = ref(false)
const dirty = ref(false)
const busy = ref(false)
const saving = ref(false)
const error = ref('')
const status = ref('')
let generation = 0
let decision: ((proceed: boolean) => void) | undefined

async function mayDiscard() {
  if (saving.value) return false
  if (busy.value) {
    ++generation
    busy.value = false
    status.value = ''
  }
  if (!dirty.value) return true
  if (decision) return false
  return new Promise<boolean>((resolve) => {
    decision = resolve
    confirmDialog.value?.showModal()
  })
}
function decide(proceed: boolean) {
  confirmDialog.value?.close()
  decision?.(proceed)
  decision = undefined
}
function reset() {
  ++generation
  document.value = undefined
  ready.value = false
  dirty.value = false
  error.value = ''
  status.value = ''
}
async function close() {
  if (await mayDiscard()) reset()
}
async function create(format: OfficeFormat) {
  if (!(await mayDiscard())) return
  reset()
  const version = ++generation
  busy.value = true
  error.value = ''
  status.value = '正在新建文档…'
  try {
    const created = await blankDocument(format)
    if (version !== generation) return
    ready.value = false
    dirty.value = false
    document.value = created
    filename.value = created.name
    status.value = ''
  } catch {
    if (version === generation) error.value = '新建失败，请重试。'
  } finally {
    if (version === generation) busy.value = false
  }
}
async function choose(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (input.value) input.value.value = ''
  if (!file) return
  const format = officeFormat(file.name)
  if (!format) {
    error.value = '请选择 DOCX、XLSX 或 PPTX 文件。'
    return
  }
  if (file.size > 30 * 1048576) {
    error.value = '文件超过 30 MB，请先缩小文件。'
    return
  }
  if (!(await mayDiscard())) return
  reset()
  const version = ++generation
  busy.value = true
  error.value = ''
  status.value = '正在读取文件…'
  try {
    const bytes = new Uint8Array(await file.arrayBuffer())
    if (version !== generation) return
    ready.value = false
    dirty.value = false
    document.value = { name: file.name, bytes, format }
    filename.value = file.name
    status.value = ''
  } catch {
    if (version === generation) error.value = '文件未能读取，请重试。'
  } finally {
    if (version === generation) busy.value = false
  }
}
async function download() {
  const active = document.value
  if (!active || !ready.value || saving.value) return false
  const version = generation
  error.value = ''
  status.value = ''
  try {
    const result = await workspace.value!.save()
    if (version !== generation) return false
    saveBlob(
      new Blob([new Uint8Array(result.data)], { type: officeMime[active.format] }),
      downloadName(filename.value, active.format),
    )
    dirty.value = false
    status.value = '下载已生成，请在电脑上保留这份文件。'
    return true
  } catch (reason) {
    if (version === generation)
      error.value = reason instanceof Error ? reason.message : '下载生成失败，请重试。'
    return false
  }
}
async function downloadThenDiscard() {
  if (await download()) decide(true)
}
function modified(value: boolean) {
  if (value) {
    dirty.value = true
    status.value = ''
  }
}
function beforeUnload(event: BeforeUnloadEvent) {
  if (document.value) {
    event.preventDefault()
    event.returnValue = ''
  }
}
function saveShortcut(event: KeyboardEvent) {
  if (document.value && (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
    event.preventDefault()
    if (!confirmDialog.value?.open) void download()
  }
}
window.addEventListener('beforeunload', beforeUnload)
window.addEventListener('keydown', saveShortcut, true)
onBeforeRouteLeave(() => mayDiscard())
onBeforeUnmount(() => {
  ++generation
  decision?.(false)
  decision = undefined
  window.removeEventListener('beforeunload', beforeUnload)
  window.removeEventListener('keydown', saveShortcut, true)
})
</script>

<template>
  <ToolPage>
    <div class="office-editor-panel">
      <div class="jay-actions office-editor-new">
        <button class="btn" type="button" :disabled="busy || saving" @click="create('docx')">
          <FileText :size="18" aria-hidden="true" />新建 Word
        </button>
        <button class="btn" type="button" :disabled="busy || saving" @click="create('xlsx')">
          <Table2 :size="18" aria-hidden="true" />新建 Excel
        </button>
        <button class="btn" type="button" :disabled="busy || saving" @click="create('pptx')">
          <Presentation :size="18" aria-hidden="true" />新建 PowerPoint
        </button>
        <label class="jay-field jay-file"
          ><input
            ref="input"
            class="jay-file-input"
            type="file"
            accept=".docx,.xlsx,.pptx"
            aria-label="打开 Office 文件"
            :disabled="busy || saving"
            @change="choose"
          /><span class="jay-file-control" aria-hidden="true"
            ><span class="btn jay-file-choice">打开文件</span></span
          ></label
        >
        <button v-if="document || busy" class="btn" type="button" :disabled="saving" @click="close">
          关闭文档
        </button>
      </div>
      <p class="jay-note">
        支持 DOCX、XLSX、PPTX，文件最多 30 MB。编辑后请下载保留，页面关闭后不会保留文档。
      </p>
      <p v-if="error" class="jay-error" role="alert">{{ error }}</p>
      <p v-if="status" class="jay-note" role="status">{{ status }}</p>
      <template v-if="document">
        <div class="office-editor-filebar">
          <label class="jay-field"
            >下载文件名<input v-model="filename" class="field" :disabled="saving"
          /></label>
          <button
            class="btn btn--prominent"
            type="button"
            :disabled="!ready || saving || busy"
            @click="download"
          >
            <Download :size="18" aria-hidden="true" />{{
              saving ? '正在生成文件…' : '下载编辑后的文件'
            }}
          </button>
        </div>
        <OfficeWorkspace
          ref="workspace"
          :name="document.name"
          :bytes="document.bytes"
          editable
          @ready="ready = $event"
          @modified="modified"
          @save-requested="download"
          @saving="saving = $event"
          @warning="error = $event"
        />
        <p class="jay-note">
          Ctrl / ⌘ + S 生成下载。文档仅在当前页面编辑，支持文字、表格、公式、幻灯片与插入图片。
        </p>
      </template>
      <div v-else class="office-editor-empty">
        <FileText :size="36" aria-hidden="true" />
        <h2>从一份文档开始</h2>
        <p>新建 Word、Excel 或 PowerPoint，也可以打开已有文件继续编辑。</p>
      </div>
      <dialog
        ref="confirmDialog"
        class="office-discard-dialog"
        aria-labelledby="office-discard-title"
        @cancel.prevent="decide(false)"
      >
        <h2 id="office-discard-title">保留还未下载的修改？</h2>
        <p>可以先生成下载，再继续；放弃修改后将关闭当前文档。</p>
        <div class="jay-actions">
          <button
            class="btn btn--prominent"
            type="button"
            :disabled="saving || !ready"
            @click="downloadThenDiscard"
          >
            下载并继续
          </button>
          <button class="btn" type="button" :disabled="saving" @click="decide(true)">
            放弃修改
          </button>
          <button class="btn" type="button" :disabled="saving" @click="decide(false)">
            返回编辑
          </button>
        </div>
      </dialog>
    </div>
  </ToolPage>
</template>
