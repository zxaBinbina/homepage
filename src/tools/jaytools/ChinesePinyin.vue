<script setup>
import TransformTool from '../freemium/components/TransformTool.vue'
import { transform, annotate } from './pinyin'
const options = [
  {
    key: 'style',
    type: 'segmented',
    label: '拼音样式',
    default: 'tone',
    options: [
      { value: 'tone', label: '带声调' },
      { value: 'normal', label: '无声调' },
      { value: 'first', label: '首字母' },
    ],
  },
]
</script>
<template>
  <TransformTool
    :transform="transform"
    :options="options"
    sample="天生我材必有用，千金散尽还复来。"
    :mono-input="false"
    output-label="拼音"
  >
    <template #below="{ input, opts, output }">
      <div v-if="output" class="jay-panel jay-ruby" aria-label="中文注音">
        <ruby v-for="(item, index) in annotate(input.slice(0, 3000), opts.style)" :key="index"
          >{{ item.hans }}<rt>{{ item.py === item.hans ? '' : item.py }}</rt></ruby
        >
      </div>
      <p class="jay-note">
        注音预览最多显示 3000 个字符。多音字会按词典推断，姓名与生僻读音请自行核对。
      </p>
    </template>
  </TransformTool>
</template>
