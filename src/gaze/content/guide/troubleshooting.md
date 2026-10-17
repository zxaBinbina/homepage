<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# 故障排查

如果 Gaze 已安装但认证不稳定，请将本页作为快速诊断清单使用。

从本地图形会话开始：

```bash
gaze doctor
```

它会在不捕获相机帧、也不更改系统的情况下，检查服务、配置、DBus、PipeWire 相机可见性、登记状态、PAM 设置、桌面集成以及 TPM 要求。请遵循每条警告或错误下方打印的建议修复方法。带有错误的结果会以状态 `1` 退出，这也使该命令适用于支持脚本。

每行都标有它所发现的内容：

| 标记 | 含义 |
|---|---|
| `✓` | 正常工作。 |
| `○` | 你已关闭的可选功能，例如 GDM 登录人脸认证。其下方变暗的一行是开启它的方法。已禁用的模板加密会作为警告报告，因为模板是以明文存储的。 |
| `!` | 警告：Gaze 仍可工作，但某些方面降级或未接好。 |
| `✗` | 错误：这部分在你修复之前无法工作。`gaze doctor` 退出 `1`。 |

如果某次尝试结束得比你预期的早，或者你想知道某条消息来自哪个截止时间，[一次认证尝试](/projects/gaze/guide/how-it-works#one-authentication-attempt)会逐步讲解整个流程，而[超时与预算](/projects/gaze/guide/how-it-works#timeouts-and-budgets)列出了每个截止时间及其产生的日志行。

## 1. 守护进程未运行

检查守护进程：

```bash
systemctl status gazed
```

如果输出显示 `active (running)`，这部分就没问题。

要启动并启用服务，运行：

```bash
sudo systemctl enable --now gazed
```

如果仍然失败：

```bash
journalctl -u gazed -n 200 --no-pager
```

该命令显示最近的守护进程日志消息。

### 启用模板加密时守护进程退出

如果 `gazed` 拒绝启动，且日志显示类似 *"template encryption is enabled ([storage] encrypt_templates) but no usable TPM is available"* 的消息，守护进程是有意失败关闭的。对于新建或省略的存储设置，加密默认启用；它不会悄悄以未加密方式存储生物识别数据。

```bash
journalctl -u gazed -n 50 --no-pager
```

用以下两种方式之一修复：

- 启用 TPM。确认存在 TPM 2.0 设备（`ls /dev/tpmrm0`）并在你的固件/BIOS 中开启，然后重启：`sudo systemctl restart gazed`。
- 关闭该功能。在 `/etc/gaze/config.toml` 的 `[storage]` 下设置 `encrypt_templates = false` 并重启。

如果日志改为显示 *"Failed to open specified TCTI device file /dev/tpmrm0: Permission denied"*，说明设备存在但守护进程可能无法打开它。发行版将 TPM 节点限制为 `tss` 用户与组，因此 `gazed` 需要 `CAP_DAC_OVERRIDE`（打包的 unit 文件已授予）或属于该组。检查节点与 unit 文件：

```bash
ls -l /dev/tpmrm0 /dev/tpm0
systemctl show gazed -p CapabilityBoundingSet -p SupplementaryGroups
```

如果本地覆盖项或 drop-in 收紧了 `CapabilityBoundingSet`，请改为添加 `SupplementaryGroups=tss`：

```bash
sudo systemctl edit gazed   # [Service] / SupplementaryGroups=tss
sudo systemctl restart gazed
```

如果你在登记后重置/清除了 TPM，之前封存的密钥将无法再被解封。删除过期的密钥目录并重新登记你的人脸：

```bash
sudo systemctl stop gazed
# 破坏性操作：仅在确认 TPM 已重置并备份你所需的任何状态之后执行。
# 没有原始 TPM 密钥，旧的加密模板无法恢复。
sudo rm -rf /var/lib/gaze/tpm /var/lib/gaze/users
sudo systemctl start gazed
```

### 升级后旧版模板或不完整的 TPM 密钥错误

如果日志提到 `unbound or plaintext templates require explicit migration` 或 `legacy unbound templates require explicit migration`，请停止守护进程并运行[模板维护流程](/projects/gaze/guide/configuration#upgrade-legacy-encrypted-templates)。这也适用于被中断的旧迁移遗留的混合存储。不要简单地不断重试启动：明文与旧版密文被刻意设计为不会自动校验或重新绑定。如果存储的账户归属无法被信任，请改为重新登记。

如果日志提到 `incomplete legacy TPM key pair`，请从受保护的备份中恢复缺失的 `dek.pub` 或 `dek.priv`。不要删除幸存的文件来绕过错误；新密钥无法解密现有模板。无效的 `dek.blob` 同样是一个错误，并且永远不会触发回退到旧版文件。

`template storage needs recovery` 错误意味着存储/配置回滚失败。该守护进程中的匹配与写入被禁用。请停止它，保留 `/var/lib/gaze` 的受保护副本（包括任何 `.gaze-recode-users-*` 同级存储），检查磁盘空间与文件系统错误，然后重启。活动的 `users` 目录是一个完整存储。启动时会移除被遗弃的暂存副本，并根据配置设置校验活动格式的合法性。如果在发布明文之后、保存禁用加密请求之前发生了崩溃，仍启用的设置会拒绝该明文；请校验活动存储的归属并运行上面的显式维护迁移。它在重启时不会被悄悄信任。在整个恢复过程中请保持密码登录可用。

### 守护进程加载共享库失败："error while loading shared libraries: libopencv_*"（Arch Linux）

在 Arch Linux 及兼容发行版上，将 OpenCV 提升到新的次版本（例如 4.13 到 5.0）的系统更新会移除 `gazed` 构建时所依赖的库版本，守护进程会立即以状态 127 退出。请更新到针对新 OpenCV 构建的 `gaze-bin` 版本：

```bash
yay -Syu gaze-bin
```

较新的软件包声明了带版本上限的 `opencv` 依赖，因此 pacman 会在一开始就拒绝 OpenCV 升级，而不是破坏已安装的守护进程。如果 pacman 报告升级 `opencv` 会破坏依赖且尚无更新的 `gaze-bin`，请等待重建版本发布后再升级，或者针对新 OpenCV 从源码构建并安装 Gaze。

### AUR 助手升级后 Gaze 消失（Arch Linux）

如果人脸认证在各个界面同时停止工作（sudo、polkit、锁屏、greetd），且 `systemctl status gazed` 报告该 unit 不存在，请检查是否有 AUR 助手用无关软件包替换了 Gaze：

```bash
pacman -Qi gaze 2>/dev/null | head -n 3
ls /usr/lib/security/pam_gaze.so
```

一个名为 `gaze` 的无关 AUR 软件包（一个文件监视器，目前版本号高得多）也存在。如果 Gaze 是以普通名称 `gaze` 与 `gaze-gui` 安装的，例如通过对 GitHub 发布附带的 `.pkg.tar.zst` 文件运行 `pacman -U`，pacman 会将其记录为外部软件包，而 `yay -Syu` 或 `paru -Syu` 会把无关的 AUR `gaze` 当作更新版本安装到我们的包之上。这会移除 `gazed`、两个 PAM 模块以及 systemd unit，并把 `/etc/gaze/config.toml` 变成 `.pacsave` 文件。

该故障是静默的：那些 `sufficient` 的 PAM 行无法加载缺失的模块，记录 `PAM adding faulty module: pam_gaze.so`，每个界面都回退到指纹或密码。

通过移除错误的软件包并重新安装 AUR 软件包来恢复。已登记的模板位于 `/var/lib/gaze` 中，会在该操作中幸存：

```bash
sudo pacman -Rns gaze gaze-gui
yay -S --needed gaze-bin gaze-gui-bin
sudo systemctl enable --now gazed
```

如果 `/etc/gaze/config.toml.pacsave` 存在，请从中恢复你的设置。AUR 软件包以 `gaze-bin` 与 `gaze-gui-bin` 名称安装，不会发生冲突，因此一旦切换到它们，这种情况就不会再发生。

### 守护进程加载共享库失败："error while loading shared libraries: libopencv_*"（Debian/Ubuntu）

```
gazed: error while loading shared libraries: libopencv_core.so.406:
cannot open shared object file: No such file or directory
```

每个 Debian/Ubuntu 发行版附带的 OpenCV soversion 都不同（24.04 为 4.6，26.04 为 4.10），因此这意味着已安装的软件包是针对另一个发行版构建的。检查你拥有哪个版本，以及 apt 指向哪个套件：

```bash
dpkg-query -W -f='${Version}\n' gaze
grep gundulabs /etc/apt/sources.list.d/gundulabs.list
```

版本后缀（`1~ubuntu24.04`、`1~ubuntu25.10`、`1~ubuntu26.04`、`1~ubuntu26.10`、`1~debian13`、`1~debian14`）必须与你的发行版匹配。将 apt 指向你发行版的套件并重新安装：

```bash
suite="$(. /etc/os-release && echo "${VERSION_CODENAME:-$UBUNTU_CODENAME}")"
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gundulabs-archive-keyring.gpg] https://packages.gundulabs.com/deb $suite main" \
  | sudo tee /etc/apt/sources.list.d/gundulabs.list >/dev/null
sudo apt update
sudo apt install --reinstall gaze gaze-gui
sudo systemctl restart gazed
```

避免将较新的 OpenCV 库符号链接到缺失的 soname。soname 改变是因为 C++ ABI 变了，因此守护进程可能启动，但之后会崩溃或破坏数据。

## 2. 相机未被检测到

首先检查 Gaze 运行时加载的 GStreamer 插件是否已安装。它们是动态加载的，因此缺失的插件会表现为 `no element "jpegdec"`、`no element "v4l2src"` 或 `no element "pipewiresrc"`，而不是链接错误：

```bash
gaze doctor
```

如果 `GStreamer plugins` 检查失败，请为你的发行版安装 base、good 与 PipeWire 插件包：

::: code-group

```bash [Debian/Ubuntu]
sudo apt install gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-pipewire
```

```bash [Fedora/RHEL]
sudo dnf install gstreamer1-plugins-base gstreamer1-plugins-good pipewire-gstreamer
```

```bash [openSUSE Tumbleweed]
sudo zypper install gstreamer-plugins-base gstreamer-plugins-good gstreamer-plugin-pipewire
```

```bash [Arch Linux / Manjaro]
sudo pacman -S gst-plugins-base gst-plugins-good gst-plugin-pipewire
```

:::

然后用 `sudo systemctl restart gazed` 重启守护进程。

作为第一步，尝试主 GStreamer 相机来源：

```toml
[cameras]
rgb = "primary"
```

如果你需要特定相机，运行 `gaze config` 并选择某个检测到的 PipeWire 相机，或者手动设置 GStreamer 来源：

```toml
[cameras]
rgb = "pipewiresrc target-object=<pipewire-target>"
```

你也可以将 `rgb` 直接指向一个相机，使用 `/dev/video*` 节点或 `usb:VVVV:PPPP` id，它们会直接指定内核节点。

对于认证，守护进程始终直接捕获内核 `/dev/video*` 节点，永远不需要 PipeWire 会话，即使在 GDM 登录界面上也是如此。`rgb = "primary"` 表示第一个彩色节点；如果选错了相机，请将 `rgb` 设置为特定的 `/dev/video*` 节点或 `usb:VVVV:PPPP` id。`pipewiresrc target-object=` 的值会解析为该同一相机背后的 V4L2 节点。

### Intel IPU6/IPU7 MIPI 相机（`does not support ... colorimetry`）

许多近年的 Intel 笔记本（Meteor Lake、Lunar Lake 等）在 Intel IPU 之后使用 MIPI 相机。其 `/dev/video*` 节点是原始捕获节点，只有在 libcamera 配置好相机后才会出流，因此直接打开它会失败，并出现类似 `Device '/dev/video0' does not support 2:0:0:0 colorimetry` 的错误。

在 `rgb = "primary"` 下，当它选中的彩色节点只能经由 libcamera 驱动，或没有任何彩色节点可见时，Gaze 会回退到 libcamera。守护进程自行运行 libcamera，永远不会使用用户的 PipeWire 会话。请安装 libcamera GStreamer 插件并重启守护进程：

::: code-group

```bash [Debian/Ubuntu]
sudo apt install gstreamer1.0-libcamera
```

```bash [Fedora/RHEL]
sudo dnf install libcamera-gstreamer
```

```bash [openSUSE Tumbleweed]
sudo zypper install gstreamer-plugins-libcamera
```

```bash [Arch Linux / Manjaro]
sudo pacman -S libcamera gst-plugin-libcamera
```

:::

如果 `gaze auth` 报告 `libcamera fallback also failed` 且 `reason not-negotiated`，而守护进程日志显示来自 libcamera 的 `Failed to fork: Function not implemented`，说明你的 libcamera 构建附带的 IPA 模块签名无法校验。libcamera 随后会尝试在独立的沙箱进程中运行它们，而这被守护进程的加固所阻止，并且没有其软件 ISP，相机只提供原始帧。在 Fedora 44 上，此问题已在 `libcamera-0.7.1-2.fc44` 及更高版本中修复。在该版本进入稳定仓库之前，请从 updates-testing 安装：

```bash
journalctl -u gazed -b | grep -i 'failed to fork'
sudo dnf upgrade --enablerepo=updates-testing --refresh 'libcamera*'
```

重启守护进程以应用相机变更：

```bash
sudo systemctl restart gazed
```

## 3. 登记正常，但认证经常失败

请尝试以下顺序：

1. 在配置中保持 `level = "medium"`。
2. 改善样本覆盖：

```bash
gaze refine-face default
```

3. 测试分数：

```bash
gaze auth --verbose
```

4. 为常见变化添加第二个档案：

```bash
gaze add-face glasses
```

如果相似度分数在带有宽屏（16:9）相机的机器上升级 Gaze 后立即下降，请重新登记一次人脸：较旧的版本将宽屏帧拉伸为 4:3，因此在修复前登记的模板对未失真的帧匹配效果不如新登记的模板。

### `gaze auth --verbose` 显示分数通过但仍然失败

一个越过相似度阈值的人脸只是判定的一半：反欺诈检查也必须通过。当未通过时，运行以

```
Face matched, but the liveness check did not pass.
```

结束，且 `journalctl -u gazed -b` 会记录带有 `matched=true` 的 `VerifyStart: frame budget spent`。在扫描期间轻微移动、提高你面部的光照，或者如果你的相机分数持续低于阈值，则降低 `/etc/gaze/config.toml` 中的 `liveness.threshold`：

```toml
[liveness]
threshold = 0.7
```

在同一节中设置 `enabled = false` 会完全关闭反欺诈模型，代价是接受一张照片。

### 认证中止并提示 "IR camera stream stopped unexpectedly"

一些单功能 Windows Hello 网络摄像头无法同时流式传输其 RGB 与 IR 传感器。Logitech BRIO 4K（`046d:085e`，不是使用不同产品 ID 的较新 Brio 300/500/100）就是一个已知例子。登记工作正常，但并行捕获 RGB 与 IR 会丢弃 IR 子流，本次尝试回退到你的密码。

Gaze 默认一次只捕获一个相机，因此首先检查是否设置了 `cameras.parallel_capture`：

```bash
gaze config --show | grep parallel_capture
```

如果它是 `always`，请将其设置为 `auto`（会串行化传感器共享同一硬件功能的相机）或 `never`。如果你在 `never` 下看到此情况，说明这两个传感器即使顺序进行也无法共存。单独配置 IR 相机，并将 `rgb` 留空，以便 Gaze 仅运行 IR：

```toml
[cameras]
rgb = ""
ir = "/dev/video2"
emitter_enabled = true
```

## 4. 锁屏未触发人脸认证

### GNOME

从你的 GNOME 会话启用或重新启用扩展：

```bash
gnome-extensions enable gaze@gundulabs.com
gsettings set org.gnome.shell.extensions.gaze enable-face-authentication true
```

如果 `gnome-extensions enable` 报告 `Extension "gaze@gundulabs.com" does not exist`，说明 GNOME Shell 尚未拾取新安装的扩展。请重启，然后重新运行该命令。在 Wayland 上这是唯一方式；Shell 不会在运行中的会话里重新扫描扩展。一行式安装程序通过直接写入等效的 dconf 键来规避此问题，这些键在下次登录时生效，而无需 `gnome-extensions enable` 成功。

对于 GDM 登录，如果人脸认证文本出现了但相机灯从未亮起，请检查守护进程日志中的相机/PipeWire 错误：

```bash
journalctl -u gazed -b
```

较旧的 Gaze 构建可能会在所选用户的 PipeWire 运行时存在之前就尝试使用它。如果你看到此行为，请更新 Gaze。

#### GDM 完全不显示人脸认证，且其日志毫无记录

与下面的 SELinux 情况不同：在那里提示会出现且相机保持黑暗，而在这里登录界面上没有任何关于人脸认证的内容出现，且欢迎界面不记录任何内容，同时锁屏、`sudo` 与 `gaze auth` 都正常工作。

欢迎界面开启了 GNOME Shell 的扩展终止开关，这会停止那里的每个扩展，无论是什么启用了它们：

```bash
sudo env DCONF_PROFILE=gdm XDG_CONFIG_HOME=/var/lib/gdm/seat0/config \
  gsettings get org.gnome.shell disable-user-extensions
```

如果输出为 `true`，说明该值位于 GDM 自己的 dconf 数据库中。该数据库是欢迎界面配置文件中唯一比 Gaze 安装在 `/etc/dconf/db/gdm.d` 下的键文件优先级更高的层，因此在那里添加覆盖项无济于事。请在源头清除它并重启：

```bash
sudo rm -f /var/lib/gdm/seat0/config/dconf/user
sudo reboot
```

GDM 会再次以自己的默认值写入该文件。该路径在 Debian 与 Ubuntu 上位于 `/var/lib/gdm3` 下，而多席位机器上每个席位各有一个目录。`gaze doctor` 将此报告为 **GDM 登录人脸认证**，并会给出确切的文件名。

#### GDM 在 Fedora 或启用了 SELinux 的系统上从不扫描

如果人脸认证在你的桌面会话中工作（`sudo`、锁屏、`gaze auth`），但 GDM 登录界面从不打开相机，SELinux 可能正在拒绝欢迎界面访问相机设备。Gaze 为此附带了一个策略模块，扩展包会在安装时加载它，但该步骤无法让软件包事务失败，因此被拒绝的策略除了欢迎界面静默不扫描之外不会留下任何痕迹。2025 年初以来制作的 Fedora 与 openSUSE Tumbleweed 安装在默认情况下强制执行 SELinux；较旧的 openSUSE 安装使用 AppArmor，该检查不适用于这种情况。

`gaze doctor` 将此报告为 **GDM camera SELinux policy**，但仅在 `sudo` 下：读取已加载模块列表需要 root，因此普通的 `gaze doctor` 会说该检查无法运行，而不是说明模块是否存在。要手动检查：

```bash
sudo semodule -l | grep gaze-gdm-camera
sudo ausearch -m avc -ts today | grep xdm_t
```

如果模块未列出，请加载它并重启：

```bash
sudo semodule -i /usr/share/gaze/gaze-gdm-camera.pp
sudo reboot
```

#### 在 SELinux 系统上密钥环解锁从未发生

如果 GDM 或锁屏人脸登录一直工作，直到你启用 `unlock_gnome_keyring`（或 `unlock_kwallet`），然后每次尝试都以 "Keyring unlock unavailable. Enter your password." 结束，说明欢迎界面的 PAM worker 被拒绝了交接所需的内容。它以 `xdm_t` 受限运行，且发行版策略将其对 `/etc/shadow` 的读取隐藏在 `dontaudit` 规则之后，因此在 `ausearch` 中不会出现任何内容。Gaze 为此附带了第二个策略模块，`gaze keyring` 在登记凭据后会加载它；`sudo gaze doctor` 将其报告为 **Keyring SELinux policy**。该 worker 也会记录失败的步骤：

```bash
sudo journalctl -b -g 'pam_gaze:'
sudo semodule -l | grep gaze-greeter-keyring
```

如果模块未列出，请加载它并重试人脸登录：

```bash
sudo semodule -i /usr/share/gaze/gaze-greeter-keyring.pp
```

### Cinnamon

从你的 Cinnamon 会话检查扩展是否已启用：

```bash
gsettings get org.cinnamon enabled-extensions | grep gaze@gundulabs.com
```

如果缺失，请从 **System Settings → Extensions** 启用，或使用 [Cinnamon 扩展指南](/projects/gaze/guide/cinnamon#enable-the-extension)中的命令，然后重新加载 Cinnamon（`Alt + F2`、`r`、回车）。

在使用独立 `cinnamon-screensaver` 的 X11 会话（Linux Mint 22.x 及类似系统）上，锁屏通过 `/etc/pam.d/cinnamon-screensaver` 而非扩展进行认证。那里的人脸解锁需要 `pam_gaze.so` 位于该服务或共享 auth 栈中，并且它无法显示确认按钮，因此 `require_confirmation_lock_screen = true` 在该界面上不被强制执行。参见[锁屏行为](/projects/gaze/guide/cinnamon#lock-screen-behavior)。

### KDE Plasma

检查 `gaze doctor` 中的 "KDE lock screen" 行，然后：

```bash
sudo gaze-kde-pam enable
gaze-kde-pam status
```

锁屏只有在 `/etc/pam.d/kde-fingerprint` 运行 `pam_gaze.so` 时才会自行启动人脸认证。没有它，KScreenLocker 就没有可启动的生物识别槽位，人脸认证会一直等到你提交密码字段。

如果 `gaze doctor` 警告该槽位以 simultaneous 模式运行 `pam_gaze.so`，请将其替换为不带 `simultaneous` 的普通模块：simultaneous 模式会等待欢迎界面永远无法回答的密码提示，从而让该槽位在剩余锁屏期间卡住。

在**登录欢迎界面**（Plasma Login Manager 或 SDDM）上，人脸认证是选择启用的，并且除非欢迎界面提供前置的生物识别服务，否则只在提交登录表单时启动：在密码字段为空时按回车，就像你在那里对指纹读取器所做的那样。参见 [KDE Plasma 指南](/projects/gaze/guide/kde)。

### Omarchy

检查 `gaze doctor` 中的 "Omarchy lock" 行，然后从你已解锁的桌面：

```bash
gaze-omarchy doctor
gaze-omarchy enable
```

`gaze-omarchy doctor` 会报告缺失的是哪一部分：主机兼容性、`/etc/pam.d/gaze-omarchy-face` 服务、登记状态，还是正在运行的锁屏插件。在 Omarchy 更新更改 shell 文件后，人脸扫描会停止，直到 `gaze-omarchy` 被更新。参见 [Omarchy 指南](/projects/gaze/guide/omarchy)。

## 5. PAM 认证流程似乎损坏

重新安装软件包（推荐）：

```bash
curl -fsSL https://gaze.gundulabs.com/install.sh | sh
```

这会重新应用由软件包管理的 PAM 集成。

### Bitwarden 浏览器扩展从不启动人脸认证

Bitwarden 浏览器解锁是间接到达 Gaze 的：扩展通过原生消息与 Bitwarden 桌面应用通信，而桌面应用请求 Polkit 授权。首先验证 `polkit-1` 的 PAM 路径会启动 Gaze：

```bash
gaze doctor
pkexec /usr/bin/true
```

如果这能工作，但点击扩展中的 **Unlock with biometrics** 没有打开任何 Polkit 提示，请排查 Bitwarden 桌面应用与原生消息连接，而不是添加另一条 PAM 规则。如果 Polkit 测试未使用 Gaze，请修复发行版特定的 `polkit-1` 设置。完整的设置与诊断划分参见[通过 Polkit 的浏览器扩展](/projects/gaze/guide/pam#browser-extensions-through-polkit-bitwarden)。

### 启用 Gaze 后另一项服务停止认证（dovecot、sshd、cron）

症状出现在该服务自己的日志中，而不是 Gaze 的。通过 `pam-auth-update` 启用 Gaze 配置文件会把模块放入 `common-auth`，而几乎每个服务都包含它，因此模块中的问题会波及与人脸认证无关的服务。对于 dovecot，IMAP 登录失败，且 `mail.log` 显示两种模式之一。

auth worker 在模块加载时崩溃：

```
dovecot: auth-worker: Error: OpenBLAS error: Memory allocation still failed after 10 retries, giving up.
dovecot: auth-worker: Error: Unexpected exit - converting to abort
dovecot: auth: Error: auth-worker: Aborted PASSV request for user: Worker process died unexpectedly
dovecot: imap-login: Login aborted: Connection closed (auth service reported temporary failure)
```

较旧的软件包将 OpenCV 链接进了 `pam_gaze.so`。在 Debian 与 Ubuntu 上，OpenCV 会引入 OpenBLAS，其启动代码会预留按每个 CPU 核心大小分配、供每线程使用的内存。限制自身地址空间的服务（如 dovecot 的 auth worker，默认 256 MB）无法满足该预留，并在任何 Gaze 代码运行前中止。确认模块不再链接它：

```bash
objdump -p /usr/lib/security/pam_gaze.so | grep NEEDED
```

除 libc、libgcc、libm 与动态加载器外，不应出现其他内容。

或者 auth worker 停滞，直到 dovecot 放弃它：

```
dovecot: auth: Error: auth-worker: Aborted PASSV request for user: Lookup timed out
```

较旧的软件包会在每次成功的密码登录（包括网络登录）后清压强制度锁定，方法是在服务自身进程内启动线程池与 D-Bus 调用。当前的软件包在任何工作之前就完全跳过网络服务与远程调用方。

两者在当前软件包中都已修复，因此请更新：

```bash
curl -fsSL https://gaze.gundulabs.com/install.sh | sh
```

要在更新前恢复邮件服务，请用 `sudo pam-auth-update --disable gaze gaze-simultaneous` 在共享栈中禁用 Gaze。

## 6. 首次运行较慢

首次认证可能需要稍长一点时间，因为 Gaze 要下载模型。之后的尝试应该会更快。

## 7. 验证已安装的版本与二进制文件

```bash
gaze --version
which gaze
which gaze-gui
```

这些命令的作用：

- `gaze --version`：确认 CLI 已安装
- `which gaze`：显示 CLI 二进制文件的位置
- `which gaze-gui`：显示 GUI 二进制文件的位置

## 8. 软件包仓库未加载或签名不匹配

如果你在运行 `apt update`、`dnf makecache` 或 `zypper refresh` 时看到诸如仓库连接失败、元数据哈希不匹配或仓库 GPG 签名失败等错误，请从[安装指南](/projects/gaze/guide/installation)重新安装当前的软件包源配置。在 openSUSE Tumbleweed 上，确认仓库 URL 是 Tumbleweed 仓库且其架构为 `x86_64`；Fedora 仓库与 Tumbleweed 的滚动库 ABI 不兼容。

## 9. PAM 模块在 Ubuntu 26.04+ 上加载失败

如果 `journalctl` 显示类似以下行：

```
PAM unable to dlopen(pam_gaze.so): /usr/lib/security/pam_gaze.so: cannot open shared object file
PAM adding faulty module: pam_gaze.so
```

说明你安装的软件包早于 Ubuntu 26.04 的 PAM 模块搜索路径修复。请用一行式安装程序更新到最新软件包：

```bash
curl -fsSL https://gaze.gundulabs.com/install.sh | sh
```

## 10. 在较旧 CPU 上启动时崩溃（SIGSEGV 或 SIGILL）

在没有 AVX2 的 CPU 上（大致为 2013 年之前的 Intel、2015 年之前的 AMD），较旧版本的 `gaze` 与 `gaze-gui` 会因为静态链接的 ONNX Runtime 需要 AVX2 而立即以段错误崩溃。当前的软件包不再将 ONNX Runtime 链接进客户端二进制文件，因此如果你看到此情况，请更新到最新软件包。

`gazed` 守护进程仍然需要一个支持 AVX2 的 CPU，没有它无法工作。用以下命令确认：

```bash
grep -qw avx2 /proc/cpuinfo && echo "AVX2 present" || echo "AVX2 missing"
```

当前的 `gazed` 构建会在启动时检测这一点，并在到达 ONNX Runtime 之前以状态 78 退出，且 systemd unit 设置了 `RestartPreventExitStatus=78`，因此服务会停在失败状态，而不是无限重启。日志显示一行：

```
gazed: AVX2 is unavailable; gazed cannot run on this CPU. Use a machine with AVX2 support. The CLI can run here, but the daemon cannot.
```

较旧的构建（0.3.2 及更早）则会在每次启动时以 `status=4/ILL` 崩溃并进入崩溃循环，因为 `Restart=on-failure` 不断重新调度它们：

```
WARNING: This CPU does not support AVX2, which is required by ort's prebuilt ONNX Runtime binaries.
gazed.service: Main process exited, code=dumped, status=4/ILL
gazed.service: Scheduled restart job, restart counter is at 63.
```

如果你被困在这样的构建上，`sudo systemctl disable --now gazed` 会停止该循环。

## 11. 守护进程核心转储并提示 "Failed to initialize ORT API"

```
The requested API version [27] is not available, only API versions [1, 26] are supported in this build. Current ORT Version is: 1.26.0
thread 'main' panicked at ort-2.0.0-rc.13/src/lib.rs: Failed to initialize ORT API
```

加载的 ONNX Runtime 比 Gaze 请求的 API 更旧。当前的构建会在初始化前校验 API 21，并在已注册的厂商运行时不兼容时尝试使用捆绑的 CPU 运行时。常规软件包会捆绑其 CPU 运行时；Nix 使用 Nix 管理的库。

Gaze 需要 ONNX Runtime 1.21 或更新版本。请更新 Gaze 及其运行时软件包，或者将 `ORT_DYLIB_PATH` 指向兼容的厂商运行时并提供其 `LD_LIBRARY_PATH`。对于 Intel 或 AMD 加速，请如[硬件加速](/projects/gaze/guide/acceleration)中所述注册兼容的 SDK 并重启 `gazed`。

## 12. 在寻求帮助前收集有用的日志

```bash
gaze doctor
systemctl status gazed
journalctl -u gazed -n 300 --no-pager
gaze auth --verbose
```

报告问题时，请包含完整的 `gaze doctor` 输出、发行版版本以及桌面环境（GNOME/KDE 等）。在 KDE 上，附加 `gaze-kde-pam status` 与 `/etc/pam.d/kde-fingerprint` 的内容。在 Omarchy 上，附加 `gaze-omarchy doctor` 与 `omarchy-shell lock status`。
