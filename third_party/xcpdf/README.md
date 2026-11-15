# 信创 PDF 工具箱 XCPDF V7.3

作者：相声的技术备忘录 / [wallechfox](https://github.com/wallechfox)。项目：[offline-pdf-tools](https://github.com/wallechfox/offline-pdf-tools)。

本站接入用户提供的 `信创PDF工具箱V7.3-43项功能-单文件版.html`。原始文件完整保存在 [upstream.html](upstream.html)，其 SHA-256 与 [2026-11-05 发布提交](https://github.com/wallechfox/offline-pdf-tools/tree/98424086829730f3dd7313a8871bbbbb49e80cd8) 中的同名文件完全一致：

```text
80dc72dabeee647753e371d5fb864240cce83fdb167c35356e90b66cbc2756dc
```

该提交的许可为 [MIT](LICENSE)，版权原文为 `Copyright (c) 2026 wallechfox`。上游后来于 2026-11-06 更换许可；本站固定上述 MIT 发布版，不能以此许可证假定新版本仍可同样适配。发布的 MIT 副本位于 [public/licenses/xcpdf.txt](../../public/licenses/xcpdf.txt)。

[upstream.json](upstream.json) 记录版本、提交、校验值及全部 43 项工具到独立站内地址和原面板的映射。已有 Web Tools PDF 转图片入口继续保留，XCPDF 的对应功能另有地址。

`build/xcpdf.ts` 在开发和构建期间核对归档 SHA-256，生成 `/tool-assets/xcpdf/runtime.html`。生成过程保留原 PDF 引擎、内嵌字体映射、工作线程和许可证头部；界面结构从原始页面的解码器还原，样式及消息桥来自 `src/tools/xcpdf/`。不直接修改归档、不将生成文件作为源码维护。

沙盒禁止同源权限与网络连接；输入、密码和收藏初始化数据只存于内存。父页面仅传递主题及选择的面板，接收高度、准备状态和用户主动复制的文本。重新开始或卸载清理运行环境。处理库随 HTML 加载，不新增 npm 依赖，不替换已有 Web Tools 的 PDF.js。

第三方代码包含 PDF.js 2.16.105（Apache-2.0）、内嵌 Adobe CMaps、@cantoo/pdf-lib（MIT）、JSZip 3.10.1（选择 MIT）、UTIF.js 与 pako（MIT）；原 SVG 插图来自 Twemoji（CC-BY-4.0）。保留原许可证头部及内嵌版权声明，完整补充说明随 [public/licenses/xcpdf-dependencies.txt](../../public/licenses/xcpdf-dependencies.txt) 发布。

维护检查：

```bash
node scripts/check-xcpdf.mjs
npm run build
HOMEPAGE_TEST_URL=http://127.0.0.1:4173 python3 scripts/check-xcpdf-browser.py
```

工具清单、使用限制与全站验证入口见 [docs/tools.md](../../docs/tools.md#信创-pdf-工具箱)。
