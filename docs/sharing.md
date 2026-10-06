# 微信与 QQ 分享元信息

`site.config.ts` 是个人主页、项目目录、网页工具、小游戏与 RDP 子站 的标题、简介、域名和分享封面的统一配置来源。默认域名为 `https://zxabinbina.cc.cd/`，沿用原页面的 title 和 description。

`vite.config.ts` 注册 `build/pageTemplates.ts` 插件，使用 EJS 渲染唯一的 `index.html` 基础模板。开发时按请求地址注入元信息，构建时根据 `src/pages.ts` 自动生成所有已注册 URL 的 HTML；页面结构由 `.vue` 模板维护。标签在开发服务器返回 HTML、生产构建生成 HTML 时注入，直接出现在页面源码中，不依赖 Vue 挂载或浏览器执行 JavaScript。`<%= … %>` 会转义属性中的特殊字符。

已包含：

- `title`、唯一的 `description`、canonical。
- `og:title`、`og:description`、`og:type`、`og:site_name`、`og:locale`、`og:url`。
- `og:image`、HTTPS 地址、类型、尺寸和替代文字。
- QQ 的 `itemprop="name"`、`itemprop="image"`，以及复用同一个 description 标签的 `itemprop="description"`。
- `robots` 索引指令与 `max-image-preview:large`，允许搜索结果使用大图预览。
- JSON-LD `WebSite` 与 `WebPage`（项目 / 工具 / 游戏目录为 `CollectionPage`），标记页面名称、描述、规范地址及所属网站。

分享图片按页面分组：

| 页面范围                           | 分享图片                                         | 格式与尺寸      |
| ---------------------------------- | ------------------------------------------------ | --------------- |
| 个人主页、项目目录、工具与游戏页面 | `public/images/share-avatar.jpg`（个人头像）     | JPEG，256 × 256 |
| RDP 官网、Wiki 与下载页            | `public/images/rdp-access-auth.png`（软件 Logo） | PNG，512 × 394  |

头像原文件 `avatar.png` 实际为 JPEG；分享专用的 `share-avatar.jpg` 是它的原样副本，使用正确扩展名以匹配服务器响应格式。更新头像时同步更新该副本。OG 图片地址、格式、尺寸和替代文字统一由 `site.config.ts` 提供，QQ 图片与 JSON-LD 同步使用相同图片，站内切换时也同步更新。原 Minecraft `share-cover.jpg` 继续用于 README 展示。

修改文案可编辑 `site.config.ts`；修改部署地址可设置 `SITE_URL` 环境变量（完整 HTTPS 地址，也支持子目录）。运行 `npm run build` 后发布完整 `dist/`，确保页面和分享图片无需登录即可访问。正式域名上的内容只有部署后才会更新。

微信和 QQ 的实际卡片呈现还取决于平台的抓取、缓存与分享入口；这些标签提供抓取信息，不等同于微信 JS-SDK 的自定义分享接口。

运行 `python3 scripts/check-sharing.py` 检查所有页面的构建输出；也可传入保存的开发服务器 HTML 文件路径。

## 搜索引擎收录

构建时 `build/pageTemplates.ts` 从 `src/pages.ts` 自动生成 `sitemap.xml`，只包含 32 个页面的规范地址，不包含查询参数、锚点、旧地址或错误页。地址与 canonical 一样使用 `SITE_URL`；没有可靠的内容修改时间时不生成 `lastmod`，避免每次构建都错误地标记更新。`robots.txt` 允许抓取并声明站点地图地址。部署完整 `dist/` 后，可在 Google Search Console、Bing Webmaster Tools 等站长平台验证域名并提交 `https://zxabinbina.cc.cd/sitemap.xml`。

构建同时生成带 `noindex` 的 `404.html`，让 Cloudflare Pages 对未知路径返回真实 404，避免把不存在的地址当作首页收录。已注册页面与历史地址仍由现有 HTML 产物和 301 规则承接。此状态码行为由部署平台提供，Vite 预览服务不模拟 Cloudflare 的 404 策略。

正文继续按原来的 Vue 客户端逻辑加载，动画和交互不变；JSON-LD 随站内切换更新。当前优化帮助搜索引擎发现页面与理解元信息，正文抓取仍依赖搜索引擎执行 JavaScript 的能力，不能保证收录或排名。无需填写关键词堆砌标签，也不虚构评价或评分。

构建后运行 `python3 scripts/check-seo.py`，验证 sitemap 与所有 HTML canonical 一一对应、JSON-LD、robots 指令和错误页。自定义域名构建时，检查脚本使用相同的 `SITE_URL`。如果部署到子目录，需在域名根路径另外提供 `robots.txt`，搜索引擎只从根路径读取该文件。

## 项目子页

RDP Access Auth 官网和 Wiki 的标题与简介由 `site.config.ts` 的 `projectPages` 配置提供，通过 `createSiteMeta` 与主页共用生成逻辑，canonical 和 `og:url` 根据 `site.config.ts` 的基础域名生成，分别指向 `/projects/rdp-access-auth` 和 `/projects/rdp-access-auth/wiki`。官网、Wiki 与下载页使用 RDP Access Auth 软件 Logo 作为分享图片。元信息在构建时写入 HTML，不依赖 JavaScript；Wiki 正文在构建时转换为模块数据，由 Vue 组件在浏览器中渲染，与主页的客户端渲染架构保持一致。项目页面的浏览器检查使用 `scripts/check-rdp-pages.py`，所有页面的原始 HTML 分享检查均使用 `scripts/check-sharing.py`。

个人主页浏览器图标沿用 `public/favicon.svg`；RDP 官网与 Wiki 使用透明的 `public/images/rdp-access-auth.png`。图标按页面由同一 EJS 模板选择，分享封面配置独立于浏览器图标。

项目目录 `/project` 的标题、简介同样由 `site.config.ts` 提供，复用主页头像分享图片与 favicon；`/project` 可直接访问，canonical 统一为 `/project`。

站内无刷新切换时，`src/router.ts` 复用 `createSiteMeta` 更新浏览器标题、description、canonical、Open Graph、QQ 标签及 favicon。`vite.config.ts` 将同一 `SITE_URL` 注入客户端，确保运行时与 EJS 构建结果一致。分享平台直接请求各页面时仍可从 HTML 源码获取完整标签。

页面路径统一不带末尾斜线，canonical 与 `og:url` 直接复用 `src/pages.ts` 的路径。构建输出为根 `index.html`、`project.html`、`projects/rdp-access-auth.html`、`projects/rdp-access-auth/wiki.html`；Cloudflare Pages 以无 `.html` 的地址提供页面，自动生成的 `_redirects` 将旧的带斜线与 `/index.html` 地址转到规范地址。部署时保留该文件。

## 网页工具

工具目录 `/tool` 的元信息由 `site.config.ts` 提供；十二个 `/tools/*` 页面（JSON、Base64、URL、时间戳、UUID、文本、进制、哈希、JWT、密码、HTML 实体、颜色）的标题、简介来自 `src/tools/catalog.ts`。这些页面使用主页 favicon 与头像分享图片，构建生成 `tool.html` 和 `tools/*.html`，同样支持无刷新切换、原始 HTML 分享标签与规范地址重定向。`scripts/check-sharing.py` 覆盖所有工具页面。

## 小游戏

游戏目录 `/game` 的元信息由 `site.config.ts` 提供；十三个 `/games/*` 页面（2048、扫雷、纸牌接龙、俄罗斯方块、数独、中国象棋、五子棋、贪吃蛇、消灭星星、华容道、跳一跳、国际象棋单机版、围棋）的标题和简介来自 `src/games/catalog.ts`。这些页面沿用主页 favicon 与头像分享图片，构建生成 `game.html` 和 `games/*.html`。规范地址、原始 HTML 分享标签、JSON-LD、站点地图和旧地址重定向均沿用公共构建逻辑，`scripts/check-sharing.py` 与 `scripts/check-seo.py` 覆盖这些新页面。
