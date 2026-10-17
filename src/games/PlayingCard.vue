<script setup lang="ts">
import { rankName, suits, type Card } from './solitaire'
defineProps<{ card: Card }>()
function displayRank(rank: number) { return rank === 14 ? '小王' : rank === 15 ? '大王' : rankName(rank) }
</script>
<template>
  <span class="playing-card-face" aria-hidden="true"
    ><span class="card-corner"
      >{{ displayRank(card.rank) }}<span>{{ card.rank > 13 ? '' : suits[card.suit] }}</span></span
    ><span v-if="card.rank <= 13" class="card-center">{{ suits[card.suit] }}</span><span v-else class="card-center card-joker">★</span></span
  >
  <span class="playing-card-reverse" aria-hidden="true">✦</span>
</template>
