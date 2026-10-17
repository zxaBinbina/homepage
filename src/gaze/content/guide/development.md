<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# 开发

本页面向贡献者，介绍源码构建、测试、打包以及 Flatpak 工作流。

有关拉取请求流程、测试预期与安全注意事项，请参见[参与贡献](/projects/gaze/guide/contributing)。

## 先决条件

Gaze 面向 Linux 平台 API（V4L2、PAM、TPM2/tss2、polkit、GTK4/libadwaita、Flatpak、SELinux），这些在 macOS 或 Windows 上并不存在，因此这些平台无法原生构建。

有三种方式获取环境，最终都会落到相同的 `just` 配方上。选择对你要求最少的那一种。

### Nix：最短路径

```bash
nix develop
```

这就是完整的设置。该 shell 已配好 Rust 工具链与所有原生依赖（OpenCV、GStreamer、GTK4、ONNX Runtime、tpm2-tss）。参见 [Nix 与 NixOS 指南](/projects/gaze/guide/nixos)。

### Docker：如果你不在 Linux 上

```bash
just docker build-rust
```

任何配方也都可以在一个与 CI 镜像一致的容器内运行，因此宿主机只需 Docker。参见[在没有 Linux 宿主机的情况下构建](#building-without-a-linux-host-docker)。

### 发行版软件包

安装工具链：

- 当前稳定版 Rust，通过 [rustup](https://rustup.rs)。被锁定的 GTK 与 GStreamer 依赖需要 Rust 1.92 或更新版本。
- [`just`](https://github.com/casey/just) 1.51+，下面所有任务都经由的任务运行器
- [`cargo-audit`](https://github.com/RustSec/rustsec/tree/main/cargo-audit)，用于 `just audit`
- [`nfpm`](https://nfpm.goreleaser.com)，仅用于 `just package`
- [`flatpak-builder`](https://github.com/flatpak/flatpak-builder)，仅用于 `just build-flatpak`

CI 使用稳定版 Rust，并在 `.github/workflows/ci.yml` 中固定 `just` 版本。为所需的检查准备 Rust 工具：

```bash
rustup update stable
rustup default stable
rustup component add rustfmt clippy
cargo install just --locked
cargo install cargo-audit --locked
```

然后安装系统库。仅运行时软件包不会提供 `just lint` 与 `just test` 所需的头文件和 pkg-config 文件：

::: code-group

```bash [Debian/Ubuntu]
sudo apt update
sudo apt install build-essential pkg-config clang libclang-dev \
  libopencv-dev libv4l-dev libpam0g-dev libtss2-dev libssl-dev \
  libgtk-4-dev libadwaita-1-dev \
  libcairo2-dev libglib2.0-dev libgdk-pixbuf-2.0-dev \
  libpango1.0-dev libgraphene-1.0-dev \
  libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-pipewire \
  gettext-base \
  flatpak flatpak-builder elfutils
```

```bash [Fedora/RHEL]
sudo dnf install @development-tools pkg-config clang clang-devel \
  opencv-devel libv4l-devel pam-devel tpm2-tss-devel openssl-devel \
  gtk4-devel libadwaita-devel \
  gstreamer1-devel gstreamer1-plugins-base-devel \
  gstreamer1-plugins-base gstreamer1-plugins-good pipewire-gstreamer \
  checkpolicy policycoreutils \
  gettext \
  flatpak flatpak-builder elfutils
```

```bash [openSUSE Tumbleweed]
sudo zypper install --no-recommends \
  clang clang-devel opencv-devel libv4l-devel pam-devel tpm2-0-tss-devel \
  libopenssl-devel gtk4-devel libadwaita-devel \
  gstreamer-devel gstreamer-plugins-base-devel \
  gstreamer-plugins-base gstreamer-plugins-good gstreamer-plugin-pipewire \
  checkpolicy policycoreutils pkgconf-pkg-config envsubst gcc gcc-c++ \
  flatpak flatpak-builder elfutils
```

```bash [Arch Linux / Manjaro]
sudo pacman -S base-devel pkgconf clang llvm \
  opencv v4l-utils pam tpm2-tss openssl \
  gtk4 libadwaita \
  gstreamer gst-plugins-base gst-plugins-good gst-plugin-pipewire \
  gettext \
  flatpak flatpak-builder elfutils
```

:::

`libtss2-dev`/`tpm2-tss-devel`/`tpm2-tss`/`tpm2-0-tss-devel` 与 `libssl-dev`/`openssl-devel`/`openssl`/`libopenssl-devel` 支撑 `tss-esapi` 和 `openssl-sys` crate（守护进程将人脸模板密钥封存到 TPM）；`gettext-base`/`gettext`/`envsubst` 提供 `envsubst`，下方 `package` 配方需要它。

OpenCV 4 和 5 均可使用。在提供 OpenCV 5 的发行版（如 Arch Linux）上，`just` 配方会自动将 `opencv` crate 指向 `opencv5` 这个 pkg-config 名称；直接运行 `cargo` 时，需自行设置 `OPENCV_PKGCONFIG_NAME=opencv5`。

只有 `gaze-gui` 需要 gtk4 和 libadwaita（`libgtk-4-dev`/`gtk4-devel`/`gtk4`、`libadwaita-1-dev`/`libadwaita-devel`/`libadwaita`，以及在 Debian/Ubuntu 上与它们一起列出的 cairo、glib、gdk-pixbuf、pango 和 graphene 头文件）。对于仅 TUI 的检出，设置 `GAZE_GUI=0`（也可为 `false`、`no` 或 `off`）并跳过这些软件包：`build-rust`、`test` 和 `lint` 随后会排除 `gaze-gui`，而 `dev-link-system` 会跳过它从未构建的二进制。守护进程、`gaze` TUI、CLI 和 PAM 模块不受影响。与 `OPENCV_PKGCONFIG_NAME` 一样，这仅覆盖这些 `just` 配方：裸 `cargo build`/`cargo test` 仍会构建工作区的每个成员，且打包路径（`package`、`build-flatpak` 以及 spec `srpm` 源）始终包含 GUI，因此构建软件包仍需安装 GUI 依赖。

## 设置

```bash
git clone https://github.com/zxaBinbina/gaze-zh
cd gaze-zh
just setup-hooks
just build-rust
just test
```

这是一个完整可用的检出。`just --list` 会显示所有其他配方。

Git 钩子是每次检出本地的。`just setup-hooks` 将 Git 指向受版本控制的钩子脚本，这样在仓库变更时，预提交检查仍能保持最新。CI 仍会对推送和拉取请求运行相同的必需检查。

## 工作区布局

Rust 软件包位于 `crates/` 下；桌面集成源码位于 `integrations/` 下。软件包定义与已安装的系统配置位于 `packaging/` 下。请从仓库根目录运行构建、测试与打包命令。

- `crates/gazed`：`gazed` 守护进程、ML 流水线以及用户数据库。
- `crates/gaze-cli`：`gaze` CLI 二进制。它位于自己的 crate 中，因此客户端二进制不会静态链接 ONNX Runtime（见下方警告）。
- `crates/gaze-core`：共享的配置/DBus/IR 库。刻意保持轻量：不含 OpenCV、GStreamer 或 ONNX Runtime，因此 PAM 模块可以依赖它。
- `crates/gaze-security`：TPM 封存与 GNOME Keyring 凭据存储。仅链接 tpm2-tss 以及纯 Rust 加密库（`aes-gcm`、`sha2`），不再引入更重的依赖，因此 `pam-gaze` 可以依赖它。
- `crates/gaze-vision`：摄像头捕获、人脸检测与推理。检测功能位于 `detection` cargo 特性之后。工作区依赖关闭了默认特性，因此 CLI 和 GUI 只获得摄像头支持，只有 `gazed` 启用 `detection`。
- `crates/pam-gaze`：`cdylib` PAM 模块。依赖 `gaze-core` 和 `gaze-security` 以进行 TPM 钥匙环解封，绝不依赖 `gaze-vision`；`just check-pam-link` 强制其遵循库白名单（见下方警告）。
- `crates/pam-gaze-grosshack`：已弃用的 `cdylib` 兼容垫片，它会强制 `PamMode::Simultaneous` 并打印弃用通知。它通过 `#[path]` 包含 `pam-gaze` 自身的模块，而非重复它们。每个软件包仍会安装它，以便旧的 PAM 行继续工作，它已被计划移除；新工作应在 `pam-gaze` 中进行。
- `crates/gaze-gui`：GTK4/libadwaita 应用。位于 `integrations/` 的桌面集成是单独打包的。

## 构建并测试 Rust 组件

```bash
just build-rust
just test
just lint
just fmt-check
just audit             # 检查依赖中已知的 CVE
just check-pam-link    # 检查 PAM 模块的共享库占用
just fmt               # 应用格式化（fmt-check 仅检查）
```

标准守护进程同时包含 Intel OpenVINO 和 AMD Vitis AI 适配器，并在启动时动态加载 ONNX Runtime。`just build-rust` 会将固定的 CPU 运行时及其声明文件暂存到 `gazed` 旁边；软件包构建会将其安装到 `/usr/lib/gaze`。

请按照[硬件加速](/projects/gaze/guide/acceleration)中的说明注册厂商运行时。要在不安装的情况下测试自定义 SDK，请将 `ORT_DYLIB_PATH` 设置为它完整的 ONNX Runtime 库，并用该 SDK 的 `LD_LIBRARY_PATH` 启动守护进程。请将系统服务库放在 `/home` 和 `/root` 之外，因为 `gazed.service` 会隐藏这些目录。

::: warning 在 `ort` 依赖上保留 `api-21` 特性
`gazed` 与 `gaze-vision` 依赖 `ort` 时使用了 `default-features = false` 和 `api-21`，这会固定二进制所请求的 ONNX Runtime C API 版本。`ort` 默认指向其发布目标的最新 API，而一个比该版本更旧的运行时会让 ONNX Runtime 交回一个空 API 指针，`ort` 会将其在进程拆解时转换为 panic 并导致核心转储。一个来自固定下载之外的运行时（Nix、`ORT_DYLIB_PATH` 或厂商 SDK）可能旧到 ONNX Runtime 1.21，因此升级 `ort` 时必须保留 `api-21` 特性，而不是继承新的默认值。`gazed` 还会在触碰 `ort` 之前检查已加载的运行时，而 `gaze-vision` 的 `inference::` 测试会在运行时过旧时失败。

`api-21` 也是 Gaze 能够安全请求的最新 API 级别。从 `api-22` 起，`ort` 的会话构建器会在每个会话上设置一个自动执行提供者选择策略，使 ONNX Runtime 从平台的硬件设备列表中选择执行提供者，而不是安装内置的 CPU 提供者。ONNX Runtime 1.22 在 Linux 上没有设备发现机制，因此该列表为空，选择代码会 unchecked 地解引用它并中止进程，即使 Gaze 只请求了 CPU 推理。Gaze 没有用到任何需要 API 22 或更新的东西，因此停留在 `api-21` 会使会话创建保持在直接安装 CPU 提供者的路径上。
:::

`just lint` 会编译两个厂商适配器，`just test` 会在没有 NPU 硬件的情况下验证配置、硬件发现、运行时/API 校验以及 CPU 回退。`just test-openvino` 会针对 Intel 的 onnxruntime-openvino 运行时重跑推理测试（包括被忽略的 OpenVINO 会话测试），它会下载该运行时并按固定的 SHA256 校验（仅 x86_64；CI 在测试作业中运行它）。实际的 NPU 执行、模型算子覆盖、驱动兼容性，以及识别/活体精度，需要两家厂商的[硬件验证](/projects/gaze/guide/acceleration#hardware-validation)。

::: warning 使用 `just build-rust` 构建，而非 `cargo build --workspace`
`just build-rust` 会以独立的 cargo 调用分别构建守护进程和客户端，这样特性统一（feature unification）就无法将 ONNX Runtime 链接进 CLI、GUI 或 PAM 模块。这使推理代码远离客户端和 PAM 模块；守护进程会在加载 ONNX Runtime 之前检查 CPU 支持。
:::

::: warning 切勿让 PAM 模块依赖 `gaze-vision`
`pam_gaze.so` 会被 dlopen 进每个通过 `common-auth` 进行认证的进程，包括 `sshd` 和 `dovecot` 等网络服务。在那里链接视觉栈会引入 OpenCV，进而引入 OpenBLAS，其 ELF 构造器会为每一个核心预留按线程分配的缓冲区。对地址空间设限的服务随后会在加载时中止，这此前已导致 IMAP 认证中断。将它与客户端和 PAM 模块隔开的是 crate 边界，而非 cargo 特性，因为特性会在一次 `cargo build` 调用中跨软件包统一。`just check-pam-link` 会验证构建出的模块只链接基础系统库，而对于主 PAM 模块，只额外链接钥匙环解封所需的 TPM 库。它会作为 `just build-rust` 以及每次软件包构建的一部分运行。
:::

## 运行本地构建的守护进程

守护进程不接受 CLI 参数；路径是编译时确定的：

- 配置：`/etc/gaze/config.toml`
- 用户模板：`/var/lib/gaze/users`
- 模型：`/var/cache/gaze`

它还拥有**系统** DBus 总线上的 `com.gundulabs.Gaze`，这需要 root 权限。你无法以你的用户身份运行第二个守护进程。

**选项 A：将你的构建链接到已安装的文件之上**（便于反复迭代）：

这会将你的检出叠加到一个*已有的*软件包安装之上；它并不安装软件包本身。如果你在这台机器上从未安装过 Gaze，请先构建并安装一次软件包（`just package rpm` 然后 `sudo <包管理器> install dist/packages/gaze-zh-*.rpm`，或对应的 `deb`/`archlinux`）；如果 `gazed.service` 尚未安装，`dev-link-system` 会快速失败并指回这里。

```bash
just build-rust
just dev-link-system    # 自行在 sudo 下运行 scripts/dev-link-system.sh
```

`dev-link-system`（`scripts/dev-link-system.sh enable`）做的不仅仅是替换二进制：

- 将 `/usr/bin/gazed`、`/usr/bin/gaze`、PAM 模块、polkit 策略以及 GNOME 扩展（系统范围与当前用户）链接到软件包安装的文件之上。构建产出 `/usr/bin/gaze-gui` 时也会链接它，在 `GAZE_GUI=0` 构建后则跳过。
- 如果 `/etc/pam.d/sudo` 中还没有，则添加一行 `pam_gaze.so`。
- 为 `gazed` 安装一个 systemd drop-in，清除 `InaccessiblePaths=/home /root`，使打包的单元能够执行从你的检出链接来的二进制，然后重启 `gazed`。
- 如果存在 TPM，则开启 `[storage] encrypt_templates` 并将一个密钥封存到它上面（设置 `GAZE_DEV_TPM=0` 可跳过此步）。

`just dev-unlink-system` 会从备份中撤销上述全部操作，包括 PAM 行与加密设置。`just dev-link-status` 会显示当前链接的内容、TPM/加密状态，以及磁盘上有多少模板已被加密。

**选项 B：在前台运行守护进程**：

```bash
sudo systemctl stop gazed
just build-rust
sudo RUST_LOG=debug ./target/release/gazed
```

`RUST_LOG` 接受标准的 `tracing` 过滤器（`info`、`debug`、`gaze=trace` 等）。按 Ctrl-C 停止，完成后用 `sudo systemctl start gazed` 恢复系统守护进程。

如果你在这台机器上从未安装过 Gaze，在守护进程能够声明其名称或加载之前，你还需要放置好 DBus 策略与配置文件。最简单的方式是先安装一次软件包，然后针对二进制进行迭代：

```bash
sudo install -Dm644 packaging/config/com.gundulabs.Gaze.conf \
  /etc/dbus-1/system.d/com.gundulabs.Gaze.conf
sudo install -Dm644 packaging/config/config.toml /etc/gaze/config.toml
sudo systemctl reload dbus
```

CLI 和 GUI 无需特殊设置；它们与当前拥有总线名称的那个 `gazed` 通信：

```bash
./target/release/gaze list-faces
./target/release/gaze auth --verbose
./target/release/gaze-gui
```

## 迭代 PAM 模块

`pam-gaze` 以 `cdylib` 形式构建。在 `just build-rust` 之后，你会得到：

- `target/release/libpam_gaze.so`
- `target/release/libpam_gaze_grosshack.so`（已弃用的垫片；只有 openSUSE 软件包会安装它）

`just build-rust` 还会对其运行 `just check-pam-link`，如果模块链接了 libc、libgcc、libm、动态加载器以及钥匙环的 `libtss2-esys.so.0`、`libtss2-mu.so.0`、`libtss2-tctildr.so.0` 之外的任何东西，构建就会失败。该 TPM 例外仅适用于 `libpam_gaze.so`，而不适用于兼容垫片。

要通过真实 PAM 运行它们，请复制到系统 PAM 库目录（路径因发行版而异）：

```bash
# Debian/Ubuntu up to 25.10
sudo cp target/release/libpam_gaze.so /lib/x86_64-linux-gnu/security/pam_gaze.so

# Ubuntu 26.04+ (libpam looks in /usr/lib/security)
sudo cp target/release/libpam_gaze.so /usr/lib/security/pam_gaze.so

# Fedora/RHEL
sudo cp target/release/libpam_gaze.so /lib64/security/pam_gaze.so

# Arch
sudo cp target/release/libpam_gaze.so /usr/lib/security/pam_gaze.so
```

::: warning 不要把自己锁在外面
在改动 PAM 文件之前，**请保持一个打开的、拥有活跃 root shell 的第二个终端**（`sudo -s`）。如果模块崩溃或行为异常，你可以从该 shell 中恢复。先针对一个非关键服务进行测试（例如向 `/etc/pam.d/su` 或自定义服务添加一行），而不是 `system-auth` 或 `sudo`。
:::

`.so` 就位后最快的端到端测试：

```bash
sudo -k   # 使缓存的 sudo 凭据失效
sudo -v   # 强制触发一次新的 PAM 提示
```

## 迭代 GNOME 扩展

扩展源码位于 `integrations/gnome-shell/`。要在不打包的情况下从源码树运行它：

```bash
mkdir -p ~/.local/share/gnome-shell/extensions
ln -sfn "$PWD/integrations/gnome-shell" \
  ~/.local/share/gnome-shell/extensions/gaze@gundulabs.com

# 编译 gsettings schema 一次
glib-compile-schemas ~/.local/share/gnome-shell/extensions/gaze@gundulabs.com/schemas

# 在 Xorg 上：Alt+F2 然后 `r`。在 Wayland 上：注销并重新登录。
gnome-extensions enable gaze@gundulabs.com
gsettings set org.gnome.shell.extensions.gaze enable-face-authentication true
```

在迭代时观察 shell 日志：

```bash
journalctl -f /usr/bin/gnome-shell
```

对于解锁对话框会话模式（锁屏），更改仅在全新锁屏后生效，而非 shell 重新加载后。

## 测试 GNOME Shell 兼容性

使用 Node.js 22 或更新版本，运行：

```bash
node scripts/test-gnome.mjs
```

这会下载 GNOME Shell 45.0 至 51.0 的认证源码，并与 Gaze 扩展一起运行。测试涵盖人脸启动与资格判定、通过键盘与按钮确认、密码回退、取消、过期的 D-Bus 回复、GNOME 51 重试模式、Polkit 会话处理器，以及移除扩展钩子。CI 运行相同的命令。要在没有网络访问的情况下使用下载的源码，请传入一个包含从这些发布版中取得的 `45.0/js/` 到 `51.0/js/` 的目录。

该测试工具模拟原生控件、GObject 信号与 D-Bus。在将一个新的 Shell 发布视为完全验证之前，请在 GNOME 桌面会话中实际测试 GDM 登录、锁屏解锁与 Polkit 提示。

## 迭代 Cinnamon 扩展

扩展源码位于 `integrations/cinnamon/`。Cinnamon 从其扩展目录读取设置 schema，因此不需要 `glib-compile-schemas` 步骤：

```bash
mkdir -p ~/.local/share/cinnamon/extensions
ln -sfn "$PWD/integrations/cinnamon" \
  ~/.local/share/cinnamon/extensions/gaze@gundulabs.com
```

用 `Alt + F2`、`r`、Enter 重新加载 Cinnamon，然后从**系统设置 → 扩展**中启用它。用以下命令观察其日志：

```bash
journalctl -f /usr/bin/cinnamon
```

当 `/usr/share/cinnamon` 存在时，`just dev-link-system` 还会在系统范围以及为调用用户链接此扩展，因此已安装的检出无需上述符号链接即可拾取它。

## 构建文档

站点基于 VitePress，通过 `bun` 驱动：

```bash
just build-docs        # bun install && bun run docs:build
bun run docs:dev       # 实时预览，地址 http://localhost:5173
```

在两种情况下都会先运行 `scripts/prepare-docs.sh`，并将归档版本暂存到 `docs/archive/` 下。请编辑 `docs/src/`；切勿编辑 `docs/.vitepress/dist` 下生成的输出。

## 在没有 Plasma 的情况下检查 KDE 锁屏

`just kde-harness` 驱动 PAM 服务的方式，与 KScreenLocker 的登录管理器驱动其非交互式生物识别槽位完全一致：它会渲染错误消息、丢弃信息消息，并在模块发出提示时大声失败（这会让真实的登录管理器在剩余锁屏期间卡住）。传入一个服务名和轮数，以模拟密码错误后的重新布防：

```bash
just kde-harness kde-fingerprint 2
```

## 测试 KDE PAM 兼容性

使用 Node.js 22.15 或更新版本，运行：

```bash
node scripts/test-kde.mjs
```

这会下载每个受支持发行版所提供的 KDE 锁屏与登录管理器 PAM 栈（kscreenlocker、sddm、plasma-login-manager，以及它们所包含的基础栈），并针对它们运行 `gaze-kde-pam`。Fedora 会运行两次，一次使用默认 authselect 配置，一次使用 `with-fingerprint with-faillock`。测试会用 Linux-PAM 的分发规则评估编辑后的栈，并覆盖刷脸解锁、账户锁定与 nologin 闸门、不应计为登录失败的未匹配、指纹读取器保留自己的槽位、登录管理器处的密码回退，以及禁用时逐字节复原。CI 运行相同的命令。要在没有网络访问的情况下使用下载的源码，请传入一个目录，其中每个目标对应一个文件夹（如 `arch` 或 `fedora-44`），包含该脚本本应下载的文件。

PAM 模块是模拟的。在将某个发行版发布视为完全验证之前，请实际解锁一个 Plasma 会话，或使用 `just kde-harness`。

## 测试 Cinnamon 兼容性

使用 Node.js 22 或更新版本，运行：

```bash
node scripts/test-cinnamon.mjs
```

这会下载 Cinnamon 的 Polkit 代理（来自 6.2、6.4、6.6 以及 6.8 开发系列），再加上 6.8 的锁屏解锁对话框，并与 Gaze 扩展一起运行。6.2 之前的版本没有 Cinnamon Polkit 代理，因此那里的测试只检查 D-Bus 注册与干净禁用。测试涵盖通过键盘与按钮确认、密码提示与回退、摄像头提示、错误消息、Polkit 重试、锁屏重试模式，以及禁用时复原每个上游方法。CI 运行相同的命令。要在没有网络访问的情况下使用下载的源码，请传入一个目录，其中每个 Cinnamon 标签对应一个文件夹（如 `6.6.9`），包含该脚本本应下载的文件。

控件、信号与 D-Bus 是模拟的。在将某个发布视为完全验证之前，请实际解锁一个 Cinnamon 会话并批准一个 Polkit 提示。

## 打包

```bash
just package <deb | rpm | archlinux>
```

软件包输出：

- `dist/packages/`

## Flatpak 构建

构建配方会添加 Flathub 远程仓库，并安装或更新 manifest 所声明的 GNOME 运行时/SDK 以及 Rust/LLVM 扩展，使它们的版本有单一事实来源。使用以下命令构建：

```bash
just build-flatpak
```

它会先运行一个 `[private]` 预备配方（`prepare-flatpak-vendor`），因此即使沙箱化构建本身是 `--offline`，首次运行仍需要网络访问：`cargo vendor --locked --versioned-dirs` 会从 crates.io 填充 `.flatpak-cache/cargo`。

它会被缓存到 `.flatpak-cache/` 下（由 `just clean` 清除），因此只有每次检出的首次构建才需要支付网络/从源码编译 OpenCV 的代价；预计首次构建耗时较长，因为 OpenCV 会在沙箱内从源码编译。

输出包：

- `dist/packages/com.gundulabs.Gaze-<arch>.flatpak`（例如 `com.gundulabs.Gaze-x86_64.flatpak`）
- `dist/packages/com.gundulabs.Gaze.flatpakref` 和 `.flatpakrepo`（只有在发布到真实仓库后才有意义；本地构建可忽略）

设置 `FLATPAK_GPG_SIGN=<key-id>` 以对仓库/包签名；本地构建可留空。

## 在没有 Linux 宿主机的情况下构建（Docker）

macOS 和 Windows 无法原生运行上述任何配方。`just docker <target>` 会在一个与 CI 工具链镜像一致的临时 Ubuntu 容器内运行相同的 `just` 目标（`packaging/docker/Dockerfile.build`），因此它适用于 `build-rust`、`build-flatpak`、`package <deb|rpm|archlinux>` 等，宿主机上无需本地 Rust/OpenCV/Flatpak 设置：

```bash
just docker build-rust
just docker build-flatpak
just docker package deb
```

宿主机的需求：

- Docker（或与 Docker 兼容的运行时；Colima 在 macOS 上可用）。
- 容器以 `--privileged` 运行，这是 `flatpak-builder` 的 ostree 后端所需要的。

注意：

- `just docker-image` 会构建（并缓存）构建镜像；`just docker <target>` 会在首次使用时自动构建它。
- Cargo 注册表、构建目标与 Flatpak 状态会在各次运行之间持久保存在命名的 Docker 卷中，因此重复构建不会重新下载 crate 或 GNOME SDK。
- 对于 `build-flatpak`，该配方会在目标首次运行时将 manifest 的 GNOME/Rust/LLVM 依赖安装到一个卷中。
- 如果你的检出位于 sshfs 支持的挂载上（例如位于外部/网络驱动器上的 Colima 虚拟机），Flatpak 的 ostree 仓库无法存活于该挂载上。包装脚本已将对 `flatpak-builder` 的 state/build/repo 目录重定向到虚拟机内的 Docker 卷，因此开箱即用。请勿将 `FLATPAK_STATE_DIR`/`FLATPAK_BUILD_DIR`/`FLATPAK_REPO_DIR` 重新覆盖回 bind 挂载。
- 产物会落到宿主机上的 `dist/` 中，与本地构建相同；当容器以 root 运行（原生 Docker）时，会重新归属到你的宿主机用户/组；在像 Colima 的 sshfs 这样的 uid 映射后端上，文件已属于你，因而原样保留。

## 清理构建产物

```bash
just clean
```
