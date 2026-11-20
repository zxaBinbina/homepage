<script setup lang="ts">
import OfficeWorkspace from './OfficeWorkspace.vue'
defineProps<{ name: string; bytes: Uint8Array }>()
</script>
<template><OfficeWorkspace :name="name" :bytes="bytes" /></template>
