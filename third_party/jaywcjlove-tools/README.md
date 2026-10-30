# Web Tools 源码来源

- 仓库：[jaywcjlove/tools](https://github.com/jaywcjlove/tools)
- 固定提交：[`40d5879e86ce4ad53153ac0003d42de96796232b`](https://github.com/jaywcjlove/tools/tree/40d5879e86ce4ad53153ac0003d42de96796232b)
- 许可证：MIT，Copyright (c) 2022 小弟调调™。原文随站点发布于 [jaywcjlove-tools.txt](../../public/licenses/jaywcjlove-tools.txt)。
- 原始源码：[upstream-source.tar.gz](upstream-source.tar.gz)，直接保存 GitHub 下载归档，未改写归档内容。
- 完整清单与校验值：[upstream.json](upstream.json)，包括归档、路由文件和每个原始工具入口的 SHA-256。

以该提交的 `website/src/Router.tsx` 为准，共 **31 个实际工具页面**，其中 **15 个新增、16 个重复**，每个页面都有明确去向。`website/src/menus.tsx` 中的第三方网站推荐链接不含这些网站的源码，未将其计为可迁入工具。

本站原有 Freemium 的 41 个工具全部保留，合并后共 56 个。去重按功能进行：例如 `json-yaml` 对应现有两个转换方向，`markdown-to-html` 和 `simple-markdown-editor` 都由现有 Markdown 预览及 HTML 导出覆盖。逐项映射见清单中的 `existingTools`。

## Vue 适配

迁入位置为 `src/tools/jaytools/`，目录见 `catalog.ts`。上游 React 组件改写为 Vue，复用本站 Freemium 编辑器、选项控件、复制下载和全站主题。没有接入上游导航、React、CodeMirror 或收藏存储。

- JSON/INI、JSON/XML、TOML、金额转换保留上游解析库与转换流程；XML 增加属性和文本标记，并拒绝 DTD；金额以字符串传入，避免先转换为 Number 导致精度丢失。
- 简繁转换保留上游字表、例外字与一对多时取首项的行为；规范汉字表保留完整 8105 字，增加分级、搜索、分页与复制。
- 拼音改用浏览器字典 `pinyin-pro`，避免旧 `pinyin` 的 Node 分词依赖，保留声调、无声调、首字母和注音预览。
- HTML 转 Markdown 保留 unified → rehype → remark → GFM 管线；不做上游只用于网页装饰的标题锚点、语法着色或视频组件注入。
- SVG 使用 SVGO 的浏览器构建并更新到当前插件 API；保留 viewBox、标题、描述与 ID，默认 3 位小数，支持 1–8 位精度。与 JavaScript 混淆一样，在可取消的 Worker 中运行。
- JavaScript 混淆保留上游五种选项集合；可用 JSON 覆盖全部选项，支持 Source Map 下载。使用不附带云服务 CLI 依赖的 `javascript-obfuscator@4.1.1` 浏览器构建；转换不执行代码。
- 徽章保留全部七份 GitHub、npm、Docker 模板数据及自定义模式，修复 Badgen 经典域名拼写、Docker 命名空间和 URL 转义。引用代码在本地生成，远程徽章仅通过访客主动打开链接加载。
- CSS 缓动保留全部 24 项预设、四类效果、控制点编辑与 CSS 输出；改用 SVG 指针事件并补上键盘、取消与减少动态效果支持。
- 代码图片按上游所用 [code-image](https://github.com/jaywcjlove/code-image) 的编辑与导出流程适配，使用 `highlight.js` 和 `html-to-image`，支持 PNG/JPEG/SVG、配色、留白、字号、行号与窗口标题；[code-image 许可证](../../public/licenses/code-image.txt) 一并保留。
- PDF 使用 PDF.js 本地 Worker、字体、CMap 和 WASM；修复上游批量导出漏掉最后一页的流程，改为全部页面 ZIP 下载。新增密码、错误提示、任务取消、资源释放和内存限制。
- EXIF 保留 ExifReader 解析、MakerNote 清理、字段查看与 JSON 输出，增加失败状态与过期任务隔离。

没有新增应用后端，继续使用 Cloudflare Pages；浏览器 Web Worker 只处理本地计算，与 Cloudflare Worker 部署无关。

## 依赖许可证

[依赖声明](../../public/licenses/jaytools-dependencies.txt) 包含新增依赖及其递归依赖的版本、来源和许可证。通过 `node scripts/update-jaytools-notices.mjs` 从已安装的锁定版本重新生成。npm 未附带的许可文本保存在 `dependency-licenses/`；nzh 仅在 package.json 声明 BSD-2-Clause，补充文件明确区分原声明与标准许可证模板。

ExifReader 使用 MPL-2.0，库源码未修改，并在 [/licenses/exifreader-source.tar.gz](../../public/licenses/exifreader-source.tar.gz) 随站点提供对应源码。PDF.js 使用 Apache-2.0，其字体、CMap、WASM 自带许可证由 `build/toolAssets.ts` 一同发布到 `/tool-assets/pdfjs/`。

## 验证

`node scripts/check-tools.mjs` 会调用 `check-jaytools.mjs`，核对归档、31 个原始路由、15 个新增页面、16 个去重映射及转换边界。`scripts/check-tools-browser.py` 遍历全部 56 个工具；`scripts/check-jaytools-browser.py` 专项检查真实 PDF/EXIF 文件、图片与 ZIP 导出、取消、主题、响应式和切换动画。
