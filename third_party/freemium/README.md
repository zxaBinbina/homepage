# Freemium 源码来源

- 仓库：[incentius-foss/freemium](https://github.com/incentius-foss/freemium)
- 获取日期：2026-10-30
- 固定提交：`ddae2a2ebee1354b2f69766cf673e06ef1593658`
- 许可证：[MIT](LICENSE)，Copyright (c) 2024 incentius-foss
- 范围：上游 `src/tools/registry.js` 登记的全部 41 个工具

通过 GitHub 搜索并核对仓库许可证后获取源码。选择该项目是因为其 MIT 许可、完整的浏览器内处理工具与 Vue 单文件组件便于与本站集成。

```bash
git clone https://github.com/incentius-foss/freemium.git
cd freemium
git checkout ddae2a2ebee1354b2f69766cf673e06ef1593658
```

[upstream.json](upstream.json) 保留未修改上游文件的校验摘要和完整工具清单。功能源码迁入 `src/tools/freemium/`，后续适配直接维护这些源文件；本站目录与异步加载映射分别维护在 `src/tools/catalog.ts`、`src/tools/components.ts`。工具完整清单、适配内容与验证方式见 [网页工具说明](../../docs/tools.md)。

许可证副本位于 `public/licenses/freemium.txt`。上游 `cacert.pem` 保留 Mozilla / curl 数据来源与 MPL-2.0 声明，其许可证全文位于 `public/licenses/MPL-2.0.txt`；运行时依赖许可证和版本记录位于 `public/licenses/tools-dependencies.txt`，均随构建发布。迁入时没有引入上游 Quasar 框架、独立应用外壳或存储机制。
