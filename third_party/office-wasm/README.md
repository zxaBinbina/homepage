# Office WASM 文件预览

独立 iframe 程序基于 [unestgroup/office-wasm-viewer 0.2.0](https://github.com/unestgroup/office-wasm-viewer/tree/34b8235)（AGPL-3.0-or-later）；主站只使用 [office-wasm-sdk 0.1.0](https://github.com/unestgroup/office-wasm-sdk/tree/390bcc8) 的 Apache-2.0 消息桥。它读取实际 DOCX / XLSX / PPTX 字节，经 x2t.wasm 转成 Office 内部格式，由 ONLYOFFICE 原生文档、电子表格、演示文稿引擎绘制。

主站 `https://zxabinbina.cc.cd` 嵌入同一 Pages 构建的 `https://homepage-r2n.pages.dev/office-viewer/v0.2.0/index.html`。本地开发与预览在 `localhost` 和 `127.0.0.1` 之间切换来源、复用同一端口。可用公开的 `VITE_OFFICE_VIEWER_ORIGIN` 覆盖来源；该来源必须托管本构建的资源，与主站来源不同。

## 固定上游与许可

| 内容                            | 来源                                                           | 许可                         |
| ------------------------------- | -------------------------------------------------------------- | ---------------------------- |
| Viewer                          | unestgroup/office-wasm-viewer，`34b8235`                       | AGPL-3.0-or-later            |
| 消息桥                          | unestgroup/office-wasm-sdk，`390bcc8`                          | Apache-2.0                   |
| sdkjs、web-apps                 | cryptpad/onlyoffice-editor，`v9.3.2+3`                         | AGPL-3.0，保留上游版权与品牌 |
| x2t.wasm                        | cryptpad/onlyoffice-x2t-wasm，`v9.3.2+4`                       | AGPL-3.0                     |
| Arimo、Tinos、Cousine、Carlito  | 上述 CryptPad 字体包，原始字体文件                             | SIL OFL 1.1                  |
| Noto Sans CJK SC Regular / Bold | notofonts/noto-cjk，`f8d157532fbfaeda587e826d4cd5b21a49186f7c` | SIL OFL 1.1                  |
| 数学替代字体                    | Viewer 的 `fonts/math/`                                        | SIL OFL 1.1，详见 NOTICE.md  |

`manifest.json` 记录下载输入的 SHA-256、归档分片和逐文件校验。原始 editor ZIP 和 x2t ZIP 已逐一核对官方 SHA-512。发布资源仅包含中英文界面、三种查看器、单线程 WASM 和明确许可的字体；移除帮助、拼写字典、Visio、PDF 编辑器、Monaco、源码映射及其他字体。不分发 Arial、Calibri、无许可声明的越南语原始字体。

`viewer-source.tar.gz` 是上游源码归档，排除无许可字体和示例文档。`viewer/` 保存本部署的可审阅修改：中文界面、只读权限、Brotli WASM 路径、Word 适应宽度、即时主题切换和临时偏好存储。`prepare.py` 从固定下载包生成运行归档，保留真正的 Office 引擎；它移除原生页中的 Service Worker 注册，加入临时存储适配，补齐原生主题配置路径和中文字体映射。SDK 的改动在 `src/tools/office/office-viewer.mjs`：iframe 限制、来源校验沿用上游，补全销毁时的启动计时器及监听清理。

## 生成与发布

下载 manifest 中的固定 editor / x2t ZIP，以及 Noto 的两份字体到同一目录，执行：

```sh
python3 third_party/office-wasm/prepare.py /path/to/downloads
npm run build
```

正常构建不访问网络，`build/officeViewer.ts` 从分片校验并解包到 `.cache/office-wasm/`，原样复制到构建目录；不将 AGPL 引擎链接进主站 bundle。所有静态资源低于 Cloudflare Pages 的 25 MiB 单文件上限。38 MiB 的 x2t 模块以 6.5 MiB 的 `.wasm.br` 发布，局部 `_headers` 和本地中间件提供 `Content-Encoding: br` / `Content-Type: application/wasm`，浏览器解压后编译，无需全站 COOP / COEP。

查看器以 `postMessage` 接收当前结果的副本，不上传文件，不保存输入。iframe 销毁后清除文档、Worker、内存偏好和 Blob URL；HTTP 缓存仅保存静态引擎。保留原下载按钮；查看器内禁用编辑、上传、插件、打印和另存为。源码入口随预览展示，发布路径 `source/index.html` 提供本地修改源码、上游源码及固定引擎源码链接，满足网络使用的源码提供义务。

字体使用开放替代字体，和 Microsoft Office 的专有字体可能有字距与分页差异；这是实际 Office 引擎的文件预览，不重新用 HTML 表格或 SVG 复写文档内容。
