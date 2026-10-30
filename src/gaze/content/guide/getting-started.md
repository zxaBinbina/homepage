<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# 快速上手

在 10 分钟内让 Gaze 跑起来：安装它、录入你的脸，并测试认证。

## 开始之前

- 带有可用的 PipeWire/GStreamer 摄像头的 Linux 桌面
- `sudo` 权限
- 首次下载模型时需要联网

## 第 1 步：安装 Gaze

`v0.5.1` 提供 GUI、CLI 与 PAM 的中文认证提示；认证成功时显示“人脸已验证。”[下载最新版](https://github.com/zxaBinbina/gaze-zh/releases/latest)。一键安装会匹配系统与 CPU 架构，显示安装菜单，并在检测到的桌面对应选项旁标注「推荐」。由你选择 GUI 与桌面集成，最后一项为「不安装 GUI，仅安装命令行」：

```bash
curl -fsSL https://zxabinbina.cc.cd/projects/gaze/install.sh | sh
```

中文版自动安装支持 Fedora 44/45、Ubuntu 24.04 的 x86_64 与 ARM64，以及 Linux Mint 22、openSUSE Tumbleweed 的 x86_64。ARM 与 x86 下载包分别提供，脚本自动匹配。Arch 另提供手动下载压缩包。没有匹配包时会停止并提示参考安装指南，其他版本和架构可选择上游渠道。

手动安装时，下载对应系统的压缩包，校验并解压，再按包内 `README.md` 安装主程序、可选 GUI 和一个桌面集成包；不同系统的 RPM/DEB 不可混用。组件选择、升级与 KRDP 修复范围见[安装指南](/projects/gaze/guide/installation)。

## 第 2 步：检查守护进程状态

```bash
systemctl status gazed
```

如果服务没有运行，启用并启动它：

```bash
sudo systemctl enable --now gazed
```

## 第 3 步：录入你的第一张脸

```bash
gaze add-face default
```

录入时的提示：

- 让面部居中并保持良好的光照。
- 第一次采集时自然地正对摄像头；后续的方向提示都是相对于该姿态来测量的。
- 做幅度小而有意识的动作，并在每个被提示的角度上保持静止。
- 如果可能，移除强烈的逆光。

## 第 4 步：测试认证

```bash
gaze auth
```

要查看本次认证尝试的更多细节，加上 `--verbose`：

```bash
gaze auth --verbose
```

## 第 5 步：打开 GUI（可选）

```bash
gaze-gui
```

使用 GUI 录入额外的脸（例如，戴眼镜和不戴眼镜各一张）。

## 第 6 步：验证 GNOME 锁屏认证（可选）

仅当你使用 GNOME 并且希望在锁屏上使用刷脸解锁时，才执行以下步骤。一行命令安装器会在可能的情况下为当前 GNOME 用户启用该扩展。如果你是手动安装软件包的，或者自动启用失败，请运行：

```bash
gnome-extensions enable gaze@gundulabs.com
gsettings set org.gnome.shell.extensions.gaze enable-face-authentication true
```

请在一个**在**软件包安装之后才启动的 GNOME 会话中运行这些命令。GNOME Shell 会在会话启动时扫描扩展目录，并丢弃它尚未见过的扩展 ID。如果你在安装它的那个会话里启用该扩展，设置可能看起来有效，但在你注销后就会消失。请重启，然后再次运行这些命令。`gaze doctor` 会将其报告为 “GNOME 扩展：已安装，但尚未为当前用户启用”，并打印相同的步骤。参见[扩展在注销后又一次消失](/projects/gaze/guide/gnome#the-extension-disappears-again-after-a-logout)。

通过此扩展实现的免手动锁屏和 GDM 登录认证是 GNOME 特有的。Cinnamon 有一个用于其锁屏和 PolKit 提示的独立扩展；参见 [Cinnamon 指南](/projects/gaze/guide/cinnamon)。KDE Plasma 使用 KScreenLocker 提前启动的生物识别 PAM 槽位；参见 [KDE Plasma 指南](/projects/gaze/guide/kde)。其他登录界面使用 PAM 集成。参见 [Hyprland](/projects/gaze/guide/hyprland)、[LightDM](/projects/gaze/guide/lightdm)、[控制台登录（TTY）](/projects/gaze/guide/console) 以及 [PAM](/projects/gaze/guide/pam) 的指南。
GDM 登录刷脸认证是独立的，并且默认禁用，这与 GNOME 钥匙环的行为有关。
关于详情和可选的登录启用（包括可选的基于 TPM 的钥匙环解锁，可消除该限制），请参见 [GNOME 扩展](/projects/gaze/guide/gnome)。

## 如果某项失败

前往[故障排查指南](/projects/gaze/guide/troubleshooting)处理摄像头、守护进程、PAM 以及低匹配率问题。

## 下一步

- 在[配置指南](/projects/gaze/guide/configuration)中调整行为
- 在 [CLI 指南](/projects/gaze/guide/cli)中学习命令
- 通过 [GUI 指南](/projects/gaze/guide/gui)使用桌面应用
- 在 [PAM](/projects/gaze/guide/pam) 中查看 PAM 设置
- 在 [GNOME 扩展](/projects/gaze/guide/gnome)中查看锁屏/登录行为
- 为 Cinnamon 锁屏和 PolKit 提示配置 [Cinnamon 扩展](/projects/gaze/guide/cinnamon)
- 配置 [KDE Plasma](/projects/gaze/guide/kde) 锁屏与系统设置页面
- 为 [Hyprland (hyprlock)](/projects/gaze/guide/hyprland) 启用刷脸解锁
- 为 [LightDM](/projects/gaze/guide/lightdm) 或[控制台登录（TTY）](/projects/gaze/guide/console)添加刷脸认证
