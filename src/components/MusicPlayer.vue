<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  ArrowUpRight,
  Check,
  Headphones,
  ListMusic,
  LoaderCircle,
  Pause,
  Play,
  Search,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
} from 'lucide-vue-next'
import music from '../data/music.json'
import { mergeLyrics } from '../utils/lyrics'
import type { LyricLine } from '../utils/lyrics'

const props = withDefaults(
  defineProps<{
    active?: boolean
    compact?: boolean
    overlayPlaylist?: boolean
    playOnMount?: boolean
  }>(),
  {
    active: true,
    compact: false,
  },
)
const emit = defineEmits<{
  playing: [value: boolean]
  playlist: [value: boolean]
  track: [value: string]
}>()

const tracks = music.tracks
const index = ref(
  Math.max(
    0,
    tracks.findIndex((track) => track.id === music.defaultTrackId),
  ),
)
const current = computed(() => tracks[index.value]!)
watch(current, (track) => emit('track', `${track.title} - ${track.artist}`), { immediate: true })
const audio = ref<HTMLAudioElement>()
const playing = ref(false)
watch(playing, (value) => emit('playing', value))
const loading = ref(false)
const error = ref('')
const position = ref(0)
const duration = ref(0)
const seekable = ref(false)
const volume = ref(1)
const muted = ref(false)
const listOpen = ref(false)
const playlistVisible = ref(false)
function finishPlaylistClose() {
  if (listOpen.value) return
  playlistVisible.value = false
}
const listButton = ref<HTMLButtonElement>()
const searchInput = ref<HTMLInputElement>()
const playlistViewport = ref<HTMLDivElement>()
watch(listOpen, async (value) => {
  if (value) playlistVisible.value = true
  // Resize with the content transition; retain the grid until the content leaves.
  emit('playlist', value)
  await nextTick()
  if (value) searchInput.value?.focus({ preventScroll: true })
  else listButton.value?.focus({ preventScroll: true })
})
const query = ref('')
const coverFailed = ref(false)
const lyricLines = ref<LyricLine[]>([])
const plainLyrics = ref('')
const lyricState = ref<'loading' | 'ready' | 'instrumental' | 'empty' | 'error'>('loading')
const lyricsViewport = ref<HTMLElement>()
interface LyricsData {
  instrumental: boolean
  lyric: string
  translation: string
}
const lyricCache = new Map<number, LyricsData>()
let lyricAbort: AbortController | undefined
const activeLine = computed(() => {
  for (let i = lyricLines.value.length - 1; i >= 0; i--) {
    if (position.value >= lyricLines.value[i]!.time) return i
  }
  return -1
})

async function loadLyrics() {
  lyricAbort?.abort()
  if (!props.active) return
  const id = current.value.id
  lyricLines.value = []
  plainLyrics.value = ''
  lyricState.value = 'loading'
  const controller = new AbortController()
  lyricAbort = controller
  const timeout = setTimeout(() => controller.abort(), 10000)
  try {
    let data = lyricCache.get(id)
    if (!data) {
      const response = await fetch(`/api/music/lyrics?id=${id}`, { signal: controller.signal })
      if (!response.ok) throw new Error('Lyrics unavailable')
      data = (await response.json()) as LyricsData
      if (typeof data.lyric !== 'string' || typeof data.translation !== 'string')
        throw new Error('Invalid lyrics')
      lyricCache.set(id, data)
    }
    if (id !== current.value.id || lyricAbort !== controller || !props.active) return
    if (data.instrumental) {
      lyricState.value = 'instrumental'
      return
    }
    lyricLines.value = mergeLyrics(data.lyric, data.translation)
    if (!lyricLines.value.length) plainLyrics.value = data.lyric.replace(/\[[^\]]*\]/g, '').trim()
    lyricState.value = lyricLines.value.length || plainLyrics.value ? 'ready' : 'empty'
  } catch {
    if (id === current.value.id && lyricAbort === controller && props.active)
      lyricState.value = 'error'
  } finally {
    clearTimeout(timeout)
  }
}
watch(() => [current.value.id, props.active], loadLyrics, { immediate: true })
watch([activeLine, () => props.active, lyricState], async () => {
  if (!props.active) return
  await nextTick()
  const viewport = lyricsViewport.value
  const line = viewport?.querySelector<HTMLElement>('[data-active="true"]')
  if (viewport && line)
    viewport.scrollTo({
      top:
        viewport.scrollTop +
        line.getBoundingClientRect().top -
        viewport.getBoundingClientRect().top -
        viewport.clientHeight / 2 +
        line.clientHeight / 2,
      behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
    })
})

function seekToLine(time: number) {
  if (!audio.value || !seekable.value) return
  audio.value.currentTime = Math.min(time, duration.value)
  position.value = audio.value.currentTime
}
let playRequest = 0
const songUrl = computed(() => `https://music.163.com/#/song?id=${current.value.id}`)
const source = computed(
  () => `https://music.163.com/song/media/outer/url?id=${current.value.id}.mp3`,
)
const cover = computed(() =>
  current.value.id === music.defaultTrackId
    ? `${import.meta.env.BASE_URL}images/music-cover.webp`
    : current.value.cover,
)
const filtered = computed(() =>
  tracks
    .map((track, trackIndex) => ({ ...track, trackIndex }))
    .filter((track) =>
      `${track.title} ${track.artist}`
        .toLocaleLowerCase()
        .includes(query.value.trim().toLocaleLowerCase()),
    ),
)
function locateCurrentTrack(smooth = false) {
  if (!listOpen.value || !props.active) return
  const viewport = playlistViewport.value
  const selected = viewport?.querySelector<HTMLElement>('.music-track.selected')
  // A search can exclude the current track; keep the user's filter intact.
  if (!viewport || !selected) return
  const top = Math.max(
    0,
    Math.min(
      viewport.scrollHeight - viewport.clientHeight,
      viewport.scrollTop +
        selected.getBoundingClientRect().top -
        viewport.getBoundingClientRect().top -
        (viewport.clientHeight - selected.offsetHeight) / 2,
    ),
  )
  // Skip long journeys through the list when wrapping or selecting a distant track.
  const nearby = Math.abs(top - viewport.scrollTop) <= viewport.clientHeight * 2
  viewport.scrollTo({
    top,
    behavior:
      smooth && nearby && !matchMedia('(prefers-reduced-motion: reduce)').matches
        ? 'smooth'
        : 'instant',
  })
}
watch(
  [() => current.value.id, listOpen, () => props.active, query, () => props.overlayPlaylist],
  ([id, open, active], [previousId, wasOpen, wasActive]) => {
    locateCurrentTrack(id !== previousId && open && wasOpen && active && wasActive)
  },
  { flush: 'post' },
)
const playLabel = computed(() =>
  loading.value ? '取消加载' : playing.value ? '暂停音乐' : '播放音乐',
)

function formatTime(seconds: number) {
  const safe = Number.isFinite(seconds) ? Math.max(0, Math.floor(seconds)) : 0
  return `${Math.floor(safe / 60)}:${String(safe % 60).padStart(2, '0')}`
}
function isCurrent(event: Event) {
  return event.currentTarget === audio.value
}
function onCoverError(event: Event) {
  // A cover retained for its exit animation may fail after the track has changed.
  if ((event.currentTarget as HTMLImageElement).dataset.trackId === String(current.value.id))
    coverFailed.value = true
}
function reportError() {
  loading.value = false
  playing.value = false
  error.value = '这首歌暂时无法在网页播放，可以试试下一首，或前往网易云收听。'
}
async function play() {
  const element = audio.value
  if (!element) return
  const request = ++playRequest
  error.value = ''
  loading.value = true
  if (element.error) element.load()
  try {
    await element.play()
  } catch (cause) {
    if (request !== playRequest || element !== audio.value) return
    loading.value = false
    if (cause instanceof DOMException && cause.name === 'AbortError') return
    if (cause instanceof DOMException && cause.name === 'NotAllowedError') {
      error.value = '浏览器暂停了自动续播，请点击播放按钮继续。'
    } else reportError()
  }
}
function togglePlay() {
  if (playing.value || loading.value) {
    ++playRequest
    audio.value?.pause()
    loading.value = false
    playing.value = false
  } else void play()
}
async function selectTrack(nextIndex: number) {
  ++playRequest
  audio.value?.pause()
  playing.value = false
  loading.value = false
  error.value = ''
  position.value = 0
  duration.value = 0
  seekable.value = false
  coverFailed.value = false
  index.value = (nextIndex + tracks.length) % tracks.length
  await nextTick()
  if (audio.value) audio.value.currentTime = 0
  await play()
}
function metadata(event: Event) {
  if (!isCurrent(event)) return
  const element = audio.value!
  duration.value = Number.isFinite(element.duration) ? element.duration : current.value.duration
  seekable.value = true
}
function seek(event: Event) {
  if (!audio.value || !seekable.value) return
  audio.value.currentTime = Number((event.target as HTMLInputElement).value)
  position.value = audio.value.currentTime
}
function onPlaying(event: Event) {
  if (!isCurrent(event)) return
  loading.value = false
  playing.value = true
  error.value = ''
}
function onPause(event: Event) {
  if (!isCurrent(event)) return
  playing.value = false
  loading.value = false
}
onMounted(() => {
  if (props.playOnMount && props.active) void play()
})
onBeforeUnmount(() => {
  ++playRequest
  lyricAbort?.abort()
  audio.value?.pause()
})
</script>

<template>
  <section
    class="music-card"
    :class="{
      'is-compact': compact,
      'has-playlist': playlistVisible,
      'playlist-overlay': overlayPlaylist,
    }"
    aria-label="网易云音乐播放器"
  >
    <div class="music-player-body" :inert="overlayPlaylist && listOpen">
      <div class="music-heading">
        <span><Headphones :size="15" /> 听点音乐，慢慢逛。</span>
        <a :href="music.url" target="_blank" rel="noopener noreferrer"
          >我的网易云歌单 <ArrowUpRight :size="13"
        /></a>
      </div>
      <div class="music-main">
        <div class="music-cover" :class="{ 'is-playing': playing }">
          <Transition name="track-cover">
            <img
              v-if="!coverFailed"
              :key="current.id"
              :data-track-id="current.id"
              :src="cover"
              :alt="`${current.album} 专辑封面`"
              width="76"
              height="76"
              loading="lazy"
              referrerpolicy="no-referrer"
              @error="onCoverError"
            />
            <Headphones v-else :key="`fallback-${current.id}`" :size="30" />
          </Transition>
          <span class="music-cover-shine" aria-hidden="true"></span>
        </div>
        <div class="music-info">
          <span class="music-label"
            ><span class="music-equalizer" :class="{ 'is-playing': playing }" aria-hidden="true"
              ><i></i><i></i><i></i></span
            >{{ playing ? '正在播放' : loading ? '正在加载' : '给此刻一点旋律' }}</span
          >
          <div :key="`title-${current.id}`" class="music-title-row track-info-enter">
            <h3 :title="current.title">{{ current.title }}</h3>
            <span v-if="current.vip" class="music-vip" aria-label="VIP 歌曲">VIP</span>
          </div>
          <p :key="`artist-${current.id}`" class="track-info-enter">{{ current.artist }}</p>
        </div>
        <div class="music-controls">
          <button class="music-icon-button" aria-label="上一首" @click="selectTrack(index - 1)">
            <SkipBack :size="19" />
          </button>
          <button class="music-play-button" :aria-label="playLabel" @click="togglePlay">
            <LoaderCircle v-if="loading" class="music-spinner" :size="21" /><Pause
              v-else-if="playing"
              :size="20"
              fill="currentColor"
            /><Play v-else :size="20" fill="currentColor" />
          </button>
          <button class="music-icon-button" aria-label="下一首" @click="selectTrack(index + 1)">
            <SkipForward :size="19" />
          </button>
        </div>
        <div class="music-extra">
          <div class="music-volume">
            <button
              class="music-icon-button"
              :aria-label="muted ? '取消静音' : '静音'"
              @click="muted = !muted"
            >
              <VolumeX v-if="muted || volume === 0" :size="18" /><Volume2
                v-else
                :size="18"
              /></button
            ><input
              v-model.number="volume"
              type="range"
              min="0"
              max="1"
              step="0.01"
              aria-label="音量"
            />
          </div>
          <button
            ref="listButton"
            class="music-icon-button music-list-button"
            :class="{ selected: listOpen }"
            :aria-expanded="listOpen"
            aria-controls="music-playlist"
            aria-label="展开或收起歌单"
            @click="listOpen = !listOpen"
          >
            <ListMusic :size="21" /><span>{{ tracks.length }}</span>
          </button>
        </div>
      </div>
      <div class="music-progress">
        <span>{{ formatTime(position) }}</span
        ><input
          type="range"
          min="0"
          :max="duration || current.duration"
          step="0.1"
          :value="position"
          :disabled="!seekable"
          :aria-valuetext="`${formatTime(position)}，共 ${formatTime(duration || current.duration)}`"
          aria-label="播放进度"
          :style="{ '--progress': `${(position / (duration || current.duration || 1)) * 100}%` }"
          @input="seek"
        /><span>{{ formatTime(duration || current.duration) }}</span>
      </div>
      <section class="music-lyrics" :aria-label="error ? '播放状态' : '歌词'">
        <div :key="`${current.id}-${lyricState}-${Boolean(error)}`" class="track-lyrics-enter">
          <div v-if="error" class="lyric-placeholder music-error" role="status">
            <span>{{ error }}</span>
            <a class="lyric-retry" :href="songUrl" target="_blank" rel="noopener noreferrer">
              在网易云打开 <ArrowUpRight :size="13" />
            </a>
          </div>
          <div v-else-if="lyricState === 'loading'" class="lyric-placeholder" role="status">
            <LoaderCircle class="music-spinner" :size="19" /><span>正在加载歌词…</span>
          </div>
          <div v-else-if="lyricState === 'instrumental'" class="lyric-placeholder">
            <Headphones :size="24" /><span>纯音乐，请欣赏</span>
          </div>
          <div v-else-if="lyricState === 'error'" class="lyric-placeholder" role="status">
            <span>歌词暂时无法加载</span
            ><button class="lyric-retry" @click="loadLyrics">重试</button>
          </div>
          <div v-else-if="lyricState === 'empty'" class="lyric-placeholder">
            <span>暂无歌词，让旋律继续。</span>
          </div>
          <div
            v-else-if="lyricLines.length"
            ref="lyricsViewport"
            class="lyric-lines"
            tabindex="0"
            aria-label="滚动歌词"
          >
            <button
              v-for="(line, lineIndex) in lyricLines"
              :key="`${line.time}-${lineIndex}`"
              class="lyric-line"
              :data-active="lineIndex === activeLine"
              :aria-current="lineIndex === activeLine ? 'true' : undefined"
              :disabled="!seekable"
              @click="seekToLine(line.time)"
            >
              <span>{{ line.text }}</span
              ><small v-if="line.translation">{{ line.translation }}</small>
            </button>
          </div>
          <p v-else class="lyric-plain">{{ plainLyrics }}</p>
        </div>
      </section>
    </div>
    <Transition name="playlist-scrim">
      <button
        v-if="listOpen && overlayPlaylist"
        class="playlist-scrim"
        aria-label="关闭歌单侧栏"
        @click="listOpen = false"
      ></button>
    </Transition>
    <Transition
      @before-leave="(el) => el.setAttribute('inert', '')"
      @before-enter="(el) => el.removeAttribute('inert')"
      name="playlist"
      @after-leave="finishPlaylistClose"
      @after-enter="locateCurrentTrack()"
    >
      <aside
        v-if="listOpen"
        :inert="!listOpen"
        id="music-playlist"
        class="music-playlist"
        aria-label="播放列表"
      >
        <div class="music-list-heading">
          <span>{{ music.name }}</span
          ><label class="music-search"
            ><Search :size="14" /><input
              ref="searchInput"
              v-model="query"
              type="search"
              placeholder="搜索歌曲 / 歌手"
              aria-label="搜索歌单"
          /></label>
        </div>
        <div ref="playlistViewport" class="music-track-list" tabindex="0" aria-label="歌单曲目">
          <button
            v-for="track in filtered"
            :key="track.id"
            class="music-track"
            :class="{ selected: track.id === current.id }"
            :aria-pressed="track.id === current.id"
            @click="selectTrack(track.trackIndex)"
          >
            <span class="music-track-number"
              ><Check v-if="track.id === current.id" :size="14" /><template v-else>{{
                String(track.trackIndex + 1).padStart(2, '0')
              }}</template></span
            ><span class="music-track-title"
              ><span class="music-track-name"
                ><span>{{ track.title }}</span
                ><span v-if="track.vip" class="music-vip" aria-label="VIP 歌曲">VIP</span></span
              ><small>{{ track.artist }}</small></span
            ><span class="music-track-duration">{{ formatTime(track.duration) }}</span>
          </button>
          <p v-if="!filtered.length" class="music-empty">没有找到匹配的歌曲，换个关键词试试。</p>
        </div>
      </aside>
    </Transition>
    <audio
      :key="current.id"
      ref="audio"
      :src="source"
      preload="none"
      :volume="volume"
      :muted="muted"
      @loadedmetadata="metadata"
      @durationchange="metadata"
      @timeupdate="
        (event) => {
          if (isCurrent(event)) position = audio?.currentTime || 0
        }
      "
      @playing="onPlaying"
      @pause="onPause"
      @waiting="
        (event) => {
          if (isCurrent(event) && !audio?.paused) loading = true
        }
      "
      @error="
        (event) => {
          if (isCurrent(event)) reportError()
        }
      "
      @ended="
        (event) => {
          if (isCurrent(event)) selectTrack(index + 1)
        }
      "
    />
  </section>
</template>

<style scoped>
.music-title-row,
.music-track-name {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.music-title-row h3 {
  min-width: 0;
}
.music-vip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-family: Arial, sans-serif;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.5px;
  line-height: 1;
  padding: 3px 5px;
  color: #c39762;
  border: 1px solid #93756270;
  border-radius: 4px;
  background: #93756212;
}
.music-track-name > span:first-child {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.music-lyrics {
  margin-top: 19px;
  padding-top: 17px;
  overflow: hidden;
  border-top: 1px solid var(--border);
}
.lyric-placeholder,
.lyric-lines,
.lyric-plain {
  height: var(--lyrics-height, 210px);
}
.lyric-placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 13px;
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.4px;
}
.lyric-placeholder > svg {
  color: var(--blue);
  opacity: 0.7;
}
.lyric-retry {
  font-size: 11px;
  color: var(--blue);
  border: 1px solid var(--border);
  background: transparent;
  padding: 7px 14px;
  border-radius: 15px;
}
.lyric-lines {
  position: relative;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 30px 8px;
  mask-image: linear-gradient(transparent, #000 15%, #000 85%, transparent);
}
.lyric-line {
  display: block;
  text-align: center;
  width: 100%;
  padding: 9px 8px;
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.8;
  transition: color 0.25s;
  cursor: pointer;
}
.lyric-line:disabled {
  cursor: default;
}
.lyric-line[data-active='true'] {
  color: var(--blue);
  font-weight: 600;
}
.lyric-line:hover:not(:disabled) {
  color: var(--text);
}
.lyric-line small {
  display: block;
  font-size: 11px;
  opacity: 0.75;
  line-height: 1.8;
}
.lyric-plain {
  white-space: pre-line;
  text-align: center;
  font-size: 12px;
  line-height: 2.2;
  color: var(--muted);
  overflow: auto;
}
.music-card {
  margin-top: 0;
  padding: 22px 25px 18px;
  border: 0;
  border-radius: 0;
  background: linear-gradient(110deg, rgba(45, 60, 129, 0.12), transparent 70%), var(--panel);
}
.music-heading {
  display: flex;
  justify-content: space-between;
  gap: 15px;
  margin-bottom: 20px;
  font-size: 11px;
  color: var(--muted);
}
.music-heading > span,
.music-heading > a {
  display: flex;
  align-items: center;
  gap: 7px;
}
.music-heading > span > svg {
  color: var(--blue);
}
.music-heading > a:hover {
  color: var(--blue);
}
.music-main {
  display: flex;
  align-items: center;
  gap: 20px;
}
.music-cover {
  position: relative;
  width: 76px;
  height: 76px;
  border-radius: 13px;
  overflow: hidden;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  background: var(--indigo);
  color: var(--blue);
  box-shadow: 0 5px 15px var(--shadow);
  transition: box-shadow 0.4s;
}
.music-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.music-cover.is-playing {
  box-shadow: 0 5px 24px #4ea4ef28;
}
.music-cover-shine {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  box-shadow: inset 0 0 0 1px #ffffff20;
  pointer-events: none;
}
.music-info {
  min-width: 0;
  flex: 1;
}
.music-label {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 9px;
  color: var(--blue);
  letter-spacing: 0.8px;
}
.music-info h3 {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.5;
  margin: 6px 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.music-info p {
  color: var(--muted);
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.music-controls,
.music-extra,
.music-volume {
  display: flex;
  align-items: center;
  gap: 10px;
}
.music-controls {
  gap: 12px;
}
.music-extra {
  gap: 14px;
  margin-left: 12px;
}
.music-icon-button {
  width: 32px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--muted);
  border-radius: 10px;
  flex-shrink: 0;
}
.music-icon-button:hover,
.music-icon-button.selected {
  color: var(--blue);
  background: #4ea4ef10;
}
.music-play-button {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--blue);
  color: var(--bg);
  display: grid;
  place-items: center;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}
.music-play-button:hover {
  transform: scale(1.06);
  box-shadow: 0 0 22px #4ea4ef30;
}
.music-play-button > svg:last-child {
  stroke-width: 1.5;
}
.music-list-button {
  gap: 5px;
  width: auto;
  min-width: 45px;
  padding: 0 5px;
}
.music-list-button > span {
  font-size: 9px;
  font-variant-numeric: tabular-nums;
}
.music-volume {
  gap: 2px;
}
.music-volume input {
  width: 56px;
  accent-color: var(--blue);
}
input[type='range'] {
  cursor: pointer;
  height: 16px;
}
.music-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 17px;
  color: var(--muted);
  font-size: 9px;
  font-variant-numeric: tabular-nums;
}
.music-progress > span {
  min-width: 27px;
}
.music-progress > span:last-child {
  text-align: right;
}
.music-progress input {
  flex: 1;
  min-width: 0;
  margin: 0;
  appearance: none;
  background: transparent;
  --progress: 0%;
}
.music-progress input::-webkit-slider-runnable-track {
  height: 3px;
  border-radius: 4px;
  background: linear-gradient(to right, var(--blue) var(--progress), var(--border) var(--progress));
}
.music-progress input::-moz-range-track {
  height: 3px;
  border-radius: 4px;
  background: var(--border);
}
.music-progress input::-moz-range-progress {
  height: 3px;
  background: var(--blue);
}
.music-progress input::-webkit-slider-thumb {
  appearance: none;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--blue);
  margin-top: -3.5px;
}
.music-progress input::-moz-range-thumb {
  width: 10px;
  height: 10px;
  border: 0;
  border-radius: 50%;
  background: var(--blue);
}
.music-progress input:disabled {
  cursor: default;
  opacity: 0.55;
}
.music-error {
  padding: 12px 16px;
  gap: 12px;
  text-align: center;
  overflow-y: auto;
  font-size: 11px;
  color: var(--muted);
  line-height: 1.8;
}
.music-error a {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--blue);
}
.music-equalizer {
  display: flex;
  align-items: center;
  height: 11px;
  gap: 2px;
}
.music-equalizer i {
  width: 2px;
  height: 4px;
  background: var(--blue);
  border-radius: 2px;
}
.music-equalizer i:nth-child(2) {
  height: 9px;
}
.music-equalizer.is-playing i {
  animation: music-bars 0.8s ease-in-out infinite alternate;
}
.music-equalizer.is-playing i:nth-child(2) {
  animation-delay: -0.4s;
}
.music-equalizer.is-playing i:nth-child(3) {
  animation-delay: -0.2s;
}
.music-spinner {
  animation: music-spin 1s linear infinite;
}
.music-playlist {
  margin-top: 16px;
  border-top: 1px solid var(--border);
  padding-top: 13px;
}
.music-list-heading {
  display: flex;
  align-items: center;
  gap: 13px;
  margin-bottom: 10px;
}
.music-list-heading > span {
  font-size: 11px;
  color: var(--muted);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.music-search {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--muted);
}
.music-search input {
  width: 140px;
  border: 0;
  background: transparent;
  outline: none;
  font: inherit;
  font-size: 11px;
  color: var(--text);
  min-width: 0;
}
.music-search:focus-within {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}
.music-track-list {
  max-height: 280px;
  overflow: auto;
  overscroll-behavior: contain;
}
.music-track {
  display: flex;
  align-items: center;
  width: 100%;
  text-align: left;
  gap: 14px;
  background: transparent;
  border-radius: 8px;
  padding: 11px 12px;
  color: var(--text);
}
.music-track:hover {
  background: #4ea4ef0a;
}
.music-track.selected {
  background: #4ea4ef12;
  color: var(--blue);
}
.music-track-number {
  width: 21px;
  flex-shrink: 0;
  font-size: 10px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.music-track.selected .music-track-number {
  color: var(--blue);
}
.music-track-title {
  font-size: 12px;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.music-track-title small {
  display: block;
  font-size: 10px;
  color: var(--muted);
  margin-top: 4px;
}
.music-track-duration {
  font-size: 10px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.music-empty {
  text-align: center;
  color: var(--muted);
  font-size: 12px;
  padding: 25px;
}
.music-card input:focus-visible,
.music-track-list:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 4px;
}
@keyframes music-bars {
  from {
    transform: scaleY(0.4);
  }
  to {
    transform: scaleY(1.5);
  }
}
@keyframes music-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (max-width: 1050px) {
  .music-volume input {
    display: none;
  }
  .music-extra {
    margin-left: 0;
    gap: 7px;
  }
  .music-main {
    gap: 15px;
  }
  .music-info h3 {
    font-size: 14px;
  }
}
@media (max-width: 760px) {
  .music-card {
    padding: 20px;
    margin-top: 0;
  }
  .music-main {
    flex-wrap: wrap;
    gap: 14px;
  }
  .music-cover {
    width: 60px;
    height: 60px;
    border-radius: 11px;
  }
  .music-info {
    flex-basis: calc(100% - 74px);
  }
  .music-controls {
    margin-top: 2px;
  }
  .music-extra {
    margin-left: auto;
  }
  .music-volume input {
    display: block;
    width: 65px;
  }
  .music-heading {
    font-size: 10px;
    gap: 10px;
  }
  .music-heading > a {
    font-size: 9px;
  }
  .music-info h3 {
    font-size: 14px;
  }
  .music-play-button {
    width: 40px;
    height: 40px;
  }
  .music-progress {
    margin-top: 13px;
  }
  .music-list-heading {
    flex-wrap: wrap;
    gap: 9px;
  }
  .music-list-heading > span {
    flex-basis: 100%;
    font-size: 10px;
  }
  .music-search {
    flex: 1;
  }
  .music-search input {
    width: 100%;
  }
  .music-track {
    padding: 10px 6px;
    gap: 8px;
  }
  .music-track-title {
    font-size: 11px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .music-equalizer.is-playing i,
  .music-spinner {
    animation: none;
  }
  .music-play-button,
  .music-cover {
    transition: none;
  }
}
.music-card.is-compact {
  padding: 14px 16px 15px;
}
.music-card.is-compact .music-heading {
  font-size: 9px;
  margin-bottom: 14px;
  gap: 8px;
}
.music-card.is-compact .music-heading > a {
  font-size: 9px;
}
.music-card.is-compact .music-main {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr);
  gap: 12px;
}
.music-card.is-compact .music-cover {
  width: 52px;
  height: 52px;
  border-radius: 10px;
}
.music-card.is-compact .music-info {
  min-width: 0;
  flex-basis: auto;
}
.music-card.is-compact .music-info h3 {
  font-size: 13px;
  margin: 4px 0;
  line-height: 1.5;
}
.music-card.is-compact .music-info p {
  font-size: 10px;
}
.music-card.is-compact .music-label {
  font-size: 8px;
}
.music-card.is-compact .music-controls {
  grid-column: 1 / -1;
  grid-row: 2;
  justify-self: start;
  gap: 6px;
  margin: 0;
}
.music-card.is-compact .music-extra {
  grid-column: 1 / -1;
  grid-row: 2;
  justify-self: end;
  margin: 0;
  gap: 8px;
}
.music-card.is-compact .music-volume {
  gap: 0;
}
.music-card.is-compact .music-volume input {
  display: block;
  width: 45px;
}
.music-card.is-compact .music-icon-button {
  width: 30px;
  height: 32px;
}
.music-card.is-compact .music-list-button {
  min-width: 44px;
  width: auto;
  gap: 4px;
}
.music-card.is-compact .music-play-button {
  width: 36px;
  height: 36px;
}
.music-card.is-compact .music-progress {
  margin-top: 11px;
  gap: 8px;
}
.music-card.is-compact .music-lyrics {
  --lyrics-height: 145px;
  margin-top: 12px;
  padding-top: 8px;
}
.music-card.is-compact .lyric-placeholder {
  font-size: 11px;
  gap: 9px;
}
.music-card.is-compact .lyric-line {
  font-size: 12px;
  padding: 7px 4px;
}
.music-card.is-compact .music-list-heading {
  flex-wrap: wrap;
  gap: 8px;
}
.music-card.is-compact .music-list-heading > span {
  flex-basis: 100%;
  font-size: 10px;
}
.music-card.is-compact .music-search {
  flex: 1;
}
.music-card.is-compact .music-search input {
  width: 100%;
}
.music-card.is-compact .music-track-list {
  max-height: 200px;
}
.music-card.is-compact .music-track {
  padding: 9px 5px;
  gap: 7px;
}
.music-card.is-compact .music-track-title {
  font-size: 11px;
}
.music-card.is-compact .music-error {
  font-size: 10px;
}
.music-card.is-compact {
  position: relative;
  padding: 0;
}
.music-card.is-compact .music-player-body {
  min-width: 0;
  padding: 14px 16px 15px;
}
/* The popover animates its width; keep the body from reflowing during that transition. */
.music-card.is-compact:not(.playlist-overlay) .music-player-body {
  width: 378px;
}
.music-card.is-compact.has-playlist:not(.playlist-overlay) {
  display: grid;
  grid-template-columns: 378px 270px;
}
.music-card.is-compact .music-playlist {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 340px;
  max-height: calc(var(--panel-height, 600px) - 50px);
  margin: 0;
  padding: 13px 12px;
  border-top: 0;
  border-left: 1px solid var(--border);
  background: var(--panel);
}
.music-card.is-compact .music-track-list {
  flex: 1;
  min-height: 0;
  max-height: none;
}
.playlist-scrim {
  position: absolute;
  inset: 0;
  z-index: 2;
  background: #080b1840;
}
.music-card.is-compact.playlist-overlay .music-playlist {
  --playlist-enter-x: 10px;
  position: absolute;
  z-index: 3;
  top: 0;
  bottom: 0;
  right: 0;
  width: calc(100% - 35px);
  max-width: 285px;
  height: auto;
  max-height: none;
  box-shadow: -10px 0 25px var(--shadow);
}
.playlist-enter-active,
.playlist-leave-active {
  transition:
    opacity 0.28s var(--motion-ease),
    transform 0.28s var(--motion-ease);
}
.playlist-enter-from,
.playlist-leave-to {
  opacity: 0;
  transform: translateX(var(--playlist-enter-x, -10px));
}
.playlist-leave-active {
  pointer-events: none;
}
.playlist-scrim-enter-active,
.playlist-scrim-leave-active {
  transition: opacity 0.2s ease;
}
.playlist-scrim-enter-from,
.playlist-scrim-leave-to {
  opacity: 0;
}
/* Keep outgoing covers layered in the same fixed-size slot. */
.music-cover > img,
.music-cover > svg {
  grid-area: 1 / 1;
}
.track-cover-enter-active,
.track-cover-leave-active {
  transition:
    opacity 0.28s ease,
    transform 0.32s var(--motion-ease);
}
.track-cover-enter-from {
  opacity: 0;
  transform: scale(1.08);
}
.track-cover-leave-to {
  opacity: 0;
  transform: scale(0.94);
}
.track-cover-leave-active {
  pointer-events: none;
}
@media (prefers-reduced-motion: no-preference) {
  .track-info-enter {
    animation: track-info-in 0.32s var(--motion-ease);
  }
  .track-lyrics-enter {
    animation: track-info-in 0.4s var(--motion-ease);
  }
}
@keyframes track-info-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
</style>
