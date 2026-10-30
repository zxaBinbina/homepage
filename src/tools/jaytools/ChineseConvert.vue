<script setup>
import TransformTool from '../freemium/components/TransformTool.vue'
import { transform } from './chinese-convert'
const options = [
  {
    key: 'mode',
    type: 'segmented',
    label: '转换方向',
    default: 'traditional',
    options: [
      { value: 'traditional', label: '简体 → 繁体' },
      { value: 'simplified', label: '繁体 → 简体' },
    ],
  },
]
const sample = (opts) =>
  opts.mode === 'traditional'
    ? '在代码与方块之间，创造一点不一样。'
    : '在代碼與方塊之間，創造一點不一樣。'
</script>
<template>
  <TransformTool
    :transform="transform"
    :options="options"
    :sample="sample"
    :swap="{ key: 'mode', values: ['traditional', 'simplified'] }"
    :mono-input="false"
  >
    <template #below
      ><p class="jay-note">
        使用上游逐字字表，多对一或一对多时采用首个对应字；不按上下文判断词义，转换后请核对人名与地名。
      </p></template
    >
  </TransformTool>
</template>
