<script setup>
import TransformTool from '../freemium/components/TransformTool.vue'
import { transform } from './html-markdown'
const sample =
  '<h2>悠哉世界</h2>\n<p>在代码与方块之间，<strong>创造一点不一样</strong>。</p>\n<ul><li>建造</li><li>探索</li></ul>\n<pre><code>const hello = "你好";</code></pre>'
</script>
<template>
  <TransformTool
    :transform="transform"
    :sample="sample"
    input-label="HTML"
    output-label="Markdown"
    download="document.md"
  />
</template>
