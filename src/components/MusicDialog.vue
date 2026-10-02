<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { X } from 'lucide-vue-next'
import MusicPlayer from './MusicPlayer.vue'
import NeteaseIcon from './NeteaseIcon.vue'

const props = defineProps<{ anchor?: HTMLElement }>()
const emit = defineEmits<{
  playing: [value: boolean]
  opened: [value: boolean]
  track: [value: string]
}>()
const popover = ref<HTMLElement>()
const mounted = ref(false)
const opened = ref(false)
const playlistOpen = ref(false)
const overlayPlaylist = ref(false)
const panelStyle = ref<Record<string, string>>({})
let frame = 0

function positionPanel() {
  const anchor = props.anchor
  if (!anchor) return
  const bounds = anchor.getBoundingClientRect()
  const viewport = window.visualViewport
  const viewportLeft = viewport?.offsetLeft || 0
  const viewportTop = viewport?.offsetTop || 0
  const viewportWidth = viewport?.width || window.innerWidth
  const viewportHeight = viewport?.height || window.innerHeight
  overlayPlaylist.value = viewportWidth < 720
  const width = Math.min(
    playlistOpen.value && !overlayPlaylist.value ? 650 : 380,
    viewportWidth - 24,
  )
  const center = bounds.left + bounds.width / 2
  const left = Math.max(
    viewportLeft + 12,
    Math.min(
      center - Math.min(380, viewportWidth - 24) + 36,
      viewportLeft + viewportWidth - width - 12,
    ),
  )
  const top = (anchor.closest('header')?.getBoundingClientRect().bottom || bounds.bottom) + 12
  panelStyle.value = {
    left: `${left}px`,
    top: `${top}px`,
    width: `${width}px`,
    '--arrow-left': `${Math.max(20, Math.min(width - 20, center - left))}px`,
    '--panel-height': `${Math.max(100, viewportTop + viewportHeight - top - 12)}px`,
  }
}
function reposition() {
  if (!opened.value || frame) return
  frame = requestAnimationFrame(() => {
    frame = 0
    positionPanel()
  })
}
function beforeToggle(event: Event) {
  opened.value = (event as ToggleEvent).newState === 'open'
  if (opened.value) {
    mounted.value = true
    positionPanel()
  }
  emit('opened', opened.value)
}
function close() {
  popover.value?.hidePopover()
}
function onPlaylist(value: boolean) {
  playlistOpen.value = value
  positionPanel()
}
onMounted(() => {
  window.addEventListener('resize', reposition)
  window.visualViewport?.addEventListener('resize', reposition)
  window.visualViewport?.addEventListener('scroll', reposition)
})
onBeforeUnmount(() => {
  cancelAnimationFrame(frame)
  window.removeEventListener('resize', reposition)
  window.visualViewport?.removeEventListener('resize', reposition)
  window.visualViewport?.removeEventListener('scroll', reposition)
})
</script>

<template>
  <Teleport to="body">
    <div
      id="music-popover"
      ref="popover"
      popover="auto"
      role="dialog"
      aria-labelledby="music-popover-title"
      class="music-popover"
      :style="panelStyle"
      @beforetoggle="beforeToggle"
    >
      <div class="music-popover-surface">
        <div class="music-popover-header">
          <h2 id="music-popover-title"><NeteaseIcon />网易云音乐</h2>
          <button class="icon-button" aria-label="关闭音乐播放器" autofocus @click="close">
            <X :size="17" />
          </button>
        </div>
        <MusicPlayer
          v-if="mounted"
          compact
          :active="opened"
          :overlay-playlist="overlayPlaylist"
          @playing="emit('playing', $event)"
          @track="emit('track', $event)"
          @playlist="onPlaylist"
        />
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.music-popover {
  position: fixed;
  inset: auto;
  margin: 0;
  padding: 0;
  border: 0;
  width: 380px;
  max-width: calc(100vw - 24px);
  overflow: visible;
  background: transparent;
  color: var(--text);
  transform-origin: var(--arrow-left, 90%) top;
  filter: drop-shadow(0 15px 28px var(--shadow));
}
.music-popover:popover-open {
  animation: music-bubble-in 0.18s ease-out;
}
.music-popover::before {
  content: '';
  position: absolute;
  top: -6px;
  left: calc(var(--arrow-left) - 6px);
  width: 12px;
  height: 12px;
  transform: rotate(45deg);
  background: var(--panel);
  border-top: 1px solid var(--border);
  border-left: 1px solid var(--border);
  z-index: 1;
}
.music-popover-surface {
  max-height: var(--panel-height, calc(100dvh - 110px));
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-width: thin;
  scrollbar-color: var(--indigo) transparent;
  border: 1px solid var(--border);
  border-radius: 17px;
  background: var(--panel);
}
.music-popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 13px 9px 17px;
  border-bottom: 1px solid var(--border);
}
.music-popover-header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
}
.music-popover-header h2 svg {
  color: var(--blue);
  width: 17px;
  height: 17px;
}
.music-popover-header button {
  width: 28px;
  height: 28px;
  border-radius: 9px;
}
@keyframes music-bubble-in {
  from {
    opacity: 0;
    transform: translateY(-5px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  .music-popover:popover-open {
    animation: none;
  }
}
</style>
