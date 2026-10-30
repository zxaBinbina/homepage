<script setup>
import TransformTool from '../freemium/components/TransformTool.vue'
import { transform } from './json-xml'
const options = [
  {
    key: 'mode',
    type: 'segmented',
    label: '转换方向',
    default: 'encode',
    options: [
      { value: 'encode', label: 'JSON → XML' },
      { value: 'decode', label: 'XML → JSON' },
    ],
  },
]
const sample = (opts) =>
  opts.mode === 'encode'
    ? '{"site":{"@_name":"悠哉世界","player":["小彬","小蓝"]}}'
    : '<site name="悠哉世界"><player>小彬</player><player>小蓝</player></site>'
</script>
<template>
  <TransformTool
    :transform="transform"
    :options="options"
    :sample="sample"
    :swap="{ key: 'mode', values: ['encode', 'decode'] }"
    :download="(opts) => (opts.mode === 'encode' ? 'output.xml' : 'output.json')"
  >
    <template #below
      ><p class="jay-note">
        属性以 @_ 开头，文本节点使用 #text。数值会按解析规则转换；混合内容和注释不保证原样往返。
      </p></template
    >
  </TransformTool>
</template>
