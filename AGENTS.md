# 个人主页样式维护约定

本文件适用于仓库内的页面设计、前端样式及相关文档维护。用户明确提出的新设计要求优先于本文的默认约定；按任务范围完成修改，不将设计建议当作额外审批条件。

## 开始工作

1. 查看 `git status --short`，识别已有改动，保留与当前任务无关的工作。
2. 阅读 [README.md](README.md) 了解项目入口，阅读 [DESIGN.md](DESIGN.md) 了解视觉规范，再查看涉及的源码。
3. 涉及音乐时阅读 [docs/music.md](docs/music.md)；涉及标题、域名或分享封面时阅读 [docs/sharing.md](docs/sharing.md)。无需为局部样式修改遍历无关服务逻辑。
4. 以当前源码确认实际行为。文档中的「扩展建议」不代表已实现；发现与本次改动有关的差异时同步修正文档。

## 设计方向

- 延续「在代码与方块之间，创造一点不一样」的个人表达：开发作品、Minecraft 实景与亲切的中文文案。
- 保持深蓝灰、天蓝强调色、少量暖棕辅助色，以及浅色主题中的灰白层次。完整色值以 `DESIGN.md` 和 `src/style.css` 为准。
- 保持大标题、正文、辅助标签的层级，使用充足留白、细边框和圆角建立阅读节奏。
- 复用胶囊导航与按钮、项目卡片、编号栏目、图文大卡片等既有设计语言。
- 英文用于简短栏目标签和技术名词，主要内容与操作文案使用自然中文。项目描述先说明用途，技术栈放在标签中。
- 除非任务要求重新设计，否则沿用「首屏 → 关于 → 项目 → 悠哉世界 → 联系」的信息顺序和既有身份素材。

## 文件职责与修改边界

| 文件或目录                                                       | 适合修改的内容                                     |
| ---------------------------------------------------------------- | -------------------------------------------------- |
| [src/style.css](src/style.css)                                   | 全局主题变量、页面排版、通用组件、响应式和动效     |
| [src/HomePage.vue](src/HomePage.vue)                             | 个人主页结构、滚动显现、复制提示                   |
| [src/components/SiteHeader.vue](src/components/SiteHeader.vue)   | 主页、目录、工具与游戏共用导航、音乐入口、移动菜单 |
| [src/router.ts](src/router.ts)                                   | 站内无刷新导航、历史滚动恢复、运行时元信息         |
| [src/content.ts](src/content.ts)                                 | 个人资料、项目文案和链接                           |
| [src/games/](src/games/)                                         | 游戏目录、游戏页面、规则逻辑与游戏文案             |
| [src/tools/](src/tools/)                                         | 工具目录、工作页、转换逻辑与工具文案               |
| [src/components/MusicDialog.vue](src/components/MusicDialog.vue) | 音乐浮层定位、展开宽度及外观                       |
| [src/components/MusicPlayer.vue](src/components/MusicPlayer.vue) | 播放器、歌词、歌单与局部样式                       |
| [src/components/NeteaseIcon.vue](src/components/NeteaseIcon.vue) | 网易云 SVG 图标                                    |
| [public/images/](public/images/)                                 | 头像、景观、项目和分享图片                         |
| [index.html](index.html)                                         | 首次绘制前的主题初始化与 HTML 模板                 |
| [site.config.ts](site.config.ts)                                 | 站点标题、简介、域名及分享配置                     |

站内页面由 `src/main.ts`、`src/App.vue`、`src/router.ts` 与 `src/pages.ts` 使用 Vue Router 统一挂载和选择；页面内容只在 `.vue` 中维护。仅保留根目录 `index.html` 基础模板，`build/pageTemplates.ts` 自动生成各地址的 HTML 与分享标签，不要新增重复的页面 HTML 入口。共享导航由 `src/App.vue` 挂载，主页、项目目录、工具与游戏页面切换时保留播放器实例；导航逻辑修改后运行 `python3 scripts/check-navigation.py`，建议连接构建预览服务器。主题按钮与状态分别维护在 [src/components/ThemeToggle.vue](src/components/ThemeToggle.vue) 和 [src/composables/useTheme.ts](src/composables/useTheme.ts)，全站共用。

工具目录为 `/tool`，工具地址为 `/tools/*`。名称、分类和说明维护在 `src/tools/catalog.ts`，转换逻辑位于 `src/tools/transform.ts`，样式在 `src/style.css`。输入仅在本地处理，不上传、不持久保存；变更转换规则运行 `node scripts/check-tools.mjs`，交互或布局变更运行 `python3 scripts/check-tools-browser.py`。

游戏目录为 `/game`，游戏地址为 `/games/*`。名称与说明维护在 `src/games/catalog.ts`，游戏组件及纯规则逻辑位于 `src/games/`，样式在 `src/style.css`。游戏状态仅在页面内保留；更改规则运行 `node scripts/check-games.mjs`，交互或布局修改后运行 `python3 scripts/check-games-browser.py`；动效或拖拽修改还需在开发服务器运行 `python3 scripts/check-games-motion.py`，验证输入锁、取消、手机长按与减少动态效果。游戏导航沿用共享播放器与主题；不要为方向键操作注册影响全站的监听。

RDP 子站的 Vue 页面组件与样式位于 `src/rdp/`，部署正文位于 [docs/rdp-access-auth.md](docs/rdp-access-auth.md)，构建转换位于 [build/rdpWiki.ts](build/rdpWiki.ts)。子站修改后运行 `python3 scripts/check-rdp-pages.py`。Wiki 样式维护在 `src/rdp/wiki.css`，部署提示词维护在 `docs/rdp-agent-deploy.md`；修改 Wiki 搜索、目录或复制交互时执行 `python3 scripts/check-rdp-wiki.py`。

保持 Vue 3、TypeScript、原生 CSS 和现有图标体系。局部样式工作优先用已有工具完成；确有必要引入依赖时，说明用途并保持锁文件一致。

不要直接编辑 `dist/`、`node_modules/`、`*.tsbuildinfo` 或测试生成的截图来实现修改。`src/data/music.json` 是歌单快照，只有任务涉及歌单更新时才运行同步；样式调整不需要刷新它。格式化仅覆盖本次修改的文件。

## CSS 与主题

- 通用文字、表面、边框、链接和交互状态使用 `--text`、`--muted`、`--bg`、`--panel`、`--blue`、`--border` 等语义变量。
- 新增主题变量时考虑深浅两套取值，放在现有 `:root` 与 `[data-theme='light']` 中。
- 保留主标题渐变、固定蓝色主按钮、图片遮罩及项目图标变体的用途差异；不要机械地把所有固定颜色替换为同一个变量。
- 页面与通用样式放在 `src/style.css`；音乐组件细节保留在对应组件的 scoped 样式内。
- 修改前检查已有选择器和后续媒体查询覆盖，优先修改对应规则，避免通过不断追加覆盖或滥用 `!important` 解决问题。
- 保留现有字体回退栈。不要为了匹配单张截图而默认引入外部字体请求。
- 保持主题初始化与运行时切换一致：保存选择优先，否则跟随系统；避免首次绘制闪烁到错误主题。

## 布局与响应式

复用 `.shell` 主容器与既有间距。新增内容先适配现有断点，再按实际布局需要补充规则。

| 断点               | 需要保留的行为                             |
| ------------------ | ------------------------------------------ |
| `≥ 1500px`         | 首屏留白与主图高度扩展，正文保持最大宽度   |
| `≤ 1050px`         | 收紧外边距、列距与卡片布局                 |
| `≤ 760px`          | 移动菜单、关于区单列；项目仍为两列         |
| `< 720px` 可用视口 | 音乐歌单切换为浮层内覆盖式侧栏             |
| `≤ 480px`          | 项目单列，服务器操作纵排，精简导航工具     |
| `≤ 380px`          | 隐藏导航联系按钮，保留移动菜单中的联系入口 |

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

| 改动范围                       | 应完成的检查                                                                                |
| ------------------------------ | ------------------------------------------------------------------------------------------- |
| 仅 Markdown 文档               | 对修改的文件运行 Prettier 检查，核对本地链接和命令；无需构建或浏览器测试                    |
| 页面 CSS、模板、前端逻辑或图片 | `npm run build`，检查受影响区域的深浅主题和桌面、窄屏表现                                   |
| 导航、主题、复制或整体布局     | 在开发服务器运行时执行 `python3 scripts/check-browser.py`                                   |
| 音乐交互或布局                 | 构建后执行 `python3 scripts/check-music.py`，检查浮层、歌单与状态切换                       |
| 歌词解析或接口                 | `node scripts/check-lyrics.mjs`                                                             |
| 歌单同步逻辑                   | `node scripts/check-music-sync.mjs`                                                         |
| 分享配置或 HTML 元信息         | 构建后执行 `python3 scripts/check-sharing.py`；如任务改变了默认标题或域名，同步更新相关断言 |

浏览器检查需要安装 Python Playwright，并提供 Chrome / Chromium。`HOMEPAGE_BROWSER` 指定浏览器路径；页面检查的 `HOMEPAGE_TEST_URL` 默认是 `http://127.0.0.1:5173`。音乐检查会自行启动临时歌词服务，并访问真实音频，需要网络。截图输出位于 `artifacts/`。

布局修改使用 `320 / 390 / 768 / 1024 / 1440px` 检查宽度，并根据变更查看相关断点两侧。自动检查不覆盖所有视觉细节，需观察文字换行、图片焦点、浮层边界及键盘焦点；动效修改还需检查减少动态效果模式。

格式命令示例：

```bash
npx prettier --check README.md AGENTS.md DESIGN.md
```

需要修正格式时，对实际修改的文件使用 `--write`。环境缺少浏览器、依赖或网络导致检查未完成时，准确说明未执行的项目和原因，不将它报告为通过。

## 文档与交付

- `README.md` 面向项目读者，介绍视觉特色、运行方式和维护入口。
- `DESIGN.md` 记录具体设计参数与交互规则，并区分现状和扩展建议。
- `AGENTS.md` 维护协作流程、修改位置和验证要求，避免重复复制整套设计参数。
- 修改设计约定、使用命令或文件职责时，同步更新对应文档；局部实现调整不必重写无关章节。
- 完成后简要说明改动、验证结果和实际限制。报告浏览器验证时区分本次结果与旧截图；保留用户已有修改，不将无关文件混入本次工作。
