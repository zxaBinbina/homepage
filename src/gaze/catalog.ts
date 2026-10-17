/** Gaze 中文官网的文档目录：路由、侧边栏分组与分享元信息共用这一份数据。 */
export interface GazeGuide {
  id: string
  title: string
  group: string
  description: string
}

export const gazeGuideGroups = [
  { id: 'start', label: '开始使用' },
  { id: 'auth', label: '身份认证' },
  { id: 'usage', label: '使用与配置' },
  { id: 'deep', label: '深入了解' },
] as const

export const gazeGuides: GazeGuide[] = [
  {
    id: 'getting-started',
    title: '快速上手',
    group: 'start',
    description: '十分钟内把 Gaze 跑起来：安装、录入人脸，并在终端测试认证。',
  },
  {
    id: 'installation',
    title: '安装',
    group: 'start',
    description: '一行安装脚本与 Debian、Fedora、openSUSE、Arch、Flatpak 等手动安装方式。',
  },
  {
    id: 'nixos',
    title: 'Nix 与 NixOS',
    group: 'start',
    description: '通过 Nix flake 与 NixOS 模块声明式配置 Gaze 守护进程、D-Bus、polkit 与 PAM。',
  },
  {
    id: 'development',
    title: '开发',
    group: 'start',
    description: '从源码构建 Gaze：依赖、just 构建命令、打包与集成测试。',
  },
  {
    id: 'contributing',
    title: '参与贡献',
    group: 'start',
    description: '贡献代码、报告问题与参与项目开发的指南。',
  },
  {
    id: 'pam',
    title: 'PAM 集成',
    group: 'auth',
    description: '为 sudo、polkit 与共享 PAM 栈配置面部认证，理解模式、回退与安全边界。',
  },
  {
    id: 'gnome',
    title: 'GNOME 扩展',
    group: 'auth',
    description: 'GNOME 锁屏与 GDM 登录的面部认证：安装、启用、常见问题与钥匙串解锁。',
  },
  {
    id: 'cinnamon',
    title: 'Cinnamon 扩展',
    group: 'auth',
    description: '为 Cinnamon 锁屏与 PolKit 提示配置 Gaze 面部认证。',
  },
  {
    id: 'kde',
    title: 'KDE Plasma',
    group: 'auth',
    description: 'KDE Plasma 锁屏免按键面部解锁、登录欢迎程序与系统设置页面。',
  },
  {
    id: 'hyprland',
    title: 'Hyprland（hyprlock）',
    group: 'auth',
    description: '在 Hyprland 上通过 hyprlock 的 PAM 服务实现面部解锁。',
  },
  {
    id: 'omarchy',
    title: 'Omarchy',
    group: 'auth',
    description: 'Omarchy Quickshell 锁屏插件：密码、指纹与人脸三种独立认证方式。',
  },
  {
    id: 'lightdm',
    title: 'LightDM',
    group: 'auth',
    description: '通过 PAM 为 LightDM 登录管理器添加面部认证。',
  },
  {
    id: 'greetd',
    title: 'greetd',
    group: 'auth',
    description: '在 greetd 登录 greeter 中使用 Gaze 的 PAM 集成。',
  },
  {
    id: 'console',
    title: '控制台登录（TTY）',
    group: 'auth',
    description: '在虚拟控制台登录中启用面部认证及其注意事项。',
  },
  {
    id: 'gui',
    title: '图形界面指南',
    group: 'usage',
    description: '使用 GTK 图形应用录入、管理与测试面部认证。',
  },
  {
    id: 'cli',
    title: '命令行指南',
    group: 'usage',
    description: 'gaze 命令全集：录入、认证、管理人脸、钥匙串与诊断。',
  },
  {
    id: 'configuration',
    title: '配置',
    group: 'usage',
    description: '/etc/gaze/config.toml 全部配置项：推理、安全、摄像头、活体检测与存储。',
  },
  {
    id: 'acceleration',
    title: '硬件加速',
    group: 'usage',
    description: 'Intel OpenVINO 与 AMD Ryzen AI NPU 推理加速的安装与验证。',
  },
  {
    id: 'uninstallation',
    title: '卸载',
    group: 'usage',
    description: '彻底移除 Gaze：软件包、PAM 配置、模型与数据。',
  },
  {
    id: 'troubleshooting',
    title: '故障排查',
    group: 'usage',
    description: '摄像头选择、守护进程启动、DBus 权限、PAM 锁定与模型问题的排查步骤。',
  },
  {
    id: 'how-it-works',
    title: '工作原理',
    group: 'deep',
    description: '从摄像头帧到认证结果的完整链路：检测、对齐、特征向量、比对与活体检测。',
  },
  {
    id: 'comparison',
    title: '同类项目对比',
    group: 'deep',
    description: 'Gaze 与 Howdy 等同类面部认证项目的对比。',
  },
]

export const gazeGuideIds = gazeGuides.map((guide) => guide.id)

export function gazeGuide(id: string): GazeGuide | undefined {
  return gazeGuides.find((guide) => guide.id === id)
}

export function gazeGuidePath(id: string): string {
  return `/projects/gaze/guide/${id}`
}

export const gazeRepoUrl = 'https://github.com/zxaBinbina/gaze-zh'

/** 派生自指南 id 的 Vue Router 页面名（如 gaze.getting-started）。 */
export function gazePageName(id: string): string {
  return `gaze.${id}`
}

export function gazeGuideIdForPage(name: unknown): string | undefined {
  return typeof name === 'string' && name.startsWith('gaze.') ? name.slice(5) : undefined
}
