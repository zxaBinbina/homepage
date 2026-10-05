<script setup lang="ts">
import { ArrowUpRight, Gamepad2 } from 'lucide-vue-next'
import SiteFooter from '../components/SiteFooter.vue'
import { pages } from '../pages'
import { gameCatalog, gameIds } from './catalog'
</script>

<template>
  <div>
    <main id="main" class="directory-main shell games-directory">
      <section class="directory-intro directory-entry">
        <p class="overline">PLAYGROUND / {{ String(gameIds.length).padStart(2, '0') }}</p>
        <h1>不赶时间，<span class="games-accent">来玩一会儿。</span></h1>
        <p>给自己留一点放空的时间。<br />几款熟悉的小游戏，打开就能玩。</p>
      </section>
      <div class="games-directory-meta">
        <span><Gamepad2 :size="18" aria-hidden="true" /> 随时开局，慢慢玩</span
        ><span>{{ gameIds.length }} 款游戏</span>
      </div>
      <div class="games-grid">
        <a v-for="(id, index) in gameIds" :key="id" :href="pages[id]" class="game-card">
          <div class="game-preview" :class="`game-preview-${id}`" aria-hidden="true">
            <div v-if="id === 'twenty48'" class="preview-numbers">
              <span v-for="n in [2, 4, 8, 16, 32, 64, 128, 2048, 256]" :key="n">{{ n }}</span>
            </div>
            <div v-else-if="id === 'minesweeper'" class="preview-mines">
              <span
                v-for="(n, i) in [
                  '',
                  '',
                  '',
                  '',
                  '',
                  '',
                  '1',
                  '1',
                  '1',
                  '',
                  '',
                  '1',
                  '⚑',
                  '1',
                  '',
                  '',
                  '1',
                  '1',
                  '1',
                  '',
                  '',
                  '',
                  '',
                  '',
                  '',
                ]"
                :key="i"
                :class="{ 'is-number': n }"
                >{{ n }}</span
              >
            </div>
            <div v-else class="preview-cards">
              <span>J<small>♠</small></span
              ><span>Q<small>♥</small></span
              ><span>K<small>♣</small></span>
            </div>
            <span class="game-preview-index">0{{ index + 1 }}</span>
          </div>
          <div class="game-card-content">
            <p class="overline">{{ gameCatalog[id].label }}</p>
            <h2>{{ gameCatalog[id].name }}</h2>
            <p class="game-card-description">{{ gameCatalog[id].description }}</p>
            <div class="game-card-bottom">
              <span>{{ gameCatalog[id].category }}</span
              ><span>开始游戏 <ArrowUpRight :size="17" aria-hidden="true" /></span>
            </div>
          </div>
        </a>
      </div>
      <p class="games-note">不用下载，也不用赶进度。玩得开心就好。</p>
    </main>
    <SiteFooter />
  </div>
</template>
