<template>
  <ToolPage fill>
    <template #options>
      <label v-if="sheetNames.length > 1" class="opt">
        <span>工作表</span>
        <select v-model="sheet" class="field opt__control">
          <option v-for="n in sheetNames" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <Segmented
        v-model="shape"
        label="行格式"
        :options="[
          { value: 'objects', label: '对象' },
          { value: 'arrays', label: '数组' },
        ]"
      />
      <Toggle v-model="allSheets" label="全部工作表" />
      <Toggle v-model="raw" label="原始数值" />
    </template>

    <div class="split">
      <section
        class="drop card"
        :class="{ 'drop--active': dragging }"
        aria-label="工作簿"
        @dragover.prevent="dragging = true"
        @dragleave="dragging = false"
        @drop.prevent="onDrop"
      >
        <header class="drop__bar">
          <h2 class="drop__label">工作簿</h2>
          <span class="drop__spacer" />
          <button class="btn btn--plain btn--sm" type="button" @click="loadSample">
            <AppIcon name="sparkles" :size="16" />示例
          </button>
          <button
            class="icon-btn icon-btn--sm"
            type="button"
            aria-label="清空"
            title="清空"
            :disabled="!fileName"
            @click="clear"
          >
            <AppIcon name="clear" :size="18" />
          </button>
        </header>
        <div class="drop__body">
          <div class="drop__zone">
            <ToolIcon icon="table" color="green" :size="56" />
            <template v-if="fileName">
              <p class="t-headline">{{ fileName }}</p>
              <p class="t-footnote t-secondary">
                {{ sheetNames.length }} {{ sheetNames.length === 1 ? 'sheet' : 'sheets' }} ·
                {{ rowCount.toLocaleString() }} 行
              </p>
            </template>
            <template v-else>
              <p class="t-headline">将 Excel 文件拖到这里</p>
              <p class="t-footnote t-secondary">支持 .xlsx、.xls、.ods、.csv，仅在本地读取文件。</p>
            </template>
            <button class="btn btn--prominent" type="button" @click="fileInput.click()">
              <AppIcon name="docOpen" :size="16" />选择文件…
            </button>
            <input
              ref="fileInput"
              class="sr-only"
              type="file"
              accept=".xlsx,.xls,.xlsm,.ods,.csv"
              tabindex="-1"
              aria-hidden="true"
              @change="onPick"
            />
          </div>
        </div>
        <footer v-if="error" class="drop__foot">
          <p class="drop__error" role="status"><AppIcon name="warning" :size="16" />{{ error }}</p>
        </footer>
      </section>

      <CodePane :model-value="output" label="JSON" :download="downloadName" readonly />
    </div>
  </ToolPage>
</template>

<script setup>
import { computed, ref, shallowRef } from 'vue'
import { read, utils } from 'xlsx'
import ToolPage from '../../components/ToolPage.vue'
import CodePane from '../../components/CodePane.vue'
import AppIcon from '../../components/AppIcon.vue'
import ToolIcon from '../../components/ToolIcon.vue'
import Segmented from '../../components/ui/Segmented.vue'
import Toggle from '../../components/ui/Toggle.vue'

const fileInput = ref(null)
const dragging = ref(false)
const workbook = shallowRef(null)
const fileName = ref('')
const sheet = ref('')
const shape = ref('objects')
const allSheets = ref(false)
const raw = ref(true)
const error = ref('')

const sheetNames = computed(() => workbook.value?.SheetNames || [])
const downloadName = computed(() => `${(fileName.value || 'workbook').replace(/\.\w+$/, '')}.json`)

function sheetToJson(name) {
  return utils.sheet_to_json(workbook.value.Sheets[name], {
    header: shape.value === 'arrays' ? 1 : undefined,
    raw: raw.value,
    defval: null,
  })
}

const data = computed(() => {
  if (!workbook.value || !sheet.value) return null
  if (allSheets.value) return Object.fromEntries(sheetNames.value.map((n) => [n, sheetToJson(n)]))
  return sheetToJson(sheet.value)
})
const output = computed(() => (data.value ? JSON.stringify(data.value, null, 2) : ''))
const rowCount = computed(() => {
  if (!data.value) return 0
  return Array.isArray(data.value)
    ? data.value.length
    : Object.values(data.value).reduce((n, r) => n + r.length, 0)
})

async function loadBuffer(buffer, name) {
  error.value = ''
  try {
    workbook.value = read(buffer, { cellDates: true })
    fileName.value = name
    sheet.value = workbook.value.SheetNames[0] || ''
    if (!sheet.value) error.value = '工作簿中没有工作表。'
  } catch (e) {
    workbook.value = null
    fileName.value = ''
    error.value = `文件读取失败：${e.message}`
  }
}

async function loadFile(file) {
  if (file) await loadBuffer(await file.arrayBuffer(), file.name)
}
function onPick(e) {
  loadFile(e.target.files[0])
  e.target.value = ''
}
function onDrop(e) {
  dragging.value = false
  loadFile(e.dataTransfer.files[0])
}
async function loadSample() {
  try {
    const res = await fetch('/tools/freemium-sample.xlsx')
    await loadBuffer(await res.arrayBuffer(), 'sample.xlsx')
  } catch (e) {
    error.value = `示例加载失败：${e.message}`
  }
}
function clear() {
  workbook.value = null
  fileName.value = ''
  sheet.value = ''
  error.value = ''
}
</script>

<style scoped>
.opt {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8125rem;
  color: var(--label-2);
}
.opt__control {
  min-height: 32px;
  width: auto;
  font-size: 0.8125rem;
  border-radius: 999px;
}
@media (pointer: coarse) {
  .opt__control {
    min-height: 44px;
  }
}
.drop {
  display: flex;
  flex-direction: column;
  min-height: 260px;
  overflow: hidden;
  transition: box-shadow 160ms ease;
}
.drop--active {
  box-shadow: inset 0 0 0 2px var(--tint);
}
.drop__bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 8px 6px 16px;
  min-height: 46px;
}
.drop__label {
  font-size: 0.9375rem;
  font-weight: 600;
}
.drop__spacer {
  flex: 1;
}
.drop__bar .btn--plain {
  color: var(--tint-text);
}
.drop__body {
  flex: 1;
  display: flex;
  padding: 0 12px 12px;
}
.drop__zone {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  text-align: center;
  border-radius: 14px;
  border: 1.5px dashed var(--separator);
}
.drop__zone .btn {
  margin-top: 8px;
}
.drop__foot {
  padding: 6px 16px 10px;
  border-top: 0.5px solid var(--separator);
}
.drop__error {
  display: flex;
  gap: 6px;
  align-items: flex-start;
  color: var(--danger-text);
  font-size: 0.8125rem;
  font-weight: 500;
}
</style>
