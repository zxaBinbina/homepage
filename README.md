# a彬彬a · 个人主页

在代码与方块之间，创造一点不一样。

这是 a彬彬a（zxabinbina）的个人主页，展示开发项目、Minecraft 悠哉世界和日常热爱。使用 Vue 3、Vue Router、TypeScript 与 Vite 构建，以原生 CSS 实现布局、主题和动效，通用图标来自 Lucide。

[访问主页](https://zxabinbina.cc.cd/) · [设计规范](DESIGN.md) · [协作约定](AGENTS.md)

![主页 Minecraft 主视觉：蓝天下的方块雕像](public/images/share-cover.jpg)

## 视觉设计

页面围绕「开发者与方块世界构筑者」的身份展开，以真实项目图像和 Minecraft 实景建立个人特色。

- **深蓝灰与天蓝**：深色基底搭配蓝色行动按钮、链接和重点文字；浅色主题使用灰白背景与更深的蓝色。
- **舒展的阅读节奏**：居中双行首屏标题、大幅景观、编号分区与充足留白，将访客从自我介绍引向作品和社区。
- **柔和的组件层次**：悬浮毛玻璃导航、胶囊按钮、细边框圆角卡片，辅以少量光晕和项目图像透视。
- **轻量动效**：首屏错峰淡入、区块滚动显现、悬停反馈；适配减少动态效果的系统偏好。
- **完整的窄屏布局**：移动菜单、项目单列布局、可收纳的音乐歌单，支持最小 `320px` 视口。

主题优先使用访客保存的选择，否则跟随系统。字体栈为 Inter、Noto Sans SC 和系统无衬线字体；当前未额外加载字体文件。

精确色值、字号、间距、断点、素材用途及组件状态见 [DESIGN.md](DESIGN.md)。

## 页面内容

| 区域     | 内容                                                                    |
| -------- | ----------------------------------------------------------------------- |
| 首屏     | 个人主张、自我介绍、作品与服务器入口、Minecraft 横幅                    |
| 关于     | 个人资料、开发与创造兴趣                                                |
| 精选项目 | YouzaiWorldCore、Youzai World Web、Gaze 中文与登录修复、RDP Access Auth |
| 悠哉世界 | 服务器实景、特色、官网、地址复制与游玩指南                              |
| 联系     | 邮箱、GitHub、Bilibili                                                  |
| 音乐浮层 | 网易云播放控制、歌词、歌单搜索，桌面侧栏与窄屏覆盖式歌单                |

音乐在访客首次点击入口后尝试播放，关闭浮层后继续播放。页面还包含主题切换、键盘焦点、移动菜单、复制反馈和分享卡片元信息。

## 项目目录

主页、项目目录与 RDP 子站共用完全一致的 `src/components/SiteFooter.vue` 页脚。

访问 `https://zxabinbina.cc.cd/project`（规范地址 `/project`）可查看全部已公开项目，支持按名称、简介、仓库原名、所属账号或技术栈搜索。列表与个人主页复用 `src/content.ts` 的项目数据和 `src/components/ProjectCard.vue` 卡片组件，统一图标、透视图片、文字标签与悬停效果；目录展示完整列表，首页通过 `featured` 标记保留四个精选项目。当前列表于 2026-10-04 从 [个人仓库](https://github.com/zxaBinbina?tab=repositories) 和 [组织仓库](https://github.com/orgs/Youzai-World-Team/repositories) 核对，核对了 12 个公开仓库，目录收录其中 9 个项目（个人 2 个、组织 7 个），保留开发分支，排除本站 `homepage` 项目、个人自我介绍与组织 `.github` 等资料仓库。列表为本地维护快照，不在访客打开页面时请求 GitHub；更新时同时维护 `repository`、用途说明和 `projectCatalog.checkedAt`。页面模板位于 `src/ProjectDirectory.vue`，沿用个人主页主题、图标和萌备页脚；从主页导航「项目」或项目区「查看全部项目」进入。主页与目录页共用 `src/components/SiteHeader.vue` 完整导航，包含主题、音乐、GitHub、联系与移动菜单；桌面与移动导航均提供「首页」（`/`）、「项目」（`/project`）、「工具」（`/tool`）、「游戏」（`/game`）和「悠哉世界」（`https://mcyzw.top`），联系入口保留主页锚点。发布完整构建产物即可上线。运行 `python3 scripts/check-project-directory.py` 检查目录访问、搜索、图片和响应式，可用 `HOMEPAGE_TEST_URL` 指定开发服务器地址。

## 网页工具

访问 `https://zxabinbina.cc.cd/tool`，或点击桌面 / 移动导航中的「工具」，可按分类与关键词查找十二个网页工具。工具页沿用主页的深浅主题、胶囊导航、圆角卡片和共用页脚；主页、项目目录、工具与游戏之间切换时保留播放器实例。

| 工具          | 地址               | 功能                                                              |
| ------------- | ------------------ | ----------------------------------------------------------------- |
| JSON 格式化   | `/tools/json`      | 语法校验、2 / 4 空格或 Tab 缩进、压缩；保留长整数、键顺序和重复键 |
| Base64 编解码 | `/tools/base64`    | UTF-8 文本与标准 / URL 安全 Base64 双向转换，支持中文和 Emoji     |
| URL 编解码    | `/tools/url`       | 参数值或完整网址转换，可将参数中的 `+` 解码为空格                 |
| 时间戳转换    | `/tools/timestamp` | 秒 / 毫秒与日期双向转换，显示 UTC 和本地时区，支持当前时间        |
| UUID 生成     | `/tools/uuid`      | 浏览器安全随机数生成 UUID v4，每批 1–100 个，可选大写和连字符     |
| 文本整理      | `/tools/text`      | 按行去重、移除空行、清理行首尾空格、大小写转换和字符 / 行数统计   |
| 进制转换      | `/tools/radix`     | 2–36 进制整数互转，支持正负数、匹配进制的前缀和超长整数           |
| 哈希计算      | `/tools/hash`      | UTF-8 文本的 SHA-256 / SHA-384 / SHA-512 / SHA-1 摘要             |
| JWT 解析      | `/tools/jwt`       | 查看 Header、Payload、签发 / 到期时间；不验证签名                 |
| 密码生成      | `/tools/password`  | 安全随机密码，自选长度、字符类型、数量，可排除易混字符            |
| HTML 实体转换 | `/tools/html`      | 特殊字符转义与带分号实体还原，结果始终按文本显示                  |
| 颜色转换      | `/tools/color`     | HEX / RGB / HSL 互转、原生取色器和颜色预览                        |

所有输入仅在浏览器内处理，不发送到接口、不持久保存，离开页面后清空。结果支持复制和下载；文本工具提供示例与清空，可继续转换的结果支持「将结果用作输入」。修改输入或转换选项后旧结果立即失效，避免误复制。文本输入处理上限为 100 万个 UTF-16 字符，JSON 支持最多 64 层嵌套，格式化结果上限为 400 万字符。Base64 工具用于 UTF-8 文本，不用于二进制文件。进制转换支持最多 4096 位整数，使用 BigInt 保留精度。哈希通过 Web Crypto 计算，支持空文本；等待计算时修改输入或选项会丢弃旧任务的结果。JWT 只解析内容与时间字段，不验证签名或授权。密码长度为 8–128，每批 1–50 个，使用浏览器安全随机数，每个密码包含所选的每类字符。颜色转换支持三位 / 六位 HEX、整数 RGB 与 HSL，不含透明度。

工具目录与工作页位于 `src/tools/`，名称、说明与分类统一维护在 `src/tools/catalog.ts`，转换逻辑位于 `src/tools/transform.ts`，样式位于 `src/style.css`。新增工具时同时登记 `src/pages.ts`、`src/router.ts` 和分享检查断言；`site.config.ts` 根据目录文案生成工具元信息。构建自动生成 `tool.html` 和 `tools/*.html`，随完整构建产物部署到现有 Cloudflare Pages 即可。

运行 `node scripts/check-tools.mjs` 检查转换规则和边界；预览服务启动后运行 `python3 scripts/check-tools-browser.py` 检查工具操作、复制下载、地址刷新、主题、移动菜单和响应式。浏览器脚本支持 `HOMEPAGE_TEST_URL` 与 `HOMEPAGE_BROWSER`，本次截图写入 `artifacts/tool*.png`。

## 小游戏

访问 `https://zxabinbina.cc.cd/game`，或点击桌面 / 移动导航中的「游戏」，进入小游戏目录。游戏沿用本站深浅主题与共用导航、页脚，无需登录或安装。

| 游戏     | 地址                 | 玩法与操作                                                                                       |
| -------- | -------------------- | ------------------------------------------------------------------------------------------------ |
| 2048     | `/games/2048`        | 方向键 / WASD、棋盘滑动与方向按钮；合并计分、达到 2048 后继续挑战、最多撤销 100 步               |
| 扫雷     | `/games/minesweeper` | 9 × 9 / 10 雷、12 × 12 / 24 雷；首步及周围安全、空白展开、插旗、数字周围快速翻开、计时与胜负提示 |
| 纸牌接龙 | `/games/solitaire`   | 经典 Klondike，翻一张、无限循环；红黑交替、整段移动、同花色 A → K 收牌、撤销与残局自动完成       |

2048 的键盘操作仅在棋盘与方向按钮内生效；滑动与合并动画约 230ms，期间不接受下一步移动，可勾选「无动画」立即操作，重开保留此选项。扫雷可右键或按 F 插旗，方向键移动焦点，回车 / 空格翻开；手机用「翻开 / 插旗」切换操作。纸牌支持点击选牌后放置、鼠标按住拖动和手机长按 300ms 后拖拽，拖到无效位置会回弹；普通滑动仍可滚动牌桌，竖屏时提供可关闭的横屏游玩提示。纸牌随机发牌，不保证每局可解；「自动完成」仅在全部暗牌翻开、牌堆与翻牌区清空时可用。

扫雷提供翻砖、踩雷爆炸和获胜扫描动画；纸牌提供移动、从牌堆翻出和翻开暗牌的动画。新翻出的牌覆盖在旧牌上方，旧牌保持原位；牌堆用完后，翻牌会逐张翻面收回，按牌数自动调整速度，整轮在 0.5 秒内完成，只记一步并可一次撤销。胜利时会播放可跳过或重播的翻转弹跳庆祝。牌面与牌背均适配深浅主题。系统启用减少动态效果时直接显示结果，所有玩法继续可用。

三个游戏均可通过「重新开始」右侧的全屏图标进入网页全屏，只显示游戏画面与操作区，隐藏站点导航、标题、玩法说明和页脚。进入与退出使用短暂淡入淡出，减少动态效果时立即切换。点击同一位置的退出图标或按 Esc 返回，当前牌局、得分、撤销记录与原页面滚动位置继续保留；手机支持竖屏和横屏，内容较多时可在游戏区域内滚动。

各游戏页先展示完整玩法教程，再显示游戏界面；教程末尾提醒离开或刷新会重新开局。游戏内保留胜负结果、必要操作与手机横屏提示，不再显示重复的操作摘要或每步文字反馈。游戏状态只保留在当前页面内，不上传、不持久保存。站内导航继续保留音乐播放器实例。名称和说明位于 `src/games/catalog.ts`，目录与游戏组件、独立规则逻辑均位于 `src/games/`，样式集中在 `src/style.css`。新增游戏时登记 `src/pages.ts`、`src/router.ts`、目录及 `GamePage.vue` 的游戏组件，并更新分享与站点地图检查断言。构建自动生成 `game.html` 和 `games/*.html`，随完整 `dist/` 部署即可。

运行 `node scripts/check-games.mjs` 验证合并规则、扫雷首步安全与胜负、接龙合法移动与发牌完整性。构建预览服务启动后，运行 `HOMEPAGE_TEST_URL=http://127.0.0.1:4173 python3 scripts/check-games-browser.py` 检查游戏交互、键盘 / 触摸、路由刷新、主题和响应式；截图写入 `artifacts/game-*.png`。共享导航与音乐实例由 `scripts/check-navigation.py` 一并检查。动效和拖拽专项运行 `python3 scripts/check-games-motion.py`，连接开发服务器（默认 `http://127.0.0.1:5173`），覆盖动画耗时、输入锁、取消 / 重开、鼠标整段拖动、手机长按与原生滚动、胜利庆祝和减少动态效果；终局动画使用仅开发环境可访问的组件状态构造测试牌面，不向正式页面添加测试入口。专项截图写入 `artifacts/game-motion-*.png`。

网页全屏专项运行 `python3 scripts/check-games-fullscreen.py`，检查全屏前后的游戏状态、按钮位置、焦点限制、Esc / 页面切换后的清理、全屏鼠标与手机拖拽、深浅主题和视口适配，截图写入 `artifacts/game-fullscreen-*.png`。

## 站内页面切换

主页、项目目录、网页工具、小游戏与 RDP 子站之间的普通链接使用 Vue Router 无刷新切换，保留浏览器前进 / 后退、历史滚动位置和跨页锚点。只接管当前同源且已注册的页面；外站、下载、接口、未知路径和新标签页操作仍按浏览器原有方式处理。地址栏直接访问或刷新仍由构建生成的 HTML 入口承接。站内页面路径统一不带末尾斜线，例如 `/project`、`/tool`、`/tools/json` 和 `/projects/rdp-access-auth/wiki`；旧的带斜线、`.html` 和 `/index.html` 地址会转到规范地址，并保留查询参数和锚点。

共享导航由 `src/App.vue` 挂载，主页、项目目录、工具与游戏页切换时保留音乐播放器实例。进入 RDP 子站时固定导航容器保持可见，仅平滑交叉变换导航内容，个人主页播放器随之卸载。RDP 概览与 Wiki 之间切换时保留项目导航和页脚，仅更新正文，避免导航重复入场闪烁。切换同步更新标题、canonical、Open Graph、QQ 标签和 favicon；分享抓取仍使用 EJS 在构建时注入的原始 HTML。新增页面需登记 `src/pages.ts`、`src/router.ts` 的懒加载组件与 `site.config.ts` 元信息。构建会生成 `project.html`、`projects/rdp-access-auth.html`、`projects/rdp-access-auth/wiki.html` 与 Cloudflare Pages 的 `_redirects`，发布时一并上传；源码仍只有一个 HTML 基础模板。运行 `python3 scripts/check-navigation.py` 验证导航，推荐用 `HOMEPAGE_TEST_URL` 指向构建预览服务。

## RDP Access Auth 官网与 Wiki

- 官网：`https://zxabinbina.cc.cd/projects/rdp-access-auth`
- Wiki：`https://zxabinbina.cc.cd/projects/rdp-access-auth/wiki`
- 下载：`https://zxabinbina.cc.cd/projects/rdp-access-auth/downloads`

主页的 RDP 项目卡片进入官网。项目导航提供自动读取 GitHub Releases 的下载页；Wiki 提供 RPM / DEB 安装、浏览器或终端部署向导、Turnstile 配置、维护与排错；源码入口保留给开发和构建发行版的维护者。

页面与主页统一使用 Vue 3、TypeScript、Vite、原生 CSS 和 Lucide Vue 组件。`src/main.ts` 统一挂载 `src/App.vue`，通过 `src/router.ts` 和 Vue Router 根据 `src/pages.ts` 的路径表按需加载页面。个人主页模板为 `src/HomePage.vue`，官网和 Wiki 模板分别为 `src/rdp/components/OverviewPage.vue` 与 `src/rdp/components/WikiPage.vue`，由 `src/rdp/App.vue` 组合正文和页脚；项目导航由根 `src/App.vue` 持久挂载。仓库仅保留一份 `index.html` 基础挂载与元信息模板，不在 HTML 中编写页面内容。主页与子站共用 `src/components/ThemeToggle.vue` 和 `src/composables/useTheme.ts`，子站通用样式位于 `src/rdp/style.css`，Wiki 阅读布局位于 `src/rdp/wiki.css`。Wiki 正文维护在 [docs/rdp-access-auth.md](docs/rdp-access-auth.md)，基于 [上游 README](https://github.com/zxaBinbina/rdp-access-auth/blob/main/readme.md) 整理，应随上游部署方式更新。`build/rdpWiki.ts` 使用 `marked` 在构建时将受信任的本地 Markdown 转为章节、内容块和搜索数据，由 Wiki Vue 组件展示，访问页面无需下载解析器。`build/pageTemplates.ts` 在构建时从公共模板自动生成各页面地址的 HTML，可直接访问、刷新并抓取分享元信息。与主页一起发布完整 `dist/` 到现有 Cloudflare Pages 即可，无需新建站点或 DNS 记录。

Wiki 按「开始部署、使用与维护、了解项目」组织内容，提供全文范围的章节搜索、可收起的移动目录、六步安装包部署编号和命令复制。页面中的「交给 Agent 部署」提供可一键复制的 [部署提示词](docs/rdp-agent-deploy.md)，填写主机、认证域名、RDP 地址与隧道 ID 后即可交给具备终端能力的 Agent 使用。提示词要求凭据在服务器终端安全输入，并区分实际验收与待人工验证。

官网首屏提供密码输入与认证成功 / 失败的动画演示，可暂停、重播或切换场景；滚动显现和进入动效遵循系统的减少动态效果偏好。演示仅在本地运行，不提交密码或调用认证接口。

开发服务器启动后，执行 `python3 scripts/check-rdp-pages.py` 检查入口、目录锚点、主题与响应式。动效检查使用 `python3 scripts/check-rdp-motion.py`（默认端口 4174）；两个脚本都可用 `HOMEPAGE_TEST_URL` 指向开发或构建预览地址。分享标签检查使用 `python3 scripts/check-sharing.py`，覆盖主页、官网与 Wiki。Wiki 搜索、复制与移动目录专项检查使用 `python3 scripts/check-rdp-wiki.py`，默认端口 4174，同样支持 `HOMEPAGE_TEST_URL`。

## 本地运行

建议使用 Node.js `22.12+` 与 npm。安装依赖后启动开发服务器：

```bash
npm ci
npm run dev
```

开发地址默认是 `http://127.0.0.1:5173`，实际端口以终端输出为准。

构建与预览：

```bash
npm run build
npm run preview
```

`build` 先执行 Vue / TypeScript 类型检查，再生成 `dist/`；预览地址默认是 `http://127.0.0.1:4173`。

## 修改设计与内容

| 修改内容                             | 主要文件                                                         |
| ------------------------------------ | ---------------------------------------------------------------- |
| 配色、排版、布局、断点与全局动效     | [src/style.css](src/style.css)                                   |
| 区块结构、滚动显现与复制交互         | [src/HomePage.vue](src/HomePage.vue)                             |
| 个人资料、项目名称、描述与链接       | [src/content.ts](src/content.ts)                                 |
| 音乐浮层的位置、宽度与开合           | [src/components/MusicDialog.vue](src/components/MusicDialog.vue) |
| 播放器、歌词与歌单样式               | [src/components/MusicPlayer.vue](src/components/MusicPlayer.vue) |
| 头像、项目图像、服务器景观与分享封面 | [public/images/](public/images/)                                 |
| 站点标题、简介、域名与分享图片配置   | [site.config.ts](site.config.ts)                                 |

修改样式前先阅读 [DESIGN.md](DESIGN.md)，复用现有主题变量和组件语言；协作流程见 [AGENTS.md](AGENTS.md)。设计约定发生变化时同步更新文档。

仅格式化本次修改的文件，例如：

```bash
npx prettier --write README.md AGENTS.md
```

## 验证

样式或组件变更后运行 `npm run build`，并检查深浅主题、桌面与窄屏、键盘操作及减少动态效果模式。常用检查宽度为 `320 / 390 / 768 / 1024 / 1440px`。

仓库提供以下检查脚本，按改动范围选用：

| 命令                                | 作用与前置条件                                                                     |
| ----------------------------------- | ---------------------------------------------------------------------------------- |
| `python3 scripts/check-browser.py`  | 页面、图片、主题、复制与移动布局；先启动开发服务器                                 |
| `python3 scripts/check-music.py`    | 构建产物中的音乐交互与布局；先构建，脚本自行启动临时歌词服务，需要外网访问真实音频 |
| `node scripts/check-lyrics.mjs`     | 歌词解析、翻译合并与歌词接口检查                                                   |
| `node scripts/check-music-sync.mjs` | 使用模拟接口验证歌单同步及失败处理                                                 |
| `python3 scripts/check-sharing.py`  | 检查构建产物中的分享元信息；先构建，断言基于本站默认标题与域名                     |

两个浏览器脚本需要 Python 的 `playwright` 包和可用的 Chrome / Chromium，默认浏览器路径是 `/usr/bin/google-chrome`，可通过 `HOMEPAGE_BROWSER` 指定其他路径。页面检查默认连接 `http://127.0.0.1:5173`，可通过 `HOMEPAGE_TEST_URL` 修改。生成的截图保存在被 Git 忽略的 `artifacts/` 中。

纯文档修改检查 Markdown 格式与链接即可，不需要启动浏览器或重新构建。

## 音乐与部署

歌单使用本地快照；需要更新时运行 `npm run sync:music`。播放与歌词依赖网易云服务，无法播放的歌曲会显示提示及官方入口。详细行为、同步工作流和验证说明见 [docs/music.md](docs/music.md)。

Cloudflare Pages 使用仓库根目录、构建命令 `npm run build`、输出目录 `dist`。歌词接口还需要部署根目录的 `functions/`；Git 集成可以同时部署静态站点与函数。仅上传静态产物不会包含歌词接口，具体步骤见音乐文档。

站点分享配置和 `SITE_URL` 用法见 [docs/sharing.md](docs/sharing.md)。

构建自动生成搜索引擎使用的 `sitemap.xml`、`robots.txt`、页面 JSON-LD 结构化数据及 `noindex` 错误页；保持原有 Vue 正文加载与动画。部署后可向搜索引擎站长平台提交 `/sitemap.xml`。运行 `python3 scripts/check-seo.py` 检查构建输出，收录说明见 [搜索引擎收录](docs/sharing.md#搜索引擎收录)。

## 许可证

仓库代码采用 [Apache License 2.0](LICENSE)。

Gaze 官方图标 [gaze.svg](public/images/gaze.svg) 来自 [Gundu Labs 官方仓库](https://github.com/gundulabs/gaze/blob/main/packaging/gui/com.gundulabs.Gaze.svg)，原样保留，版权归 2026 Gundu Labs，遵循 [GPL-3.0-or-later](public/images/gaze.LICENSE.txt)；该第三方素材不适用本站代码许可证。
