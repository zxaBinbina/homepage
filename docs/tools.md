# 网页工具

本站以 [incentius-foss/freemium](https://github.com/incentius-foss/freemium) 的 MIT 源码替换原有 12 个工具，完整接入上游版本的 **41 个工具**。入口 `/tool`，工具均使用站内页面与延迟加载组件，源码随本站构建，不嵌入外站工具。

## 工具清单

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

## 输入与使用范围

- 输入和选项只在当前组件内保留，不写入浏览器存储、不上传。离开工具页或刷新会清空；首次进入某个工具仍需要加载它的代码，本站没有新增离线缓存服务。
- 通用文本转换上限为 100 万字符，文本文件导入上限 5 MB；哈希文件上限 20 MB。较大的 Excel 文件、图片和复杂文档仍可能占用较多内存。
- JSON 与相关格式转换沿用上游 JavaScript 解析规则；超过安全整数范围的编号应使用字符串，重复对象键会按解析结果合并。原工具的无损 JSON 排版实现已移除。
- HTML 在不具备同源权限的沙盒中预览，默认关闭脚本；预览内容配置 CSP，阻止网络资源和连接，图片可用 Data URI。Markdown 预览净化 HTML，不自动加载外部图片。预览是本地查看工具，不是完整网站运行环境。
- JWT 支持解析与 HMAC 签名校验；签名正确并不等于业务授权有效。证书校验使用随构建提供的 Mozilla 根证书快照，检查链签名、有效期、主机名和私钥匹配，不联网查询吊销状态。
- 正则表达式在 Worker 内运行，超时 1 秒会中止；离开页面会清理任务。通用转换输入改变时立即撤销旧结果；全屏编辑保留原输入，退出恢复焦点。

## 源码与许可证

上游提交固定为 [`ddae2a2ebee1354b2f69766cf673e06ef1593658`](https://github.com/incentius-foss/freemium/tree/ddae2a2ebee1354b2f69766cf673e06ef1593658)。完整上游清单与原文件 SHA-256 保存在 [upstream.json](../third_party/freemium/upstream.json)，迁入的功能位于 `src/tools/freemium/pages/tools/`。共享编辑器、表单、复制与弹层位于同目录的 `components/`、`composables/`，证书逻辑与数据位于 `tools/`。

保留 [Freemium MIT 许可证](../public/licenses/freemium.txt)、[MPL-2.0](../public/licenses/MPL-2.0.txt) 和 [运行时依赖声明](../public/licenses/tools-dependencies.txt)。Mozilla 根证书数据 `cacert.pem` 的 MPL-2.0 声明保留在原文件头部；数据未修改。发布时这些许可文件随 `public/licenses/` 一并部署。更多来源信息见 [third_party/freemium/README.md](../third_party/freemium/README.md)。

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
HOMEPAGE_TEST_URL=http://127.0.0.1:4173 python3 scripts/check-navigation.py
python3 scripts/check-sharing.py
python3 scripts/check-seo.py
```

布局检查覆盖 320 / 390 / 768 / 1024 / 1440px；工具浏览器检查同时验证两套配色的深浅主题、完整工具清单、示例、文件导入、二维码识别、复制下载、状态清空、全屏焦点和减少动态效果。截图写入 `artifacts/`。
