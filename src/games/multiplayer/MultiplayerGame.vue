<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import {
  Check,
  Copy,
  DoorOpen,
  MessageCircle,
  Play,
  Plus,
  RotateCcw,
  Send,
  Undo2,
  Users,
} from 'lucide-vue-next'
import SegmentedControl from '../../components/SegmentedControl.vue'
import CollapsePanel from '../../components/CollapsePanel.vue'
import GameFullscreenButton from '../GameFullscreenButton.vue'
import OnlineBoard from './OnlineBoard.vue'
import TurnstileWidget from './TurnstileWidget.vue'
import RoomLeaveConfirm from './RoomLeaveConfirm.vue'
import { useGameRoom } from './useGameRoom'
import type { OnlineKind, RoomSettings } from './types'
const props = defineProps<{ kind: OnlineKind }>()
const emit = defineEmits<{ left: [] }>()
const { room, self, host, error, status, session, pending, enter, send, leave, reconnect } =
  useGameRoom(props.kind)
const operation = ref<'create' | 'join'>('create'),
  name = ref(''),
  code = ref(''),
  verified = ref(''),
  chatText = ref(''),
  chatOpen = ref(false),
  copied = ref(false),
  chatLog = ref<HTMLElement>(),
  widget = ref<InstanceType<typeof TurnstileWidget>>(),
  leaveConfirm = ref<InstanceType<typeof RoomLeaveConfirm>>()
const now = ref(Date.now()),
  tick = setInterval(() => {
    now.value = Date.now()
  }, 1000)
const serverOffset = ref(0)
watch(
  () => room.value?.serverTime,
  (value) => {
    if (value) {
      serverOffset.value = value - Date.now()
      now.value = Date.now()
    }
  },
)
let copyTimer: ReturnType<typeof setTimeout> | undefined
const seats = computed(() =>
  Array.from({ length: props.kind === 'doudizhu' ? 3 : 2 }, (_, seat) =>
    room.value?.players.find((p) => p.seat === seat),
  ),
)
const canStart = computed(
  () =>
    host.value &&
    room.value?.phase !== 'playing' &&
    room.value?.players.filter((p) => !p.bot).every((p) => p.ready && p.connected) &&
    (props.kind === 'doudizhu' || room.value?.players.filter((p) => !p.bot).length === 2),
)
const connected = computed(() => status.value === 'online')
const turnPlayer = computed(() =>
  room.value?.players.find((p) => p.seat === room.value?.game?.turn),
)
const turnText = computed(() => {
  if (!connected.value) return status.value === 'retrying' ? '正在重新连接…' : '正在连接房间…'
  if (room.value?.pauseUntil) return '等待玩家重连'
  if (room.value?.phase !== 'playing')
    return room.value?.phase === 'finished' ? '本局结束，准备再来一局' : '等朋友一起准备'
  if (room.value.game?.status === 'setup') return '双方正在布阵'
  if (room.value.game?.status === 'scoring') return '双方核对死子与地盘'
  return turnPlayer.value?.id === self.value?.id
    ? '轮到你了'
    : (turnPlayer.value?.name ?? '对手') + '的回合'
})
const remaining = computed(() =>
  room.value?.deadline
    ? Math.max(0, Math.ceil((room.value.deadline - now.value - serverOffset.value) / 1000))
    : null,
)
const pauseRemaining = computed(() =>
  room.value?.pauseUntil
    ? Math.max(0, Math.ceil((room.value.pauseUntil - now.value - serverOffset.value) / 1000))
    : null,
)
const undoBlocked = computed(
  () =>
    props.kind === 'doudizhu' ||
    (props.kind === 'junqi' && room.value?.settings.junqi === 'hidden'),
)
async function submit() {
  if (!verified.value) return
  await enter(
    name.value.trim(),
    verified.value,
    operation.value === 'join' ? code.value.trim() : undefined,
  )
  verified.value = ''
  widget.value?.reset()
}
function updateSettings(settings: RoomSettings) {
  send({ type: 'settings', settings })
}
const leaveMessage = computed(() => {
  if (room.value?.players.filter((player) => !player.bot).length === 1)
    return '房间里只剩你，离开后会清空房间和聊天。'
  const consequence =
    room.value?.phase === 'playing'
      ? props.kind === 'doudizhu'
        ? '当前席位将由电脑接管。'
        : '离开后，当前对局将判你负。'
      : '离开后会释放你的席位。'
  return consequence + (host.value ? '房主身份会转交给其他真人玩家。' : '')
})
async function requestLeave() {
  if (session.value) {
    await nextTick()
    void leaveConfirm.value?.show()
  } else emit('left')
}
function confirmLeave() {
  leave()
  emit('left')
}
defineExpose({ requestLeave })
async function copyCode() {
  if (!room.value) return
  try {
    await navigator.clipboard.writeText(room.value.code)
    copied.value = true
    if (copyTimer) clearTimeout(copyTimer)
    copyTimer = setTimeout(() => {
      copied.value = false
    }, 1800)
  } catch {
    error.value = '暂时无法复制，请手动选取房间号。'
  }
}
function postChat() {
  if (chatText.value.trim() && send({ type: 'chat', text: chatText.value.trim() }))
    chatText.value = ''
}
watch(
  () => room.value?.chat.at(-1)?.id,
  async () => {
    await nextTick()
    chatLog.value?.scrollTo({ top: chatLog.value.scrollHeight, behavior: 'instant' })
  },
)
onBeforeUnmount(() => {
  clearInterval(tick)
  if (copyTimer) clearTimeout(copyTimer)
})
</script>

<template>
  <div class="game-layout room-layout" :class="{ 'dd-layout': kind === 'doudizhu' }">
    <section
      class="game-surface room-surface"
      :class="{
        'doudizhu-surface': kind === 'doudizhu' && room?.game,
        'strategy-surface': kind !== 'doudizhu',
      }"
      aria-label="联机房间"
    >
      <template v-if="!session">
        <header class="room-entry-heading">
          <span class="room-entry-icon"><Users :size="24" aria-hidden="true" /></span>
          <div>
            <p class="overline">PLAY TOGETHER</p>
            <h2>分享一个号码，<span>一起开局。</span></h2>
            <p>无需登录，叫上朋友来玩一会儿。</p>
          </div>
        </header>
        <div class="room-entry-grid">
          <form class="room-entry-form" @submit.prevent="submit">
            <SegmentedControl
              v-model="operation"
              :options="[
                { value: 'create', label: '创建房间' },
                { value: 'join', label: '加入房间' },
              ]"
              label="房间操作"
            />
            <label class="room-field"
              >你的昵称<input
                v-model="name"
                name="nickname"
                maxlength="16"
                autocomplete="nickname"
                placeholder="朋友怎么称呼你？"
                required
            /></label>
            <label v-if="operation === 'join'" class="room-field"
              >6 位数字房间号<input
                v-model="code"
                name="room-code"
                inputmode="numeric"
                pattern="[1-9][0-9]{5}"
                maxlength="6"
                autocomplete="off"
                placeholder="输入朋友分享的号码"
                required
            /></label>
            <TurnstileWidget
              ref="widget"
              :action="operation === 'create' ? 'room_create' : 'room_join'"
              @verified="verified = $event"
            />
            <button
              class="game-button room-primary room-entry-submit"
              :disabled="pending || !verified"
            >
              <Plus v-if="operation === 'create'" :size="16" aria-hidden="true" /><DoorOpen
                v-else
                :size="16"
                aria-hidden="true"
              />{{ pending ? '正在进入…' : operation === 'create' ? '创建房间' : '加入房间' }}
            </button>
          </form>
          <div class="room-entry-notes">
            <p class="overline">A FRIENDLY ROUND</p>
            <h3>从准备开始，慢慢玩。</h3>
            <ol>
              <li>房主把房间号分享给朋友。</li>
              <li>所有真人准备后，由房主开局。</li>
              <li>
                {{
                  kind === 'doudizhu'
                    ? '1～3 位真人都能玩，空位由电脑补足。'
                    : '两位真人一人一方，轮流操作。'
                }}
              </li>
            </ol>
            <p>房主可设置每步限时和悔棋规则。掉线后保留 3 分钟重连时间，刷新不会立即丢失席位。</p>
          </div>
        </div>
      </template>
      <template v-else>
        <div class="game-toolbar room-toolbar">
          <div class="game-stats">
            <div>
              <span>房间号码</span
              ><button
                class="room-number"
                :aria-label="'复制房间号 ' + (room?.code ?? session.code)"
                @click="copyCode"
              >
                {{ room?.code ?? session.code }}<Check v-if="copied" :size="16" /><Copy
                  v-else
                  :size="16"
                />
              </button>
            </div>
            <div>
              <span>{{ host ? '你是房主' : '朋友对局' }}</span
              ><strong class="strategy-turn" role="status">{{ turnText }}</strong>
            </div>
            <div v-if="remaining !== null">
              <span>本步剩余</span><strong>{{ remaining }}<small> 秒</small></strong>
            </div>
          </div>
          <div class="game-actions">
            <button
              v-if="room?.game"
              class="game-button"
              :disabled="pending || !connected || undoBlocked || !room.game.canUndo"
              @click="send({ type: 'undo' })"
            >
              <Undo2 :size="16" />悔棋
            </button>
            <div class="game-restart-actions">
              <button
                v-if="room?.phase === 'playing'"
                class="game-button"
                :disabled="pending || !connected || !!room.proposal"
                @click="send({ type: 'restart' })"
              >
                <RotateCcw :size="16" />申请重开</button
              ><GameFullscreenButton />
            </div>
            <RoomLeaveConfirm ref="leaveConfirm" :message="leaveMessage" @confirm="confirmLeave" />
          </div>
        </div>
        <p v-if="!connected" class="room-feedback" role="status">
          连接中断时会保留席位 3 分钟。<button class="game-button" @click="reconnect">
            重新连接
          </button>
        </p>
        <p v-if="pauseRemaining !== null" class="room-feedback" role="status">
          正在等朋友回来，剩余 {{ pauseRemaining }} 秒；对局已暂停。
        </p>
        <div class="room-seats">
          <article
            v-for="(player, index) in seats"
            :key="index"
            class="room-seat"
            :class="{
              'is-ready': player?.ready,
              'is-current': room?.phase === 'playing' && room.game?.turn === index,
            }"
          >
            <span class="room-avatar">{{ player?.name.slice(0, 1) ?? '?' }}</span>
            <div>
              <strong
                >{{ player?.name ?? (kind === 'doudizhu' ? '电脑候补' : '等待朋友加入')
                }}<small v-if="player?.id === room?.hostId">房主</small></strong
              ><span>{{
                player
                  ? player.bot
                    ? '电脑玩家'
                    : !player.connected
                      ? player.auto
                        ? '电脑托管'
                        : '暂时离线'
                      : room?.phase === 'playing'
                        ? index === self?.seat
                          ? '我方'
                          : '对方'
                        : player.ready
                          ? '已准备'
                          : '未准备'
                  : kind === 'doudizhu'
                    ? '开局时自动补足'
                    : '分享房间号邀请'
              }}</span>
            </div>
            <Check v-if="player?.ready && room?.phase !== 'playing'" :size="18" />
          </article>
        </div>
        <template v-if="room && room.phase !== 'playing'">
          <fieldset class="room-settings" :disabled="!host || !connected || pending">
            <legend>房间设置</legend>
            <div>
              <label class="room-field"
                >每步时限<select
                  :value="room.settings.turnSeconds"
                  @change="
                    updateSettings({
                      ...room.settings,
                      turnSeconds: Number(
                        ($event.target as HTMLSelectElement).value,
                      ) as RoomSettings['turnSeconds'],
                    })
                  "
                >
                  <option :value="0">不限时</option>
                  <option :value="30">30 秒</option>
                  <option :value="60">60 秒</option>
                  <option :value="120">120 秒</option>
                </select></label
              ><label class="room-field"
                >悔棋规则<select
                  :value="undoBlocked ? 'disabled' : room.settings.undo"
                  :disabled="undoBlocked"
                  @change="
                    updateSettings({
                      ...room.settings,
                      undo: ($event.target as HTMLSelectElement).value as RoomSettings['undo'],
                    })
                  "
                >
                  <option value="enabled">启用 · 直接悔棋</option>
                  <option value="ask">询问 · 对手同意</option>
                  <option value="disabled">禁用</option>
                </select></label
              ><label v-if="kind === 'junqi'" class="room-field"
                >军旗玩法<select
                  :value="room.settings.junqi"
                  @change="
                    updateSettings({
                      ...room.settings,
                      junqi: ($event.target as HTMLSelectElement).value as RoomSettings['junqi'],
                    })
                  "
                >
                  <option value="open">明棋</option>
                  <option value="hidden">暗棋</option>
                </select></label
              >
            </div>
          </fieldset>
          <p class="room-help">
            {{ host ? '修改设置后，所有真人需要重新准备。' : '房主可在开局前调整设置。'
            }}{{ undoBlocked ? '斗地主和暗棋军旗不支持悔棋。' : '' }}
          </p>
          <div class="room-ready-actions">
            <button
              class="game-button"
              :class="{ 'room-primary': !self?.ready }"
              :disabled="pending || !connected"
              @click="send({ type: 'ready', ready: !self?.ready })"
            >
              <Check :size="16" />{{ self?.ready ? '取消准备' : '我准备好了' }}</button
            ><button
              v-if="host"
              class="game-button room-primary"
              :disabled="!canStart || pending || !connected"
              @click="send({ type: 'start' })"
            >
              <Play :size="16" />{{ room.phase === 'finished' ? '再来一局' : '开始对局' }}
            </button>
          </div>
        </template>
        <p v-if="room?.notice" class="room-help" role="status">{{ room.notice }}</p>
        <div v-if="room?.proposal" class="room-proposal" role="status">
          <p>
            {{ room.players.find((p) => p.id === room?.proposal?.requester)?.name }}申请{{
              room.proposal.type === 'undo' ? '悔棋' : '重新开局'
            }}。{{
              room.proposal.accepted.includes(room.selfId) ? '正在等待其他玩家答复。' : '是否同意？'
            }}
          </p>
          <div v-if="!room.proposal.accepted.includes(room.selfId)" class="game-actions">
            <button
              class="game-button room-primary"
              :disabled="pending"
              @click="send({ type: 'answer', proposalId: room.proposal.id, accept: true })"
            >
              同意</button
            ><button
              class="game-button"
              :disabled="pending"
              @click="send({ type: 'answer', proposalId: room.proposal.id, accept: false })"
            >
              拒绝
            </button>
          </div>
        </div>
        <OnlineBoard
          v-if="room?.game && self"
          :key="room.kind"
          :kind="room.kind"
          :game="room.game"
          :players="room.players"
          :seat="self.seat"
          :enabled="connected && !room.pauseUntil && room.phase === 'playing'"
          :pending="pending"
          @action="send"
        />
        <div v-if="room" class="room-chat">
          <button
            class="game-button"
            :aria-expanded="chatOpen"
            aria-controls="room-chat-panel"
            @click="chatOpen = !chatOpen"
          >
            <MessageCircle :size="16" />房间聊天<span v-if="room.chat.length">{{
              room.chat.length
            }}</span></button
          ><CollapsePanel id="room-chat-panel" :open="chatOpen"
            ><div class="room-chat-content">
              <div
                ref="chatLog"
                class="room-chat-log"
                role="log"
                aria-label="房间聊天"
                aria-live="polite"
              >
                <p v-if="!room.chat.length" class="room-help">和朋友打个招呼吧。</p>
                <p v-for="message in room.chat" :key="message.id">
                  <strong>{{ message.name }}</strong
                  ><span>{{ message.text }}</span>
                </p>
              </div>
              <form class="room-chat-form" @submit.prevent="postChat">
                <label class="sr-only" for="room-chat-message">聊天消息</label
                ><input
                  id="room-chat-message"
                  v-model="chatText"
                  maxlength="200"
                  placeholder="说点什么…"
                  :disabled="!connected"
                /><button
                  class="game-button"
                  :disabled="!connected || !chatText.trim()"
                  aria-label="发送消息"
                >
                  <Send :size="16" />
                </button>
              </form>
              <p class="room-help">房间解散后，聊天与对局会一并清空。</p>
            </div></CollapsePanel
          >
        </div>
      </template>
      <p v-if="error" class="room-feedback" role="alert">{{ error }}</p>
    </section>
  </div>
</template>
