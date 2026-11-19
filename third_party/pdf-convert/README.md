# PDF 办公格式转换来源

四个站内工具位于 `src/tools/pdfconvert/`，PDF 解析与图片渲染复用本站的 PDF.js，本地 Word、Excel、PowerPoint 文件分别由 docx、SheetJS 与 PptxGenJS 生成。

文字分析流水线迁入 [opendocsg/pdf2md](https://github.com/opendocsg/pdf2md/tree/5d3a505928bd3216a303c669457e61696d7fd6ed)，固定提交 `5d3a505928bd3216a303c669457e61696d7fd6ed`、版本 0.4.0，许可证 MIT。原始源码归档、归档校验值、每个迁入文件的原始 SHA-256 与对应路径见 [upstream.json](upstream.json)，MIT 原文见 [LICENSE](LICENSE)。本站没有迁入其 Node CLI 或旧 PDF 解析器。

迁入代码改为 ES modules，以小型本地枚举替换 enumify；先识别表格并隔离对应文字，再分析标题、列表与段落。列表识别先于标题识别，避免中文列表被当作大写标题；未依据缩进猜测代码块。最后一个转换步骤也执行清理阶段。表格检测、中文兼容字符处理、文件生成、Web Worker、取消清理与界面为本站实现。

调研时还评估了 DoxDock、PaperDock、reamkit、fizzdoc 等实现；本站未复制它们的源码，不将这些仓库列为发布依赖。转换不提供 OCR，不保证复杂版面、合并单元格或跨行表格的还原；Word / PowerPoint 图片模式用于保留整页画面，图片中的文字不可编辑。

发布许可与新增依赖的完整声明见 [pdf-convert.txt](../../public/licenses/pdf-convert.txt)，由 `node scripts/update-pdf-convert-notices.mjs` 更新。PDF.js、SheetJS 与 fflate 的既有声明继续随站点发布。
