<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# LightDM

LightDM 是 Linux Mint、Xubuntu、Ubuntu MATE、Ubuntu Cinnamon、Linux Lite 以及 Manjaro Xfce 的登录界面。Gaze 可以在你输入任何内容之前在此进行认证，因为 LightDM 一旦选中用户就立即运行 PAM 栈，而不是等待密码。

这能否变成"免动手"登录，取决于你的发行版所搭载的 greeter（登录管理器前端）。详见 [greeter 支持](#greeter-support)。

## 配置

没有 `gaze-lightdm` 软件包。LightDM 的 PAM 服务已经包含了共享认证栈，因此按常规方式启用 Gaze 就足够了：

::: code-group

```bash [Debian/Ubuntu/Mint]
sudo pam-auth-update --package
```

```bash [Fedora and compatible]
sudo authselect select gaze with-silent-lastlog --force
```

```bash [openSUSE Tumbleweed]
sudo pam-config --add --gaze
sudo pam-config --update
```

```bash [Arch]
# /etc/pam.d/lightdm 包含了 system-login，而后者又包含了 system-auth
```

:::

Debian 的 `/etc/pam.d/lightdm` 被打补丁为 `@include common-auth`，Fedora 的为 `auth substack system-auth`，openSUSE 的为 `auth include common-auth`，Arch 的为 `auth include system-login`。无论哪种情况，你为 `sudo` 启用的配置文件或模块也会覆盖到登录界面。

用 `gaze doctor` 确认，然后注销并选择你的用户。

## greeter 支持

LightDM 本身会在你输入之前完成认证。随后由各个 greeter 决定是自动启动会话还是等待点击，它们各不相同：

| Greeter | 发行版 | 免动手 |
|---|---|---|
| slick-greeter 2.2.7+ | Linux Mint、LMDE | 是 |
| slick-greeter 2.2.7 之前版本 | Linux Mint 22 及更早 | 否，需按 **Log In** |
| lightdm-gtk-greeter | Xubuntu、Manjaro Xfce | 否，需按 **Log In** |

Mint 在 slick-greeter 2.2.7 中放宽了该项检查，使得一次产生提示消息（而非密码提示）的成功认证会直接让你登录。Gaze 在寻找你的面孔时会发出这样的消息，因此在 Mint 上会话会自行启动。

`lightdm-gtk-greeter` 仍要求用户先被提示过，才会启动会话，因此面部认证虽然成功，但 greeter 会等待 **Log In** 按钮。这是上游的固有限制，Gaze 无法从 PAM 模块层面绕开。

::: warning 密码框会等待相机
LightDM 一次只运行一个认证，因此在 Gaze 寻找你的面孔期间，greeter 不会接受输入的密码。面部尝试一结束就会立即接受密码。这会影响 LightDM 上的每一个生物识别模块，不仅仅是 Gaze，这也是为何在该场景下 `auth.start_delay_ms` 应保持较低值。

greeter 在屏幕熄灭时也不会取消一次认证，因此在屏幕关闭前开始的扫描会一直运行到完成。
:::

## 登录界面的相机

认证始终直接捕获内核 V4L2 设备，因此 greeter 是否存在 PipeWire 会话对认证没有影响。`gazed` 打开相机而非 greeter，因此 greeter 自身的沙箱隔离不会构成阻碍。

将 `cameras.rgb` 保持为 `primary`（第一个彩色 V4L2 节点），将其固定到 `usb:VVVV:PPPP`，或固定到一个 `pipewiresrc target-object=` 值，该值会被解析到同一相机背后的 V4L2 节点。详见 [选择相机源](/projects/gaze/guide/configuration#select-a-camera-source)。

Gaze 仅在 greeter 是 seat0 上的活动会话时才使用该 greeter 的相机，这也正是 greeter 持有相机访问控制条目的条件。因此有两种情况没有可供认证的 greeter：

- **自动登录。** 配置了自动登录后，LightDM 会直接启动你的会话，且从不创建 greeter，因此没有可认证的登录界面。
- **seat0 之外的座位。** Gaze 只关注 seat0，因此第二个座位上的 greeter 不在覆盖范围内。

当某个会话停止活动后，已打开的相机不会被关闭，因此上一个会话中遗留下来的程序可能继续占用该设备，导致捕获因设备忙而失败。

## 密钥环与加密主目录

用你的面孔登录意味着没有可用于解锁 GNOME 密钥环或 KWallet 的密码，因此会话启动后你会被要求输入。这与 [GNOME 登录警告](/projects/gaze/guide/gnome#login-warning-gnome-keyring) 中描述的权衡相同。如果你更希望保持密钥环自动解锁，请在登录界面用密码认证，并将 Gaze 用于 `sudo`、polkit 和锁屏。

::: danger 不要在加密主目录下启用此功能
如果你的主目录由登录密码解锁，即通过 `pam_ecryptfs` 或类似模块，那么登录界面的面部认证将无法解锁它。随后会话会打开并立即关闭，LightDM 返回 greeter 并重试，看起来就像是面部认证不断重启的登录循环。要摆脱这种情况，需要遮住相机直到出现密码提示。

在登录界面启用 Gaze 之前，请检查 `/etc/pam.d/common-auth` 中是否存在 `pam_ecryptfs`。加密主目录与 greeter 处的面部登录互不兼容；请改用 Gaze 用于 `sudo`、polkit 和锁屏。
:::

## 关闭它

从共享栈中移除 Gaze，或仅为提权保留它：

```bash
sudo pam-auth-update --disable gaze gaze-simultaneous
```

在 openSUSE Tumbleweed 上，改用 `pam-config`：

```bash
sudo pam-config --delete --gaze --gaze_grosshack
sudo pam-config --update
```

然后遵循 [选择性配置](/projects/gaze/guide/pam#selective-setup-password-at-gdm-face-authentication-for-sudo-and-polkit) 将 Gaze 仅重新添加到 `sudo` 与 polkit。
