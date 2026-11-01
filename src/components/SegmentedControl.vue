<script setup lang="ts" generic="T extends string | number | boolean">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

type Option = {
  value: T
  label?: string
  title?: string
  disabled?: boolean
  id?: string
  controls?: string
  icon?: string
  iconOnly?: boolean
}
const props = withDefaults(
  defineProps<{
    modelValue?: T | null
    options: readonly (T | Option)[]
    label: string
    semantics?: 'radio' | 'buttons' | 'tabs'
    vertical?: boolean
    wrap?: boolean
    disabled?: boolean
    itemClass?: string
    selectedValues?: readonly T[]
  }>(),
  { semantics: 'radio' },
)
const emit = defineEmits<{ 'update:modelValue': [value: T]; select: [value: T] }>()
const root = ref<HTMLElement>()
const normalized = computed<Option[]>(() =>
  props.options.map((option) =>
    typeof option === 'object' ? option : { value: option, label: String(option) },
  ),
)
const multiple = computed(() => props.selectedValues !== undefined)
const semantics = computed(() => (multiple.value ? 'buttons' : props.semantics))
const activeIndex = computed(() =>
  normalized.value.findIndex((option) => option.value === props.modelValue),
)
const focusIndex = computed(() =>
  activeIndex.value >= 0 && !normalized.value[activeIndex.value]?.disabled
    ? activeIndex.value
    : normalized.value.findIndex((option) => !option.disabled),
)
const ready = ref(false)
const animate = ref(false)
const thumb = ref({ x: 0, y: 0, width: 0, height: 0 })
let observer: ResizeObserver | undefined
let frame = 0

function buttons() {
  return Array.from(root.value?.querySelectorAll<HTMLButtonElement>(':scope > .seg__item') ?? [])
}

function selected(value: T) {
  return multiple.value ? props.selectedValues!.includes(value) : value === props.modelValue
}
function measure() {
  const button = buttons()[activeIndex.value]
  if (!root.value?.offsetWidth || !button?.offsetWidth || multiple.value) {
    ready.value = false
    return
  }
  thumb.value = {
    x: button.offsetLeft,
    y: button.offsetTop,
    width: button.offsetWidth,
    height: button.offsetHeight,
  }
  ready.value = true
  if (!animate.value) {
    cancelAnimationFrame(frame)
    frame = requestAnimationFrame(() => {
      animate.value = true
    })
  }
}
function observe() {
  observer?.disconnect()
  if (root.value) observer?.observe(root.value)
  buttons().forEach((button) => observer?.observe(button))
  measure()
}
function choose(option: Option) {
  if (props.disabled || option.disabled) return
  if (!multiple.value) emit('update:modelValue', option.value)
  emit('select', option.value)
}
function onKey(event: KeyboardEvent) {
  if (props.disabled || event.altKey || event.ctrlKey || event.metaKey) return
  const steps: Record<string, number> = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }
  if (!(event.key in steps) && event.key !== 'Home' && event.key !== 'End') return
  const enabled = normalized.value
    .map((option, index) => (option.disabled ? -1 : index))
    .filter((index) => index >= 0)
  if (!enabled.length) return
  event.preventDefault()
  const current = buttons().indexOf(document.activeElement as HTMLButtonElement)
  const index =
    event.key === 'Home'
      ? enabled[0]!
      : event.key === 'End'
        ? enabled.at(-1)!
        : enabled[
            (Math.max(enabled.indexOf(current), 0) + steps[event.key]! + enabled.length) %
              enabled.length
          ]!
  if (!multiple.value) choose(normalized.value[index]!)
  buttons()[index]?.focus({ preventScroll: true })
}
watch(() => props.modelValue, measure, { flush: 'post' })
watch(
  normalized,
  async () => {
    await nextTick()
    observe()
  },
  { flush: 'post' },
)
onMounted(() => {
  observer = new ResizeObserver(measure)
  observe()
})
onBeforeUnmount(() => {
  observer?.disconnect()
  cancelAnimationFrame(frame)
})
</script>

<template>
  <div
    ref="root"
    class="seg"
    :class="{
      'seg--wrap': wrap,
      'seg--animated': animate,
      'seg--multiple': multiple,
      'seg--vertical': vertical,
    }"
    :role="semantics === 'tabs' ? 'tablist' : semantics === 'radio' ? 'radiogroup' : 'group'"
    :aria-label="label"
    :aria-orientation="semantics !== 'buttons' ? (vertical ? 'vertical' : 'horizontal') : undefined"
    @keydown="onKey"
  >
    <button
      v-for="(option, index) in normalized"
      :id="option.id"
      :key="String(option.value)"
      type="button"
      class="seg__item"
      :class="itemClass"
      :role="semantics === 'tabs' ? 'tab' : semantics === 'radio' ? 'radio' : undefined"
      :aria-checked="semantics === 'radio' ? selected(option.value) : undefined"
      :aria-selected="semantics === 'tabs' ? selected(option.value) : undefined"
      :aria-pressed="semantics === 'buttons' ? selected(option.value) : undefined"
      :aria-controls="option.controls"
      :tabindex="multiple || index === focusIndex ? 0 : -1"
      :disabled="disabled || option.disabled"
      :title="option.title"
      @click="choose(option)"
    >
      <span v-if="multiple" class="seg__selection" aria-hidden="true" />
      <slot name="option" :option="option" :selected="selected(option.value)">{{
        option.label
      }}</slot>
    </button>
    <span
      v-if="!multiple"
      class="seg__thumb"
      :style="{
        width: `${thumb.width}px`,
        height: `${thumb.height}px`,
        transform: `translate(${thumb.x}px, ${thumb.y}px)`,
        opacity: ready ? 1 : 0,
      }"
      aria-hidden="true"
    />
  </div>
</template>
