<script setup>
import TransformTool from '../freemium/components/TransformTool.vue'
import { transform } from './rmb'
</script>
<template>
  <TransformTool
    :transform="transform"
    sample="1234567.89"
    input-label="金额"
    output-label="中文金额"
    placeholder="例如 1234567.89"
    :accept="false"
    :mono-input="false"
  />
</template>
