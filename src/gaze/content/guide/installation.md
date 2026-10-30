<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# 安装

**最新中文版为 [v0.4.1-zh.2](https://github.com/zxaBinbina/gaze-zh/releases/tag/v0.4.1-zh.2)**（2026-10-30）：同步上游 GNOME 认证重试修复与 ONNX Runtime 1.31.1，安装包修订号从 `1` 升到 `2`。下载附件按发行版与 CPU 架构分为八份压缩包，每份保留七个独立组件。

## 中文版安装：一键命令（推荐）

```bash
curl -fsSL https://zxabinbina.cc.cd/projects/gaze/install.sh | sh
```

脚本根据系统版本与 CPU 架构匹配下载包，显示当前桌面，再展示安装菜单。**桌面检测只用于在对应选项旁标注「推荐」，最终由你选择**；无法识别桌面时也会展示相同菜单：

1. KDE Plasma：GUI + KDE 集成
2. GNOME：GUI + GNOME 扩展
3. Cinnamon：GUI + Cinnamon 扩展
4. Hyprland / Hyprlock：GUI + Hyprlock 集成
5. Omarchy：GUI + Omarchy 集成（需已有 Omarchy 环境）
6. 安装 GUI，不安装桌面集成
7. **不安装 GUI，仅安装命令行**

所有选项都包含 `gaze-zh` 主程序、命令行、守护进程与 PAM 模块。选择最后一项时，只安装核心包，不添加 `gaze-gui` 或桌面集成包。输入编号后，脚本校验压缩包与组件，再安装所选软件包。已有的 GUI 不会因选择命令行方案而被卸载。

当前支持 **Fedora 44/45、Ubuntu 24.04 的 x86_64 与 ARM64 系统**，以及 Linux Mint 22、openSUSE Tumbleweed 的 x86_64 系统。ARM64 / AArch64 与 x86_64 / amd64 分开打包，脚本依据本机架构选择。Fedora 44 x86_64 对应 `fedora-44-x86_64`，不会使用 Fedora 45 的包。Arch 的中文版提供手动下载包；其他系统请参考下方上游渠道。没有匹配包时，脚本停止并提供安装指南链接。

桌面变量缺失时，脚本从当前用户的图形登录会话读取桌面信息。普通 `curl … | sh` 调用直接显示菜单，并从终端读取选择，无需先运行其他命令。`--yes` 不会代选桌面；无人值守时通过 `--profile=kde/gnome/cinnamon/hyprlock/omarchy/gui/cli` 明确指定方案，例如仅安装命令行：

```bash
curl -fsSL https://zxabinbina.cc.cd/projects/gaze/install.sh | sh -s -- --profile=cli
```

可传入 `--no-pam` 跳过 PAM 配置。排查匹配问题时也可使用可选的 `--dry-run`；它只显示检测和匹配结果，不选择组件、不安装软件或改动 PAM：

```bash
curl -fsSL https://zxabinbina.cc.cd/projects/gaze/install.sh | sh -s -- --dry-run
```

## 中文版手动下载与升级

从 [v0.4.1-zh.2 发行页](https://github.com/zxaBinbina/gaze-zh/releases/tag/v0.4.1-zh.2) 选择以下一份，并下载同页的 `SHA256SUMS`：

| 系统 / 架构                         | 下载标识                     | 包格式         |
| ----------------------------------- | ---------------------------- | -------------- |
| Ubuntu 24.04 / Linux Mint 22，amd64 | `ubuntu-24.04-amd64`         | DEB            |
| Ubuntu 24.04，arm64                 | `ubuntu-24.04-arm64`         | DEB            |
| Fedora 44，x86_64                   | `fedora-44-x86_64`           | RPM            |
| Fedora 44，aarch64                  | `fedora-44-aarch64`          | RPM            |
| Fedora 45，aarch64                  | `fedora-45-aarch64`          | RPM            |
| Fedora 45，x86_64                   | `fedora-45-x86_64`           | RPM            |
| openSUSE Tumbleweed，x86_64         | `opensuse-tumbleweed-x86_64` | RPM            |
| Arch Linux，x86_64                  | `archlinux-x86_64`           | `.pkg.tar.zst` |

Fedora 与 openSUSE 的 RPM 使用不同依赖及 PAM 配置，请勿混用；Ubuntu 24.04 构建的 DEB 也不适用于所有 Debian/Ubuntu 版本。请按照构建环境选择，其他系统使用下面的上游渠道或自行构建。

下载后校验所选压缩包并解压，在解压目录中运行：

```bash
sha256sum -c SHA256SUMS
```

压缩包内的 `README.md` 提供具体命令。以 Fedora 44 x86_64 的压缩包为例，安装或升级主程序与图形界面：

```bash
sudo dnf install ./gaze-zh-0.4.1-2.x86_64.rpm ./gaze-gui-0.4.1-2.x86_64.rpm
```

若使用 KDE Plasma，再安装同一压缩包中的 `gaze-kde`；GNOME、Cinnamon、Hyprlock、Omarchy 各自选择对应组件。不要一次安装全部桌面组件。核心包与 GUI、桌面集成的文件不重复，合并下载附件后仍可按需安装与卸载。

### KRDP 修复范围

标准发行包保留中文提示与 PAM 层的 KRDP 登录兼容逻辑。Fedora 44 / KRDP 6.7.5 专用的私有画面冻结修复库属于单独的历史合并构建，**未包含在标准下载包中**。其源码、构建与回退说明见 [docs/krdp-fix.md](https://github.com/zxaBinbina/gaze-zh/blob/main/docs/krdp-fix.md)。

## CPU 要求

在 x86_64 上，`gazed` 守护进程要求 **AVX2**（Intel Haswell 及更新，大致自 2013 年起；AMD Excavator 及更新，大致自 2015 年起）。它所链接的 ONNX Runtime 在启动期间会发出 AVX2 指令，因此在较旧的 CPU 上，守护进程会立即退出，而不是以降级方式运行。

安装前检查：

```bash
grep -qw avx2 /proc/cpuinfo && echo "AVX2 present" || echo "AVX2 missing"
```

Gaze 的推理运行时在 x86_64 上需要 AVX2。如果你的 CPU 不支持，下方的上游一行命令安装器会在改动系统之前停止；软件包安装会让 `gazed` 处于停止状态，但 CLI 和 PAM 模块仍然安装。`gaze doctor` 也会报告这一限制。刷脸认证需要一个支持 AVX2 的 CPU；详见[故障排查](/projects/gaze/guide/troubleshooting)。

## 路径 A：一行命令安装器（其他发行版的官方渠道）

```bash
curl -fsSL https://gaze.gundulabs.com/install.sh | sh
```

安装器会添加：

- Gaze 守护进程与 CLI
- `gaze-gui`
- 仅在检测到 GNOME 桌面会话时才安装 GNOME Shell 扩展包
- 仅在检测到 Cinnamon 桌面会话时才安装 Cinnamon 扩展包

安装器还会在需要时配置软件包更新，并启用 `gazed` 守护进程。在受支持的情况下，它会为当前用户启用锁屏刷脸解锁或 PolKit 确认。

桌面集成取决于它所检测到的会话。在 KDE Plasma 上，它会安装 `gaze-kde` 来接入锁屏；在 Cinnamon 上，它会安装 `gaze-cinnamon-extension`。对于 Quickshell Omarchy，它会选择 `gaze-omarchy`；设置说明和支持的版本请参见 [Omarchy 指南](/projects/gaze/guide/omarchy)。其他桌面不会收到桌面扩展包。

在 Silverblue、Bazzite 和 Kinoite 等 OSTree 系统上，安装器使用 `rpm-ostree` 来分层安装软件包。在 openSUSE Tumbleweed 上，它使用 `zypper` 以及 Gaze 针对 Tumbleweed 的 RPM 仓库。

桌面行为：

- CLI、GUI 和普通的 PAM 提示在没有桌面扩展的情况下也能工作。
- 如果安装器检测到 Cinnamon，它会安装 `gaze-cinnamon-extension` 并为该会话启用它。
- 如果安装器检测到 KDE Plasma，它会随基础软件包一起安装 `gaze-kde`，这样锁屏会自行启动刷脸认证，并且系统设置中会出现一个 Gaze 页面。
- 在 Quickshell Omarchy 上，它会安装 Gaze 锁屏插件，并从已解锁的桌面用户会话中启用它。
- 如果你之后想要 GNOME 或 Cinnamon 锁屏支持，请从你的桌面会话中手动安装相应的扩展包。
- GDM 在扩展包安装好后从软件包默认值加载该扩展，但在你显式启用之前，GDM 登录刷脸认证保持禁用。

对于非交互式安装：

```bash
curl -fsSL https://gaze.gundulabs.com/install.sh | sh -s -- --yes
```

要安装但不向任何 PAM 栈添加 Gaze，请传入 `--no-pam`。安装器会将此选择记录在 `/etc/gaze/pam.optout` 中，只要该文件存在，软件包升级就不会改动 PAM。删除该文件并重新运行安装器，即可为 PAM 开启刷脸认证。

```bash
curl -fsSL https://gaze.gundulabs.com/install.sh | sh -s -- --no-pam
```

安装器以你的普通用户身份运行，并在需要时请求 `sudo`。以 root 身份运行时则不使用 `sudo`，但在 Arch 上例外，因为 AUR 辅助工具拒绝以 root 身份构建。在最后，它会检查守护进程是否正在运行、是否有 PAM 服务使用了 Gaze，并列出任何需要注意的事项，而不是报告成功。

在基于镜像的 Fedora（Silverblue、Kinoite、Bazzite）上，无法即时应用（live）的软件包会在重启后生效。安装器会暂存守护进程和 authselect 配置，使两者都在这次启动中完成。

## 路径 B：手动安装软件包

如果你更愿意自己配置软件包来源，请使用此方式。Debian/Ubuntu、Fedora 兼容系统以及 openSUSE Tumbleweed 使用 Gundu Labs 的仓库。Arch Linux 以及 Manjaro 和 CachyOS 等与 Arch 兼容的发行版使用 AUR 软件包。

Debian/Ubuntu 软件包是按发行版分别构建的，每个 apt 套件只携带该发行版的构建产物：`noble`（Ubuntu 24.04）、`questing`（Ubuntu 25.10）、`resolute`（Ubuntu 26.04）、`stonking`（Ubuntu 26.10）、`trixie`（Debian 13）和 `forky`（Debian 14）。下面的片段会选择与你的系统匹配的套件；安装其他发行版的软件包会导致 `gazed` 无法加载其 OpenCV 库。

Debian 14（forky）仍处于测试阶段，因此其库会不断变化。`forky` 软件包是针对发布时测试版所携带的 OpenCV 和 GTK soname 构建的，一旦测试版中发生 soname 变更，就可能导致 `gazed` 在下一次 Gaze 发布并针对新库重新构建之前无法启动。在这种 soname 变更之后，从 `forky` 套件重新安装即可获取重新构建的软件包。

如果你要替换现有的手动仓库配置，请先删除当前的仓库文件：

**Debian / Ubuntu：**

```bash
sudo rm -f /etc/apt/sources.list.d/gundulabs.list /usr/share/keyrings/gundulabs-archive-keyring.gpg
```

**Fedora 及兼容的 DNF/rpm-ostree 系统：**

```bash
sudo rm -f /etc/yum.repos.d/gundulabs.repo /etc/pki/rpm-gpg/RPM-GPG-KEY-gundulabs
```

**openSUSE Tumbleweed：**

```bash
sudo rm -f /etc/zypp/repos.d/gundulabs.repo /etc/pki/rpm-gpg/RPM-GPG-KEY-gundulabs
```

::: code-group

```bash [Debian/Ubuntu]
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://packages.gundulabs.com/keys/gundulabs-repo.gpg \
  | sudo tee /usr/share/keyrings/gundulabs-archive-keyring.gpg >/dev/null
suite="$(. /etc/os-release && echo "${VERSION_CODENAME:-$UBUNTU_CODENAME}")"
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gundulabs-archive-keyring.gpg] https://packages.gundulabs.com/deb $suite main" \
  | sudo tee /etc/apt/sources.list.d/gundulabs.list >/dev/null
sudo apt update
sudo apt install gaze gaze-gui
```

```bash [Fedora 及兼容发行版]
sudo rpm --import https://packages.gundulabs.com/keys/gundulabs-repo.asc
sudo tee /etc/yum.repos.d/gundulabs.repo >/dev/null <<'EOF'
[gundulabs]
name=Gundu Labs
baseurl=https://packages.gundulabs.com/rpm/fedora/$releasever/$basearch
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.gundulabs.com/keys/gundulabs-repo.asc
EOF
sudo dnf makecache
sudo dnf install gaze gaze-gui
```

```bash [Fedora OSTree (Silverblue / Bazzite / Kinoite)]
sudo tee /etc/yum.repos.d/gundulabs.repo >/dev/null <<'EOF'
[gundulabs]
name=Gundu Labs
baseurl=https://packages.gundulabs.com/rpm/fedora/$releasever/$basearch
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.gundulabs.com/keys/gundulabs-repo.asc
EOF
sudo rpm-ostree install gaze gaze-gui
```

```bash [通过 Copr 的 Fedora]
# 上面 Gundu Labs dnf 仓库的替代方案；请勿同时启用两者。
# Copr 在 Fedora 自己的构建器上构建并签署这些软件包。
sudo dnf install dnf-plugins-core
sudo dnf copr enable @gundulabs/gaze
sudo dnf install gaze gaze-gui
```

```bash [openSUSE Tumbleweed]
sudo rpm --import https://packages.gundulabs.com/keys/gundulabs-repo.asc
sudo tee /etc/zypp/repos.d/gundulabs.repo >/dev/null <<'EOF'
[gundulabs]
name=Gundu Labs
baseurl=https://packages.gundulabs.com/rpm/opensuse/tumbleweed/$basearch
enabled=1
autorefresh=1
type=rpm-md
gpgcheck=1
gpgkey=https://packages.gundulabs.com/keys/gundulabs-repo.asc
EOF
sudo zypper refresh
sudo zypper install gaze gaze-gui
```

```bash [Arch Linux / Manjaro / CachyOS]
# 需要像 yay 或 paru 这样的 AUR 辅助工具。此处以 yay 为例。
yay -S --needed gaze-bin gaze-gui-bin
```

:::

openSUSE 的 RPM 附带一个 `pam-config` 定义，并在其安装后脚本中为 `sudo`、GDM 以及其他包含 `common-auth` 的服务启用 Gaze。要在更改 PAM 模块后手动重新应用该设置，请运行：

```bash
sudo pam-config --add --gaze
sudo pam-config --update
```

一行命令安装器也会在软件包安装完成后，在 `pam-config` 可用时重新应用此设置。

::: warning Arch：请安装 `-bin` 软件包，而非发布产物
在 Arch 上，请仅通过上述 AUR 软件包安装 Gaze。每个 GitHub 发布附带的
`gaze-*.pkg.tar.zst` 文件是 AUR 封装器解包所用的输入，而不是受支持的
安装途径：它们携带的是普通包名 `gaze` 和 `gaze-gui`，并且还有一个无关的
AUR 软件包也叫 `gaze`（一个文件监视器）。用 `pacman -U` 安装它们会留下一个
外来（foreign）的 `gaze`，下一次 `yay -Syu` 或 `paru -Syu` 会悄悄将其
“升级”为那个无关的软件包，从而移除 `gazed`、PAM 模块以及 systemd 单元。
如果这已经发生在你身上，请参见[在 AUR 辅助工具升级后 Gaze 消失了](/projects/gaze/guide/troubleshooting#gaze-disappears-after-an-aur-helper-upgrade-arch-linux)。
:::

## 路径 C：仅通过 Flatpak 的 GUI

Flatpak 发布于 Gundu Labs 仓库。`flatpakref` 中内嵌了签名密钥和仓库 URL，因此一条命令即可添加该远程仓库并安装应用：

```bash
flatpak install --from https://packages.gundulabs.com/flatpak/com.gundulabs.Gaze.flatpakref
```

这只安装沙箱化的 Gaze GUI。它通过系统总线与 `gazed` 守护进程通信，因此你仍然需要安装其中一个系统软件包（路径 A 或 B）来提供守护进程和 PAM 集成。当你希望 GUI 独立于系统软件包更新时，请使用此路径。

### 手动安装后启用 GNOME 锁屏认证

仅在你需要锁屏刷脸解锁的 GNOME 桌面上运行此步骤。首先为你所在的发行版安装扩展包，然后为你的用户启用它；软件包管理器无法安全地更改每用户扩展设置。

::: code-group

```bash [Debian/Ubuntu]
sudo apt install gaze-gnome-extension
```

```bash [Fedora 及兼容发行版]
sudo dnf install gaze-gnome-extension
```

```bash [openSUSE Tumbleweed]
sudo zypper install gaze-gnome-extension
```

```bash [Arch Linux / Manjaro / CachyOS]
yay -S --needed gaze-gnome-extension-bin
```

:::

```bash
gnome-extensions enable gaze@gundulabs.com
gsettings set org.gnome.shell.extensions.gaze enable-face-authentication true
```

如果在安装或更新扩展后锁屏没有立即识别它，请重启一次。请从**在**软件包安装之后才启动的会话中运行上面的两条命令：GNOME Shell 会丢弃它尚未扫描的扩展 ID，因此从你安装的那个会话中启用扩展，可能看起来正常，却在下次注销后消失。参见[扩展在注销后又一次消失](/projects/gaze/guide/gnome#the-extension-disappears-again-after-a-logout)。

GDM 登录刷脸认证在你显式启用之前保持禁用；在此之前请参见 [GNOME 扩展指南](/projects/gaze/guide/gnome)。

### KDE Plasma 及其他基于 PAM 的桌面

一行命令安装器会检测到 KDE Plasma，并有意跳过 `gaze-gnome-extension`，因为该包依赖于 GNOME Shell。它会改为安装 `gaze-kde`，使 KDE **锁屏**无需按键即可自行启动刷脸认证，并向系统设置添加一个 Gaze 页面。在测试期间请保持密码回退启用。

KDE **登录管理器**（Plasma Login Manager，或 SDDM）是一个独立的程序，上游并未为其提供前置的生物识别槽位，因此那里的刷脸认证在你提交登录表单时开始，正如同一屏幕上的指纹读取器一样。参见 [KDE Plasma 指南](/projects/gaze/guide/kde#login-greeter)。

对于其他基于 PAM 的桌面，请使用基础 `gaze` 软件包的 PAM 模块，并参见 [PAM 指南](/projects/gaze/guide/pam)。

### Omarchy Quickshell 锁屏

请使用 [Omarchy 指南](/projects/gaze/guide/omarchy)。`gaze-omarchy` 软件包提供独立的刷脸、密码和指纹 PAM 对话。安装后，从你已解锁的桌面中不带 sudo 地运行 `gaze-omarchy enable`。它支持 Omarchy 4.0.2/4.0.3，并在启用前检查 shell 文件。

### 为 hyprlock 启用刷脸解锁

在使用 hyprlock 的 Hyprland 上，请安装 `gaze-hyprlock` 软件包（在检测到 Hyprland 时会由一行命令安装器自动安装），并将 hyprlock 指向 Gaze 的 PAM 服务。参见 [Hyprland 指南](/projects/gaze/guide/hyprland)。

## 路径 D：Nix 与 NixOS

Gaze 附带一个 Nix flake，其中包含软件包，以及一个以声明式方式设置守护进程、D-Bus/polkit 策略和 PAM 的 NixOS 模块：

```nix
# flake.nix inputs
inputs.gaze.url = "github:zxaBinbina/gaze-zh";
```

```nix
# NixOS configuration
imports = [ inputs.gaze.nixosModules.default ];
services.gaze = {
  enable = true;
  gui.enable = true;
};
```

在没有 NixOS 但装有 Nix 或 home-manager 的系统上，你可以从 flake 安装 CLI 和 GUI，但守护进程和 PAM 集成仍然需要一个系统软件包（路径 A 或 B）。有关模块选项、GNOME/hyprlock 集成以及 home-manager 用法，请参见 [Nix 与 NixOS 指南](/projects/gaze/guide/nixos)。

## 安装后重启

无论通过哪种方式安装 Gaze，请重启一次以应用所有系统级更改。

```bash
sudo reboot
```

## 验证安装

```bash
systemctl status gazed
gaze --version
gaze doctor
gaze-gui --help
```

请以你的桌面用户身份运行 `gaze doctor`。这样它才能检查你的 PipeWire 会话和桌面集成情况。

如果守护进程处于非活跃状态，请用以下命令启动并启用它：

```bash
sudo systemctl enable --now gazed
```

## 首次运行

```bash
gaze add-face default
gaze auth --verbose
```

## 开发版与源码构建

有关源码构建、测试、打包以及 Flatpak 开发工作流，请参见[开发指南](/projects/gaze/guide/development)。
