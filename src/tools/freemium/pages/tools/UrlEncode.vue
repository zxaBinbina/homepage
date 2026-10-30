<template>
  <TransformTool
    :transform="transform"
    :options="options"
    :swap="{ key: 'mode', values: ['encode', 'decode'] }"
    sample="https://example.com/search?q=liquid glass & café&lang=en-US#top"
    :download="(o) => (o.mode === 'encode' ? 'encoded.txt' : 'decoded.txt')"
  />
</template>

<script setup>
import TransformTool from '../../components/TransformTool.vue'

const options = [
  {
    key: 'mode',
    type: 'segmented',
    label: '方向',
    default: 'encode',
    options: [
      { value: 'encode', label: '编码' },
      { value: 'decode', label: '解码' },
    ],
  },
  {
    key: 'scheme',
    type: 'select',
    label: '编码方式',
    default: 'component',
    options: [
      { value: 'component', label: '参数值（encodeURIComponent）' },
      { value: 'uri', label: '完整网址（encodeURI）' },
      { value: 'form', label: '表单（空格转为 +）' },
    ],
  },
  { key: 'perLine', type: 'toggle', label: '逐行处理', default: false },
]

function encodeOne(s, scheme) {
  if (scheme === 'uri') return encodeURI(s)
  const out = encodeURIComponent(s)
  return scheme === 'form' ? out.replace(/%20/g, '+') : out
}

function decodeOne(s, scheme) {
  const src = scheme === 'form' ? s.replace(/\+/g, ' ') : s
  try {
    return scheme === 'uri' ? decodeURI(src) : decodeURIComponent(src)
  } catch {
    throw new Error('URL 编码不正确，百分号后需要两个十六进制数字。')
  }
}

function transform(input, { mode, scheme, perLine }) {
  const fn = mode === 'encode' ? encodeOne : decodeOne
  return perLine
    ? input
        .split('\n')
        .map((l) => fn(l, scheme))
        .join('\n')
    : fn(input, scheme)
}
</script>
