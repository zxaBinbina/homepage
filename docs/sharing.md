# 微信与 QQ 分享元信息

`site.config.ts` 是个人主页、项目目录、RDP 官网与 Wiki 的标题、简介、域名和分享封面的统一配置来源。默认域名为 `https://zxabinbina.cc.cd/`，沿用原页面的 title 和 description。

`vite.config.ts` 注册 `build/pageTemplates.ts` 插件，使用 EJS 渲染唯一的 `index.html` 基础模板。开发时按请求地址注入元信息，构建时根据 `src/pages.ts` 自动生成四个 URL 的 HTML；页面结构由 `.vue` 模板维护。标签在开发服务器返回 HTML、生产构建生成 HTML 时注入，直接出现在页面源码中，不依赖 Vue 挂载或浏览器执行 JavaScript。`<%= … %>` 会转义属性中的特殊字符。

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

运行 `python3 scripts/check-sharing.py` 检查四个页面的构建输出；也可传入保存的开发服务器 HTML 文件路径。

## 项目子页

RDP Access Auth 官网和 Wiki 的标题与简介由 `site.config.ts` 的 `projectPages` 配置提供，通过 `createSiteMeta` 与主页共用生成逻辑，canonical 和 `og:url` 根据 `site.config.ts` 的基础域名生成，分别指向 `/projects/rdp-access-auth/` 和 `/projects/rdp-access-auth/wiki/`。目前复用个人主页分享封面。元信息在构建时写入 HTML，不依赖 JavaScript；Wiki 正文在构建时转换为模块数据，由 Vue 组件在浏览器中渲染，与主页的客户端渲染架构保持一致。项目页面的浏览器检查使用 `scripts/check-rdp-pages.py`，四个页面的原始 HTML 分享检查均使用 `scripts/check-sharing.py`。

个人主页浏览器图标沿用 `public/favicon.svg`；RDP 官网与 Wiki 使用透明的 `public/images/rdp-access-auth.png`。图标按页面由同一 EJS 模板选择，分享封面配置独立于浏览器图标。

项目目录 `/project/` 的标题、简介同样由 `site.config.ts` 提供，复用主页分享封面与 favicon；`/project` 可直接访问，canonical 统一为 `/project/`。
