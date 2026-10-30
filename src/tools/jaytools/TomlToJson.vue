<script setup>
import TransformTool from '../freemium/components/TransformTool.vue'
import { transform } from './toml'
const sample =
  'title = "悠哉世界"\n\n[server]\nport = 25565\nenabled = true\nplayers = ["小彬", "小蓝"]'
</script>
<template>
  <TransformTool
    :transform="transform"
    :sample="sample"
    input-label="TOML"
    output-label="JSON"
    download="config.json"
  />
</template>
