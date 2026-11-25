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
    src: folder + 'lyrics-double.webp',
    width: 740,
    height: 74,
    caption: '双行歌词 · 原文与翻译',
    panel: true,
  },
  single: {
    src: folder + 'lyrics-single.webp',
    width: 740,
    height: 74,
    caption: '单行歌词 · 歌曲与歌手信息',
    panel: true,
  },
  karaoke: {
    src: folder + 'karaoke-detail.webp',
    original: folder + 'cover-circle-popup.webp',
    width: 570,
    height: 330,
    caption: '完整歌词 · 暂停时保留当前高亮',
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
    src: folder + 'cover-right.webp',
    width: 740,
    height: 74,
    caption: '圆角封面靠右 · 固定宽度',
    panel: true,
  },
  circle: {
    src: folder + 'cover-circle.webp',
    width: 740,
    height: 74,
    caption: '圆形封面靠左 · 自动宽度',
    panel: true,
  },
  playlist: {
    src: folder + 'playlist-detail.webp',
    original: folder + 'playlist-popup.webp',
    width: 570,
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
    src: folder + 'theme-dark-detail.webp',
    original: folder + 'lyrics-popup-dark.webp',
    width: 586,
    height: 268,
    caption: '手动深色 · 蓝色强调',
  },
} satisfies Record<string, Screenshot>
