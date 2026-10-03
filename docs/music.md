# 网易云音乐播放器

点击导航栏主题按钮右侧的网易云音乐图标打开播放器气泡。图标使用提供的 SVG 路径，通过 `currentColor` 适配深浅主题。播放时悬停图标显示当前歌曲名与歌手，暂停后恢复“网易云音乐”。

气泡默认宽 380px，顶部尖角指向音乐按钮，不遮罩页面。歌单在右侧展开为独立侧栏，入场从左向右渐显；窄屏上从右侧滑出覆盖式侧栏，避免横向溢出。桌面点击歌单按钮收起列表，窄屏点击侧栏左侧遮罩收起。布局随窗口大小和可用视口调整。

`src/components/MusicDialog.vue` 管理气泡，`src/components/MusicPlayer.vue` 管理播放。收起后继续播放，再次打开保留歌曲、进度与音量；支持 Escape、点击外部、再次点击音乐按钮和关闭按钮收起。

默认选中 HOYO-MiX 的《飞鼠进行曲 The Parade of Flying Squirrels》（`2613484729`），歌单为 `8410450907`。

页面初始不请求音频、不自动播放。访客点击后开始播放，支持上一首、下一首、曲终续播、进度、音量、静音与歌单搜索。列表和切歌顺序完全遵循网易云原顺序，默认歌曲只影响初始选中项，不调整列表位置，也不修改网易云歌单。

歌曲名称和列表项右侧按网易云 `fee === 1` 显示 VIP 标记，付费专辑或仅下载付费不混同为 VIP。标记随歌单同步更新，不表示所有 VIP 歌曲支持外链播放。

## 更新歌单

`.github/workflows/sync-music.yml` 配置 GitHub Actions 在北京时间每月 **1 日、16 日 10:30** 自动同步（UTC cron：`30 2 1,16 * *`）。这是按每月两次计算的“半个月”，并非严格间隔 360 小时；GitHub 的定时任务可能排队延迟。

将工作流和播放器相关文件一并推送到 GitHub 默认分支后生效。同步完成后会安装依赖、构建网站并检查歌词函数，全部通过才将 `src/data/music.json` 提交回默认分支。Cloudflare Pages 需启用此仓库默认分支的 Git 自动部署，收到新提交后发布最新歌单及歌词允许列表；无需配置额外 Token 或部署 Hook。

可在 GitHub 仓库 **Actions → Sync NetEase playlist → Run workflow** 立即同步。工作流使用仓库自带的 `GITHUB_TOKEN`，申请 `contents: write` 权限；仓库策略须允许 Actions 写入默认分支。如果分支保护要求所有修改必须经 PR，此直接提交工作流会失败，需按仓库策略调整。定时工作流在公开仓库连续 60 天无活动时可能被 GitHub 停用，可在 Actions 中重新启用。

网易云接口失败、歌单或歌曲详情不完整、默认曲目缺失以及构建失败时，不会提交更新，线上继续使用旧歌单。可在 Actions 查看失败日志并重新运行。

也可在本地手动同步并构建：

```bash
npm run sync:music
npm run build
```

`scripts/sync-music.mjs` 从网易云公开接口同步歌曲名称、歌手、封面、时长、VIP 信息与顺序至 `src/data/music.json`。构建使用本地快照，不依赖构建时网络可用。访客刷新网页不会请求歌单同步；“我的网易云歌单”链接可查看网易云最新歌单。同步失败时保留原快照。

音频始终由网易云官方公开外链提供，不下载或托管音乐文件，也不使用第三方代理。默认专辑封面保存在 `public/images/music-cover.webp`；其他专辑封面使用网易云 HTTPS 地址。平台无法提供外链播放的歌曲会显示提示及对应的官方歌曲链接。

HTML 中的 `upgrade-insecure-requests` 策略将网易云外链的 HTTP CDN 重定向升级为 HTTPS。真实浏览器已验证默认曲目在 HTTPS 页面上播放、暂停与跳转进度。

## 验证

先运行 `npm run build`，再在装有 Playwright 的 Python 环境中运行 `python scripts/check-music.py`。默认使用 `/usr/bin/google-chrome`，可通过 `HOMEPAGE_BROWSER` 修改。

脚本会临时启动本地歌词服务，首先验证网易云真实音频和纯音乐状态，然后用短音频和原创测试歌词验证切歌、续播、歌词同步、歌词定位、VIP、搜索、音量、弹窗关闭后的播放与手机布局。截图写入 `artifacts/`。

`node scripts/check-lyrics.mjs` 检查 LRC 时间戳、重复时间、偏移、翻译合并及 Pages Function 的打包和失败处理。

`node scripts/check-music-sync.mjs` 使用隔离的临时目录和模拟接口，检查同步顺序、VIP 标记，以及接口失败、缺曲和不完整歌单时旧快照不会被覆盖。

## 歌词与 Cloudflare Pages

播放器打开时请求同源 `/api/music/lyrics?id=歌曲ID`，由 `functions/api/music/lyrics.ts` 调用网易云公开歌词接口。只允许读取当前歌单中的歌曲，提供超时、失败重试和缓存；歌词不写入静态文件。开发和预览服务器通过 Vite 中间件使用相同处理逻辑。

支持滚动歌词、播放高亮、点击歌词跳转和已有翻译。纯音乐显示“纯音乐，请欣赏”，没有歌词或请求失败时分别显示空状态或重试入口。各歌词状态保持相同高度，避免切换时窗口跳动。切歌会取消旧请求，避免错配；关闭弹窗不再请求歌词。

Cloudflare Pages 的项目根目录保持仓库根目录，构建命令 `npm run build`，输出目录 `dist`。Git 集成部署会同时编译根目录 `functions/`。`public/_routes.json` 将函数执行限制在歌词接口。

如使用命令行直接上传，应从仓库根目录执行 `npx wrangler pages deploy dist --project-name 你的项目名`，让 Wrangler 同时发现 `functions/`。仅在控制台拖拽上传 `dist` 不会部署歌词函数。无需网易云账号、Token 或额外密钥。

主页与项目目录页的音乐入口由 `src/components/SiteHeader.vue` 共用，导航在 `src/App.vue` 中持久挂载，浮层仍由 `MusicDialog.vue` 管理。页面内收起浮层不会卸载播放器；主页与目录之间无刷新切换时保留歌曲、进度和播放状态。进入使用独立导航的 RDP 子站或离开本站时，个人主页播放器会卸载。
