export const profile = {
  name: 'a彬彬a',
  handle: 'zxabinbina',
  email: 'zxabinbina@mcyzw.top',
  github: 'https://github.com/zxabinbina',
  bilibili: 'https://b23.tv/jS91pO8',
  server: 'https://mcyzw.top',
  address: 'play.mcyzw.top',
}

export const partners = [
  {
    id: 'csituka',
    name: 'Csituka_D',
    image: 'company/csituka.webp',
    url: 'https://csituka.top',
    domain: 'csituka.top',
    description: '去伙伴的个人空间坐坐，打个招呼。',
  },
]

export const aiAssistants = [
  {
    id: 'chatgpt',
    name: 'ChatGPT',
    image: 'company/chatgpt.svg',
    url: 'https://chatgpt.com',
    description: '聊想法，找灵感',
  },
  {
    id: 'claude',
    name: 'Claude',
    image: 'company/claude.svg',
    url: 'https://claude.ai',
    description: '推敲文字，梳理思路',
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    image: 'company/deepseek.svg',
    url: 'https://chat.deepseek.com',
    description: '拆解问题，探索解法',
  },
  {
    id: 'glm',
    name: 'GLM',
    image: 'company/glm.svg',
    url: 'https://chatglm.cn',
    description: '中文交流，代码协作',
  },
]

export const projectCatalog = {
  checkedAt: '2026-11-26',
  organization: 'https://github.com/Youzai-World-Team',
}

export type Project = {
  id: string
  repository: string
  role: string
  featured: boolean
  image?: { file: string; width: number; height: number }
  number: string
  title: string
  subtitle: string
  description: string
  tags: string[]
  url: string
  link: string
  icon?: 'youzai' | 'shield' | 'database' | 'server'
}

const myriadLogo = { file: 'myriad.svg', width: 180, height: 180 }

export const projects: Project[] = [
  {
    id: 'core',
    repository: 'Youzai-World-Team/YouzaiWorldCore',
    role: '团队项目',
    featured: true,
    image: { file: 'youzaiworld-core.png', width: 64, height: 64 },
    number: '01',
    title: 'YouzaiWorldCore',
    subtitle: '让方块世界，多一点可能。',
    description:
      '悠哉世界的核心模组。从自定义界面、传送锚点到宠物与成长系统，把想法变成可以游玩的体验。',
    tags: ['Java', 'Fabric', 'Minecraft'],
    url: 'https://github.com/Youzai-World-Team/YouzaiWorldCore',
    link: '探索源码',
    icon: 'youzai',
  },
  {
    id: 'web',
    repository: 'Youzai-World-Team/YouzaiWorldWebNew',
    role: '团队项目',
    featured: true,
    image: { file: 'youzaiworld-web.webp', width: 1200, height: 612 },
    number: '02',
    title: 'Youzai World Web',
    subtitle: '一个世界，从这里开始。',
    description: '悠哉世界的官网，连接服务器动态、状态监控、下载与教程，让每一次出发都更简单。',
    tags: ['Vue / Nuxt', 'TypeScript', 'Rust'],
    url: 'https://mcyzw.top',
    link: '访问网站',
    icon: 'youzai',
  },
  {
    id: 'gaze',
    repository: 'zxaBinbina/gaze-zh',
    role: '分支维护',
    featured: true,
    image: { file: 'gaze.svg', width: 128, height: 128 },
    number: '03',
    title: 'Gaze · 中文与登录修复',
    subtitle: '让日常使用，顺手一点。',
    description:
      '基于 Gaze 的中文源码分支，汉化图形界面与命令行，并修复 KDE 远程桌面误触发本机人脸扫描的问题。',
    tags: ['Rust', 'Linux', 'PAM'],
    url: '/projects/gaze',
    link: '访问官网',
  },
  {
    id: 'rdp',
    repository: 'zxaBinbina/rdp-access-auth',
    role: '个人项目',
    featured: true,
    image: { file: 'rdp-access-auth.png', width: 512, height: 394 },
    number: '04',
    title: 'RDP Access Auth',
    subtitle: '为远程连接，多守一道门。',
    description:
      '面向 SakuraFrp 远程桌面的网页认证入口，结合通行密钥与 IP 授权，让远程访问更从容。',
    tags: ['Python', 'WebAuthn', 'Cloudflare'],
    url: '/projects/rdp-access-auth',
    link: '官网与部署 Wiki',
    icon: 'shield',
  },
  {
    id: 'myriad',
    repository: 'zxaBinbina/myriad',
    role: '个人项目',
    featured: true,
    image: myriadLogo,
    number: '05',
    title: '万象 · Myriad',
    subtitle: '把常用入口，收进一页。',
    description:
      '替换浏览器新标签页的扩展，把快捷方式、小组件和多引擎搜索放在一起，还能订阅热榜与 RSS。',
    tags: ['Vue', 'TypeScript', 'WXT'],
    url: 'https://github.com/zxaBinbina/myriad',
    link: '源码与安装说明',
  },
  {
    id: 'sptl',
    repository: 'zxaBinbina/SplayerPlasmaTaskbarLyrics',
    role: '个人项目',
    featured: true,
    image: { file: 'sptl.png', width: 833, height: 833 },
    number: '06',
    title: 'SPTL · SPlayer 任务栏歌词',
    subtitle: '让歌词，留在任务栏。',
    description:
      '为 KDE Plasma 带来 SPlayer Next 同步歌词、专辑封面与播放控制，听歌时少切一次窗口。',
    tags: ['QML', 'KDE Plasma', 'Python'],
    url: '/projects/SPTL',
    link: '官网与安装指南',
  },
  {
    id: 'api',
    repository: 'Youzai-World-Team/YouzaiWorldApi',
    role: '团队项目',
    featured: false,
    number: '07',
    title: 'YouzaiWorldApi',
    subtitle: '连接世界背后的服务。',
    description: '悠哉世界服务器使用的 API 项目，为服务器相关功能提供接口支持。',
    tags: ['Vue', 'API'],
    url: 'https://github.com/Youzai-World-Team/YouzaiWorldApi',
    link: '探索仓库',
    icon: 'youzai',
  },
  {
    id: 'assets',
    repository: 'Youzai-World-Team/YouzaiWorldWebAssets',
    role: '团队项目',
    featured: false,
    number: '08',
    title: 'YouzaiWorldWebAssets',
    subtitle: '让网站素材各就各位。',
    description: '集中存放悠哉世界主站资源文件，用于同步到 Cloudflare。',
    tags: ['Shell', 'Cloudflare', '静态资源'],
    url: 'https://github.com/Youzai-World-Team/YouzaiWorldWebAssets',
    link: '探索仓库',
    icon: 'youzai',
  },
  {
    id: 'status',
    repository: 'Youzai-World-Team/YouzaiWorldServiceStatus',
    role: '团队项目',
    featured: false,
    number: '09',
    title: 'YouzaiWorldServiceStatus',
    subtitle: '关心每一次连接。',
    description: '检查悠哉世界相关服务的可用性，帮助了解服务是否正常运行。',
    tags: ['TypeScript', '状态监控'],
    url: 'https://github.com/Youzai-World-Team/YouzaiWorldServiceStatus',
    link: '探索仓库',
    icon: 'youzai',
  },
  {
    id: 'email',
    repository: 'Youzai-World-Team/YouzaiWorldDonaimEmailWorker',
    role: '团队项目',
    featured: false,
    number: '10',
    title: 'YouzaiWorldDonaimEmailWorker',
    subtitle: '打理域名下的往来。',
    description: '悠哉世界的域名邮件管理器，用于管理域名邮件。',
    tags: ['JavaScript', '邮件'],
    url: 'https://github.com/Youzai-World-Team/YouzaiWorldDonaimEmailWorker',
    link: '探索仓库',
    icon: 'youzai',
  },
  {
    id: 'modpack',
    repository: 'Youzai-World-Team/YouzaiWorldModpack',
    role: '团队项目',
    featured: false,
    number: '11',
    title: 'YouzaiWorldModpack',
    subtitle: '准备好，来世界里坐坐。',
    description: '存放悠哉世界服务器整合包的下载资源，方便玩家获取游玩所需的整合包。',
    tags: ['Minecraft', '整合包'],
    url: 'https://github.com/Youzai-World-Team/YouzaiWorldModpack',
    link: '探索仓库',
    icon: 'youzai',
  },
  {
    id: 'myriad-api',
    repository: 'zxaBinbina/myriad_api',
    role: '个人项目',
    featured: false,
    image: myriadLogo,
    number: '12',
    title: '万象同步服务',
    subtitle: '换台设备，也能接着用。',
    description: '可自建的万象后端，用于跨设备同步和云端备份，并提供天气、热榜和 RSS 等数据接口。',
    tags: ['TypeScript', 'Cloudflare Workers', 'Yjs'],
    url: 'https://github.com/zxaBinbina/myriad_api',
    link: '源码与部署说明',
    icon: 'database',
  },
  {
    id: 'browser-api',
    repository: 'zxaBinbina/homepage-browser-api',
    role: '个人项目',
    featured: false,
    number: '13',
    title: '私人网页浏览器后端',
    subtitle: '为临时浏览会话提供服务。',
    description: '为本站的私人网页浏览器提供密码认证和网页中转，让访客在临时会话中打开网页。',
    tags: ['TypeScript', 'Cloudflare Workers', 'Scramjet'],
    url: 'https://github.com/zxaBinbina/homepage-browser-api',
    link: '源码与部署说明',
    icon: 'server',
  },
]

export const featuredProjects = projects.filter((project) => project.featured)
