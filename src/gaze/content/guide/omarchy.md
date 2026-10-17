<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# Omarchy

`gaze-omarchy` 软件包将 Gaze 与 Omarchy 的 Quickshell 锁屏集成在一起。它提供相互独立的面部、密码与指纹 PAM 对话。面部识别失败后屏幕保持锁定，且在扫描过程中始终可以输入密码。

Gaze 支持 Omarchy **4.0.2 与 4.0.3**。启用时会检查 shell 文件的兼容性。更早的使用 hyprlock 的 Omarchy 版本应遵循 [Hyprland 指南](/projects/gaze/guide/hyprland)。

## 安装与启用

[安装程序](/projects/gaze/guide/installation) 会检测在 Hyprland 下运行的 Omarchy，选择 Omarchy 集成软件包，并以桌面用户身份调用 `gaze-omarchy enable`。在基于 Quickshell 的 Omarchy 上，它不会修改 `hyprlock.conf`。

在 Arch 上手动安装：

```bash
yay -S --needed gaze-bin gaze-gui-bin gaze-omarchy-bin
gaze config
gaze add-face default
gaze auth
gaze-omarchy enable
gaze-omarchy doctor
```

这些命令在你已解锁的桌面环境下运行，无需 sudo。请在正常的工作距离下录入，并按照 Gaze 引导的头部动作进行。已有的 Gaze 录入数据以及相机/安全配置都会被复用。

该软件包会将其插件安装到 `/usr/share/gaze/omarchy` 下。启用时会将其链接到当前用户的 Omarchy 插件目录，启用 `com.gundulabs.gaze.lock`，并在确认桌面已解锁且密码 PAM 服务已配置完成后才重启 shell。已有的自定义锁屏插件必须先禁用。启用过程会保留 Gaze 插件路径下无关的其他目录。

## 锁屏行为

- 会话锁定的安全状态确立后，会排队执行一次自动扫描，并有三秒延迟，以便你有时间离开。
- 唤醒被锁屏程序熄屏的显示器时，会排队执行一次新的尝试。在显示器处于唤醒状态时普通的鼠标移动不会持续重启扫描。
- 在空的密码框中按 Enter 会重试。Escape 取消已排队或正在进行的扫描。输入文字会停止已排队的自动尝试。
- 在面部扫描期间密码输入始终可用。每次尝试有十二秒的外部超时。Gaze 自身的扫描与锁定限制仍然适用。
- 面部尝试期间屏幕不会熄灭。面部失败提示文字与密码错误分开显示。
- 若启用了 `auth.require_confirmation_lock_screen`，识别到面孔后会提示按 Enter。插件响应 Gaze 特定的确认提示；它绝不会将密码转发到面部对话中。屏幕解锁前 PAM 仍必须返回成功。

可见的已录入面孔在延迟之后可以解锁刚刚锁定的会话。如需显式确认，请在 `gaze config` 中启用 `auth.require_confirmation_lock_screen`。UI 延迟是在任何已配置的守护进程启动延迟之外的额外延迟；较长的守护进程延迟可能超出插件的超时，从而需要密码解锁。

## 认证边界

该插件针对 `/etc/pam.d/gaze-omarchy-face` 进行认证，该文件由 Gaze Omarchy 软件包所有。只有成功的 `pam_gaze.so` 结果才能认证该服务；缺失录入、守护进程错误以及 `PAM_IGNORE` 都会回退到 `pam_deny.so`。`pam_faillock` 的锁定同样会阻断面部通道。该服务不包含密码栈。就绪状态检测通过系统总线使用 `HasEnrolledFaces`，不会打开相机，也不会验证面孔。

Gaze 的系统守护进程保留对识别、活体检测、模板存储、远程会话检查以及翻盖策略的掌控。sudo 与 polkit 使用 [Gaze 的 PAM 集成](/projects/gaze/guide/pam)。

RGB 与 IR（红外）相机支持遵循你的 Gaze 配置。仅 IR 并非深度传感器，且无论本插件还是摄像头活体检测都无法达到 Windows Hello / Face ID 的同等水平。实际的识别能力与防伪（活体攻击）抵抗取决于硬件、录入数据与策略。

## 更新与诊断

```bash
gaze doctor
gaze-omarchy doctor
```

这些检查都是只读的。Omarchy 检查会核验主机指纹、专用 PAM 规则与所有权、录入状态、插件启用情况以及正在运行的锁屏插件身份/版本。它不使用公共服务映射中的 `active` 标志，因为 Omarchy 在那里隐藏了认证服务。

更新 Gaze 之后，从你已解锁的桌面环境重新加载：

```bash
gaze-omarchy enable
```

如果 Omarchy 更新改变了 shell 文件，兼容性检查会报告差异并停止面部扫描。请用你的密码解锁，并更新 `gaze-omarchy`。从已解锁的桌面环境运行 `gaze-omarchy enable` 来重新加载。

## 禁用与卸载

从你已解锁的桌面环境：

```bash
gaze-omarchy disable
```

这会启用原生的 `omarchy.lock`、重启 shell、检查密码 PAM 是否已就绪且 Gaze 不再作为活动锁屏插件，并仅移除由软件包拥有的符号链接。录入数据对其他 Gaze 客户端仍然可用。

然后移除 `gaze-omarchy-bin`（或源码构建的 `gaze-omarchy` 软件包）。在移除共享的系统软件包之前，需为每个桌面用户重复执行禁用操作。软件包移除保护会检查默认的 `/home/*/.config` 与 `/root/.config` 位置；使用自定义 `XDG_CONFIG_HOME` 位置的用户必须显式禁用。`gaze uninstall` 会在移除 Gaze 之前恢复当前用户的 Omarchy 锁屏程序，若恢复失败则停止。
