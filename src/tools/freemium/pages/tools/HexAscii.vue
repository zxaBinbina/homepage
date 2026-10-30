<template>
  <TransformTool
    :transform="transform"
    :options="options"
    :swap="{ key: 'mode', values: ['toHex', 'toText'] }"
    sample="Hello, Freemium ✓"
    :input-label="'输入'"
    :download="(o) => (o.mode === 'toHex' ? 'hex.txt' : 'text.txt')"
  />
</template>

<script setup>
import TransformTool from '../../components/TransformTool.vue'

const options = [
  {
    key: 'mode',
    type: 'segmented',
    label: '方向',
    default: 'toHex',
    options: [
      { value: 'toHex', label: '文本 → 十六进制' },
      { value: 'toText', label: '十六进制 → 文本' },
    ],
  },
  {
    key: 'format',
    type: 'select',
    label: '十六进制格式',
    default: 'spaced',
    options: [
      { value: 'spaced', label: '48 65 6c' },
      { value: 'plain', label: '48656c' },
      { value: '0x', label: '0x48 0x65' },
      { value: 'escape', label: '\\x48\\x65' },
    ],
  },
  { key: 'upper', type: 'toggle', label: '大写', default: false },
]

function transform(input, o) {
  if (o.mode === 'toHex') {
    const hex = Array.from(new TextEncoder().encode(input), (b) => {
      const h = b.toString(16).padStart(2, '0')
      return o.upper ? h.toUpperCase() : h
    })
    if (o.format === 'plain') return hex.join('')
    if (o.format === '0x') return hex.map((h) => `0x${h}`).join(' ')
    if (o.format === 'escape') return hex.map((h) => `\\x${h}`).join('')
    return hex.join(' ')
  }
  const clean = input.replace(/0x|\\x|[\s,:-]/gi, '')
  if (/[^0-9a-f]/i.test(clean))
    throw new Error(
      'Hex input can only contain 0–9 and a–f (separators, 0x and \\x prefixes are ignored).',
    )
  if (clean.length % 2)
    throw new Error(`十六进制数字数量为奇数（${clean.length}），每个字节需要两个数字。`)
  const bytes = new Uint8Array(clean.length / 2)
  for (let i = 0; i < bytes.length; i++) bytes[i] = parseInt(clean.substr(i * 2, 2), 16)
  return new TextDecoder('utf-8', { fatal: false }).decode(bytes)
}
</script>
