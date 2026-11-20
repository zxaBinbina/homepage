# SPTL 项目子页

入口为 `/projects/SPTL`，与 Gaze、RDP 子页共用 Vue 路由、站点主题和页脚样式。
页面包含项目介绍、可交互的任务栏歌词演示、源码下载、四步安装、设置分组及常见问题。
演示不播放音频，离开视口或切到后台时暂停推进；减少动态效果时默认暂停，仍可手动操作。

页面不展示作者邮箱、官网地址或许可证说明，也没有返回项目目录、个人主页的入口。
这些项目资料由 SPTL 仓库的 Plasma 5/6 元数据提供给 KDE 小组件信息界面。
站内目录保留 SPTL 卡片供访客进入，首页仍为原来的四个精选项目。

## 维护位置

| 文件                           | 用途                                       |
| ------------------------------ | ------------------------------------------ |
| `src/sptl/HomePage.vue`        | 页面正文、命令复制、FAQ 与滚动显现         |
| `src/sptl/TaskbarDemo.vue`     | 示例歌词、布局切换、播放暂停与换句         |
| `src/sptl/SptlHeader.vue`      | 品牌、安装入口、共享主题面板及 GitHub 链接 |
| `src/sptl/content.ts`          | 版本、下载位置及功能文案                   |
| `src/sptl/style.css`           | 使用站点语义变量与 token 的局部样式        |
| `public/images/sptl.png`       | 项目所有者提供的透明 PNG 图标              |
| `public/images/sptl-share.png` | 1200 × 630 分享封面                        |
| `public/projects/SPTL/`        | 包含完整项目源码的下载归档                 |

路由、分享标签、favicon 与站点地图分别由 `src/pages.ts`、`src/router.ts`、
`site.config.ts` 和公共构建模板维护，不添加独立 HTML 入口。
SPTL 的共享页脚关闭品牌链接，其他页面保持原有行为。

## 更新源码下载

源码包是本站的静态资源，部署与运行不需要相邻仓库或 GitHub API。
更新下载内容时使用以下命令，参数指向 SPTL 源码仓库：

```sh
python3 scripts/package-sptl.py ../SplayerPlasmaTaskbarLyrics
```

脚本只打包 Git 跟踪的项目源码、文档、测试和构建材料，排除本地配置、缓存及构建产物，
保留完整 LICENSE。版本取自 Plasma 元数据；更新版本后同步 `src/sptl/content.ts`。
归档内的顶层目录为 `SPTL-版本号`，安装命令与该目录一致。

运行开发服务器后，可重新生成分享封面：

```sh
python3 scripts/render-sptl-share.py
```

该脚本复用网页的主题色和歌词演示面板，不生成真实桌面截图。

## 验证

```sh
npm run build
python3 scripts/check-sptl.py
python3 scripts/check-project-directory.py
python3 scripts/check-navigation.py
python3 scripts/check-sharing.py
python3 scripts/check-seo.py
```

浏览器检查的 `HOMEPAGE_TEST_URL` 默认是 `http://127.0.0.1:5173`，也可指向构建预览。
SPTL 检查覆盖实际导航、元信息、演示暂停及布局切换、剪贴板、真实 ZIP 下载与独立构建、
FAQ 键盘操作，以及四套主题在 320 / 390 / 768 / 1024 / 1440px 下的布局。
截图保存在 `artifacts/sptl-*.png`，发布网站仍需部署完整 `dist/`。
