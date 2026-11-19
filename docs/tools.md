# 网页工具

本站收录 **105 个工具**：[Freemium](https://github.com/incentius-foss/freemium)（MIT）的全部 41 个工具、[jaywcjlove/tools](https://github.com/jaywcjlove/tools)（MIT）的 15 个新增工具、[XCPDF V7.3](https://github.com/wallechfox/offline-pdf-tools/tree/98424086829730f3dd7313a8871bbbbb49e80cd8)（固定 MIT 发布版）的全部 43 项功能，另有 PDF 转办公格式与 Markdown 四个工具，以及本站自制的 Codex 对话加密字段清理与私人网页浏览器。Web Tools 固定版本共有 31 个实际工具页面，其余 16 个与本站重复，已逐项映射到已有功能。入口 `/tool`，工具均使用站内页面与延迟加载组件，本地工具源码随本站构建；私人网页浏览器使用独立中转与隔离浏览环境。

## 工具清单

工具目录按名称升序排列，使用 `zh-CN` 本地化排序（中文按拼音，英文不区分大小写，数字按数值比较）。分类和搜索结果保持相同顺序，卡片编号对应完整排序中的位置。分类使用统一的分段胶囊和滑动选中块，窄屏下分三列显示，支持方向键、Home / End 切换。

| 工具              | 地址                         | 用途                                        |
| ----------------- | ---------------------------- | ------------------------------------------- |
| JSON 格式化       | `/tools/json-formatter`      | 格式化、校验、排序与压缩 JSON 数据。        |
| HTML 格式化       | `/tools/html-beautify`       | 整理或压缩 HTML 和 ERB 模板。               |
| CSS 格式化        | `/tools/css-beautify`        | 格式化或压缩 CSS、SCSS 和 LESS 样式。       |
| JavaScript 格式化 | `/tools/js-beautify`         | 整理 JavaScript 代码的缩进与布局。          |
| XML 格式化        | `/tools/xml-beautify`        | 校验、格式化和压缩 XML 文档。               |
| SQL 格式化        | `/tools/sql-formatter`       | 按数据库方言整理 SQL 查询语句。             |
| 文本排序与去重    | `/tools/line-sort`           | 按行排序、去重、去空行与整理空白。          |
| YAML 转 JSON      | `/tools/yaml-to-json`        | 将 YAML 文档转换为 JSON 数据。              |
| JSON 转 YAML      | `/tools/json-to-yaml`        | 将 JSON 数据转换为易读的 YAML。             |
| JSON 转 CSV       | `/tools/json-to-csv`         | 将 JSON 数据转换为 CSV 表格。               |
| CSV 转 JSON       | `/tools/csv-to-json`         | 读取 CSV 表格并转换为 JSON 数据。           |
| Excel 转 JSON     | `/tools/excel-to-json`       | 本地读取工作簿，导出单张或全部工作表。      |
| 进制转换          | `/tools/number-base`         | 二进制、八进制、十进制及任意进制整数互转。  |
| 文本大小写转换    | `/tools/text-case`           | 转换大小写、驼峰、蛇形及其他命名格式。      |
| HTML 转 JSX       | `/tools/html-to-jsx`         | 将 HTML 标记转换为 React JSX。              |
| PHP 与 JSON       | `/tools/php-json`            | 转换 PHP 数组、序列化数据和 JSON。          |
| SVG 转 CSS        | `/tools/svg-to-css`          | 将 SVG 嵌入 CSS 背景或生成 Data URI。       |
| cURL 转代码       | `/tools/curl-to-code`        | 将 cURL 命令转换为多种语言的请求代码。      |
| JSON 转类型定义   | `/tools/json-to-code`        | 从 JSON 生成 TypeScript、Go、Swift 等类型。 |
| 十六进制与文本    | `/tools/hex-ascii`           | 在十六进制字节与 UTF-8 文本之间转换。       |
| Unix 时间转换     | `/tools/unix-time`           | 时间戳与日期互转，查看不同时区的时间。      |
| JWT 调试          | `/tools/jwt-debugger`        | 解析令牌内容，校验 HMAC 签名。              |
| 正则表达式测试    | `/tools/regex-tester`        | 高亮匹配、查看捕获组并测试替换。            |
| HTML 预览         | `/tools/html-preview`        | 在隔离区域预览 HTML，切换设备宽度。         |
| 文本差异对比      | `/tools/text-diff`           | 按行、词或字符比较两段文本的差异。          |
| 字符串检查        | `/tools/string-inspector`    | 统计字数、字节、字符与 Unicode 码点。       |
| Markdown 预览     | `/tools/markdown-preview`    | 实时预览 Markdown，复制或下载 HTML。        |
| Cron 表达式解析   | `/tools/cron-parser`         | 解读定时规则，查看指定时区的执行时间。      |
| 颜色转换          | `/tools/color-converter`     | 在多种颜色格式间转换，查看颜色与对比度。    |
| URL 解析          | `/tools/url-parser`          | 拆解网址的组成部分，编辑查询参数。          |
| UUID 与 ULID      | `/tools/uuid`                | 批量生成 UUID v4、v7 和 ULID，解读标识。    |
| 占位文本生成      | `/tools/lorem-ipsum`         | 生成段落、句子或单词，用于排版测试。        |
| 二维码工具        | `/tools/qr-code`             | 生成二维码，或从本地图片识别内容。          |
| 哈希生成          | `/tools/hash-generator`      | 计算文本或文件摘要，支持 HMAC。             |
| 随机字符串        | `/tools/random-string`       | 安全生成随机密码、字符和自定义字母表。      |
| Base64 文本       | `/tools/base64`              | 支持 UTF-8 与 URL 安全模式的编解码。        |
| 图片与 Base64     | `/tools/image-base64`        | 图片与 Base64 互转，导出网页嵌入代码。      |
| URL 编解码        | `/tools/url-encode`          | 编码或还原 URL 与查询参数。                 |
| HTML 实体转换     | `/tools/html-entity`         | 转义 HTML 特殊字符或还原实体。              |
| 反斜杠转义        | `/tools/backslash-escape`    | 按编程语言格式转义与还原字符串。            |
| 证书解析与校验    | `/tools/certificate-decoder` | 检查 X.509 证书链、主机名及私钥匹配。       |

## Web Tools 新增清单

| 工具             | 地址                                    | 用途                                                |
| ---------------- | --------------------------------------- | --------------------------------------------------- |
| HTML 转 Markdown | `/tools/html-to-markdown`               | 将网页标记转换为 Markdown，保留表格、链接和代码块。 |
| TOML 转 JSON     | `/tools/toml-to-json`                   | 解析 TOML 配置文件，转换为结构清晰的 JSON。         |
| JSON 与 XML      | `/tools/json-xml`                       | 在 JSON 与 XML 之间转换，保留属性与文本节点。       |
| JSON 与 INI      | `/tools/json-ini`                       | 转换 JSON 对象与 INI 配置，整理配置文件。           |
| 汉字转拼音       | `/tools/chinese-pinyin-conversion`      | 为中文注音，输出带声调拼音、无声调拼音或首字母。    |
| 简繁体转换       | `/tools/simplified-traditional-chinese` | 逐字转换简体与繁体中文，保留其他文字和标点。        |
| 通用规范汉字表   | `/tools/standard-chinese-characters`    | 查询 8105 个规范汉字、拼音与序号，按级别浏览。      |
| 人民币大写       | `/tools/amount-in-rmb`                  | 将数字转换为中文大小写与人民币金额大写。            |
| 代码转图片       | `/tools/code-to-image`                  | 把代码制作成可分享的图片，调整配色、字号和留白。    |
| PDF 转图片       | `/tools/pdf-to-img`                     | 本地预览 PDF，导出单页图片或打包下载全部页面。      |
| 图片 EXIF 查看   | `/tools/exif-viewer`                    | 读取照片中的拍摄参数、尺寸及位置等元数据。          |
| SVG 优化         | `/tools/svg-optimizer`                  | 精简 SVG 标记与路径，调整精度并比较文件大小。       |
| CSS 缓动曲线     | `/tools/css-easing-animation`           | 调节贝塞尔曲线，预览动画并复制 CSS。                |
| 项目徽章生成     | `/tools/generate-github-badges`         | 生成 GitHub、npm、Docker 和自定义徽章的引用代码。   |
| JavaScript 混淆  | `/tools/js-obfuscator`                  | 转换变量与代码结构，生成可下载的混淆代码。          |

## 信创 PDF 工具箱

完整接入用户提供的《信创PDF工具箱V7.3-43项功能-单文件版.html》，作者为相声的技术备忘录（wallechfox）。本站保留已有 PDF 转图片工具，并为 XCPDF 的 43 项功能分别提供站内地址；目录按「PDF 页面」「PDF 转换」「PDF 编辑」筛选，也可搜索「PDF」「信创」或「XCPDF」。

| 工具                   | 地址                            |
| ---------------------- | ------------------------------- |
| PDF 常规合并           | `/tools/pdf-merge`              |
| PDF 交替合并           | `/tools/pdf-merge-alternating`  |
| PDF 常规拆分           | `/tools/pdf-split`              |
| PDF 按书签拆分         | `/tools/pdf-split-bookmarks`    |
| PDF 按书签拆成独立文件 | `/tools/pdf-explode-bookmarks`  |
| PDF 页面重排           | `/tools/pdf-reorder`            |
| PDF 页面倒序           | `/tools/pdf-reverse`            |
| PDF 补齐空白页         | `/tools/pdf-pad-even`           |
| PDF 删除页面           | `/tools/pdf-delete-pages`       |
| PDF 自动删除空白页     | `/tools/pdf-remove-blank-pages` |
| PDF 页面批量旋转       | `/tools/pdf-rotate`             |
| PDF 页面逐页旋转       | `/tools/pdf-rotate-pages`       |
| PDF 页面拼版           | `/tools/pdf-impose`             |
| PDF 小册子排版         | `/tools/pdf-booklet`            |
| PDF 小册子拆分         | `/tools/pdf-split-booklet`      |
| PDF 统一页面大小       | `/tools/pdf-resize`             |
| PDF 拆分对开页         | `/tools/pdf-split-spread`       |
| PDF 倾斜校正           | `/tools/pdf-deskew`             |
| PDF 裁剪白边           | `/tools/pdf-crop-margins`       |
| 生成空白 PDF           | `/tools/pdf-blank`              |
| PDF 转图片             | `/tools/pdf-to-images`          |
| 图片转 PDF             | `/tools/pdf-images-to-pdf`      |
| PDF 提取文本           | `/tools/pdf-extract-text`       |
| PDF 扁平化             | `/tools/pdf-flatten`            |
| PDF 提取图片           | `/tools/pdf-extract-images`     |
| PDF 页面滤镜           | `/tools/pdf-filters`            |
| PDF 工程蓝图           | `/tools/pdf-blueprint`          |
| PDF 模拟扫描件         | `/tools/pdf-scan-effect`        |
| PDF 添加页码           | `/tools/pdf-page-numbers`       |
| PDF Bates 编页         | `/tools/pdf-bates`              |
| PDF 文字水印           | `/tools/pdf-text-watermark`     |
| PDF 图片水印           | `/tools/pdf-image-watermark`    |
| PDF 添加图章           | `/tools/pdf-stamp`              |
| PDF 扇形骑缝章         | `/tools/pdf-seam-stamp`         |
| PDF 批注               | `/tools/pdf-annotate`           |
| PDF 涂黑               | `/tools/pdf-redact`             |
| PDF 文档信息           | `/tools/pdf-metadata`           |
| PDF CA 签章查看        | `/tools/pdf-signature-info`     |
| PDF 添加与编辑书签     | `/tools/pdf-edit-bookmarks`     |
| PDF 删除书签           | `/tools/pdf-remove-bookmarks`   |
| PDF 压缩               | `/tools/pdf-compress`           |
| PDF 解密               | `/tools/pdf-decrypt`            |
| PDF 加密               | `/tools/pdf-encrypt`            |

提供的 HTML 与上游提交 `98424086829730f3dd7313a8871bbbbb49e80cd8`（2026-11-05）的文件 SHA-256 完全一致，当时仓库许可证为 MIT。上游于 2026-11-06 改为非开源许可；本站归档和标注仅对应已获 MIT 许可的固定版本，不将当前主分支标为 MIT。原文件、43 项映射与许可证保存在 [third_party/xcpdf/](../third_party/xcpdf/README.md)，发布许可见 [MIT 原文](../public/licenses/xcpdf.txt)及[第三方声明](../public/licenses/xcpdf-dependencies.txt)。

操作区由 `src/tools/xcpdf/XcpdfTool.vue` 管理；`build/xcpdf.ts` 从未改动的上游归档生成本地运行资源，保留 PDF 处理引擎，通过独立沙盒适配本站主题。界面颜色映射维护在 `build/xcpdfUiTheme.ts`，构建样式与运行时动态列表、提示、结果共用，文档画布和导出色板保持实际颜色。每项工具只显示对应操作面板，共用本站导航、播放器、标题和页脚；取消清空与来源许可集中在操作区下方。原工具箱首页、收藏入口和独立导航不在页面中显示。运行库仅在打开相应工具后读取，不从 CDN 加载，也不新增后端或 Service Worker。

所有文档、密码和结果只保留在运行中的沙盒，无法读取本站浏览器存储；CSP 阻止网络连接与表单提交，文件不上传。取消并清空、切换工具或离开页面会丢弃整个运行环境及工作线程，旧任务不能继续下载。单个文件上限 30 MB；大型文件和高分辨率导出仍受浏览器内存限制。

文本提取只读取现有文字层，不包含 OCR；扫描件没有文字层时无法直接提取文字。CA 签章查看展示签名与证书字段，不校验证书信任、撤销状态或法律效力。解密需要正确的打开密码；添加水印、批注、压缩、涂黑等修改可能使原数字签名失效。涂黑导出会栅格化页面，使用前后应核对实际遮盖范围。部分扫描件操作会将页面转换为图片，文字可选性、书签和页面尺寸以对应工具说明及实际导出为准。

## PDF 转办公格式与 Markdown

新增四个工具，分类为「PDF 转换」，可搜索 Word、Excel、PowerPoint、Markdown 或办公格式。

| 工具              | 地址                       | 输出与模式                                                      |
| ----------------- | -------------------------- | --------------------------------------------------------------- |
| PDF 转 Word       | `/tools/pdf-to-word`       | `.docx`，可编辑文字、标题、列表和表格；也可选择整页图片。       |
| PDF 转 Excel      | `/tools/pdf-to-excel`      | `.xlsx`，仅表格或全部文字；每页一个工作表或合并工作表。         |
| PDF 转 PowerPoint | `/tools/pdf-to-powerpoint` | `.pptx`，默认每页一张图片；也可选择可编辑文字。                 |
| PDF 转 Markdown   | `/tools/pdf-to-markdown`   | `.md`，标题、文字列表与表格；可保留页间注释，预览、复制和下载。 |

共享组件位于 `src/tools/pdfconvert/PdfConvertTool.vue`，PDF.js 解析与渲染使用本站字体、CMap 和 WASM；生成器按输出格式加载。文字分析迁入 [opendocsg/pdf2md 0.4.0](https://github.com/opendocsg/pdf2md/tree/5d3a505928bd3216a303c669457e61696d7fd6ed)（MIT），Word 与 PowerPoint 生成分别使用 docx 9.16.0、PptxGenJS 4.0.1（MIT），Excel 复用现有 SheetJS。固定源码、SHA-256、适配说明见 [来源归档](../third_party/pdf-convert/README.md)，发布声明见 [pdf-convert.txt](../public/licenses/pdf-convert.txt)。依赖更新后运行 `node scripts/update-pdf-convert-notices.mjs`。

文件上限 30 MB；可输入开始页与结束页，结束页留空时转换至末页。文字模式每次最多 300 页，Word / PowerPoint 图片模式最多 100 页。图片宽度可选 1200 / 1800 像素，单页最多 600 万像素、总图片最多 60 MB、最终结果最多 80 MB；任务总超时两分钟。取消并清空会清除文件、密码和结果，修改选项或离开页面会终止旧任务。文件生成在可终止的 Web Worker 中进行，不上传文件，不保存输入或密码。

文字模式只读取已有文字层，不含 OCR，图片、矢量图形和背景不导出。没有文字层时显示说明；部分页面缺少文字层时，结果提示对应页数。扫描件可选 Word / PowerPoint 的整页图片模式，图中的文字不可编辑。Word 可编辑模式重排内容，保留标题、文字列表和表格，不承诺原版面；图片模式将页面图像放在 Word 页内。PowerPoint 文字模式只保留文字与大致位置，以替代字体和固定文字颜色排版；图片模式按原页比例适配首张幻灯片尺寸。

表格按文字间距和列起点识别，至少需要三行且列数、起点相近；不读取边框结构。两行表格、右对齐列、复杂多栏、合并单元格、跨页及单元格内换行可能无法准确识别，需核对输出，或使用 Excel「全部文字」。全部文字按识别到的段落置于首列；重复页眉与页脚保留。PDF 将项目符号绘制为图形时无法恢复文字列表。默认把 Excel 单元格保留为文字；开启数字识别后只转换普通小数及三位分组数字，保留前导零、日期、长编号和超过 15 位的数值，公式样式文字也作为普通文本写入。

Markdown 预览最多 5 万字符；复制和下载包含全部结果。转换不会执行提取的 Markdown。下载后应核对内容及排版；数字签名、书签、批注、嵌入文件与原 PDF 的交互结构不迁移。

## 私人网页浏览器

地址 `/tools/web-browser`，分类「检查调试」。主页只提供中文操作界面，中转后端独立维护在同级 `../bin-api/`。`api.zxabinbina.cc.cd` 提供 `/v1/auth/*` 与 `/v1/proxy/*` 模块，`browse.zxabinbina.cc.cd` 承载隔离浏览环境；目标网页不能直接访问主页界面的 DOM。

- 仅支持 Windows / Linux 上的 Chrome 和 Edge，移动设备显示抱歉与返回工具集入口。桌面设备模拟仍可选择手机和平板尺寸，并可修改宽高、旋转、缩放及 User-Agent；无法完整复现其他浏览器内核、操作系统、真实触摸或 DevTools 的全部功能。
- 使用随机访问密码解锁，每次凭据有效期一小时。密码只提交到认证接口，凭据只保存在运行中的页面与浏览器工作线程中，不写入 URL 或浏览器持久存储。退出、到期或离开工具会关闭浏览环境，清理代理源站的 IndexedDB、网站存储和缓存；新会话开始前再次清理。异常关闭、浏览器崩溃等情况下，可能直到下次进入时才完成清理，不能将其视为浏览器原生无痕模式的完整替代。下载到电脑的文件不自动删除。
- 网页、图片、脚本、接口、Cookie、表单与文件上传会通过 Worker 发送至目标网站，属于本站本地计算工具之外的明确例外。后端不建立浏览历史、Cookie 数据库或应用访问日志，不缓存私人页面；平台本身的网络和安全处理不属于应用清理范围。
- 「Bing 简洁搜索」是独立的备用入口，读取 Bing 公开 RSS 结果，供个人非商业阅读。搜索和打开结果继续经过中转，保留原版 Bing 入口；结果数量和排序可能与原版不同。
- 新会话默认进入 Bing 简洁搜索。启动时先在独立导航页清理旧会话，再启动新的浏览服务；卡住时显示具体启动阶段及超时信息，可使用「清理并重建」清空当前浏览数据并重新进入，无需在凭据有效期内重复输入密码。
- 支持普通 HTTP/HTTPS 和 WebSocket 中转，视频采用流式转发与 Range 请求；表单和文件上传在浏览器内最多暂存 32 MiB，下载交由浏览器处理。Bing 搜索、米哈游登录、抖音视频分别需要实测；验证码、目标站限制和跨域机制可能影响兼容性。云原神的 WebRTC 音视频连接无法仅凭普通 HTTP/WebSocket 转发保证可用，设备模拟也不会改变这一限制。
- 浏览器运行库使用 Scramjet 1.1.0（MIT）及其 bare-mux 2.1.9 接口，所有运行资源由浏览子域名本地提供，无外部 CDN 依赖。bare-mux 上游已标记弃用，当前固定版本用于匹配 Scramjet 的已发布接口；升级时应同步验证整个运行库。许可证随 `browse` 的 `/vendor/scramjet/LICENSE.txt`、`/vendor/bare-mux/LICENSE.txt` 发布。

前端实现位于 `src/tools/browser/BrowserTool.vue`，样式以 `.browser-*` 限定。开发联调可通过 `VITE_BIN_API_ORIGIN` 和 `VITE_BIN_BROWSE_ORIGIN` 指定本地 Worker，生产默认使用上述域名。部署、免费配额、密钥轮换和后端测试命令见 `../bin-api/README.md`。

2026-11-07 线上实测已验证 Bing 简洁搜索返回结果并打开 MDN，以及一条抖音公开视频的实际播放。原版 Bing 仍有结果区域不可见的问题，米哈游登录子页面为空，云原神登录与实际游玩未通过验收；完整记录在同级项目 `../bin-api/VERIFICATION.md`。

## Codex 对话加密字段清理

地址 `/tools/codex-jsonl-cleaner`，分类「格式整理」。导入 UTF-8 JSONL 或粘贴 Codex / Codex CLI 导出的事件，每行必须是一个 JSON 对象；文件与文本上限均为 20 MB。支持 UTF-8 BOM、LF 与 CRLF，文件末尾单个换行不增加行数，内部空行会作为非法行报告。

「选择文件」旁提供「导入教程」按钮，默认收起，点击后显示三步说明：按系统打开目录、在子文件夹中查找 `.jsonl` 并核对会话、返回工具选择文件和清理。Windows 默认目录为 `%USERPROFILE%\.codex\sessions`，macOS / Linux 为 `~/.codex/sessions`；归档记录位于同一根目录的 `archived_sessions`。设置了 `CODEX_HOME` 时使用自定义根目录；WSL、远程开发和容器需在实际运行 Codex 的环境中查找。教程组件在 `src/tools/codex/CodexImportGuide.vue`，位置依据 [OpenAI 官方故障排查文档](https://learn.chatgpt.com/docs/reference/troubleshooting)与[环境变量说明](https://learn.chatgpt.com/docs/config-file/environment-variables)。

教程根据浏览器提供的系统信息预选 Windows、macOS 或 Linux；优先使用 UA Client Hints，缺失时读取 User-Agent 与平台信息，不请求额外权限。未知系统、Android、iPhone / iPad 和 ChromeOS 默认展示 Windows 教程，避免将移动设备误判为桌面系统。用户可手动切换，目录路径、归档路径和操作说明随选择变化；收起再展开保留手动选择，离开页面后重置。识别逻辑位于 `src/tools/codex/importPlatform.ts`。

- **精确模式（默认）**：删除含 `"encrypted_content"` 或 `type` 为 `reasoning` / `Reasoning` 的整行，兼容冒号周围的空白、嵌套对象与转义后的字段名。其余行保留原文，`reasoning_effort`、`reasoning_output_tokens` 等参数与用量元数据不会单独触发删除。
- **宽泛模式**：按原始行文本匹配 `encrypted_content` 或 `reasoning`，不区分大小写。任何位置命中都会删整行，包括元数据键和普通正文中的词语。
- **只删字段不删行**：解析后递归删除 `encrypted_content`、`reasoning` 键，以及 `type` 为 `reasoning` / `Reasoning` 的对象。嵌套推理对象从父属性或数组中移除，顶层推理对象写成 `{}`，保留全部事件行与参数 / 用量元数据，再序列化为单行 JSON。此模式遵循 JavaScript JSON 解析规则，重复键会合并，大整数可能舍入；最多支持 256 层嵌套。

先逐行校验，非法 JSON、非对象事件和无法处理的行均显示原始行号（最多展示前 100 处，统计全部错误），任何一行失败都会阻止整份文件导出，需修正后重试。成功后显示处理前后及删除行数，字段模式还显示发生清理的行数。结果可关闭预览或查看前 10 / 30 / 100 行，下载始终包含全部结果；全部行被删除时可下载空文件。输出采用 LF 换行，非空文件保留末尾换行。

清理在本地 Worker 中运行，30 秒超时；取消、修改输入或模式、读取新文件及卸载都会清理旧任务和下载结果，不上传或持久保存内容。仅清理所选规则覆盖的字段和行，正文及其他字段仍会保留。自制组件、规则与 Worker 位于 `src/tools/codex/`，不修改上游源码归档，也没有新增依赖。

## 输入与使用范围

- 除私人网页浏览器外，输入和选项只在当前组件内保留，不写入浏览器存储。工具计算不上传输入；徽章链接仅在主动打开时向对应服务发送项目名或自定义徽章内容。离开工具页或刷新会清空。网页浏览器的 Service Worker 仅注册在独立浏览子域名，个人主页与其他工具不注册离线缓存服务。
- 通用文本转换上限为 100 万字符，文本文件导入上限 5 MB；哈希文件上限 20 MB。较大的 Excel 文件、图片和复杂文档仍可能占用较多内存。
- JSON 与相关格式转换沿用上游 JavaScript 解析规则；超过安全整数范围的编号应使用字符串，重复对象键会按解析结果合并。原工具的无损 JSON 排版实现已移除。
- HTML 在不具备同源权限的沙盒中预览，默认关闭脚本；预览内容配置 CSP，阻止网络资源和连接，图片可用 Data URI。Markdown 预览净化 HTML，不自动加载外部图片。预览是本地查看工具，不是完整网站运行环境。
- JWT 支持解析与 HMAC 签名校验；签名正确并不等于业务授权有效。证书校验使用随构建提供的 Mozilla 根证书快照，检查链签名、有效期、主机名和私钥匹配，不联网查询吊销状态。
- 正则表达式在 Worker 内运行，超时 1 秒会中止；离开页面会清理任务。通用转换输入改变时立即撤销旧结果；全屏编辑保留原输入，退出恢复焦点。

- Web Tools 的 PDF 转图片文件上限 30 MB，单页上限 1600 万像素；ZIP 最多 100 页、64 MB，包含最后一页。支持密码文档；密码只保留在当前组件。取消、重新读取或离开时清理解析和渲染任务，字体、CMap、图像解码 WASM 全部由本站提供。
- EXIF 文件上限 30 MB，可包含原始照片的 GPS 信息；不自动访问地图或外部图片。SVG 最多 50 万字符、15 秒超时；JavaScript 混淆最多 10 万字符、20 秒超时，源码只转换不执行，选项改变后清除旧结果。
- 简繁转换为逐字映射，不处理上下文歧义；拼音按词典推断，注音预览最多 3000 字。汉字表保留 8105 字，每页 120 字。金额支持 16 位整数和最多 2 位小数，以文本处理避免 Number 舍入。
- 代码图片最多 2 万字符，支持 PNG/JPEG/SVG，位图默认 2 倍导出；JPEG 透明区域填白，SVG 使用 foreignObject。代码图片的固定深浅配色仅影响导出作品，操作区始终跟随本站主题。

## 源码与许可证

上游提交固定为 [`ddae2a2ebee1354b2f69766cf673e06ef1593658`](https://github.com/incentius-foss/freemium/tree/ddae2a2ebee1354b2f69766cf673e06ef1593658)。完整上游清单与原文件 SHA-256 保存在 [upstream.json](../third_party/freemium/upstream.json)，迁入的功能位于 `src/tools/freemium/pages/tools/`。共享编辑器、表单、复制与弹层位于同目录的 `components/`、`composables/`，证书逻辑与数据位于 `tools/`。

保留 [Freemium MIT 许可证](../public/licenses/freemium.txt)、[MPL-2.0](../public/licenses/MPL-2.0.txt) 和 [运行时依赖声明](../public/licenses/tools-dependencies.txt)。Mozilla 根证书数据 `cacert.pem` 的 MPL-2.0 声明保留在原文件头部；数据未修改。发布时这些许可文件随 `public/licenses/` 一并部署。更多来源信息见 [third_party/freemium/README.md](../third_party/freemium/README.md)。

Web Tools 的原始归档、完整 31 项清单、15 个新增与 16 个去重映射见 [源码来源](../third_party/jaywcjlove-tools/README.md)。新增运行时代码适配为 Vue；保留 MIT 原文及 [新增依赖声明](../public/licenses/jaytools-dependencies.txt)。ExifReader（MPL-2.0）的未修改源码随站点提供，PDF.js（Apache-2.0）的附带字体与 WASM 许可随资源发布。

本站适配包括中文文案、本站主题变量与 Lucide 图标、原生 CSS 布局、进入 / 退出 / 筛选切换动画、取消输入持久保存、过期结果清理和全屏焦点恢复。没有引入 Quasar、上游导航、收藏、最近记录或独立路由框架。

## 维护与验证

名称、分类、搜索词和路径在 `src/tools/catalog.ts`；按需加载映射在 `src/tools/components.ts`。`src/pages.ts`、`src/router.ts`、分享标签和站点地图从目录派生。新增或升级工具时对照上游完整清单、依赖锁文件和许可证，并更新回归检查。

```bash
npm install
npm run build
node scripts/check-tools.mjs
npm run preview -- --port 4173
# 在另一终端运行，需要 Python Playwright 与 Chrome / Chromium
HOMEPAGE_TEST_URL=http://127.0.0.1:4173 python3 scripts/check-tools-browser.py
HOMEPAGE_TEST_URL=http://127.0.0.1:4173 python3 scripts/check-pdf-convert-browser.py
HOMEPAGE_TEST_URL=http://127.0.0.1:4173 python3 scripts/check-codex-cleaner-browser.py
HOMEPAGE_TEST_URL=http://127.0.0.1:4173 python3 scripts/check-jaytools-browser.py
HOMEPAGE_TEST_URL=http://127.0.0.1:4173 python3 scripts/check-xcpdf-browser.py
HOMEPAGE_TEST_URL=http://127.0.0.1:4173 python3 scripts/check-navigation.py
python3 scripts/check-sharing.py
python3 scripts/check-seo.py
```

布局检查覆盖 320 / 390 / 768 / 1024 / 1440px；工具浏览器检查同时验证两套配色的深浅主题、完整工具清单、示例、文件导入、二维码识别、复制下载、状态清空、全屏焦点和减少动态效果。截图写入 `artifacts/`。
