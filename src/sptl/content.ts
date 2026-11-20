export const sptlProject = {
  version: '0.1.1',
  repository: 'https://github.com/zxaBinbina/SplayerPlasmaTaskbarLyrics',
  source: '/projects/SPTL/sptl-0.1.1-source.zip',
}

export const features = [
  {
    label: '01 / LYRICS',
    title: '原文与翻译，一起看',
    description: '双行显示原文和翻译，也能切换音译或下一句。喜欢简洁？用单行歌词搭配歌曲信息。',
    icon: 'lyrics',
  },
  {
    label: '02 / IN SYNC',
    title: '跟着每一句，慢慢唱',
    description: '支持逐字高亮和长歌词滚动。暂停时停在当前字，切歌时柔和过渡。',
    icon: 'sync',
  },
  {
    label: '03 / PLAYBACK',
    title: '播放控制，就在手边',
    description: '悬停即可切歌、播放或暂停，滚轮调节音量；打开完整歌词，还能点击歌词跳转。',
    icon: 'playback',
  },
  {
    label: '04 / YOUR PANEL',
    title: '跟着任务栏，自然适配',
    description: '封面、两行文字与按钮随面板高度缩放。封面可放左侧或右侧，宽度可自动或固定。',
    icon: 'panel',
  },
  {
    label: '05 / APPEARANCE',
    title: '让桌面，保持你的样子',
    description: '跟随 SPlayer 或 Plasma 主题，也可手动选择明暗和主题色。界面动画可以单独关闭。',
    icon: 'theme',
  },
  {
    label: '06 / SHARED SETTINGS',
    title: '设置一次，多处同步',
    description: '在 KDE 小组件中修改并应用设置，其他 SPTL 小组件也会同步；关闭播放器后仍然保留。',
    icon: 'settings',
  },
] as const

export const settingGroups = [
  { title: '歌词显示', description: '单行 / 双行、翻译 / 音译、基准字号与实时预览。' },
  { title: '尺寸与布局', description: '封面位置、自动 / 固定宽度和最大显示宽度。' },
  { title: '主题与动画', description: '主题来源、手动明暗、主题色与界面动画。' },
  { title: '交互与离线', description: '主体点击、歌词跳转，以及播放器关闭时的显示与操作。' },
]
