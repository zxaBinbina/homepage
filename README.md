# a彬彬a · 个人主页

在代码与方块之间，创造一点不一样。

这是 a彬彬a（zxabinbina）的个人主页，展示开发项目、Minecraft 悠哉世界和日常热爱。使用 Vue 3、TypeScript 与 Vite 构建，以原生 CSS 实现布局、主题和动效，通用图标来自 Lucide。

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
| 区块结构、导航、主题与复制交互       | [src/App.vue](src/App.vue)                                       |
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

## 许可证

仓库采用 [Apache License 2.0](LICENSE)。
