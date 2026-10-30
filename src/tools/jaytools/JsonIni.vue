<script setup>
import TransformTool from '../freemium/components/TransformTool.vue'
import { transform } from './json-ini'
const options = [
  {
    key: 'mode',
    type: 'segmented',
    label: '转换方向',
    default: 'encode',
    options: [
      { value: 'encode', label: 'JSON → INI' },
      { value: 'decode', label: 'INI → JSON' },
    ],
  },
]
const sample = (opts) =>
  opts.mode === 'encode'
    ? '{"site":{"name":"悠哉世界","enabled":true}}'
    : '[site]\nname=悠哉世界\nenabled=true'
</script>
<template>
  <TransformTool
    :transform="transform"
    :options="options"
    :sample="sample"
    :swap="{ key: 'mode', values: ['encode', 'decode'] }"
    :download="(opts) => (opts.mode === 'encode' ? 'config.ini' : 'config.json')"
  >
    <template #below
      ><p class="jay-note">
        INI 的普通数值按文本读取；数组、布尔值和分节使用 INI 库的语法。
      </p></template
    >
  </TransformTool>
</template>
