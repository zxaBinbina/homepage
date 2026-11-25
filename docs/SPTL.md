# SPTL 项目子页

入口为 `/projects/SPTL`，与 Gaze、RDP 子页共用 Vue 路由、站点主题和页脚。
首屏使用本机小组件的实拍 GIF，六项功能卡片直接展示对应设置下的实际截图。
录屏不含音频；可手动暂停，离开视口或切到后台时切换为静态帧，减少动态效果时默认暂停。
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
| `src/sptl/DesktopRecording.vue`              | 首屏实拍动图、暂停、视口与动态效果偏好   |
| `src/sptl/ShotImage.vue` / `screenshots.ts`  | 实拍展示、原图链接与特性对应关系         |
| `src/sptl/SptlHeader.vue` / `style.css`      | 品牌、主题入口与局部样式                 |
| `server/sptlRelease.ts`                      | 最新 GitHub Release、限流回退与响应缓存  |
| `functions/api/projects/SPTL/release.ts`     | Cloudflare Pages 接口                    |
| `public/projects/SPTL/install.sh`            | 一键安装 / 更新脚本                      |
| `public/projects/SPTL/sptl-1.2.1-source.zip` | 本站已核对的独立源码包                   |
| `public/images/sptl/`                        | 实拍 GIF、静态帧、任务栏与弹窗照片       |
| `public/images/sptl.png` / `sptl-share.png`  | 项目图标与 1200 × 630 分享封面           |

素材于 2026-11-25 经项目所有者授权从本机录制，曲目为《Light in Abyss (Full ver)》
与《Walk Thru Fire》。首屏 GIF 为 28 个实际桌面帧，保留录制时的歌词推进和封面旋转。
功能照片包括单行 / 双行、暂停高亮、悬停播放控制、原生音量提示、封面位置与形状、
播放列表、手动深浅主题。每张图的说明对应拍摄时实际应用的设置，点击可查看原图。

只公开裁剪后的任务栏、歌词弹窗与音量提示，不公开完整桌面截图。对歌词和主题的局部
裁剪另保留原始弹窗链接。原始帧、拍摄记录与原设置备份位于被忽略的 `artifacts/sptl-capture/`。
拍摄结束后恢复全部原设置及音量，播放器暂停。后续拍摄也应先备份设置，并在退出时恢复。
页面使用这些静态文件，不调用本机歌词服务或播放器接口。
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

浏览器检查需运行预览服务器，例如 `npm run preview -- --port 4183`。
安装测试使用真实源码、临时 XDG 路径和模拟桌面服务，验证安装、更新、配置保留、管道执行、
校验失败、不安全归档、版本不一致及安装失败，不改动本机 SPTL 安装。
页面检查覆盖实拍动图的播放 / 暂停、减少动态效果与离开视口、十张特性图片、
动态新版本、失败状态、复制、脚本 / ZIP 下载与独立构建、FAQ 键盘操作，
以及四套主题在 320 / 390 / 768 / 1024 / 1440px 下的布局。截图输出到 `artifacts/`。
