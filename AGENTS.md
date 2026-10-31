# 个人主页协作约定

本文件面向在本仓库工作的协作者与自动化代理，说明**怎么开始、改哪里、怎么验证**。

- 项目的功能与用法见 [README.md](README.md)。
- 视觉与交互的具体参数（色值、字体、布局、组件状态、响应式、动效、可访问性）见 [DESIGN.md](DESIGN.md)。

用户明确提出的新设计要求优先于本文件的默认约定；按任务范围完成修改，不将设计建议当作额外审批条件。本文件只记录**流程与边界**，不复制设计参数；参数以 `DESIGN.md` 和源码为准。

## 开始工作

1. 查看 `git status --short`，识别已有改动，保留与当前任务无关的工作。
2. 阅读 [README.md](README.md) 了解项目入口，阅读 [DESIGN.md](DESIGN.md) 了解视觉规范，再查看涉及的源码。
3. 涉及音乐时阅读 [docs/music.md](docs/music.md)；涉及标题、域名或分享封面时阅读 [docs/sharing.md](docs/sharing.md)；涉及工具来源与许可时阅读 [docs/tools.md](docs/tools.md)。无需为局部样式修改遍历无关服务逻辑。
4. 以当前源码确认实际行为。文档中的「扩展建议」不代表已实现；发现与本次改动有关的差异时同步修正文档。
5. 明确本次改动属于哪一类（页面样式、工具、游戏、子站、错误页、文档），据此选择 [验证方式](#验证方式) 中对应的检查项。

## 设计方向

- 延续「在代码与方块之间，创造一点不一样」的个人表达：开发作品、Minecraft 实景与亲切的中文文案。
- 保持深蓝灰、天蓝强调色、少量暖棕辅助色，以及浅色主题中的灰白层次。
- 保持大标题、正文、辅助标签的层级，使用充足留白、细边框和圆角建立阅读节奏。
- 复用胶囊导航与按钮、项目卡片、编号栏目、图文大卡片等既有设计语言。
- 英文用于简短栏目标签和技术名词，主要内容与操作文案使用自然中文。项目描述先说明用途，技术栈放在标签中。
- 除非任务要求重新设计，否则沿用「首屏 → 关于 → 项目 → 悠哉世界 → 联系」的信息顺序和既有身份素材。

具体色值、字号、间距、圆角、断点与动效时长一律以 [DESIGN.md](DESIGN.md) 为准，本文件不重复列出。

## 文件职责与修改边界

### 主要文件

| 文件或目录                                                                     | 适合修改的内容                                     |
| ------------------------------------------------------------------------------ | -------------------------------------------------- |
| [src/style.css](src/style.css)                                                 | 全局主题变量、页面排版、通用组件、响应式和动效     |
| [src/HomePage.vue](src/HomePage.vue)                                           | 个人主页结构、滚动显现、复制提示                   |
| [src/components/SiteHeader.vue](src/components/SiteHeader.vue)                 | 主页、目录、工具与游戏共用导航、音乐入口、移动菜单 |
| [src/components/SiteFooter.vue](src/components/SiteFooter.vue)                 | 全站共用页脚：品牌、版权与备案                     |
| [src/components/ThemeToggle.vue](src/components/ThemeToggle.vue)               | 浅色 / 深色切换按钮                                |
| [src/components/ColorPalettePicker.vue](src/components/ColorPalettePicker.vue) | 芙芙蓝 / 胡桃红配色选择弹窗                        |
| [src/components/ProjectCard.vue](src/components/ProjectCard.vue)               | 项目目录卡片结构与视觉                             |
| [src/components/MusicDialog.vue](src/components/MusicDialog.vue)               | 音乐浮层定位、展开宽度及外观                       |
| [src/components/MusicPlayer.vue](src/components/MusicPlayer.vue)               | 播放器、歌词、歌单与局部样式                       |
| [src/components/NeteaseIcon.vue](src/components/NeteaseIcon.vue)               | 网易云 SVG 图标                                    |
| [src/components/AnimatedCursor.vue](src/components/AnimatedCursor.vue)         | 加载区域的跟随鼠标指针动画                         |
| [src/router.ts](src/router.ts)                                                 | 站内无刷新导航、历史滚动恢复、运行时元信息         |
| [src/pages.ts](src/pages.ts)                                                   | 页面路径表，工具路径由工具目录自动派生             |
| [src/content.ts](src/content.ts)                                               | 个人资料、项目文案和链接                           |
| [src/composables/useTheme.ts](src/composables/useTheme.ts)                     | 主题状态：保存选择优先，否则跟随系统               |
| [src/loading/](src/loading/)                                                   | 内联首屏加载样式、等待与失败状态、路由加载事件     |
| [src/composables/usePageLoading.ts](src/composables/usePageLoading.ts)         | 工具与游戏异步正文的等待、失败和卸载清理           |
| [src/utils/lyrics.ts](src/utils/lyrics.ts)                                     | 歌词解析与翻译合并                                 |
| [src/data/music.json](src/data/music.json)                                     | 歌单快照，只有歌单更新任务才改动                   |
| [src/ProjectDirectory.vue](src/ProjectDirectory.vue)                           | 项目目录页：搜索、结果计数与空状态                 |
| [src/games/](src/games/)                                                       | 游戏目录、游戏页面、规则逻辑与游戏文案             |
| [src/tools/](src/tools/)                                                       | 工具目录、工作页、上游工具源码与中文文案           |
| [src/rdp/](src/rdp/)                                                           | RDP 子站页面、样式与 Wiki 阅读布局                 |
| [src/gaze/](src/gaze/)                                                         | Gaze 子站页面、指南内容与摘要                      |
| [src/errors/](src/errors/)                                                     | 错误页组件与状态码文案                             |
| [public/images/](public/images/)                                               | 头像、景观、项目和分享图片                         |
| [public/projects/](public/projects/)                                           | Gaze 安装脚本等子站静态资源                        |
| [public/cursors/](public/cursors/)                                             | 芙芙蓝与胡桃红两套鼠标指针资源                     |
| [public/licenses/](public/licenses/)                                           | 第三方工具的许可证副本                             |
| [index.html](index.html)                                                       | 首次绘制前的主题初始化与 HTML 模板                 |
| [site.config.ts](site.config.ts)                                               | 站点标题、简介、域名及分享配置                     |
| [build/](build/)                                                               | 构建期模板生成：页面 HTML、Wiki 内容、工具资源     |
| [functions/api/](functions/api/)                                               | Cloudflare Pages 函数：歌词服务与棋类经验库        |
| [docs/](docs/)                                                                 | 专题文档：音乐、分享、工具、RDP                    |
| [third_party/](third_party/)                                                   | 上游工具清单、许可证与源码快照                     |

### 通用约定

站内页面由 `src/main.ts`、`src/App.vue`、`src/router.ts` 与 `src/pages.ts` 使用 Vue Router 统一挂载和选择；页面内容只在 `.vue` 中维护。仅保留根目录 `index.html` 基础模板，`build/pageTemplates.ts` 自动生成各地址的 HTML 与分享标签，不要新增重复的页面 HTML 入口。共享导航由 `src/App.vue` 挂载，主页、项目目录、工具与游戏页面切换时保留播放器实例；导航逻辑修改后运行 `python3 scripts/check-navigation.py`，建议连接构建预览服务器。主题按钮与状态分别维护在 `src/components/ThemeToggle.vue` 和 `src/composables/useTheme.ts`，全站共用。

保持 Vue 3、TypeScript、原生 CSS 和现有图标体系。局部样式工作优先用已有工具完成；确有必要引入依赖时，说明用途并保持锁文件一致。

不要直接编辑 `dist/`、`node_modules/`、`*.tsbuildinfo` 或测试生成的截图来实现修改。样式调整不需要刷新 `src/data/music.json`；只有任务涉及歌单更新时才运行同步。格式化仅覆盖本次修改的文件。

### 站内路由

`src/App.vue` 通过 `RouterView` 展示页面，主页和目录共用持久挂载的 `SiteHeader.vue`。`src/router.ts` 处理同源已注册页面的普通点击、历史记录与滚动恢复，保留原生链接和新标签页操作。跨页导航后将焦点移到正文，锚点定位继续预留 `110px`；前进 / 后退优先恢复原阅读位置。RDP 概览与 Wiki 切换时复用 `src/rdp/App.vue`，保留导航与页脚，只重新挂载正文；导航不重复播放入场动画。正文切换后重新观察滚动显现元素，目录监听和认证演示随正文挂载、卸载而初始化或清理。页面切换同步更新标题、分享元信息、favicon 和 `rdp-site` 正文样式标记。非根页面使用不带末尾斜线的路径；构建生成同名 `.html` 供无扩展名地址访问，并生成旧地址的 301 重定向。开发与构建预览服务采用相同的地址规范。

### 网页工具

工具目录为 `/tool`，工具地址为 `/tools/*`。名称、分类、搜索词和路径由 `src/tools/catalog.ts` 汇总，其中 jaywcjlove/tools 的条目维护在 `src/tools/jaytools/catalog.ts`；异步组件登记在 `src/tools/components.ts`。页面路径、分享标签与站点地图从工具目录派生，无需逐项编辑 `src/pages.ts`。

工具源码分两处：

- `src/tools/freemium/`：Freemium（MIT）迁入的全部上游工具源码。
- `src/tools/jaytools/`：jaywcjlove/tools（MIT）补充工具的 Vue 实现与本地资源。

共享样式在 `src/style.css`（`.freemium-workbench` 与 `.jay-*` 范围），Freemium 组件的专用样式随组件保留。来源、版本、许可证与使用限制见 [docs/tools.md](docs/tools.md)、[Freemium 来源说明](third_party/freemium/README.md) 与 [Web Tools 来源说明](third_party/jaywcjlove-tools/README.md)。升级时核对完整上游清单，更新固定版本、源码归档、校验值与逐项去重映射，保留原始许可证。更新 jaytools 依赖后运行 `node scripts/update-jaytools-notices.mjs`，并核对依赖声明、补充许可证与 ExifReader 对应源码。

工具计算仅在浏览器内处理输入，不上传、不持久保存；项目徽章的引用代码在本地生成，只有主动打开远程徽章链接时才向对应服务发送项目名或徽章文字。保留计算任务的取消、过期结果隔离与卸载清理。PDF.js 的字体、CMap、WASM 与附带许可证由 `build/toolAssets.ts` 在开发和构建时提供本地资源；新增工具无需应用后端，浏览器 Web Worker 不改变 Cloudflare Pages 部署方式。

变更清单或转换规则运行 `node scripts/check-tools.mjs`，该入口已包含 `check-jaytools.mjs`，无需重复执行；归档校验需要系统提供 `tar`。交互或布局变更运行 `python3 scripts/check-tools-browser.py`，涉及 jaytools 时再运行 `python3 scripts/check-jaytools-browser.py`，检查真实文件、图片与 ZIP 导出、取消、主题、响应式和动效。后者还需要 Python Pillow（`PIL`），截图与下载结果位于 `artifacts/jaytools/`。

### 小游戏

游戏目录为 `/game`，游戏地址为 `/games/*`。名称与说明维护在 `src/games/catalog.ts`，游戏组件及纯规则逻辑位于 `src/games/`，样式在 `src/style.css`。

游戏状态仅在页面内保留。通用外壳由 `src/games/GamePage.vue` 提供教程、结算与网页全屏；`GameGuide.vue`、`GameFullscreenButton.vue`、`GameResult.vue` 供各游戏复用；`useGameMotion.ts` 统一处理动画完成、取消及减少动态效果，`useSolitaireDrag.ts` 管理指针手势，`useGameFit.ts` 计算全屏缩放，`SolitaireCelebration.vue` 管理庆祝绘制与清理。

各游戏的组件与纯规则逻辑成对维护，新增游戏时沿用同样的拆分：

| 游戏       | 组件                                   | 规则逻辑         |
| ---------- | -------------------------------------- | ---------------- |
| 2048       | `NumberGame.vue`                       | `twenty48.ts`    |
| 扫雷       | `MinesweeperGame.vue`                  | `minesweeper.ts` |
| 纸牌接龙   | `SolitaireGame.vue`、`PlayingCard.vue` | `solitaire.ts`   |
| 俄罗斯方块 | `TetrisGame.vue`                       | `tetris.ts`      |
| 数独       | `SudokuGame.vue`                       | `sudoku.ts`      |
| 中国象棋   | `BoardGame.vue`                        | `xiangqi.ts`     |
| 五子棋     | `BoardGame.vue`                        | `gomoku.ts`      |
| 贪吃蛇     | `SnakeGame.vue`                        | `snake.ts`       |
| 消灭星星   | `PopstarGame.vue`                      | `popstar.ts`     |
| 华容道     | `HuarongdaoGame.vue`                   | `huarongdao.ts`  |
| 跳一跳     | `JumpGame.vue`                         | `jump.ts`        |
| 国际象棋   | `ChessGame.vue`、`ChessPiece.vue`      | `chess.ts`       |
| 围棋       | `GoGame.vue`                           | `go.ts`          |
| 欢乐斗地主 | `DoudizhuGame.vue`                     | `doudizhu.ts`    |
| 军旗       | `JunqiGame.vue`                        | `junqi.ts`       |

电脑对手统一复用 `useComputer.ts` 与内联 Worker。游戏样式集中在 `src/style.css` 的 `.game-*`、`.games-*`、`.number-*`、`.mine-*`、`.solitaire-*` 等范围。

更改规则运行 `node scripts/check-games.mjs`；交互或布局修改后运行 `python3 scripts/check-games-browser.py`；动效或拖拽修改还需在开发服务器运行 `python3 scripts/check-games-motion.py`，验证输入锁、取消、手机长按与减少动态效果。游戏导航沿用共享播放器与主题；不要为方向键操作注册影响全站的监听。

网页全屏入口和模态容器由 `src/games/GamePage.vue` 与 `src/games/GameFullscreenButton.vue` 维护；修改后执行 `python3 scripts/check-games-fullscreen.py`，检查原有游戏状态保留、退出与焦点恢复、手机布局和模态区域内拖拽。

### RDP 子站

RDP 子站的 Vue 页面组件与样式位于 `src/rdp/`，部署正文位于 [docs/rdp-access-auth.md](docs/rdp-access-auth.md)，构建转换位于 [build/rdpWiki.ts](build/rdpWiki.ts)。子站修改后运行 `python3 scripts/check-rdp-pages.py`。Wiki 样式维护在 `src/rdp/wiki.css`，部署提示词维护在 [docs/rdp-agent-deploy.md](docs/rdp-agent-deploy.md)；修改 Wiki 搜索、目录或复制交互时执行 `python3 scripts/check-rdp-wiki.py`，动效改动执行 `python3 scripts/check-rdp-motion.py`。

子站组件：官网 `src/rdp/components/OverviewPage.vue`、Wiki `src/rdp/components/WikiPage.vue`、下载 `src/rdp/components/DownloadsPage.vue`，由 `src/rdp/App.vue` 组合正文与页脚；认证演示在 `src/rdp/components/AuthDemo.vue`，Wiki 代码块在 `src/rdp/components/WikiCodeBlock.vue`。子站导航与页脚分别在 `ProjectHeader.vue`、`ProjectFooter.vue`。

### Gaze 子站

Gaze 页面位于 `src/gaze/`，指南正文位于 `src/gaze/content/guide/`，摘要维护在 `src/gaze/catalog.ts`，安装脚本位于 `public/projects/gaze/install.sh`。更新发行版时需同步官网消息、两份指南与摘要，并运行 `python3 scripts/check-gaze-installer.py` 验证架构匹配、菜单选择与校验失败路径。

### 错误页

错误页位于 `src/errors/`，状态码、文案和路径统一维护在 [src/errors/catalog.ts](src/errors/catalog.ts)，页面组件为 [src/errors/ErrorPage.vue](src/errors/ErrorPage.vue)，样式在 `src/style.css`。保留未知路由的原地址、共享导航与 `noindex`，错误页不进入站点地图。修改后构建并在预览服务器运行 `python3 scripts/check-errors.py`，同时检查分享元信息和 SEO；脚本在本地模拟深层地址的 404 响应，线上 HTTP 状态仍由部署平台决定。

## CSS 与主题

- 通用文字、表面、边框、链接和交互状态使用 `--text`、`--muted`、`--bg`、`--panel`、`--blue`、`--border` 等语义变量。
- 新增主题变量时考虑深浅两套取值，放在现有 `:root` 与 `[data-theme='light']` 中。
- 保留主标题渐变、按配色变化的主按钮、图片遮罩及项目图标变体的用途差异；不要机械地把所有固定颜色替换为同一个变量。
- 页面与通用样式放在 `src/style.css`；音乐组件细节保留在对应组件的 scoped 样式内。
- 修改前检查已有选择器和后续媒体查询覆盖，优先修改对应规则，避免通过不断追加覆盖或滥用 `!important` 解决问题。
- 保留现有字体回退栈。不要为了匹配单张截图而默认引入外部字体请求。
- 保持主题初始化与运行时切换一致：保存选择优先，否则跟随系统；避免首次绘制闪烁到错误主题。

## 布局与响应式

复用 `.shell` 主容器与既有间距。新增内容先适配现有断点，再按实际布局需要补充规则。现有断点与各断点下的具体行为见 [DESIGN.md](DESIGN.md#7-响应式规则)。

- 支持 `320px` 最小宽度，检查长项目名、邮箱、歌名和标签是否造成横向溢出。
- 不通过全局隐藏横向溢出来掩盖超宽组件；修正产生溢出的宽度、换行、网格或定位规则。
- 图片使用适合用途的 `object-fit` 和焦点位置，检查窄屏裁切后是否仍能识别主体。
- 保留图片尺寸信息、首屏响应式图片与优先加载策略，页面下方图片继续按需延迟加载。
- 仅像素风项目图标使用 `image-rendering: pixelated`；景观、封面和网页预览保持正常渲染。

## 交互、动效与可访问性

- 跳转使用链接，状态切换使用按钮。项目卡片是整卡链接，内部不嵌套交互控件。
- 保留「跳至内容」、图标按钮可读名称、可见焦点、导航当前项及状态提示。交互不能只依赖颜色或悬停。
- 关闭的移动菜单不能继续接收焦点，退场期间保留 `inert`；Escape 和菜单选项的关闭行为应继续可用。
- 固定导航与锚点滚动保持协调，当前顶部滚动预留为 `110px`。
- 动效优先使用透明度、位移与轻微缩放，复用 `--motion-ease`。滚动显现的 `translate` 与悬停的 `transform` 不应互相覆盖。
- 保留 `prefers-reduced-motion` 分支，减少动态效果时内容直接可见；不要将正文可见性绑定到动画成功执行。
- 新增控件以至少 `44 × 44px` 的触摸区域为目标；既有紧凑按钮的改动需结合导航空间判断。
- 保持原生滚动，浮层、歌词和歌单在可用区域内滚动；不要引入滚动劫持。

音乐相关修改还应保留以下体验：首次点击入口前不请求音频或自动播放；关闭浮层不卸载正在播放的实例；歌词状态保持一致高度；桌面侧栏与窄屏覆盖歌单不越出可用视口；加载、失败、空状态和重试入口保持可读、可操作。

## 验证方式

根据改动选择检查，避免为纯文档或简单样式调整添加只复述实现的测试。修复具体行为缺陷时，必要的回归检查应能识别原始问题。

| 改动范围                       | 应完成的检查                                                                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 仅 Markdown 文档               | 对修改的文件运行 Prettier 检查，核对本地链接和命令；无需构建或浏览器测试                                                                         |
| 页面 CSS、模板、前端逻辑或图片 | `npm run build`，检查受影响区域的深浅主题和桌面、窄屏表现                                                                                        |
| 导航、主题、复制或整体布局     | 在开发服务器运行时执行 `python3 scripts/check-browser.py`                                                                                        |
| 首屏与页面加载提示             | 构建后在预览服务器执行 `python3 scripts/check-loading.py`，检查慢速 / 失败资源、连续导航、主题、窄屏和减少动态效果                               |
| 项目目录                       | `python3 scripts/check-project-directory.py`                                                                                                     |
| 工具清单或转换规则             | `node scripts/check-tools.mjs`（已包含 `check-jaytools.mjs`）                                                                                    |
| 工具交互或布局                 | `python3 scripts/check-tools-browser.py`；涉及 jaytools 时另运行 `python3 scripts/check-jaytools-browser.py`                                     |
| 游戏规则                       | `node scripts/check-games.mjs`                                                                                                                   |
| 游戏交互或布局                 | `python3 scripts/check-games-browser.py`                                                                                                         |
| 游戏动效、拖拽与终局           | `python3 scripts/check-games-motion.py`、`python3 scripts/check-games-options-motion.py`                                                         |
| 经典与棋类游戏                 | `python3 scripts/check-games-classics.py`、`python3 scripts/check-games-classics-motion.py`                                                      |
| 国际象棋与围棋                 | `node scripts/check-games-chess-go.mjs`、`python3 scripts/check-games-chess-go.py`、`python3 scripts/check-games-chess-go-motion.py`             |
| 贪吃蛇与消灭星星               | `node scripts/check-games-arcade.mjs`、`python3 scripts/check-games-arcade.py`、`python3 scripts/check-games-arcade-motion.py`                   |
| 华容道与跳一跳                 | `node scripts/check-games-sliding-jump.mjs`、`python3 scripts/check-games-sliding-jump.py`、`python3 scripts/check-games-sliding-jump-motion.py` |
| 网页全屏                       | `python3 scripts/check-games-fullscreen.py`                                                                                                      |
| 延迟加载底色与全屏过渡         | `python3 scripts/check-games-paint.py`                                                                                                           |
| 音乐交互或布局                 | 构建后执行 `python3 scripts/check-music.py`，检查浮层、歌单与状态切换                                                                            |
| 歌词解析或接口                 | `node scripts/check-lyrics.mjs`                                                                                                                  |
| 歌单同步逻辑                   | `node scripts/check-music-sync.mjs`                                                                                                              |
| 错误页                         | 构建后执行 `python3 scripts/check-errors.py`，同时检查分享元信息和 SEO                                                                           |
| RDP 页面                       | `python3 scripts/check-rdp-pages.py`                                                                                                             |
| RDP Wiki 搜索、复制与目录      | `python3 scripts/check-rdp-wiki.py`                                                                                                              |
| RDP 动效                       | `python3 scripts/check-rdp-motion.py`                                                                                                            |
| Gaze 安装器                    | `python3 scripts/check-gaze-installer.py`                                                                                                        |
| 分享配置或 HTML 元信息         | 构建后执行 `python3 scripts/check-sharing.py`；如任务改变了默认标题或域名，同步更新相关断言                                                      |
| 搜索引擎收录                   | `python3 scripts/check-seo.py`                                                                                                                   |

浏览器检查需要安装 Python Playwright（`playwright` 包），并提供 Chrome / Chromium。`HOMEPAGE_BROWSER` 指定浏览器路径，默认 `/usr/bin/google-chrome`；页面检查的 `HOMEPAGE_TEST_URL` 默认是 `http://127.0.0.1:5173`，构建预览为 `http://127.0.0.1:4173`，RDP 动效与 Wiki 脚本默认 `http://127.0.0.1:4174`。音乐检查会自行启动临时歌词服务，并访问真实音频，需要网络。截图输出位于 `artifacts/`，按范围命名：`artifacts/game-motion-*.png`、`artifacts/game-options-*.png`、`artifacts/game-classics-*.png`、`artifacts/game-arcade-*.png`、`artifacts/game-new-*.png`、`artifacts/game-fullscreen-*.png`、`artifacts/error-*.png` 等。

布局修改使用 `320 / 390 / 768 / 1024 / 1440px` 检查宽度，并根据变更查看相关断点两侧。自动检查不覆盖所有视觉细节，需观察文字换行、图片焦点、浮层边界及键盘焦点；动效修改还需检查减少动态效果模式。

格式命令示例：

```bash
npx prettier --check README.md AGENTS.md DESIGN.md
```

需要修正格式时，对实际修改的文件使用 `--write`。环境缺少浏览器、依赖或网络导致检查未完成时，准确说明未执行的项目和原因，不将它报告为通过。

## 文档与交付

三份文档各司其职，不要互相复制：

- `README.md` 面向项目读者，介绍功能、玩法、运行方式和部署方式。
- `DESIGN.md` 记录具体设计参数与交互规则，并区分现状和扩展建议。
- `AGENTS.md` 维护协作流程、修改位置和验证要求，避免重复复制整套设计参数。

修改设计约定、使用命令或文件职责时，同步更新对应文档；局部实现调整不必重写无关章节。完成后简要说明改动、验证结果和实际限制。报告浏览器验证时区分本次结果与旧截图；保留用户已有修改，不将无关文件混入本次工作。
