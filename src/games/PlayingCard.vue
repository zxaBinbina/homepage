<script setup lang="ts">
import { rankName, suits, type Card } from './solitaire'
defineProps<{ card: Card }>()
</script>
<template>
  <span class="playing-card-face" aria-hidden="true"
    ><span class="card-corner"
      >{{ rankName(card.rank) }}<span>{{ suits[card.suit] }}</span></span
    ><span class="card-center">{{ suits[card.suit] }}</span></span
  >
  <span class="playing-card-reverse" aria-hidden="true">✦</span>
</template>
