<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# Cinnamon 扩展

Gaze 针对 Cinnamon 的锁屏与 PolKit 提权集成由 `gaze-cinnamon-extension` 软件包提供。一行式安装程序会尝试为你当前的 Cinnamon 用户启用该扩展。如果你是手动安装软件包，则需要自己启用它。在 openSUSE Tumbleweed 上，请先用 `sudo zypper install gaze-cinnamon-extension` 安装它。

这个 Cinnamon Spices 扩展会接入 Cinnamon 内部的 PolKit 认证代理以及原生解锁对话框。

该扩展仅为 Cinnamon 的锁屏与 PolKit 提示所需。CLI、GUI 以及 `sudo` 这类常规 PAM 提示在没有它时也能工作；如果你使用不同的桌面环境，可以保持它禁用。

> [!IMPORTANT]
> 如果你在 `/etc/gaze/config.toml` 中启用了 `require_confirmation_lock_screen = true` 或 `require_confirmation_elevation = true`，那么这个 Cinnamon 扩展**必须**处于启用状态，面部授权的确认功能才能在 Cinnamon 的图形化 PolKit 提示以及锁屏上生效。
>
> Cinnamon 的 PolKit 提示通常不允许你用一个空的密码字段来确认。当 Gaze 请求确认时，扩展会隐藏该字段，并把 **Authenticate（认证）** 按钮设为焦点。在统一的锁屏上，它会添加一个 **Confirm Face Unlock（确认面部解锁）** 按钮。
>
> 如果在 Cinnamon 下该扩展处于**未激活 / 已禁用**状态，而这两个开关中的任意一个被设置，Gaze 的 PAM 模块会**安全地绕过确认**（一旦面部匹配就立即返回成功），以防止空输入卡死和用户被锁在外面。

## 我应该启用它吗？

如果你使用 Cinnamon，并且想在锁屏上使用面部解锁，或想让图形化 PolKit 提示获得确认，请启用该扩展。

否则，你可以保持它禁用：CLI 或 GUI 录入、常规 PAM 认证，以及 Cinnamon 之外的桌面环境都不需要它。

## 启用扩展

软件包安装后，从你的 Cinnamon 会话中启用该扩展：

```bash
gsettings set org.cinnamon enabled-extensions \
  "$(gsettings get org.cinnamon enabled-extensions | sed "s/]\$/, 'gaze@gundulabs.com']/; s/^@as \[\]\$/['gaze@gundulabs.com']/")"
```

然后按 `Alt + F2`，输入 `r`，再按 `Enter` 来重新加载 Cinnamon（或者在终端中运行 `cinnamon --replace &`）。

你也可以通过图形界面启用：
1. 打开 **System Settings（系统设置）** → **Extensions（扩展）**。
2. 在列表中找到 **Gaze**。
3. 点击 **+**（添加）以激活该扩展。

## 打开扩展首选项

```bash
cinnamon-settings extensions
```

或者打开 **System Settings（系统设置）** → **Extensions（扩展）**，找到 **Gaze**，并点击该行上的 **Configure（配置）**（齿轮）按钮。

窗口只有一个 **Behavior（行为）** 页面，包含一组：

| 分组 | 包含 |
|---|---|
| **面部认证** | `Enable face authentication (lock screen)`、`Face retry mode`、`Maximum face tries`。适用于 Cinnamon 会话。 |

## 重试行为

扩展决定在一次认证周期内面部认证重试多少次。所有设置都在扩展首选项的 **Behavior → Face authentication（行为 → 面部认证）** 下：

| 设置 | 键 | 取值 | 默认值 |
|---|---|---|---|
| 面部重试模式 | `face-retry-mode` | `disabled`、`fixed`、`infinite` | `fixed` |
| 最大尝试次数 | `max-face-tries` | 2 至 20 | 3 |

- `disabled`：一次尝试。失败后，本次周期内的面部认证停止，你用密码完成。
- `fixed`：重试直到失败 `max-face-tries` 次，然后本次周期内停止。
- `infinite`：只要提示框开着就一直重试。密码输入框始终可用。

`max-face-tries` 仅适用于 `fixed` 模式，即便配置了更低的值，扩展也会把它限制在最小值 2。

## 录入面部

录入不在扩展首选项里。请使用 Gaze 设置应用或 CLI：

```bash
gaze-gui             # Faces list, press + to enroll
gaze add-face default
```

配置文件名默认为 `default`，与 CLI 快速入门流程一致。按照摄像头提示操作，直到配置文件保存。

## PolKit 提权确认

当某个管理类应用（例如 `gparted`、Software Sources（软件源）或 Gaze 配置）请求提权认证时：
1. Gaze 在后台感知你的面部。
2. 一旦面部匹配成功，扩展会自动隐藏密码输入框，把提示标签更新为 `"Face verified. Press Enter or click Authenticate to confirm."（面部已验证。按 Enter 或点击 Authenticate 确认。）"`，并把 **Authenticate（认证）** 按钮设为焦点。
3. 按 **Enter** 或点击 **Authenticate（认证）** 进行确认，无需输入密码即可继续。

## 锁屏行为

Gaze 在锁屏上的行为取决于你的 Cinnamon 桌面版本与会话类型：

### 统一原生屏保（Wayland / Cinnamon 6.8+）

在使用集成原生屏幕屏蔽（Cinnamon 6.8+ 引入，以及 Wayland 会话）的 Cinnamon 会话上，锁屏原生运行在 Cinnamon 的窗口管理器进程内（`imports.ui.screensaver.unlockDialog`）。Gaze Cinnamon 扩展会直接接入这个对话框：

1. **确认按钮**：当 `require_confirmation_lock_screen = true` 时，会出现一个带有活动进度转圈的 **Confirm Face Unlock（确认面部解锁）** 按钮。
2. **键盘导航**：按 **Enter** 或点击按钮即可确认并解锁会话。按 **Escape** 取消确认并返回密码字段。
3. **状态反馈**：交互式摄像头提示（`Please look at the camera...（请看向摄像头……）`、`Hold still...（请保持不动……）`、`Need more light...（需要更亮的环境……）`）会直接显示在锁屏标签上。
4. **可配置重试**：遵循配置的 `face-retry-mode` 与 `max-face-tries` 设置。

### 独立屏保（`cinnamon-screensaver` / Linux Mint 22.x 在 X11 上）

在 Linux Mint 22.x（以及标准 X11 会话）上，屏幕锁定由独立的 `/usr/bin/cinnamon-screensaver` 进程（用 Python/GTK3 编写）处理，它运行在 Cinnamon 的 CJS 环境之外。

- **无感面部解锁**：当 `require_confirmation_lock_screen = false` 时，Gaze 通过 PAM（`/etc/pam.d/cinnamon-screensaver`）验证你的面部，并在匹配时立即解锁屏幕。
- **确认界面**：由于 `/usr/bin/cinnamon-screensaver` 是一个独立的 GTK 应用，不支持 CJS Spices 扩展，因此自定义按钮控件无法渲染到它的解锁窗口上。提权提示（PolKit）在所有 Cinnamon 版本上都仍然完全支持带确认界面的功能。

## 验证 Cinnamon 流程

- **测试 PolKit 提权**：打开一个需要 root 授权的工具（或者在图形化终端里运行 `pkexec id`）。看向摄像头；一旦你的面部被验证，无需输入密码，按 Enter 或点击 Authenticate 即可确认。
- **测试锁屏**：锁定屏幕（`Super + L` 或 `Ctrl + Alt + L`），唤醒显示器，然后看向摄像头以解锁。
