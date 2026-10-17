<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# Nix 与 NixOS

Gaze 附带一个 Nix flake，其中包含守护进程、CLI、GUI，以及 GNOME Shell 和 Cinnamon 扩展的软件包，此外还有一个 NixOS 模块，它以声明式方式接入发行版软件包以命令式完成的所有工作：`gazed` systemd 服务、D-Bus 与 polkit 策略、PAM 集成，以及 GNOME/GDM 默认值。

刷脸认证需要系统守护进程和 PAM 配置，因此推荐使用 NixOS 模块。在没有 NixOS 但装有 Nix（包括 home-manager）的系统上，你可以从 flake 安装 CLI 和 GUI，但守护进程与 PAM 模块必须来自你所在发行版的 Gaze 软件包，这与 Flatpak 的拆分方式相同。

## Flake 输出

| 输出 | 描述 |
| --- | --- |
| `packages.<system>.gaze` | `gazed` 守护进程、`gaze` CLI 以及 PAM 模块 |
| `packages.<system>.gaze-gui` | GTK4/Adwaita 配置 GUI |
| `packages.<system>.gaze-gnome-extension` | GNOME Shell 扩展 |
| `packages.<system>.gaze-cinnamon-extension` | Cinnamon Spices 扩展 |
| `packages.<system>.default` | `packages.<system>.gaze` 的别名 |
| `nixosModules.gaze` | NixOS 模块（`services.gaze.*`） |
| `nixosModules.default` | `nixosModules.gaze` 的别名 |
| `overlays.default` | 将这四个软件包加入 `pkgs` |
| `devShells.<system>.default` | 带有完整构建环境的开发 shell |
| `checks.<system>` | 构建 `gaze`、`gaze-gui` 和 `gaze-gnome-extension` |

`<system>` 为 `x86_64-linux` 或 `aarch64-linux`。

## NixOS

添加 flake 输入并导入模块：

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    gaze = {
      url = "github:zxaBinbina/gaze-zh";
      # 可选，省去第二次 nixpkgs 求值。仅当你的
      # nixpkgs 为 unstable 时才这样做：Gaze 属于 2024 版，
      # 而稳定渠道较旧的 rustc 会在依赖树中途失败
      #（通常由 gstreamer crate 引入的 `kstring` 最先出问题）。
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { nixpkgs, gaze, ... }: {
    nixosConfigurations.myhost = nixpkgs.lib.nixosSystem {
      modules = [
        gaze.nixosModules.default
        {
          services.gaze = {
            enable = true;
            gui.enable = true;
          };

          # `sudo` 与 `polkit-1` 开箱即尝试刷脸认证，
          # 密码仍可作为回退。其他 PAM 服务逐个选择启用，例如：
          # security.pam.services.hyprlock.gaze.enable = true;
        }
        # ... 你的其余配置
      ];
    };
  };
}
```

然后重建并录入：

```bash
sudo nixos-rebuild switch
gaze add-face default
gaze auth --verbose
```

识别模型由守护进程在首次使用时下载到 `/var/cache/gaze`，与其他发行版完全一致。

::: warning ONNX Runtime 版本
`gazed` 链接的是构建该 flake 所用 nixpkgs 修订版中的 `onnxruntime` 软件包，并且需要 ONNX Runtime 1.21 或更新版本。更新的运行时没问题，因为 `gazed` 请求的是 1.21 的 API。如果你的 nixpkgs 提供的是更旧的版本，守护进程会在启动时退出，并给出同时列出两个版本的信息；此时应将 flake 的 `nixpkgs` 输入固定到带有更新 `onnxruntime` 的修订版，而不是覆盖 `follows`。
:::

### 模块选项

| 选项 | 默认值 | 描述 |
| --- | --- | --- |
| `services.gaze.enable` | `false` | 运行 `gazed` 并安装 CLI 与 PAM 模块 |
| `services.gaze.package` | flake 的 `gaze` | 守护进程/CLI/PAM 软件包 |
| `services.gaze.settings` | `{ }` | 覆盖上游默认值并合并进 `/etc/gaze/config.toml` 的选项（见[配置](/projects/gaze/guide/configuration)） |
| `services.gaze.mutableConfig` | `true` | 一次性写入 `/etc/gaze/config.toml` 后保留其可编辑（GUI 会写入其中）。设置为 `false` 以获得完全声明式、只读的配置 |
| `services.gaze.pam.defaultServices` | `[ "sudo" "polkit-1" ]` | 无需额外配置即可获得刷脸认证的 PAM 服务 |
| `security.pam.services.<name>.gaze.enable` | `pam.defaultServices` 为 `true` | 为此 PAM 服务尝试刷脸认证 |
| `security.pam.services.<name>.gaze.control` | `"sufficient"` | 该规则的 PAM 控制字段 |
| `security.pam.services.<name>.gaze.simultaneous` | `false` | 向 `pam_gaze.so` 传入 `simultaneous`（在终端与 polkit 提示中同时显示人脸与密码提示；锁屏仍先扫描）而非顺序认证 |
| `security.pam.services.<name>.gaze.retry` | `false` | 在 `pam_unix` 下方添加第二条 `pam_gaze.so retry` 规则，使刷脸认证在密码被拒后多一次尝试 |
| `security.pam.services.<name>.gaze.order` | `null` | 显式的规则 `order`；`null` 表示将 gaze 置于 `pam_fprintd` 和 `pam_unix` 之前 |
| `services.gaze.gui.enable` | `false` | 安装 `gaze-gui` |
| `services.gaze.gui.package` | flake 的 `gaze-gui` | GUI 软件包 |
| `services.gaze.gnome.enable` | `false` | 安装 GNOME Shell 扩展与 `gdm-face` PAM 服务 |
| `services.gaze.gnome.extensionPackage` | flake 的 `gaze-gnome-extension` | GNOME Shell 扩展软件包 |
| `services.gaze.gnome.enableForUsers` | `true` | 通过 dconf 默认值为每个 GNOME 用户会话开启扩展与锁屏刷脸认证。如果你自行管理 `enabled-extensions`，则设为 `false` |
| `services.gaze.gnome.gdmFaceLogin` | `false` | 同时启用 GDM 登录界面的刷脸认证（先阅读 [GNOME 指南](/projects/gaze/guide/gnome)） |
| `services.gaze.kde.lockScreen` | `false` | 定义 `kde-fingerprint`，使 Plasma 锁屏无需按键即启动刷脸解锁 |
| `services.gaze.kde.loginScreen` | `false` | 同时在 Plasma Login Manager / SDDM 栈中运行刷脸认证（提交驱动；见 [KDE 指南](/projects/gaze/guide/kde)） |
| `services.gaze.kde.unlockKwallet` | `false` | 为 KDE 刷脸登录接入 KWallet 认证/会话钩子；需要 `kde.loginScreen`、运行时显式选择，以及钱包录入（见下） |
| `services.gaze.tpm.tcti` | `null` | 守护进程的 `TPM2TOOLS_TCTI`，例如 `"device:/dev/tpm0"`。仅当 `/dev/tpmrm0` 和 `/dev/tpm0` 都不是正确节点时才需要 |

gaze 的 PAM 规则会被插入到 `pam_fprintd` 和 `pam_unix` 之前，因此会先尝试刷脸认证，而指纹读取器与密码都保留为回退。若要将 gaze 放到栈中其他位置，请设置 `order`，并从相邻规则进行偏移，而不是使用一个常量（nixpkgs 会自动分配这些数字，并且它们会在不同版本之间变化）：

```nix
# 先尝试指纹读取器，然后是 gaze，再是密码。
security.pam.services.login.gaze = {
  enable = true;
  order = config.security.pam.services.login.rules.auth.fprintd.order + 5;
};
```

::: warning `rules` 是实验性的
`security.pam.services.<name>.rules` 是一个实验性的 nixpkgs 选项，可能在未经通知的情况下变动，且内置规则的 `order` 数字会在不同版本之间移动。请始终像上面那样从相邻规则进行偏移，而不是赋予一个常量，否则一次 nixpkgs 更新可能会悄悄重排你的栈。
:::

对于选项未覆盖的内容，请直接使用 `security.pam.services.<name>.rules`，并配合 `${config.services.gaze.package}/lib/security/pam_gaze.so`。

::: warning `settings` 仅应用一次
在默认的 `mutableConfig = true` 下，`/etc/gaze/config.toml` 会在首次激活时写入，之后再也不会被覆盖，因此后续对 `services.gaze.settings` 的更改对已经拥有该文件的机器不会产生效果。要么编辑 `/etc/gaze/config.toml`（或使用 GUI），删除它并重建以重新写入，要么设置 `mutableConfig = false` 以获得完全声明式的配置。
:::

### 摄像头

除非有特定理由要固定某个摄像头，否则请将 `settings.cameras.rgb` 留空：默认的 `"primary"` 表示运行时第一个彩色 `/dev/video` 节点。若要固定摄像头，优先使用稳定的标识：`usb:VVVV:PPPP`（十六进制 VID:PID）或 `pipewiresrc target-object=<pipewire-target>`，认证会将其解析为同一摄像头背后的 V4L2 节点。固定的 `/dev/videoN` 路径也有效，但可能在不同启动之间被重新编号；注意 `pipewiresrc target-object=/dev/video0` 不会匹配任何设备。运行 `gaze doctor` 以查看 PipeWire 当前广播的来源，并逐字复制其中某个字符串。

### GNOME 锁屏

```nix
services.gaze.gnome.enable = true;
```

这会安装扩展，并通过 `services.gaze.gnome.enableForUsers`（默认开启）将 dconf 默认值写入 `user` 配置集，从而在每个 GNOME 会话中加载它并开启锁屏刷脸认证。重建后请注销并重新登录：GNOME Shell 仅在会话启动时扫描扩展目录，因此正在运行的会话不会拾取新安装的扩展。

这些是默认值，而非锁定值。要为你自己的用户更改它们，请使用扩展（Extensions）应用或扩展首选项：

```bash
gnome-extensions prefs gaze@gundulabs.com
```

你在那里进行的任何设置都会写入你自己的 dconf 数据库，并从那时起优先于系统默认值。

扩展的设置 schema 安装在扩展目录内部，而不是系统 schema 路径中，因此单纯的 `gsettings set org.gnome.shell.extensions.gaze …` 无法找到它。如果你想通过脚本设置该键，请改用 dconf 写入，它不需要 schema：

```bash
dconf write /org/gnome/shell/extensions/gaze/enable-face-authentication true
```

如果你已经在 home-manager 或你自己维护的 `programs.dconf.profiles.user` 数据库中自行管理 `org/gnome/shell` 的 `enabled-extensions`，请将 `services.gaze.gnome.enableForUsers = false;` 设为 `false`，并将 `gaze@gundulabs.com` 加入你自己的列表。两个都设置该键的系统数据库会相互覆盖而非合并，只有配置集中排在最前面的那个才会生效。

GDM *登录* 刷脸认证保持禁用，除非你设置 `services.gaze.gnome.gdmFaceLogin = true;`。扩展首选项和 `gaze doctor` 都会报告该选项被编译进 GDM dconf 配置集的情况，但该开关本身无法更改它：该配置集属于你的 NixOS 配置，因此在那里切换是唯一的方式。

### hyprlock

```nix
programs.hyprlock.enable = true;
security.pam.services.hyprlock.gaze.enable = true;
# 或者，若希望人脸与密码同时进行：
# security.pam.services.hyprlock.gaze = { enable = true; simultaneous = true; };
```

这会就地修改 `hyprlock` PAM 服务，因此不需要改动 `hyprlock.conf` 中的 `auth_pam_module`。行为细节见 [Hyprland 指南](/projects/gaze/guide/hyprland)。

### KDE Plasma

```nix
services.gaze.kde.lockScreen = true;
```

这会定义 `kde-fingerprint` PAM 服务，即 KScreenLocker 提前启动用于生物识别的槽位，因此刷脸解锁无需按键即可开始。它还会将 `security.pam.services.kde.gaze.enable` 关闭，因为登录管理器（greeter）同时运行交互式的 `kde` 服务，两个客户端会争抢同一个摄像头。不要手动设置 `kde.gaze.enable`：那是旧的提交驱动接线方式，与此冲突。

登录管理器（greeter）是独立的且需要显式选择，因为上游没有为它提供前置的生物识别槽位，因此刷脸认证只在提交登录表单时运行：

```nix
services.gaze.kde.loginScreen = true;
```

默认情况下，KWallet 在每次刷脸登录后会在一个会话内请求一次密码。对于可选的基于 TPM 的钱包解锁，请使用声明式 PAM 集成：

```nix
security.tpm2.enable = true;
services.gaze = {
  kde.loginScreen = true;
  kde.unlockKwallet = true;
  mutableConfig = false;
  settings = {
    storage.encrypt_templates = true;
    storage.unlock_kwallet = true;
    liveness.enabled = true;
  };
};
```

重建，然后以你的普通用户身份录入钱包密码：

```bash
sudo nixos-rebuild switch
gaze keyring --kwallet
```

请使用密码加密的 `kdewallet`；GPG 加密的钱包不受支持。更改钱包密码后请重新录入。这会使任何通过你的人脸与活体检测者都能访问该钱包；见 [KWallet 安全说明](/projects/gaze/guide/kde#optional-tpm-backed-kwallet-unlock)。

`kde.unlockKwallet` 使用 Nix 存储路径为 SDDM、Plasma Login Manager 及其可选的 `plasmalogin-fingerprint` 服务接入认证与会话钩子。在 NixOS 上**不要**运行 `gaze-kde-pam enable-login`：PAM 文件由模块管理。刷脸认证必须保持顺序执行，使用默认的 `sufficient` 控制，且登录服务上不要加 `gaze.retry`。一次失败的人脸尝试仍会回退到原有的密码栈。在没有录入凭据的情况下，刷脸登录仍然可用，而钱包保持锁定；锁屏服务永远不会接收到钱包密码。

如果你保留 `mutableConfig = true`，请在 `gaze config` 中启用这三个运行时设置：更改 `services.gaze.settings` 不会覆盖已有的配置文件。

系统设置条目随 `gaze-kde` 软件包而非 NixOS 模块一起提供，因此在 Nix 上请使用 `gaze add-face` 或 `services.gaze.gui.enable`。

### Cinnamon

该模块没有 Cinnamon 选项，因此需要分两部分接线。安装扩展包并在你的会话中启用它：

```nix
environment.systemPackages = [
  inputs.gaze.packages.${pkgs.stdenv.hostPlatform.system}.gaze-cinnamon-extension
];
```

然后添加锁屏的 PAM 服务，即 X11 会话中独立的屏幕保护程序：

```nix
security.pam.services.cinnamon-screensaver.gaze.enable = true;
```

Polkit 提示已由默认的 `polkit-1` 服务覆盖。关于你的 Cinnamon 版本使用哪个锁屏，以及扩展在每种情况下更改了什么，请参见 [Cinnamon 扩展指南](/projects/gaze/guide/cinnamon)。

### 其他桌面

添加相关的 PAM 服务名称，例如：

```nix
security.pam.services.login.gaze.enable = true; # 控制台/显示管理器登录
```

### 卸载

在 NixOS 上，请通过你的配置来移除 Gaze，而不是运行使用发行版软件包管理器的 `gaze uninstall`。移除该模块（或设置 `services.gaze.enable = false;`），重建，如果你想要一个干净的状态，则删除残留的状态：

```bash
sudo rm -rf /var/lib/gaze /var/cache/gaze /etc/gaze
```

## 非 NixOS 的 Nix 与 home-manager

这些软件包可与普通的 `nix profile` 以及 home-manager 配合使用：

```bash
nix profile install github:zxaBinbina/gaze-zh#gaze-gui
```

```nix
# home-manager
home.packages = [
  inputs.gaze.packages.${pkgs.stdenv.hostPlatform.system}.gaze-gui
];
```

它们通过系统总线与 `gazed` 通信，因此守护进程与 PAM 集成必须已通过 NixOS 模块或你发行版的 Gaze 软件包（[安装](/projects/gaze/guide/installation)）在系统范围内安装。在非 NixOS 系统上仅安装 flake 软件包**不会**设置守护进程、其 D-Bus/polkit 策略或 PAM。

## 开发 shell

```bash
nix develop github:zxaBinbina/gaze-zh
# 或者，在检出目录中：
nix develop
```

该 shell 提供 Rust 工具链和所有原生构建输入（OpenCV、GStreamer、GTK4、ONNX Runtime、tpm2-tss），并将 `GAZE_CPU_ORT_PATH` 指向 Nix 的 ONNX Runtime，因此 `cargo build` 开箱即用。
