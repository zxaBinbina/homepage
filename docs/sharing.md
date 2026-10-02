# 微信与 QQ 分享元信息

`site.config.ts` 是标题、简介、域名和分享封面的唯一配置来源。默认域名为 `https://zxabinbina.cc.cd/`，沿用原页面的 title 和 description。

`vite.config.ts` 使用 EJS 渲染 `index.html`。标签在开发服务器返回 HTML、生产构建生成 HTML 时注入，直接出现在页面源码中，不依赖 Vue 挂载或浏览器执行 JavaScript。`<%= … %>` 会转义属性中的特殊字符。

已包含：

- `title`、唯一的 `description`、canonical。
- `og:title`、`og:description`、`og:type`、`og:site_name`、`og:locale`、`og:url`。
- `og:image`、HTTPS 地址、类型、尺寸和替代文字。
- QQ 的 `itemprop="name"`、`itemprop="image"`，以及复用同一个 description 标签的 `itemprop="description"`。

分享图片由现有 Minecraft 主图生成，文件为 `public/images/share-cover.jpg`（1200 × 630 JPEG），正式地址为：

```
https://zxabinbina.cc.cd/images/share-cover.jpg
```

修改文案可编辑 `site.config.ts`；修改部署地址可设置 `SITE_URL` 环境变量（完整 HTTPS 地址，也支持子目录）。运行 `npm run build` 后发布完整 `dist/`，确保页面和分享图片无需登录即可访问。正式域名上的内容只有部署后才会更新。

微信和 QQ 的实际卡片呈现还取决于平台的抓取、缓存与分享入口；这些标签提供抓取信息，不等同于微信 JS-SDK 的自定义分享接口。

运行 `python3 scripts/check-sharing.py` 检查构建输出；也可传入保存的开发服务器 HTML 文件路径。
