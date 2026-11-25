type ScreenshotAsset = {
  src: string
  original?: string
  width: number
  height: number
  caption: string
  panel?: boolean
}
export type Screenshot = ScreenshotAsset & { light?: Partial<ScreenshotAsset> }

const folder = '/images/sptl/'

export const screenshots = {
  double: {
    src: folder + 'dark/double.webp',
    light: { src: folder + 'light/double.webp' },
    width: 740,
    height: 74,
    caption: '双行歌词 · 当前行与下一句',
    panel: true,
  },
  single: {
    src: folder + 'dark/single.webp',
    light: { src: folder + 'light/single.webp' },
    width: 740,
    height: 74,
    caption: '单行歌词 · 歌曲与歌手信息',
    panel: true,
  },
  karaoke: {
    src: folder + 'dark/karaoke-detail.webp',
    original: folder + 'dark/popup.webp',
    light: { src: folder + 'light/karaoke-detail.webp', original: folder + 'light/popup.webp' },
    width: 572,
    height: 322,
    caption: '完整歌词 · 暂停时保留当前高亮',
  },
  ordinaryControls: {
    src: folder + 'dark/ordinary-controls.webp',
    light: { src: folder + 'light/ordinary-controls.webp' },
    width: 740,
    height: 74,
    caption: '普通模式 · 上一首、播放/暂停、下一首与收藏',
    panel: true,
  },
  ordinaryMode: {
    src: folder + 'dark/mode-detail.webp',
    original: folder + 'dark/play-mode.webp',
    light: {
      src: folder + 'light/mode-detail.webp',
      original: folder + 'light/play-mode.webp',
      height: 174,
    },
    width: 568,
    height: 200,
    caption: '普通模式 · 播放模式菜单，当前为单曲循环',
  },
  controls: {
    src: folder + 'dark/fm-controls.webp',
    original: folder + 'dark/fm-popup.webp',
    light: { src: folder + 'light/fm-controls.webp', original: folder + 'light/fm-popup.webp' },
    width: 586,
    height: 100,
    caption: '私人 FM · 不喜欢、播放/暂停、下一首与收藏',
  },
  volume: {
    src: folder + 'dark/volume-osd.webp',
    light: { src: folder + 'light/volume-osd.webp' },
    width: 416,
    height: 84,
    caption: 'KDE 原生音量提示 · SPlayer 图标与百分比',
  },
  right: {
    src: folder + 'dark/right.webp',
    light: { src: folder + 'light/right.webp' },
    width: 740,
    height: 74,
    caption: '圆角封面靠右 · 固定宽度',
    panel: true,
  },
  circle: {
    src: folder + 'dark/circle.webp',
    light: { src: folder + 'light/circle.webp' },
    width: 740,
    height: 74,
    caption: '圆形封面靠左 · 自动宽度',
    panel: true,
  },
  playlist: {
    src: folder + 'dark/playlist-detail.webp',
    original: folder + 'dark/playlist.webp',
    light: { src: folder + 'light/playlist-detail.webp', original: folder + 'light/playlist.webp' },
    width: 572,
    height: 466,
    caption: '播放列表 · 在歌词弹窗中查看当前队列',
  },
  theme: {
    src: folder + 'dark/theme-detail.webp',
    original: folder + 'dark/popup.webp',
    width: 584,
    height: 282,
    caption: '跟随 Plasma · KDE 深色主题',
    light: {
      src: folder + 'light/theme-detail.webp',
      original: folder + 'light/popup.webp',
      caption: '跟随 Plasma · KDE 浅色主题',
    },
  },
} satisfies Record<string, Screenshot>
