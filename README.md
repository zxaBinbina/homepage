# a彬彬a · 个人主页

Vue 3 + TypeScript + Vite 构建的个人主页。以 WinIsland 的滚动展示、玻璃导航与留白为设计参考，结合 Dao_Homepage 的个人介绍与交互思路，独立实现页面。

## 本地运行

需要 Node.js 22.12+（或 20.19+）。

```bash
npm ci
npm run dev
```

打开终端提示的本地地址，默认 `http://127.0.0.1:5173`。

```bash
npm run build     # TypeScript 检查并输出 dist/
npm run preview   # 预览生产产物
npm run format    # 格式化源码
```

## 内容与设计

- 个人介绍、四个开发项目、悠哉世界 Minecraft 服务器、GitHub / Bilibili / 邮件入口。
- 固定玻璃导航、滚动入场、项目悬停效果，支持系统的减少动态效果偏好。
- 深色为默认主题，支持浅色切换和本地记忆。
- 响应式移动菜单，支持 Escape 关闭、键盘焦点与跳至内容链接。
- 服务器地址一键复制，浏览器不允许复制时提供手动复制提示。
- 页脚包含新窗口打开的 [萌ICP备20264016号](https://icp.gov.moe/?keyword=20264016)。
- 所有图片本地托管，首页主图压缩为 WebP 并提供小屏版本；运行时无需请求 GitHub API 或第三方字体。

| 配色   | RGB           | 用途       |
| ------ | ------------- | ---------- |
| 深夜蓝 | 20, 21, 33    | 页面背景   |
| 靛蓝   | 45, 60, 129   | 渐变与氛围 |
| 亮蓝   | 78, 164, 239  | 主色与交互 |
| 雾白   | 218, 226, 237 | 正文与按钮 |
| 暖棕   | 147, 117, 98  | 辅助点缀   |

## 修改位置

- `src/content.ts`：昵称、社交链接、邮箱、服务器地址、项目内容与仓库链接。
- `src/App.vue`：页面结构、其他展示文案及页脚备案链接。
- `src/style.css`：颜色变量、布局、响应式样式和动效。
- `public/images/`：头像、用户提供的 Minecraft 截图，以及悠哉世界项目的景观与 Logo。
- `index.html`：网站标题、描述与基础分享元信息。

项目介绍基于对应本地项目的 README；服务器内容依据悠哉世界官网资料。服务器状态与版本不显示硬编码的实时数据，详细游玩信息链接至官网。

## 部署

运行 `npm run build` 后，将 `dist/` 发布到静态托管平台即可，例如 Cloudflare Pages、GitHub Pages 或 Nginx。构建命令为 `npm run build`，输出目录为 `dist`。

使用相对资源路径和页内锚点，可部署到域名根目录或子目录，无需 SPA 路由回退。没有预设个人域名、站点统计或后端服务。确定正式域名后，可在 `index.html` 增加 canonical、绝对地址的 `og:url` / `og:image`，并按需要提供 sitemap。

## 浏览器检查

`scripts/check-browser.py` 使用 Python Playwright 与 Google Chrome，默认检查 `http://127.0.0.1:5173`。启动网站后运行：

```bash
python -m pip install playwright
python scripts/check-browser.py
```

通过 `HOMEPAGE_BROWSER` 指定 Chrome 可执行文件，通过 `HOMEPAGE_TEST_URL` 指定预览地址。测试涵盖图片加载、备案链接、复制成功与失败、主题记忆、移动菜单、锚点位置，以及 320 / 390 / 768 / 1024 / 1440px 下的横向溢出。截图保存在已被 Git 忽略的 `artifacts/` 目录。
