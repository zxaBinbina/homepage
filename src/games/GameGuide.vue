<script setup lang="ts">
import { Info } from 'lucide-vue-next'
import type { GameId } from './catalog'

defineProps<{ id: GameId }>()
const titles = {
  twenty48: '让相同的数字相遇。',
  minesweeper: '每个数字，都是线索。',
  solitaire: '一张一张，理出头绪。',
  tetris: '让每一行，恰好填满。',
  sudoku: '每个数字，都有位置。',
  xiangqi: '过河之前，先想一步。',
  gomoku: '五子相连，妙在一手。',
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
        <p>手机：用棋盘上方的「翻开 / 插旗」切换操作。较大棋盘可在区域内滚动，也可以全屏查看。</p>
        <p>
          可选五档难度，或自定义边长和地雷数量。更换预设难度或点击「应用并开局」会开始新的一局。
        </p>
      </div>
    </template>
    <template v-else-if="id === 'solitaire'">
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
    <template v-else-if="id === 'tetris'">
      <ol>
        <li>移动、旋转下落的方块，填满一整行即可消除。虚线方块预览落点，右侧显示下一块。</li>
        <li>每消除 5 行进入下一阶段，方块逐渐加速。消除 30 行完成挑战，堆到顶部则结束。</li>
        <li>同时消除多行得分更高；每批七种方块各出现一次。选择起始速度会重新开局。</li>
      </ol>
      <div class="game-guide-tips">
        <p>
          点击开始后：← / → 移动，↑ 旋转，↓ 加速，空格直接落下；也支持 A / D / W / S。落地即固定。
        </p>
        <p>手机使用棋盘下方按钮。按 P 或点击暂停可休息；切到其他窗口时自动暂停，回来后手动继续。</p>
      </div>
    </template>
    <template v-else-if="id === 'sudoku'">
      <ol>
        <li>用 1–9 填满棋盘，每行、每列、每个 3 × 3 宫内的数字都不能重复。题目数字不可修改。</li>
        <li>先选格子，再填数字。开启「笔记」后可用小字记下多个候选数，例如 2 和 7；这些小字不算正式答案，再点同一数字可取消。</li>
        <li>
          重复数字会标红并加下划线。擦除会清空所选格，「提示一格」补全选中空格或纠正错误。所有题目均有唯一解。
        </li>
      </ol>
      <div class="game-guide-tips">
        <p>
          电脑：方向键选格，数字键填写，Delete / Backspace 擦除，N 切换笔记。手机使用下方数字键。
        </p>
        <p>
          入门、标准、进阶三档题目；切换难度或重新开始会换题。支持撤销最近 100
          次填写，提示次数不会因撤销减少。
        </p>
      </div>
    </template>
    <template v-else-if="id === 'xiangqi'">
      <ol>
        <li>
          你执红先行，电脑执黑。点击己方棋子，再点标出的落点；将死或困毙对方即获胜，被将军时必须应将。
        </li>
        <li>
          车走直线，马走日且不能蹩腿，炮吃子须隔一枚棋子。相走田且不能塞眼、不能过河；仕走斜线、帅走一步直线，都不出九宫。
        </li>
        <li>兵只能前进，过河后可左右走，不能后退。将帅不可无子相隔直接照面。</li>
        <li>
          休闲规则：同一局面且同方行棋第三次出现，或连续 120
          步双方均未吃子，判和；不作竞赛中的长将、长捉裁决。
        </li>
      </ol>
      <div class="game-guide-tips">
        <p>
          电脑：方向键选格，回车选棋或走棋。手机直接点选；Esc 取消选棋，标记显示上一手起止位置。
        </p>
        <p>
          电脑提供休闲与挑战两档。悔棋撤回你与电脑的一轮，也能中止正在思考的电脑。切换难度会重新开局。
        </p>
      </div>
    </template>
    <template v-else>
      <ol>
        <li>你执黑先行，电脑执白。双方轮流在 15 × 15 棋盘的交点上落子。</li>
        <li>横、竖或斜线率先连成至少五子获胜。使用自由规则，黑白都没有禁手，长连也算获胜。</li>
        <li>
          先点击交点预览，再点同一交点或「确认落子」。棋子落下后不可移动，棋盘填满且无人获胜则和棋。
        </li>
      </ol>
      <div class="game-guide-tips">
        <p>电脑：方向键选点，回车预览，再次回车确认。手机点选预览后确认，Esc 取消预览。</p>
        <p>
          电脑提供休闲与挑战两档。悔棋会撤回你与电脑的一轮，也能中止电脑思考；切换难度会重新开局。
        </p>
      </div>
    </template>
    <p class="game-session-note" role="note">
      <Info :size="16" aria-hidden="true" /><span>离开或刷新页面会重新开局。</span>
    </p>
  </aside>
</template>
