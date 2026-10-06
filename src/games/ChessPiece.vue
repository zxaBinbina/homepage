<script setup lang="ts">
import type { PieceSymbol } from 'chess.js'
defineProps<{ piece: PieceSymbol; side: 'w' | 'b' }>()
</script>

<template>
  <svg
    class="chess-piece-art"
    :class="side === 'w' ? 'is-white' : 'is-black'"
    viewBox="0 0 48 48"
    aria-hidden="true"
  >
    <g stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <template v-if="piece === 'p'">
        <circle cx="24" cy="13" r="6" />
        <path d="M19 20h10l-2 5 5 10H16l5-10Z" />
      </template>
      <template v-else-if="piece === 'r'">
        <path d="M13 8h6v5h3V8h4v5h3V8h6v13l-5 4v10H18V25l-5-4Z" />
        <path d="M14 20h20M18 27h12" fill="none" />
      </template>
      <template v-else-if="piece === 'n'">
        <path d="M15 35c0-9 11-12 11-18l-8 7-8-3 4-9 10-5 1-4 5 5c9 2 11 15 5 27Z" />
        <path d="m14 17 6-3M28 12c4 5 5 10 2 15" fill="none" />
        <circle cx="24" cy="12" r="1" class="chess-piece-eye" />
      </template>
      <template v-else-if="piece === 'b'">
        <path d="M24 5c-5 5-11 9-11 15 0 4 4 7 8 8l-4 7h14l-4-7c4-1 8-4 8-8 0-6-6-10-11-15Z" />
        <path d="m24 10 5 9M18 24h12" fill="none" />
      </template>
      <template v-else-if="piece === 'q'">
        <path d="m12 14 6 7 6-12 6 12 6-7-5 17H17Z" />
        <circle cx="12" cy="11" r="3" />
        <circle cx="24" cy="6" r="3" />
        <circle cx="36" cy="11" r="3" />
        <path d="M17 31h14l2 4H15Z" />
      </template>
      <template v-else>
        <path d="M24 3v10M20 7h8" fill="none" />
        <path d="M24 16c-10-9-17 3-9 12l3 7h12l3-7c8-9 1-21-9-12Z" />
        <path d="M18 29h12M24 16v8" fill="none" />
      </template>
      <path d="M15 35h18l3 6H12Z" />
    </g>
  </svg>
</template>
