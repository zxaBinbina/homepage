<script setup lang="ts">
import { ref, watch } from 'vue'
import { Clock3 } from 'lucide-vue-next'
import OutputPanel from './OutputPanel.vue'
import { dateInputValue, parseDateInput, parseTimestamp, type TimeZone } from '../transform'

const timestamp = ref('')
const unit = ref<'seconds' | 'milliseconds'>('seconds')
const date = ref('')
const zone = ref<TimeZone>('local')
const localZone = Intl.DateTimeFormat().resolvedOptions().timeZone
const output = ref('')
const ready = ref(false)
const error = ref('')
watch(
  [timestamp, unit, date, zone],
  () => {
    output.value = ''
    ready.value = false
    error.value = ''
  },
  { flush: 'sync' },
)
function show(value: Date) {
  output.value = [
    `Unix 时间戳（秒，向下取整）：${Math.floor(value.getTime() / 1000)}`,
    `Unix 时间戳（毫秒）：${value.getTime()}`,
    `UTC：${value.toISOString()}`,
    `本地时间（${localZone}）：${dateInputValue(value, 'local').replace('T', ' ')}`,
  ].join('\n')
  ready.value = true
}
function convert(direction: 'timestamp' | 'date') {
  output.value = ''
  ready.value = false
  error.value = ''
  try {
    const value =
      direction === 'timestamp'
        ? parseTimestamp(timestamp.value, unit.value)
        : parseDateInput(date.value, zone.value)
    if (direction === 'timestamp') date.value = dateInputValue(value, zone.value)
    else
      timestamp.value = String(
        unit.value === 'seconds' ? Math.floor(value.getTime() / 1000) : value.getTime(),
      )
    show(value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '转换失败，请检查时间。'
  }
}
function now() {
  const value = new Date()
  timestamp.value = String(
    unit.value === 'seconds' ? Math.floor(value.getTime() / 1000) : value.getTime(),
  )
  date.value = dateInputValue(value, zone.value)
  error.value = ''
  show(value)
}
</script>

<template>
  <div class="tool-workspace">
    <div class="tool-controls">
      <button type="button" class="button secondary" @click="now">
        <Clock3 :size="16" aria-hidden="true" />使用当前时间</button
      ><span class="tool-muted">本地时区：{{ localZone }}</span>
    </div>
    <div class="tool-editor-grid">
      <form class="tool-form-panel" @submit.prevent="convert('timestamp')">
        <h2>时间戳 → 日期</h2>
        <label class="tool-field"
          >时间单位<select v-model="unit" aria-label="时间单位">
            <option value="seconds">秒（s）</option>
            <option value="milliseconds">毫秒（ms）</option>
          </select></label
        >
        <label class="tool-field"
          >Unix 时间戳<input
            v-model="timestamp"
            type="text"
            inputmode="text"
            placeholder="例如 1704067200"
            autocomplete="off"
        /></label>
        <button type="submit" class="button primary">转为日期</button>
      </form>
      <form class="tool-form-panel" @submit.prevent="convert('date')">
        <h2>日期 → 时间戳</h2>
        <label class="tool-field"
          >日期时区<select v-model="zone" aria-label="日期时区">
            <option value="local">本地（{{ localZone }}）</option>
            <option value="utc">UTC</option>
          </select></label
        >
        <label class="tool-field"
          >日期与时间<input
            v-model="date"
            type="datetime-local"
            min="0001-01-01T00:00"
            max="9999-12-31T23:59:59.999"
            step="0.001"
        /></label>
        <button type="submit" class="button primary">转为时间戳</button>
      </form>
    </div>
    <p v-if="error" class="tool-error" role="alert">{{ error }}</p>
    <OutputPanel
      class="tool-compact-output"
      :value="output"
      :ready="ready"
      filename="timestamp.txt"
    />
    <p class="tool-muted tool-time-note">
      夏令时结束时重复出现的本地时间按浏览器规则取较早的一次；需要明确时刻时请选择 UTC。
    </p>
  </div>
</template>
