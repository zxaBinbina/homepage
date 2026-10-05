<script setup lang="ts">
import { Info } from 'lucide-vue-next'
import type { GameId } from './catalog'

defineProps<{ id: GameId }>()
const titles = {
  twenty48: '让相同的数字相遇。',
  minesweeper: '每个数字，都是线索。',
  solitaire: '一张一张，理出头绪。',
}
</script>

<template>
  <aside class="game-guide" aria-labelledby="game-guide-title">
    <div>
      <p class="overline">HOW TO PLAY</p>
      <h2 id="game-guide-title">{{ titles[id] }}</h2>
    </div>
    <template v-if="id === 'twenty48'">
      <ol>
        <li>向一个方向移动，所有方块都会滑到那一侧。</li>
        <li>相同数字碰在一起就会合并，每步每块只合并一次。</li>
        <li>合成 2048 即达成目标，也可以继续向更大数字挑战。</li>
      </ol>
      <div class="game-guide-tips">
        <p>电脑：点击棋盘后按方向键或 WASD。手机：在棋盘上滑动，也可以使用下方方向按钮。</p>
        <p>走错一步也没关系，最多可以撤销最近 100 步。</p>
      </div>
    </template>
    <template v-else-if="id === 'minesweeper'">
      <ol>
        <li>点击任意格子开始，首步及周围八格一定安全。数字代表周围八格中的地雷数量。</li>
        <li>确定是地雷时插旗。翻开所有非雷格即可获胜，不需要把旗子全部用完。</li>
        <li>一个数字周围的旗子够了，再点它就会翻开周围剩余格子。标错旗也可能踩雷。</li>
      </ol>
      <div class="game-guide-tips">
        <p>电脑：左键翻开、右键插旗；也可用方向键移动焦点，回车或空格翻开，F 插旗。</p>
        <p>
          手机：用棋盘上方的「翻开 /
          插旗」切换操作。挑战棋盘在窄屏内可左右滚动。更换难度会开始新的一局。
        </p>
      </div>
    </template>
    <template v-else>
      <ol>
        <li>每次翻一张，牌堆可无限循环。点击明牌选中，再点击目标列或收牌区。</li>
        <li>桌面按红黑交替、数字递减排列，可以整段移动。空列只接受 K 或以 K 开头的牌组。</li>
        <li>上方四个收牌区按同花色 A → K 排列。移开暗牌上方的牌后，暗牌会自动翻开。</li>
        <li>
          点击已选的牌、按 Escape 或点击「取消选牌」可重选。可以撤销最近 100
          次操作，收牌区的牌也能移回桌面。
        </li>
      </ol>
      <div class="game-guide-tips">
        <p>鼠标按住明牌可拖动整段纸牌；手机长按片刻后拖拽，直接滑动仍可滚动牌桌。</p>
        <p>随机牌局不保证每局可解，无路可走时可以撤销或重新发牌。</p>
      </div>
    </template>
    <p class="game-session-note" role="note">
      <Info :size="16" aria-hidden="true" /><span>离开或刷新页面会重新开局。</span>
    </p>
  </aside>
</template>
