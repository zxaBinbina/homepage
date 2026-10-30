<template>
  <TransformTool
    :transform="transform"
    :options="options"
    :sample="sample"
    accept=".json,application/json,text/plain"
    :download="(o) => (o.mode === 'minify' ? 'data.min.json' : 'data.json')"
  />
</template>

<script setup>
import TransformTool from '../../components/TransformTool.vue'

const options = [
  {
    key: 'mode',
    type: 'segmented',
    label: '模式',
    default: 'format',
    options: [
      { value: 'format', label: '格式化' },
      { value: 'minify', label: '压缩' },
    ],
  },
  {
    key: 'indent',
    type: 'select',
    label: '缩进',
    default: '2',
    options: [
      { value: '2', label: '2 个空格' },
      { value: '4', label: '4 个空格' },
      { value: 'tab', label: 'Tab 缩进' },
    ],
  },
  { key: 'sortKeys', type: 'toggle', label: '按键名排序', default: false },
]

const sample = () =>
  JSON.stringify({
    id: 1024,
    name: 'Freemium',
    private: true,
    tags: ['json', 'tools'],
    owner: { login: 'incentius', url: 'https://incentius.com' },
    stars: 42.5,
    license: null,
  })

function sortDeep(v) {
  if (Array.isArray(v)) return v.map(sortDeep)
  if (v && typeof v === 'object')
    return Object.fromEntries(
      Object.keys(v)
        .sort()
        .map((k) => [k, sortDeep(v[k])]),
    )
  return v
}

// JSON.parse errors only give an offset; turn it into "line X, column Y".
function locate(input, message) {
  const m = /position (\d+)/i.exec(message)
  if (!m) return message
  const pos = Number(m[1])
  const before = input.slice(0, pos).split('\n')
  return `${message.replace(/ in JSON at position \d+.*$/i, '')} — line ${before.length}, column ${before[before.length - 1].length + 1}`
}

function transform(input, o) {
  let data
  try {
    data = JSON.parse(input)
  } catch (e) {
    throw new Error(locate(input, e.message))
  }
  if (o.sortKeys) data = sortDeep(data)
  if (o.mode === 'minify') return JSON.stringify(data)
  return JSON.stringify(data, null, o.indent === 'tab' ? '\t' : Number(o.indent))
}
</script>
