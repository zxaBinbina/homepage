<template>
  <ToolPage>
    <template #options>
      <label class="opt">
        <span class="opt__label">长度</span>
        <input v-model.number="length" class="field opt__field" type="number" min="1" max="4096" />
      </label>
      <label class="opt">
        <span class="opt__label">数量</span>
        <input v-model.number="count" class="field opt__field" type="number" min="1" max="1000" />
      </label>
      <button class="btn btn--prominent btn--sm" type="button" @click="generate">
        <AppIcon name="dice" :size="16" />生成
      </button>
    </template>

    <div class="split">
      <section class="card sets" aria-labelledby="sets-title">
        <h2 id="sets-title" class="sets__title">字符</h2>
        <ul class="inset-list" role="list">
          <li v-for="set in SETS" :key="set.key" class="row">
            <Toggle v-model="enabled[set.key]" :label="set.label" />
            <span class="row__value">{{ set.preview }}</span>
          </li>
          <li class="row">
            <Toggle v-model="enabled.custom" label="自定义" />
            <input
              v-model="custom"
              class="field sets__custom"
              type="text"
              placeholder="e.g. αβγ-_"
              aria-label="自定义字符"
              spellcheck="false"
              @input="enabled.custom = !!custom"
            />
          </li>
          <li class="row">
            <Toggle v-model="noLookalikes" label="排除易混字符（I l 1 O 0 o）" />
          </li>
        </ul>

        <div class="strength">
          <span class="badge" :class="strength.cls">
            <AppIcon :name="strength.icon" :size="12" />{{ strength.label }}
          </span>
          <span class="t-footnote t-secondary">
            {{ entropy.toFixed(0) }} 位熵 · {{ pool.length }} 种可用字符
          </span>
        </div>
        <p v-if="!pool.length" class="t-footnote warn" role="status">
          <AppIcon name="warning" :size="14" /> 请至少选择一组字符。
        </p>
        <p class="t-footnote t-secondary note">
          使用浏览器安全随机数
          <code>crypto.getRandomValues</code> 与拒绝采样，使每个字符被选中的概率相等。
        </p>
      </section>

      <CodePane :model-value="output" label="结果" readonly download="random.txt" />
    </div>
  </ToolPage>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import ToolPage from '../../components/ToolPage.vue'
import CodePane from '../../components/CodePane.vue'
import AppIcon from '../../components/AppIcon.vue'
import Toggle from '../../components/ui/Toggle.vue'
import { load, save } from '../../composables/storage'

const SETS = [
  { key: 'upper', label: '大写', chars: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', preview: 'A–Z' },
  { key: 'lower', label: '小写', chars: 'abcdefghijklmnopqrstuvwxyz', preview: 'a–z' },
  { key: 'digits', label: '数字', chars: '0123456789', preview: '0–9' },
  { key: 'symbols', label: '符号', chars: '!@#$%^&*()-_=+[]{};:,.<>/?~', preview: '!@#$%…' },
]
const LOOKALIKES = new Set('Il1O0o|`\'"'.split(''))

const saved = load('freemium:opts:random-string', {})
const length = ref(saved.length ?? 24)
const count = ref(saved.count ?? 5)
const enabled = reactive({
  upper: true,
  lower: true,
  digits: true,
  symbols: false,
  custom: false,
  ...saved.enabled,
})
const custom = ref(saved.custom ?? '')
const noLookalikes = ref(saved.noLookalikes ?? false)
const output = ref('')

const pool = computed(() => {
  let chars = SETS.filter((s) => enabled[s.key])
    .map((s) => s.chars)
    .join('')
  if (enabled.custom) chars += custom.value
  let list = [...new Set(Array.from(chars))]
  if (noLookalikes.value) list = list.filter((c) => !LOOKALIKES.has(c))
  return list
})

const clampLen = computed(() => Math.min(Math.max(Number(length.value) || 1, 1), 4096))
const clampCount = computed(() => Math.min(Math.max(Number(count.value) || 1, 1), 1000))
const entropy = computed(() =>
  pool.value.length > 1 ? clampLen.value * Math.log2(pool.value.length) : 0,
)
const strength = computed(() => {
  const e = entropy.value
  if (e < 40) return { label: '弱', icon: 'warning', cls: 'badge--err' }
  if (e < 64) return { label: '一般', icon: 'info', cls: '' }
  if (e < 100) return { label: '强', icon: 'check', cls: 'badge--ok' }
  return { label: '很强', icon: 'shield', cls: 'badge--ok' }
})

// Uniform index in [0, n) — rejects values in the biased tail of the 32-bit range.
function randomIndex(n, buf) {
  const limit = Math.floor(0x100000000 / n) * n
  for (;;) {
    crypto.getRandomValues(buf)
    if (buf[0] < limit) return buf[0] % n
  }
}

function generate() {
  const chars = pool.value
  if (!chars.length) {
    output.value = ''
    return
  }
  const buf = new Uint32Array(1)
  const lines = []
  for (let i = 0; i < clampCount.value; i++) {
    let s = ''
    for (let j = 0; j < clampLen.value; j++) s += chars[randomIndex(chars.length, buf)]
    lines.push(s)
  }
  output.value = lines.join('\n')
}

watch(
  [length, count, enabled, custom, noLookalikes],
  () => {
    save('freemium:opts:random-string', {
      length: length.value,
      count: count.value,
      enabled: { ...enabled },
      custom: custom.value,
      noLookalikes: noLookalikes.value,
    })
    generate()
  },
  { deep: true },
)

onMounted(generate)
</script>

<style scoped>
.opt {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8125rem;
  color: var(--label-2);
}
.opt__field {
  width: 84px;
  min-height: 32px;
  border-radius: 999px;
  font-size: 0.8125rem;
}
@media (pointer: coarse) {
  .opt__field {
    min-height: 44px;
  }
}

.sets {
  padding: 8px 0 16px;
  align-self: start;
  overflow: hidden;
}
.sets__title {
  padding: 6px 16px 10px;
  font-size: 0.9375rem;
  font-weight: 600;
  letter-spacing: -0.015em;
}
.sets .inset-list {
  border-radius: 0;
  border-top: 0.5px solid var(--separator);
  border-bottom: 0.5px solid var(--separator);
}
.sets .row {
  justify-content: space-between;
  min-height: 48px;
}
.sets__custom {
  max-width: 180px;
  min-height: 32px;
  border-radius: 999px;
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  letter-spacing: 0;
}
.strength {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 14px 16px 0;
}
.warn {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding: 8px 16px 0;
  color: var(--danger-text);
}
.note {
  margin: 0;
  padding: 8px 16px 0;
}
.note code {
  font-size: 0.75rem;
}
</style>
