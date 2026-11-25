export type Screenshot = {
  src: string
  original?: string
  width: number
  height: number
  caption: string
  panel?: boolean
}

const folder = '/images/sptl/'

export const screenshots = {
  double: {
    src: folder + 'dark/double.webp',
    width: 740,
    height: 74,
    caption: '双行歌词 · 当前行与下一句',
    panel: true,
  },
  single: {
    src: folder + 'dark/single.webp',
    width: 740,
    height: 74,
    caption: '单行歌词 · 歌曲与歌手信息',
    panel: true,
  },
  karaoke: {
    src: folder + 'dark/karaoke-detail.webp',
    original: folder + 'dark/popup.webp',
    width: 572,
    height: 322,
    caption: '完整歌词 · 暂停时保留当前高亮',
  },
  ordinaryControls: {
    src: folder + 'dark/ordinary-controls.webp',
    width: 740,
    height: 74,
    caption: '普通模式 · 上一首、播放/暂停、下一首与收藏',
    panel: true,
  },
  ordinaryMode: {
    src: folder + 'dark/mode-detail.webp',
    original: folder + 'dark/play-mode.webp',
    width: 568,
    height: 200,
    caption: '普通模式 · 播放模式菜单，当前为单曲循环',
  },
  controls: {
    src: folder + 'hover-controls.webp',
    width: 740,
    height: 74,
    caption: '悬停控制 · 私人 FM 显示“不喜欢”',
    panel: true,
  },
  volume: {
    src: folder + 'volume-osd.webp',
    width: 416,
    height: 84,
    caption: 'KDE 原生音量提示 · SPlayer 图标与百分比',
  },
  right: {
    src: folder + 'dark/right.webp',
    width: 740,
    height: 74,
    caption: '圆角封面靠右 · 固定宽度',
    panel: true,
  },
  circle: {
    src: folder + 'dark/circle.webp',
    width: 740,
    height: 74,
    caption: '圆形封面靠左 · 自动宽度',
    panel: true,
  },
  playlist: {
    src: folder + 'dark/playlist-detail.webp',
    original: folder + 'dark/playlist.webp',
    width: 572,
    height: 466,
    caption: '播放列表 · 在歌词弹窗中查看当前队列',
  },
  light: {
    src: folder + 'theme-light-detail.webp',
    original: folder + 'lyrics-popup-light.webp',
    width: 586,
    height: 268,
    caption: '手动浅色 · 暖色强调',
  },
  dark: {
    src: folder + 'dark/theme-detail.webp',
    original: folder + 'dark/popup.webp',
    width: 584,
    height: 282,
    caption: '跟随 Plasma · KDE 深色主题',
  },
} satisfies Record<string, Screenshot>
