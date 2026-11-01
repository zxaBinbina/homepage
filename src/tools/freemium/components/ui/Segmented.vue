<template>
  <SegmentedControl
    :model-value="modelValue"
    :options="normalized"
    :label="label"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #option="{ option }">
      <AppIcon v-if="option.icon" :name="option.icon" :size="16" />
      <span v-if="option.label" :class="{ 'sr-only': option.iconOnly }">{{ option.label }}</span>
    </template>
  </SegmentedControl>
</template>

<script setup>
import { computed } from 'vue'
import SegmentedControl from '../../../../components/SegmentedControl.vue'
import AppIcon from '../AppIcon.vue'

const props = defineProps({
  modelValue: { type: [String, Number, Boolean], default: null },
  options: { type: Array, required: true },
  label: { type: String, default: '' },
})
defineEmits(['update:modelValue'])
const normalized = computed(() =>
  props.options.map((option) =>
    typeof option === 'object' ? option : { value: option, label: String(option) },
  ),
)
</script>
