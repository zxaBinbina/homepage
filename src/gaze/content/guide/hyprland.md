<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# Hyprland（hyprlock）

对于使用 Quickshell 锁屏的 Omarchy 版本，请使用 [Omarchy 集成](/projects/gaze/guide/omarchy)。下面的 PAM 配置适用于 hyprlock。

Gaze 通过专用的 PAM 服务与 [hyprlock](https://github.com/hyprwm/hyprlock)（Hyprland 的屏幕锁定器）集成。`gaze-hyprlock` 软件包会安装 `/etc/pam.d/hyprlock-gaze`，并保持发行版自带的 `/etc/pam.d/hyprlock` 不动。

你通过将 `hyprlock.conf` 指向 Gaze 的 PAM 服务来选择加入。

## 安装

一行式安装程序在检测到 Hyprland 会话或 `hyprlock` 可执行文件时，会自动安装 `gaze-hyprlock` 并编辑 `~/.config/hypr/hyprlock.conf`。

手动安装：

::: code-group

```bash [Debian/Ubuntu]
sudo apt-get install gaze-hyprlock
```

```bash [Fedora and compatible]
sudo dnf install gaze-hyprlock
```

```bash [openSUSE Tumbleweed]
sudo zypper install gaze-hyprlock
```

```bash [Arch]
yay -S gaze-hyprlock-bin
```

:::

## 启用

在 `~/.config/hypr/hyprlock.conf` 中添加：

```ini
auth {
    pam {
        module = hyprlock-gaze
    }
}
```

重启 hyprlock 或再次锁定会话。面部解锁先运行；如果失败或超时，hyprlock 会回退到密码提示。

## 同时模式

`hyprlock-gaze-simultaneous` 服务也随包提供：

```ini
auth {
    pam {
        module = hyprlock-gaze-simultaneous
    }
}
```

它使用 `pam_gaze.so simultaneous`，但在 hyprlock 上它的表现与 `hyprlock-gaze` 一样：扫描先运行，密码在之后才被询问。Gaze 只能撤回一个由它在终端（`sudo`、`su`、`login`）上或在一个 polkit 对话框中启动的密码提示。hyprlock 用自己的线程来应答提示，因此一个与扫描同时启动的提示永远无法被收回，Gaze 也就不会启动它。

## 工作原理

`hyprlock-gaze` 是一个 PAM 服务，它在你的系统密码栈（Fedora/RHEL 与 Arch 上的 `system-auth`，Debian/Ubuntu 与 openSUSE 上的 `common-auth`）之上叠加 `pam_gaze.so`，并让 `pam_nologin` 与 `pam_faillock preauth` 在 Gaze 之前运行。这些门控必须排在前面，因为一次 `success=done` 的面部匹配会结束整个认证栈，否则就会跳过该 include 引入的锁定与 nologin 检查（这也是 `gaze-kde-pam` 在它自己的块内携带它们的原因）。认证流程如下：

1. hyprlock 以服务名 `hyprlock-gaze` 调用 PAM
2. `pam_gaze.so` 以登录用户身份运行，通过 `gazed` DBus 服务占用摄像头，并运行面部验证
3. 匹配 → `PAM_SUCCESS`，hyprlock 解锁
4. 没有录入的面部或守护进程不可用 → `PAM_IGNORE`，hyprlock 进入密码
5. 不匹配 → `PAM_AUTH_ERR`，hyprlock 进入密码

无需改动 `gazed` 配置。DBus 策略已经允许无特权用户占用摄像头，并针对他们自己的已录入模板运行验证。

## 前置条件

- `gazed` 守护进程正在运行（`systemctl status gazed`）
- 至少一个已录入的面部：`gaze add-face default`
- 可用的摄像头（用 `gaze auth` 测试）

## 禁用

从 `hyprlock.conf` 的 `auth { pam { ... } }` 块中移除 `module` 行（或把它设为 hyprlock 的默认值 `hyprlock`）。如果你不打算再次使用，请卸载该软件包：

::: code-group

```bash [Debian/Ubuntu]
sudo apt-get remove gaze-hyprlock
```

```bash [Fedora and compatible]
sudo dnf remove gaze-hyprlock
```

```bash [openSUSE Tumbleweed]
sudo zypper remove gaze-hyprlock
```

```bash [Arch]
yay -R gaze-hyprlock-bin
```

:::

## 故障排查

- **每次都回退到密码**：守护进程可能没有运行，或者当前用户没有录入的面部。请检查 `systemctl status gazed` 与 `gaze list-faces`。
- **你手动锁定后立刻自行解锁**：hyprlock 在它一启动时就启动 PAM 栈，因此面部认证会在你仍站在摄像头前时运行。请设置 [`auth.start_delay_ms`](/projects/gaze/guide/configuration) 给自己留出走开的时间，并设置 `auth.start_delay_scope = "screen_lock"`，这样延迟就不会同时拖慢 `sudo` 与 polkit 提示。注意 hyprlock 自己的 `general:grace` / `--grace` 选项对此无济于事；它是在窗口内对任意按键或光标移动解锁，而不是延迟认证。
- **摄像头忙**：另一个 Gaze 客户端（GUI、GNOME 扩展）可能占用了摄像头。请关闭它并重试。
- **日志中的 PAM 错误**：请检查 `journalctl -u gazed` 与 `journalctl --user -t hyprlock`。
