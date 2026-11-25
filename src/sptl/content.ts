import { screenshots, settingsScreenshots } from './screenshots'

export const sptlProject = {
  version: '1.2.1',
  repository: 'https://github.com/zxaBinbina/SplayerPlasmaTaskbarLyrics',
  source: '/projects/SPTL/sptl-1.2.1-source.zip',
  installer: '/projects/SPTL/install.sh',
  latest: 'https://github.com/zxaBinbina/SplayerPlasmaTaskbarLyrics/releases/latest',
}

export const releaseHighlights = [
  '滚轮调节音量时，KDE 原生提示立即显示预计百分比，音量优先通过播放器原生接口同步。',
  '播放、收藏和选曲提供即时反馈，独立操作并行处理，失败时恢复对应显示。',
  '完整歌词与播放列表切换更平滑。即时反馈与界面动画都可以在设置中关闭。',
] as const

export const features = [
  {
    label: '01 / LYRICS',
    title: '原文与翻译，一起看',
    description: '双行显示原文和翻译，也能切换音译或下一句。喜欢简洁？用单行歌词搭配歌曲信息。',
    icon: 'lyrics',
    shots: [screenshots.double, screenshots.single],
  },
  {
    label: '02 / IN SYNC',
    title: '每一句，自动滚动',
    description: '支持逐字高亮和长歌词滚动。暂停时停在当前字，切歌时柔和过渡。',
    icon: 'sync',
    shots: [screenshots.karaoke],
  },
  {
    label: '03 / PLAYBACK',
    title: '播放控制，就在手边',
    description:
      '普通模式悬停可上一首、播放/暂停、下一首和收藏；私人 FM 将上一首替换为“不喜欢”。滚轮调节音量，KDE 原生提示显示百分比。',
    icon: 'playback',
    shots: [screenshots.ordinaryControls, screenshots.controls, screenshots.volume],
  },
  {
    label: '04 / YOUR PANEL',
    title: '跟着任务栏，自然适配',
    description:
      '随面板高度缩放，宽度可自动或固定。封面可左右放置，支持方形、圆角与圆形；圆形可随播放旋转。',
    icon: 'panel',
    shots: [screenshots.right, screenshots.circle],
  },
  {
    label: '05 / PLAYLIST',
    title: '下一首，也在这里选',
    description:
      '完整歌词支持点击跳转，弹窗可切换播放模式、收藏与播放列表。列表支持翻页和点击播放。',
    icon: 'playlist',
    shots: [screenshots.playlist, screenshots.ordinaryMode],
  },
  {
    label: '06 / SHARED SETTINGS',
    title: '设置一次，多处同步',
    description:
      '主题可跟随 SPlayer、Plasma 或手动设置。应用后所有 SPTL 小组件同步，关闭播放器后仍然保留。',
    icon: 'settings',
    shots: [screenshots.theme],
  },
] as const

export const settingGroups = [
  {
    title: '歌词显示',
    description: '单行 / 双行、翻译 / 音译、基准字号与实时预览。',
    shot: settingsScreenshots.lyrics,
  },
  {
    title: '尺寸与布局',
    description: '封面位置与形状、圆角程度、圆形旋转，以及自动 / 固定宽度。',
    shot: settingsScreenshots.layout,
  },
  {
    title: '主题与动画',
    description: '主题来源、手动明暗、主题色与界面动画；无法读取 SP 配色时提示并回退 Plasma。',
    shot: settingsScreenshots.theme,
  },
  {
    title: '交互与离线',
    description: '即时操作反馈、悬停收藏、歌词跳转；空闲时可打开 SPlayer 或播放我喜欢的音乐。',
    shot: settingsScreenshots.interaction,
  },
]
