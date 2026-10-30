<script setup>
import TransformTool from '../freemium/components/TransformTool.vue'
import { useToolWorker } from './useToolWorker'
const worker = useToolWorker(
  () => new Worker(new URL('./svg.worker.js', import.meta.url), { type: 'module' }),
)
const options = [
  { key: 'floatPrecision', type: 'number', label: '小数精度', default: 3, min: 1, max: 8 },
  { key: 'multipass', type: 'toggle', label: '多轮优化', default: true },
  { key: 'pretty', type: 'toggle', label: '保留缩进', default: false },
  { key: 'removeDimensions', type: 'toggle', label: '移除固定尺寸', default: false },
]
const sample =
  '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" viewBox="0 0 200 100"><title>方块与天空</title><!-- 可以移除的注释 --><g><rect x="10.000" y="10.000" width="180" height="80" fill="#4ea4ef"/></g></svg>'
async function transform(input, opts) {
  if (input.length > 500000) throw new Error('SVG 请控制在 50 万字符以内。')
  return (await worker.run(input, opts)).result
}
const bytes = (value) => new TextEncoder().encode(value).length
</script>
<template>
  <TransformTool
    :transform="transform"
    :options="options"
    :sample="sample"
    input-label="SVG 源码"
    output-label="优化结果"
    download="optimized.svg"
    accept=".svg,image/svg+xml"
  >
    <template #below="{ input, output }"
      ><p class="jay-note" role="status">
        {{
          output
            ? `${bytes(input)} → ${bytes(output)} 字节，减少 ${(100 - (bytes(output) / bytes(input)) * 100).toFixed(1)}%`
            : '保留 viewBox、标题与描述，优化后请核对图形效果。'
        }}
      </p></template
    >
  </TransformTool>
</template>
