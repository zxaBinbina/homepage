<template>
  <TransformTool
    :transform="transform"
    :options="options"
    :sample="sample"
    input-label="YAML"
    output-label="JSON"
    accept=".yaml,.yml,text/yaml,text/plain"
    :download="(o) => (o.minify ? 'data.min.json' : 'data.json')"
  />
</template>

<script setup>
import { load, loadAll } from 'js-yaml'
import TransformTool from '../../components/TransformTool.vue'

const options = [
  {
    key: 'indent',
    type: 'select',
    label: '缩进',
    default: '2',
    options: [
      { value: '2', label: '2 个空格' },
      { value: '4', label: '4 个空格' },
      { value: 'tab', label: 'Tab 缩进' },
    ],
  },
  { key: 'minify', type: 'toggle', label: '压缩', default: false },
  { key: 'multi', type: 'toggle', label: '多个文档（---）', default: false },
]

const sample = `# Service definition
apiVersion: apps/v1
kind: Deployment
metadata:
  name: freemium
  labels:
    app: web
spec:
  replicas: 3
  ports:
    - 80
    - 443
  enabled: true
  notes: |
    Multi-line
    text block`

function transform(input, o) {
  let data
  try {
    data = o.multi ? loadAll(input) : load(input)
  } catch (e) {
    if (/expected a single document/i.test(e.message))
      throw new Error('YAML 包含多个文档，请开启“多个文档”选项。')
    throw new Error(e.message.split('\n')[0])
  }
  if (data === undefined) return ''
  if (o.minify) return JSON.stringify(data)
  return JSON.stringify(data, null, o.indent === 'tab' ? '\t' : Number(o.indent))
}
</script>
