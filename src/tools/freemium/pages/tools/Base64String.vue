<template>
  <TransformTool
    :transform="transform"
    :options="options"
    :swap="{ key: 'mode', values: ['encode', 'decode'] }"
    sample="Hello, Freemium 👋 — Base64 handles UTF-8."
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
  { key: 'urlSafe', type: 'toggle', label: 'URL 安全模式', default: false },
]

const toB64 = (bytes) => btoa(Array.from(bytes, (b) => String.fromCharCode(b)).join(''))

function transform(input, { mode, urlSafe }) {
  if (mode === 'encode') {
    const out = toB64(new TextEncoder().encode(input))
    return urlSafe ? out.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '') : out
  }
  let s = input.trim().replace(/\s+/g, '').replace(/-/g, '+').replace(/_/g, '/')
  s += '='.repeat((4 - (s.length % 4)) % 4)
  let bin
  try {
    bin = atob(s)
  } catch {
    throw new Error('Base64 格式不正确，请检查多余字符。')
  }
  return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)))
}
</script>
