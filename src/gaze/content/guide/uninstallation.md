<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# 卸载

本指南介绍如何从系统中移除 Gaze 及其组件。

## 最快捷的方式：`gaze uninstall`

```bash
gaze uninstall
```

在受支持的 Debian/Ubuntu、Fedora、openSUSE 与 Arch 包管理器安装中，该命令会执行完整的清理。它会重置 GNOME/GDM 锁屏与登录设置，移除 GNOME 扩展的系统副本与每用户副本，还原 PAM，停止守护进程，移除软件包（包括 AUR 的 `-debug` 拆分包）与软件仓库，删除 `gazed` 的核心转储，并清除 `/etc/gaze`、`/var/cache/gaze` 与 `/var/lib/gaze`。在 openSUSE 上，它还会移除 `pam-config` 条目、Tumbleweed 仓库以及签名密钥。在进行任何更改之前，它会向你展示计划并请求确认。

有用的参数：

- `--keep-data`：保留 `/var/lib/gaze`（已登记的人脸）
- `--dry-run`：仅打印计划而不执行任何操作
- `--yes`：跳过确认提示

如果你想自行执行各步骤，请遵循下面的手动流程。

## 第 1 步：禁用集成

为了让桌面集成处于干净状态，请在移除软件包之前禁用所有处于活动状态的集成。

### 重置 GNOME 锁屏设置

```bash
gnome-extensions disable gaze@gundulabs.com 2>/dev/null || true
gnome-extensions uninstall gaze@gundulabs.com 2>/dev/null || true
gsettings reset-recursively org.gnome.shell.extensions.gaze
rm -rf ~/.local/share/gnome-shell/extensions/gaze@gundulabs.com
rm -f ~/.config/autostart/gaze-gnome-enable.desktop ~/.local/share/gaze/gnome-enable.sh
```

对每个启用了锁屏人脸解锁的桌面用户重复此操作。`rm -rf` 会移除该扩展的任何每用户副本（由 `gnome-extensions install` 或开发检出遗留）；若没有它，GNOME 会把该扩展继续列为已禁用。最后一行移除安装程序遗留的一次性自启动项，用于在下次登录时完成扩展启用；该项在运行后通常会自行删除。

### 重置 Cinnamon 锁屏设置

```bash
gsettings set org.cinnamon enabled-extensions \
  "$(gsettings get org.cinnamon enabled-extensions | sed "s/, *'gaze@gundulabs.com'//; s/'gaze@gundulabs.com', *//; s/\['gaze@gundulabs.com'\]/@as []/")"
rm -rf ~/.local/share/cinnamon/extensions/gaze@gundulabs.com
rm -rf ~/.cinnamon/configs/gaze@gundulabs.com
```

对每个启用了该功能的桌面用户重复此操作，然后重新加载 Cinnamon（`Alt + F2`、`r`、回车）。最后一行移除该扩展保存的设置，Cinnamon 将这些设置保存在 dconf 之外。

### 还原 KDE 人脸解锁

移除 `gaze-kde` 会从 `/etc/pam.d/kde-fingerprint` 中剥离 Gaze，并（如果你启用了它）从登录欢迎界面的 PAM 栈中剥离。要在不移除软件包的情况下撤销：

```bash
sudo gaze-kde-pam disable
sudo gaze-kde-pam disable-login
```

你在 Gaze 标记块之外手动添加到这些文件中的 `pam_gaze` 行会被保留，因此请自行移除。

### 恢复 Omarchy 的原生锁屏

在移除 `gaze-omarchy` 或 `gaze-omarchy-bin` 之前，从每个用户已解锁的桌面运行 `gaze-omarchy disable`。这会恢复原生锁屏，并仅移除 Gaze 包所拥有的插件链接。`gaze uninstall` 会为当前用户执行此步骤，若失败则在移除前停止。参见 [Omarchy 指南](/projects/gaze/guide/omarchy#disable-and-uninstall)。

### 还原 hyprlock 人脸解锁

如果你为 hyprlock 启用了 Gaze，请从 `~/.config/hypr/hyprlock.conf` 的 `auth { pam { ... } }` 块中移除 `module = hyprlock-gaze` 这一行（或者，如果安装程序创建了备份，则恢复 `~/.config/hypr/hyprlock.conf.gaze-backup`）。对每个启用了该功能的用户重复操作。

```bash
sed -i.bak '/^\s*module\s*=\s*hyprlock-gaze/d' "${XDG_CONFIG_HOME:-$HOME/.config}/hypr/hyprlock.conf"
```

### 移除 GDM 登录默认值与覆盖项

```bash
sudo rm -f /etc/dconf/db/gdm.d/*gaze*
sudo dconf update
```

### 还原 PAM 配置

::: code-group

```bash [Debian/Ubuntu]
sudo pam-auth-update --package --remove gaze
```

```bash [Fedora and compatible]
if [ -f /etc/gaze/authselect.previous ]; then
  profile=$(sudo sed -n 's/^Profile ID:[[:space:]]*//p' /etc/gaze/authselect.previous)
  features=$(sudo sed -n 's/^- //p' /etc/gaze/authselect.previous | tr '\n' ' ')
  sudo authselect select "$profile" $features --force
else
  sudo authselect select sssd --force
fi
```

```bash [openSUSE Tumbleweed]
sudo pam-config --delete --gaze --gaze_grosshack 2>/dev/null || true
sudo pam-config --update 2>/dev/null || true
```

```bash [Arch Linux]
sudo sed -i '/pam_gaze/d' /etc/pam.d/sudo
```

```bash [手动 PAM 设置]
# Remove Gaze lines from the stack where you added them.
# Use common-auth-pc on openSUSE or system-auth on Fedora/Arch.
sudo nano /etc/pam.d/common-auth-pc  # openSUSE
# sudo nano /etc/pam.d/system-auth   # Fedora/Arch
```

:::

### 停止并禁用守护进程

```bash
sudo systemctl stop gazed
sudo systemctl disable gazed
```

## 第 2 步：移除软件包

::: code-group

```bash [Debian/Ubuntu]
sudo apt remove --purge gaze-zh gaze-gui gaze-gnome-extension gaze-cinnamon-extension gaze-hyprlock gaze-kde
sudo apt autoremove
```

```bash [Fedora and compatible]
sudo dnf remove gaze-zh gaze-gui gaze-gnome-extension gaze-cinnamon-extension gaze-hyprlock gaze-kde
```

```bash [openSUSE Tumbleweed]
sudo zypper remove gaze-zh gaze-gui gaze-gnome-extension gaze-cinnamon-extension gaze-hyprlock gaze-kde
```

```bash [Arch Linux / Manjaro]
# For packages built from this repository:
sudo pacman -Rns gaze-zh gaze-gui gaze-gnome-extension gaze-cinnamon-extension gaze-hyprlock gaze-kde
# If you installed the official AUR packages instead, use their -bin names:
sudo pacman -Rns gaze-bin gaze-gui-bin gaze-gnome-extension-bin gaze-hyprlock-bin gaze-kde-bin
# If you installed the Cinnamon extension, remove it too (check the exact name with `pacman -Qs gaze`):
sudo pacman -Rns gaze-cinnamon-extension-bin
# AUR builds may also have installed -debug split packages:
pacman -Q | awk '/^gaze.*-debug /{print $1}' | xargs -r sudo pacman -Rns --noconfirm
```

```bash [Flatpak（仅 GUI）]
flatpak uninstall com.gundulabs.Gaze
```

:::

## 第 3 步：移除软件包仓库

::: code-group

```bash [Debian/Ubuntu]
sudo rm /etc/apt/sources.list.d/gundulabs.list
sudo rm /usr/share/keyrings/gundulabs-archive-keyring.gpg
sudo apt update
```

```bash [Fedora and compatible]
sudo rm /etc/yum.repos.d/gundulabs.repo
sudo rpm -e gpg-pubkey-$(rpm -qa gpg-pubkey --qf '%{NAME}-%{VERSION}-%{RELEASE}\t%{SUMMARY}\n' | grep -i gundulabs | awk '{print $1}' | sed 's/gpg-pubkey-//')
sudo dnf makecache
```

```bash [openSUSE Tumbleweed]
sudo zypper removerepo gundulabs 2>/dev/null || true
sudo rm -f /etc/zypp/repos.d/gundulabs.repo
sudo rm -f /etc/pki/rpm-gpg/RPM-GPG-KEY-gundulabs
sudo rpm -e gpg-pubkey-$(rpm -qa gpg-pubkey --qf '%{NAME}-%{VERSION}-%{RELEASE}\t%{SUMMARY}\n' | grep -i gundulabs | awk '{print $1}' | sed 's/gpg-pubkey-//') 2>/dev/null || true
sudo zypper refresh
```

```bash [Fedora 通过 Copr]
sudo dnf copr disable @gundulabs/gaze
sudo dnf makecache
```

```bash [Arch Linux / Manjaro]
# AUR installs do not add a Gundu Labs pacman repo.
# Only run this if you previously configured the old pacman repo.
sudo sed -i '/^\[gaze\]/,/^$/d' /etc/pacman.conf
sudo rm -f /etc/pacman.d/gaze-mirrorlist
sudo pacman -Sy
```

```bash [Flatpak]
flatpak remote-delete gundulabs
```

:::

## 第 4 步：移除残留数据

移除软件包不会删除用户数据、已下载的模型或被修改过的配置文件。如果需要彻底清理，请手动移除这些内容。

软件包管理器若未运行钩子，请在移除软件包后刷新已编译的 GNOME 设置：

```bash
sudo dconf update
sudo glib-compile-schemas /usr/share/glib-2.0/schemas
```

### 人脸登记数据

`/var/lib/gaze` 保存已登记的模板（`users/`）、TPM 封存的模板密钥（`tpm/`）以及任何受 TPM 保护的 GNOME Keyring 凭据（`keyring/`）：

```bash
sudo rm -rf /var/lib/gaze
```

### 已下载的 ML 模型与缓存

```bash
sudo rm -rf /var/cache/gaze
```

### 配置

```bash
sudo rm -rf /etc/gaze
```

### systemd 附加配置（drop-in）

守护进程的本地覆盖项（调试日志、开发检出）位于 gaze 专属目录中：

```bash
sudo rm -rf /etc/systemd/system/gazed.service.d
```

### 核心转储

如果 `gazed` 曾经崩溃，systemd 可能已保存核心转储。其中可能包含来自守护进程内存的已解密人脸模板，因此请移除它们：

```bash
sudo find /var/lib/systemd/coredump \( -name 'core.gazed.*' -o -name 'core.gaze.*' -o -name 'core.gaze-gui.*' \) -delete
```

### SELinux 策略（启用了 SELinux 的 RPM 安装）

```bash
if command -v semodule >/dev/null 2>&1; then
  sudo semodule -r gaze-gdm-camera
  sudo semodule -r gaze-greeter-keyring
fi
```

## 第 5 步：重新加载系统服务

```bash
sudo systemctl daemon-reload
```

## 验证卸载

```bash
# All of these should fail with "command not found"
gaze --version
gazed --version
gaze-gui --help

# Should show "inactive" or "not found"
systemctl status gazed
```
