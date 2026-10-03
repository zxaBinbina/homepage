import type { PageName } from './src/pages'
export const siteContent = {
  title: 'a彬彬a · 在代码与方块之间',
  description:
    '你好，我是 a彬彬a（zxabinbina）。在代码与方块之间，创造一点不一样。探索我的开发项目与 Minecraft 悠哉世界服务器。',
  name: 'a彬彬a · 个人主页',
  url: 'https://zxabinbina.cc.cd/',
  image: 'images/share-cover.jpg',
  imageAlt: '蓝天下的 Minecraft 方块雕像，a彬彬a 的方块世界',
}

const projectPages = {
  directory: {
    title: '项目目录 · a彬彬a',
    description:
      '浏览 a彬彬a 已公开的开发项目：YouzaiWorldCore、悠哉世界官网、Gaze 中文与登录修复和 RDP Access Auth，查看简介、技术栈与访问入口。',
    path: 'project/',
  },
  rdp: {
    title: 'RDP Access Auth · 远程桌面，先认证再连接',
    description:
      '为 SakuraFrp 远程桌面增加 HTTPS 认证入口，支持固定密码、临时密码、WebAuthn 通行密钥与公网 IPv4 授权。',
    path: 'projects/rdp-access-auth',
  },
  wiki: {
    title: '部署与维护 Wiki · RDP Access Auth',
    description:
      'RDP Access Auth 完整源码部署指南：Python 环境、systemd、Cloudflare Tunnel、SakuraFrp 准入、通行密钥与故障排查。',
    path: 'projects/rdp-access-auth/wiki',
  },
}

export function createSiteMeta(baseUrl = siteContent.url, page: PageName = 'home') {
  const url = new URL(baseUrl)
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash) {
    throw new Error('SITE_URL 必须是不包含登录信息、查询参数和锚点的 HTTPS 网站地址')
  }
  if (!url.pathname.endsWith('/')) url.pathname += '/'
  const content = page === 'home' ? siteContent : projectPages[page]
  return {
    ...siteContent,
    title: content.title,
    description: content.description,
    url: page === 'home' ? url.href : new URL(projectPages[page].path, url).href,
    image: new URL(siteContent.image, url).href,
  }
}
