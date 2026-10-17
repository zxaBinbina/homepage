<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# Gaze 与其他 Linux 人脸认证方案对比

Gaze 是为 Linux 带来 Windows Hello 风格人脸认证的多个项目之一。它们都接入 PAM，都是开源的，并且都解决同一个基本问题：用人脸而非密码登录。它们的差异在于把安全性做到了什么程度、架构如何设计，以及覆盖了桌面的多少部分。

我们整理这份对比，是为了说明 Gaze 与 [Howdy](https://github.com/boltgolt/howdy)、[Visage](https://github.com/sovren-software/visage) 和 [Biopass](https://github.com/TickLabVN/biopass) 的不同之处。如果我们遗漏了什么或有细节错误，请[告诉我们](https://github.com/zxaBinbina/gaze-zh/issues)。

## 一览

| | **Gaze** | **Howdy** | **Visage** | **Biopass** |
|---|---|---|---|---|
| 语言 | Rust | Python + C | Rust | C++ + Tauri |
| 人脸检测 | SCRFD | dlib (HOG/CNN) | SCRFD | YOLO-Face |
| 识别 | ArcFace (MobileFaceNet / ResNet50) | dlib ResNet (128-d) | ArcFace (`w600k_r50`) | EdgeFace |
| 推理运行时 | ONNX Runtime | dlib | ONNX Runtime | ONNX Runtime |
| 红外相机支持 | 是，RGB+IR 混合合并，内置 UVC 发射器 | 是 | 是，内置 UVC 发射器 | 是 |
| 指纹 | 否 | 否 | 否 | 是 |
| 架构 | 根守护进程 + 系统 DBus | 每次认证一个子进程（无守护进程） | 守护进程 + DBus | 守护进程 + DBus |
| 每次认证是否重新加载模型 | 否（常驻守护进程） | 是（每次冷启动） | 否（常驻守护进程） | 否（常驻守护进程） |
| 静态存储模板 | TPM 封存、默认按账户绑定加密；可显式选择退出 | 明文编码 | SQLite 存储 | 本地存储 |
| 人脸登录后解锁密钥环 | 是，可选 TPM 封存的凭据回放到 `pam_gnome_keyring` | 否 | 否 | 否 |
| 模型完整性 | 下载时通过 SHA-256 校验 | 随包捆绑 | SHA-256 固定 | 随包捆绑 |
| 接口 | CLI（含 TUI）+ GTK GUI + GNOME/Cinnamon 扩展 + KDE 系统设置 | 仅 CLI | CLI + TUI 登记 | GUI（Tauri）+ CLI |
| 桌面集成 | GNOME、Cinnamon 与 KDE Plasma 锁屏、Hyprland/hyprlock、LightDM、控制台/TTY 登录 | 仅 PAM | 仅 PAM | PAM + polkit |
| 配置 | `config.toml` + CLI + GUI | 手动 ini 文件 | 配置文件 / Nix | GUI |
| 引导式多角度登记 | 是 | 基础 | 基础 | 基础 |
| 内置健康检查 | 是（一条 `doctor` 命令） | 部分 | 部分 | GUI 状态 |
| 相机来源 | GStreamer / PipeWire | V4L2 设备路径 | V4L2 设备路径 | V4L2 设备路径 |
| 是否可在较旧（AVX2 之前）CPU 上运行 | 否（`gazed` 需要 AVX2；客户端可在任意平台运行） | 是 | 视情况而定 | 视情况而定 |
| 打包方式 | deb / rpm / COPR / openSUSE / Arch / Nix / Flatpak / 安装脚本 | deb / AUR / COPR / openSUSE | deb / rpm / Nix / AUR | deb / rpm / AUR |
| 许可证 | GPL-3.0-or-later | MIT | MIT | MIT |

## 活体检测与防欺诈

活体检测是这些项目之间最大的安全差异。它正是阻止他人用你的照片或视频解锁机器的关键。

| | 方案 | 打印照片 | 屏幕回放 | 视频回放 |
|---|---|---|---|---|
| **Gaze** | MiniFASNet-V2 CNN（RGB）+ 眼球运动检测（IR） | 已拦截 | 已拦截 | 部分 |
| **Howdy** | 无（仅跳过过暗的帧） | 未拦截 | 未拦截 | 未拦截 |
| **Visage** | 关键点稳定性，零模型眼球微动检测 | 未拦截 | 未拦截 | 未拦截 |
| **Biopass** | 反欺诈模型（上游未命名）+ 红外相机检测 | 已拦截 | 已拦截 | 部分 |

Gaze 与 Biopass 在人脸裁剪区域上运行真正的反欺诈模型，因此能同时拒绝照片与屏幕。Visage 的检测仅基于运动，其自身的 README 报告被动活体检测在测试中无法区分：手持的手机屏幕比两次真实的活体尝试位移更大。Howdy 不进行主动反欺诈，其自身的 README 警告它"在安全性上远不如密码"，并且不应作为你唯一的认证方式。没有任何项目能完全击败高质量的视频回放或 3D 面具，这正是为何各处仍建议保留密码回退，*Gaze 也不例外*。

## 关于替代方案的说明

这三个项目中任意一个都能为你提供可用的人脸认证。Howdy 出现最早，打包也最广泛。Visage 是另一个支持 IR 的 Rust 守护进程，其文档说明了其活体检测的局限。Biopass 同时支持指纹与人脸，并且带有 GUI。

我们维护 Gaze，但我们更希望你选择适合自己硬件、桌面与威胁模型的方案。请检查你所选方案的安全局限。
