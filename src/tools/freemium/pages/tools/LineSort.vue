<template>
  <TransformTool
    :transform="transform"
    :options="options"
    sample="banana
Apple
cherry
apple
item 10
item 2

  date  
banana
Elderberry"
    accept=".txt,.csv,.log,text/plain"
    download="lines.txt"
  />
</template>

<script setup>
import TransformTool from '../../components/TransformTool.vue'

const options = [
  {
    key: 'sort',
    type: 'select',
    label: '顺序',
    default: 'az',
    options: [
      { value: 'none', label: '保持原顺序' },
      { value: 'az', label: 'A → Z' },
      { value: 'za', label: 'Z → A' },
      { value: 'natural', label: '自然排序（2 排在 10 前）' },
      { value: 'length', label: '短行优先' },
      { value: 'length-desc', label: '长行优先' },
      { value: 'shuffle', label: '随机打乱' },
    ],
  },
  { key: 'reverse', type: 'toggle', label: '反转', default: false },
  { key: 'dedupe', type: 'toggle', label: '移除重复行', default: true },
  { key: 'ignoreCase', type: 'toggle', label: '忽略大小写', default: true },
  { key: 'trim', type: 'toggle', label: '去除行首尾空白', default: true },
  { key: 'removeEmpty', type: 'toggle', label: '移除空行', default: true },
]

function shuffle(arr) {
  const a = [...arr]
  const rnd = new Uint32Array(a.length)
  crypto.getRandomValues(rnd)
  for (let i = a.length - 1; i > 0; i--) {
    const j = rnd[i] % (i + 1)
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function transform(input, o) {
  let lines = input.split(/\r?\n/)
  if (o.trim) lines = lines.map((l) => l.trim())
  if (o.removeEmpty) lines = lines.filter((l) => l.trim() !== '')
  if (o.dedupe) {
    const seen = new Set()
    lines = lines.filter((l) => {
      const k = o.ignoreCase ? l.toLowerCase() : l
      if (seen.has(k)) return false
      seen.add(k)
      return true
    })
  }
  const collator = new Intl.Collator(undefined, {
    sensitivity: o.ignoreCase ? 'base' : 'variant',
    caseFirst: 'upper',
    numeric: o.sort === 'natural',
  })
  switch (o.sort) {
    case 'az':
    case 'natural':
      lines.sort(collator.compare)
      break
    case 'za':
      lines.sort((a, b) => collator.compare(b, a))
      break
    case 'length':
      lines.sort((a, b) => a.length - b.length || collator.compare(a, b))
      break
    case 'length-desc':
      lines.sort((a, b) => b.length - a.length || collator.compare(a, b))
      break
    case 'shuffle':
      lines = shuffle(lines)
      break
  }
  if (o.reverse) lines.reverse()
  return lines.join('\n')
}
</script>
