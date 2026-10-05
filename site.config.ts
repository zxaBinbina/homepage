import { isProjectPage, pages, type PageName } from './src/pages'
import { isToolId, toolCatalog } from './src/tools/catalog'
export const siteContent = {
  title: 'a彬彬a · 在代码与方块之间',
  description:
    '你好，我是 a彬彬a（zxabinbina）。在代码与方块之间，创造一点不一样。探索我的开发项目与 Minecraft 悠哉世界服务器。',
  name: 'a彬彬a · 个人主页',
  url: 'https://zxabinbina.cc.cd/',
  image: 'images/share-avatar.jpg',
  imageAlt: 'a彬彬a 的头像',
  imageType: 'image/jpeg',
  imageWidth: 256,
  imageHeight: 256,
}

const projectPages = {
  tools: {
    title: '网页工具 · a彬彬a',
    description:
      '一些顺手的网页小工具：JSON 格式化、Base64 与 URL 编解码、时间戳转换、UUID 生成和文本整理，全部在浏览器本地处理。',
  },
  directory: {
    title: '项目目录 · a彬彬a',
    description:
      '浏览 a彬彬a 已公开的开发项目：YouzaiWorldCore、悠哉世界官网、Gaze 中文与登录修复和 RDP Access Auth，查看简介、技术栈与访问入口。',
  },
  rdp: {
    title: 'RDP Access Auth · 远程桌面，先认证再连接',
    description:
      '为 SakuraFrp 远程桌面增加 HTTPS 认证入口，支持固定密码、临时密码、WebAuthn 通行密钥与公网 IPv4 授权。',
  },
  wiki: {
    title: '部署与维护 Wiki · RDP Access Auth',
    description:
      'RDP Access Auth 安装包与浏览器部署向导：RPM / DEB、Cloudflare Tunnel、SakuraFrp 准入、通行密钥与故障排查。',
  },
  downloads: {
    title: '下载发行版 · RDP Access Auth',
    description:
      '从 GitHub Releases 获取 RDP Access Auth 的 RPM、DEB 和其他发行版文件，查看每个版本的说明与校验资产。',
  },
}

export function createSiteMeta(baseUrl = siteContent.url, page: PageName = 'home') {
  const url = new URL(baseUrl)
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash) {
    throw new Error('SITE_URL 必须是不包含登录信息、查询参数和锚点的 HTTPS 网站地址')
  }
  if (!url.pathname.endsWith('/')) url.pathname += '/'
  const content =
    page === 'home'
      ? siteContent
      : isToolId(page)
        ? {
            title: `${toolCatalog[page].name} · 网页工具 · a彬彬a`,
            description: toolCatalog[page].description,
          }
        : projectPages[page]
  const image = isProjectPage(page)
    ? {
        image: 'images/rdp-access-auth.png',
        imageAlt: 'RDP Access Auth 软件 Logo',
        imageType: 'image/png',
        imageWidth: 512,
        imageHeight: 394,
      }
    : siteContent
  return {
    ...siteContent,
    imageAlt: image.imageAlt,
    imageType: image.imageType,
    imageWidth: image.imageWidth,
    imageHeight: image.imageHeight,
    title: content.title,
    description: content.description,
    url: page === 'home' ? url.href : new URL(pages[page].slice(1), url).href,
    image: new URL(image.image, url).href,
  }
}

export function createStructuredData(baseUrl = siteContent.url, page: PageName = 'home') {
  const home = createSiteMeta(baseUrl)
  const meta = createSiteMeta(baseUrl, page)
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebSite',
        '@id': `${home.url}#website`,
        url: home.url,
        name: home.name,
        inLanguage: 'zh-CN',
      },
      {
        '@type': page === 'directory' || page === 'tools' ? 'CollectionPage' : 'WebPage',
        '@id': `${meta.url}#webpage`,
        url: meta.url,
        name: meta.title,
        description: meta.description,
        inLanguage: 'zh-CN',
        isPartOf: { '@id': `${home.url}#website` },
        primaryImageOfPage: { '@type': 'ImageObject', url: meta.image },
      },
    ],
  }
}

export function serializeStructuredData(data: ReturnType<typeof createStructuredData>) {
  return JSON.stringify(data).replace(/</g, '\\u003c')
}
