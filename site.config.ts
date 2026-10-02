export const siteContent = {
  title: 'a彬彬a · 在代码与方块之间',
  description:
    '你好，我是 a彬彬a（zxabinbina）。在代码与方块之间，创造一点不一样。探索我的开发项目与 Minecraft 悠哉世界服务器。',
  name: 'a彬彬a · 个人主页',
  url: 'https://zxabinbina.cc.cd/',
  image: 'images/share-cover.jpg',
  imageAlt: '蓝天下的 Minecraft 方块雕像，a彬彬a 的方块世界',
}

export function createSiteMeta(baseUrl = siteContent.url) {
  const url = new URL(baseUrl)
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash) {
    throw new Error('SITE_URL 必须是不包含登录信息、查询参数和锚点的 HTTPS 网站地址')
  }
  if (!url.pathname.endsWith('/')) url.pathname += '/'
  return {
    ...siteContent,
    url: url.href,
    image: new URL(siteContent.image, url).href,
  }
}
