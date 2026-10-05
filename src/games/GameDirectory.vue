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
            <div v-else-if="id === 'solitaire'" class="preview-cards">
              <span>J<small>♠</small></span
              ><span>Q<small>♥</small></span
              ><span>K<small>♣</small></span>
            </div>
            <div v-else-if="id === 'tetris'" class="preview-tetris">
              <span
                v-for="i in 48"
                :key="i"
                :class="{
                  'is-filled': [
                    9, 10, 16, 17, 25, 31, 32, 37, 38, 39, 40, 43, 44, 45, 46, 47, 48,
                  ].includes(i),
                }"
              ></span>
            </div>
            <div v-else-if="id === 'sudoku'" class="preview-sudoku">
              <span v-for="(n, i) in [1, '', 9, '', 5, '', 7, '', 3]" :key="i">{{ n }}</span>
            </div>
            <div v-else-if="id === 'xiangqi'" class="preview-xiangqi">
              <span>马</span><span>帅</span><span>炮</span>
            </div>
            <div v-else-if="id === 'gomoku'" class="preview-gomoku">
              <span
                v-for="i in 25"
                :key="i"
                :class="{
                  'is-black': [7, 13, 19].includes(i),
                  'is-white': [8, 12, 18].includes(i),
                }"
              ></span>
            </div>
            <div v-else-if="id === 'snake'" class="preview-snake">
              <span
                v-for="i in 36"
                :key="i"
                :class="{
                  'is-body': [14, 20, 26, 27, 28, 22, 16, 10].includes(i),
                  'is-head': i === 10,
                  'is-food': i === 12,
                }"
                >{{ i === 10 ? '••' : i === 12 ? '●' : '' }}</span
              >
            </div>
            <div v-else-if="id === 'popstar'" class="preview-popstar">
              <span
                v-for="(color, i) in [0, 1, 1, 2, 0, 3, 1, 2, 3, 3, 4, 4, 0, 2, 4, 4]"
                :key="i"
                class="star-gem"
                :data-color="color"
                >★</span
              >
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
