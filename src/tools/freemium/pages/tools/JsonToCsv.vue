<template>
  <TransformTool
    :transform="transform"
    :options="options"
    :sample="sample"
    input-label="JSON"
    output-label="CSV"
    accept=".json,application/json,text/plain"
    :download="(o) => (o.delimiter === '\t' ? 'data.tsv' : 'data.csv')"
  />
</template>

<script setup>
import { json2csv } from 'json-2-csv'
import TransformTool from '../../components/TransformTool.vue'

const options = [
  {
    key: 'delimiter',
    type: 'select',
    label: '分隔符',
    default: ',',
    options: [
      { value: ',', label: '逗号' },
      { value: ';', label: '分号' },
      { value: '\t', label: '制表符' },
      { value: '|', label: '竖线' },
    ],
  },
  { key: 'header', type: 'toggle', label: '包含表头', default: true },
  { key: 'flatten', type: 'toggle', label: '展开嵌套对象', default: true },
  { key: 'sortHeader', type: 'toggle', label: '按列名排序', default: false },
]

const sample = () =>
  JSON.stringify(
    [
      {
        id: 1,
        name: 'Ada Lovelace',
        email: 'ada@example.com',
        address: { city: 'London', zip: 'NW1' },
        active: true,
      },
      {
        id: 2,
        name: 'Grace Hopper',
        email: 'grace@example.com',
        address: { city: 'Arlington', zip: '22201' },
        active: false,
      },
      {
        id: 3,
        name: 'Alan Turing',
        email: 'alan@example.com',
        address: { city: 'Wilmslow', zip: 'SK9' },
        active: true,
      },
    ],
    null,
    2,
  )

function transform(input, o) {
  let data
  try {
    data = JSON.parse(input)
  } catch (e) {
    throw new Error(e.message)
  }
  if (!Array.isArray(data)) {
    if (data && typeof data === 'object') data = [data]
    else throw new Error('请输入对象数组或单个对象。')
  }
  if (data.some((r) => r === null || typeof r !== 'object'))
    throw new Error('数组中的每一项都必须是对象。')
  return json2csv(data, {
    delimiter: { field: o.delimiter },
    prependHeader: o.header,
    expandNestedObjects: o.flatten,
    sortHeader: o.sortHeader,
    emptyFieldValue: '',
  })
}
</script>
