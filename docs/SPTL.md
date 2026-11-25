# SPTL 项目子页

入口为 `/projects/SPTL`，与 Gaze、RDP 子页共用 Vue 路由、站点主题和页脚。
首屏使用本机小组件的连续录屏视频，六项功能卡片直接展示对应设置下的实际视频帧。
视频不含音轨，使用原生视频播放器暂停并保留当前画面；离开视口或切到后台时暂停，减少动态效果时默认暂停。
页面不单独展示作者邮箱、官网地址或许可证，也没有返回个人主页或目录的入口。
这些资料由 SPTL 元数据提供给 KDE 小组件信息界面。目录保留 SPTL 卡片，首页仍为四个精选项目。

## 一键安装与更新

在 KDE 桌面终端运行，无需 sudo：

```sh
curl -fsSL 'https://zxabinbina.cc.cd/projects/SPTL/install.sh' | sh
```

每次读取 SPTL 仓库的最新公开正式 Release。API 不可用时跟随同一仓库的
`releases/latest` 跳转，按正式版标签选择源码归档与对应 `SHA256SUMS-版本`。
校验 SHA-256、安全解压并核对源码版本后，执行该 Release 的 `tools/install.py`。
退出时清理临时文件，不依赖相邻仓库，也不固定安装某个版本。

需要 Python 3.10+、curl、SPlayer 插件 API 5+、Plasma 5.27 / Qt 5.15 或 Plasma 6 / Qt 6，
以及 systemd 用户会话。收藏需要 gdbus 和 SPlayer Linux 托盘入口。
脚本生成插件文件、安装对应小组件并启动辅助服务。用户随后在 SPlayer 插件管理中导入
`~/.local/share/sptl/zxaBinbina.sptl.js`，允许 `network`、`control`、`api` 权限。
更新后重新导入同 ID 插件；使用自定义 XDG 目录时，以脚本输出为准。

再次执行同一命令即可更新。上游安装器保留共享设置；脚本读取已有用户服务，保留
自定义 SPlayer 启动命令与配置路径。已有小组件且 Plasma 用户服务正在运行时自动重载
面板以清除旧 QML 缓存，应用窗口保留；否则更新后注销再登录。

也可先下载官网脚本，再指定选项：

```sh
sh install.sh --dry-run
sh install.sh --plasma 6 --splayer-command '/path/to/SPlayer-Next.AppImage'
sh install.sh --splayer-config '/path/to/settings.json'
sh install.sh --no-reload-plasma
sh install.sh --help
```

`--dry-run` 只读取版本与下载地址，不执行安装。`--reload-plasma` 显式要求重载；
`--no-reload-plasma` 关闭更新时的自动重载。KDE Store 提供单独小组件，仍需辅助服务与插件。

## 官网自动获取版本

进入页面时请求 `/api/projects/SPTL/release`，同步版本、发布日期、发行说明与资产链接。
接口优先读取 GitHub API，限流时读取最新发行页及资产列表，只接受 SPTL 仓库的正式版和下载地址。
成功响应浏览器缓存 60 秒、CDN 缓存 300 秒；失败响应不缓存。页面可手动刷新，离开时取消请求。
失败时保留已核对的 v1.2.1 或上次成功同步的版本，并明确说明尚未取得最新信息。
若新版缺少源码资产，辅助下载入口指向发行页，不把旧源码标为最新版。

Cloudflare Pages 函数与 Vite 开发 / 预览服务共用处理器。部署保留 Pages 函数及
`public/_routes.json` 的接口规则；单独托管 `dist/` 时安装脚本可用，页面版本接口不可用。
网站发布后，新 Release 无需修改网站代码即可更新版本与下载链接。

## 维护位置

| 文件                                         | 用途                                     |
| -------------------------------------------- | ---------------------------------------- |
| `src/sptl/HomePage.vue`                      | 正文、复制、实拍、下载、FAQ 与滚动显现   |
| `src/sptl/useSptlRelease.ts` / `release.ts`  | 最新版本请求、取消与类型                 |
| `src/sptl/content.ts`                        | 已核对版本、备用源码、功能文案与市场链接 |
| `src/sptl/DesktopRecording.vue`              | 首屏连续视频、暂停、视口与动态效果偏好   |
| `src/sptl/ShotImage.vue` / `screenshots.ts`  | 实拍展示、原图链接与特性对应关系         |
| `src/sptl/SptlHeader.vue` / `style.css`      | 品牌、主题入口与局部样式                 |
| `server/sptlRelease.ts`                      | 最新 GitHub Release、限流回退与响应缓存  |
| `functions/api/projects/SPTL/release.ts`     | Cloudflare Pages 接口                    |
| `public/projects/SPTL/install.sh`            | 一键安装 / 更新脚本                      |
| `public/projects/SPTL/sptl-1.2.1-source.zip` | 本站已核对的独立源码包                   |
| `public/images/sptl/`                        | 连续录屏、视频帧、任务栏与弹窗照片       |
| `public/images/sptl.png` / `sptl-share.png`  | 项目图标与 1200 × 630 分享封面           |

素材经项目所有者授权从本机录制。`public/images/sptl/dark/` 与 `public/images/sptl/light/`
分别在 2026-11-25 的 KDE 深色、浅色主题下拍摄；系统明暗由项目所有者切换。
普通模式歌曲《经过》，保留单曲循环，从第一句歌词（26.646 秒）开始连续录制。
通过系统屏幕共享与 PipeWire/GStreamer 获取真实视频流，H.264、30 帧/秒、无音轨；
录屏完成后裁剪任务栏与歌词弹窗，静态图从真实视频帧提取，不使用连拍图片拼接。
每套首屏任务栏与弹窗视频来自同一次录制，支持暂停当前画面、循环与自动暂停。
首屏视频、封面帧、11 张特性图片及原图链接跟随网站实际明暗模式，芙芙蓝和胡桃红使用相同的两套素材。
自动模式随系统明暗切换；单独改配色不重载视频。切换素材保留播放进度及用户选择的播放 / 暂停状态。

用于展示的 `*-compact.webp` 裁去任务栏空白或重复的弹窗标题，靠右封面和普通控制保留左右两块真实画面。
`taskbar-compact.mp4` 同样移除中间空白，保留连续录制的时间轴与 30 帧/秒，不使用静态帧拼接动画。
完整任务栏、弹窗和 `taskbar.mp4` 均保留；图片链接打开对应的完整原图。所有展示图在窄屏完整等比缩小，不需横滑。
特性卡片按各自高度紧接排列，主题照片单独显示，首屏与特性区之间保留总计约 64px 的间距。

「喜欢的样子，自己调」紧接「小小一块，刚好够用」的特性介绍，之后是发行信息和安装步骤。
其四组说明各配一张原生配置界面图，文件为两套中的 `settings-lyrics.webp`、
`settings-layout.webp`、`settings-theme.webp` 与 `settings-interaction.webp`，同样跟随页面深浅模式。
图片加载本机已安装的 `ConfigGeneral.qml`，在 Qt 窗口中读取运行中辅助服务的真实配置；
截图窗口使用 Breeze 深浅配色，包含原有控件、条件禁用状态和字号预览。拍摄后核对原配置与播放状态。
完整窗口及采集记录保存在忽略的 `artifacts/sptl-settings/`。设置说明先于图片显示，桌面两列，1024px 及以下单列；点击图片可打开清晰原图。

普通模式快捷操作与之前的私人 FM 实拍并列：普通模式显示上一首，私人 FM 显示不喜欢。
两套素材包括双行 / 单行、封面左右位置、圆角 / 圆形、普通播放控制、播放列表及单曲循环菜单。
浅色原生音量提示从本次连续录屏提取，深色音量提示沿用先前 KDE 深色下的实拍。
私人 FM 两套控制局部图裁剪自此前实际拍摄的深浅弹窗，原图保留为各套的 `fm-popup.webp`；不改动当前普通播放歌曲来重建这些对照。

只公开裁剪后的组件视频和图片，完整录屏暂存在忽略的 `artifacts/sptl-dark/`、`artifacts/sptl-light/`，不公开。
拍摄结束后恢复临时外观和音量，保留当前歌曲、普通模式及单曲循环，并按项目所有者要求暂停播放。
后续拍摄也应先备份设置，并在退出时恢复。页面只使用静态素材文件，不调用本机播放器接口。
路由、分享标签、favicon 与站点地图由公共配置和构建模板维护，不新增独立 HTML 入口。
SPTL 共享页脚关闭品牌链接。

## 备用源码与分享封面

本站源码包保留完整 LICENSE、项目源码、文档、测试和构建材料，可独立构建。
更新已核对快照时运行：

```sh
python3 scripts/package-sptl.py ../SplayerPlasmaTaskbarLyrics
```

版本取自 Plasma 元数据，随后同步 `src/sptl/content.ts` 的快照版本与路径。
自动安装与版本接口始终读取 GitHub Release，不依赖快照。分享封面复用网页主题与真实任务栏照片，
可在开发服务器运行时生成：

```sh
python3 scripts/render-sptl-share.py
```

## 验证

```sh
sh -n public/projects/SPTL/install.sh
python3 scripts/check-sptl-installer.py
node scripts/check-sptl-release.mjs
npm run build
HOMEPAGE_TEST_URL=http://127.0.0.1:4183 python3 scripts/check-sptl.py
HOMEPAGE_TEST_URL=http://127.0.0.1:4183 python3 scripts/check-project-directory.py
HOMEPAGE_TEST_URL=http://127.0.0.1:4183 python3 scripts/check-navigation.py
python3 scripts/check-sharing.py
python3 scripts/check-seo.py
```

浏览器检查需要 Playwright 和 ffprobe，并运行预览服务器，例如 `npm run preview -- --port 4183`。
安装测试使用真实源码、临时 XDG 路径和模拟桌面服务，验证安装、更新、配置保留、管道执行、
校验失败、不安全归档、版本不一致及安装失败，不改动本机 SPTL 安装。
页面检查覆盖两套连续视频的播放 / 暂停与当前帧冻结、减少动态效果和离开视口、两套各 11 张特性图片、
两种配色下的深浅切换、自动跟随系统、配色切换不重载视频、暂停 / 播放状态与进度保留、
四组原生设置图片及其深浅切换、
图片 / 任务栏视频无需横滑、卡片间距和首屏到特性区的留白、
动态新版本、失败状态、复制、脚本 / ZIP 下载与独立构建、FAQ 键盘操作，
以及四套主题在 320 / 390 / 768 / 1024 / 1440px 下的布局。截图输出到 `artifacts/`。
