<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# GNOME 扩展

Gaze 的锁屏与 GDM 集成是 GNOME 特有的，由 `gaze-gnome-extension` 软件包提供。一行式安装程序会尝试为你当前的 GNOME 用户启用锁屏面部解锁。如果你是手动安装软件包，则需要自己启用该扩展。在 openSUSE Tumbleweed 上，请先用 `sudo zypper install gaze-gnome-extension` 安装它。

该扩展会在 GNOME Shell 认证流程中启动 `gdm-face` PAM 服务。它支持 GNOME Shell 45 至 51。

该扩展仅为 GNOME 的锁屏和 GDM 流程所需。CLI、GUI 以及 `sudo` 这类常规 PAM 提示在没有它时也能工作；如果你使用其他桌面环境，可以保持该 GNOME 扩展处于禁用状态。

> [!IMPORTANT]
> 如果你在 `/etc/gaze/config.toml` 中启用了 `require_confirmation_lock_screen = true` 或 `require_confirmation_elevation = true`，那么这个 GNOME Shell 扩展**必须**处于启用状态，面部授权的确认功能才能在 GNOME 的图形化 PolKit 提示以及锁屏 / GDM 登录界面上生效。
>
> GNOME 的提示通常不允许你用一个空的密码字段来确认。当 Gaze 请求确认时，扩展会隐藏该字段，并把 PolKit 中的 **Authenticate（认证）** 按钮设为焦点。在锁屏和 GDM 登录界面上，它会添加一个 **Confirm Face Unlock（确认面部解锁）** 按钮。
>
> 如果在 GNOME 下该扩展处于**未激活 / 已禁用**状态，而这两个开关中的任意一个被设置，Gaze 的 PAM 模块会**安全地绕过确认**（一旦面部匹配就立即返回成功），以防止空输入卡死和用户被锁在外面。

## 我应该启用它吗？

如果你使用 GNOME，并且想在锁屏上使用面部解锁，请启用该扩展。

否则，你可以保持它禁用：CLI 或 GUI 录入、常规 PAM 认证，以及 GNOME 之外的桌面环境都不需要它。

## 启用扩展

安装软件包后，请重启以便 GNOME Shell 能发现该扩展。重新进入你的 GNOME 会话后，用以下命令启用它：

```bash
gnome-extensions enable gaze@gundulabs.com
gsettings set org.gnome.shell.extensions.gaze enable-face-authentication true
```

如果在重启之前运行，`gnome-extensions enable` 会报告 `Extension "gaze@gundulabs.com" does not exist`。Shell 只在会话启动时扫描扩展目录，因此在安装后立刻运行该命令（没有重启会话）总是会失败。如果你暂时无法重启，等效的 dconf 写入可以随时生效，并在下次登录时生效：

```bash
gsettings set org.gnome.shell enabled-extensions \
  "$(gsettings get org.gnome.shell enabled-extensions | sed "s/]\$/, 'gaze@gundulabs.com']/; s/^@as \[\]\$/['gaze@gundulabs.com']/")"
gsettings set org.gnome.shell.extensions.gaze enable-face-authentication true
```

### 注销后扩展又消失了

手动添加 UUID 等于给一个正在运行的 GNOME Shell 从未扫描过的扩展命名。Shell 会在下次重写 `enabled-extensions` 时丢弃它不认识的 UUID，而它在会话结束或你切换任何其他扩展时就会这么做。因此该设置可能在安装后立刻看起来正确，却在第一次注销后消失，而其间没有任何东西发生故障。

安装后请重启而不是注销，以便 Shell 在重写列表之前先扫描该扩展。

如果它已经消失了，请从**软件包安装之后**才启动的 GNOME 会话中运行[启用扩展](#enable-the-extension)下的两条命令。`gaze doctor` 会把这种情况报告为 `GNOME extension: installed, but not enabled for the current user（GNOME 扩展：已安装，但未为当前用户启用）`，并打印相同的步骤。

一行式安装程序还会留下一个一次性自启动项 `~/.config/autostart/gaze-gnome-enable.desktop`，它会在你下次 GNOME 登录时重新应用启用，然后连同其辅助脚本 `~/.local/share/gaze/gnome-enable.sh` 一起删除自己。如果你更愿意自己动手，这两者都可以安全手动删除。

## 打开扩展首选项

```bash
gnome-extensions prefs gaze@gundulabs.com
```

或者打开 **Extensions（扩展）** 应用（Extension Manager 也可以），找到 **Gaze**，并从该行打开它的设置。

窗口只有一个 **Behavior（行为）** 页面，包含两组：

| 分组 | 包含 |
|---|---|
| **面部认证** | `Enable face authentication (lock screen)`、`Face retry mode`、`Maximum face tries`。仅适用于本次会话的锁屏。 |
| **GDM 登录界面** | `Enable face authentication at GDM login`。适用于登录界面并要求管理员授权。 |

## 重试行为

扩展决定在一次认证周期内面部认证重试多少次。这两个设置都在扩展首选项的 **Behavior → Face authentication（行为 → 面部认证）** 下，并且都按 dconf 配置文件生效，因此 GDM 和你的桌面会话可以不同。

| 设置 | dconf 键 | 取值 | 默认值 |
|---|---|---|---|
| 面部重试模式 | `face-retry-mode` | `disabled`、`fixed`、`infinite` | `fixed` |
| 最大尝试次数 | `max-face-tries` | 2 至 20 | 3 |

- `disabled`：一次尝试。失败后，本次周期内的面部认证停止，你用密码完成。
- `fixed`：重试直到失败 `max-face-tries` 次，然后本次周期内停止。
- `infinite`：只要提示框开着就一直重试。密码输入框始终可用。

`max-face-tries` 仅适用于 `fixed` 模式，即便 dconf 中持有更低的值，扩展也会把它限制在最小值 2。

在终端中：

```bash
gsettings set org.gnome.shell.extensions.gaze face-retry-mode infinite
gsettings set org.gnome.shell.extensions.gaze max-face-tries 5
```

要为 GDM 登录界面设置这些项，请将它们写入下面所述的同一个 `/etc/dconf/db/gdm.d/99-gaze` 覆盖文件，并运行 `sudo dconf update`。

## 录入面部

录入不在扩展首选项里。请使用 Gaze 设置应用或 CLI：

```bash
gaze-gui             # Faces list, press + to enroll
gaze add-face default
```

配置文件名默认为 `default`，与 CLI 快速入门流程一致。按照摄像头提示操作，直到配置文件保存。

## 登录警告（GNOME keyring）

GDM 从软件包默认值加载该扩展，但 GDM 登录界面的面部认证默认是关闭的。

这主要与 GNOME keyring 的行为有关。GNOME keyring 通常由你的登录密码解锁。如果你仅用面部登录，那个密码从未被输入，因此 keyring 可能保持锁定。

发生这种情况时，读取已保存机密的那些应用（浏览器凭据、git 凭据、Wi-Fi 机密、聊天客户端等）会一直提示输入 keyring 密码，直到你手动解锁它。

### 可选的 TPM 支持 keyring 解锁

在 `gaze config` 中启用 TPM 模板加密、活体检测以及 GNOME Keyring 解锁。然后录入登录 keyring 密码：

```bash
gaze keyring
```

该密码存储在仅供 root 访问、受 TPM 保护的记录中。它不通过 DBus 发送。更改账户或 keyring 密码后请重新录入。

在 SELinux 系统上（Fedora，以及 2025 年初之后安装的 openSUSE Tumbleweed），GDM 会话 worker 是受限的，无法读取解锁所需的 `/etc/shadow` 或 TPM。`gaze keyring` 会加载 `gaze-greeter-keyring` 策略模块以允许这一点，而 `sudo gaze doctor` 会把它报告为 **Keyring SELinux policy（keyring SELinux 策略）**。

要移除存储的记录，请运行 `gaze keyring --forget`。`gaze clear-user` 也会移除它。管理员可以用 `sudo gaze keyring --user <name>` 对另一个账户操作。

请单独启用 [GDM 面部登录](#optional-enable-face-at-gdm-login)。如果你自己维护 `gdm-face` 文件，请使用以下认证顺序，并保留 session 行：

```pam
auth    required   pam_env.so
auth    [success=1 default=ignore] pam_gaze.so
auth    requisite  pam_deny.so
auth    required   pam_permit.so
auth    optional   pam_gnome_keyring.so use_authtok

session optional   pam_gnome_keyring.so auto_start
```

auth 钩子保存令牌；`session` 钩子启动并解锁 keyring。这仅在 `pam_gaze.so` 处于默认的顺序模式时有效；`simultaneous` 选项不提供令牌。

Gaze 只在面部与活体认证都成功后才设置 `PAM_AUTHTOK`。如果 TPM、记录或密码绑定不可用，GDM 会回退到正常的密码登录。没有运行过 `gaze keyring` 的用户会像往常一样登录，并被像以前一样提示输入 keyring 密码。清除 TPM，或更改账户密码，都需要重新录入。Gaze 无法在录入期间校验 keyring 密码，也无法检测到后来仅改 keyring 的密码变更：一个不正确或过期的密码会让 keyring 保持锁定，需要手动解锁并重新录入。

### 这会如何改变你的安全性

在启用 keyring 解锁之前，请审视这些安全影响。

- **该记录可被本机上的 root 恢复。** 封印没有 PCR 策略，因此任何能在这里以 root 身份运行代码的人，包括从 USB 优盘启动另一个操作系统、针对一块未加密磁盘的人，都能解封密钥并恢复明文密码。它保护的是*被盗的磁盘*，而不是别人能启动的那台机器。如果这事关重大，请启用全盘加密。
- **该密码对 `gdm-face` 栈的其余部分可见。** 一旦设置了 `PAM_AUTHTOK`，该服务中每一个后续的模块都能读取它，包括发行版管理的 `postlogin`、`system-auth` 与 `common-session` 包含项。Linux-PAM 会在服务结束时抹除它。
- **在登录界面，面部等价于你的密码。** 没有这个选项时，一次面部登录只会给攻击者一个桌面会话；有了它，还会给他们你 keyring 里的一切。

### 从较早版本的 Gaze 升级

`/etc/pam.d/gdm-face` 会在软件包升级间被保留，因此已有的安装会保留这个早于该特性、且解锁静默永不发生的栈。请运行 `sudo gaze doctor`：它会报告这个过时的文件以及该如何替换它。

## 可选：在 GDM 登录处启用面部认证

最简单的方式是 [扩展首选项](#open-the-extension-preferences) 中 **Behavior → GDM login screen（行为 → GDM 登录界面）** 下的 **Enable face authentication at GDM login（在 GDM 登录处启用面部认证）** 开关。切换它会触发一个 polkit 提示，然后守护进程为你写入 `/etc/dconf/db/gdm.d/99-gaze` 并运行 `dconf update`。

重启以应用。重启 GDM 也可以，但会立即注销活动的桌面会话。

```bash
sudo reboot
```

### 手动替代方案

如果你更喜欢从终端操作：

```bash
sudo tee /etc/dconf/db/gdm.d/99-gaze >/dev/null <<'EOF'
[org/gnome/shell/extensions/gaze]
enable-face-authentication=true
EOF
sudo dconf update
```

在 GDM 登录界面上，Gaze 仍然针对所选用户已录入的面部进行匹配，它会直接捕获内核摄像头设备，而不是通过任何用户的 PipeWire 会话：当欢迎程序拥有席位时，该尝试被绑定到所选用户，因此后台残留的会话（注销或切换用户之后）无法提供它自己的摄像头流。

## 在 GDM 登录处禁用面部认证

把 **Behavior → GDM login screen（行为 → GDM 登录界面）** 下的 **Enable face authentication at GDM login（在 GDM 登录处启用面部认证）** 开关重新关掉，或者手动移除覆盖文件：

```bash
sudo rm -f /etc/dconf/db/gdm.d/99-gaze*
sudo dconf update
```

## GDM 登录界面上什么也没出现

如果锁屏工作正常，但登录界面从不提供面部认证，且 GDM 日志里也没有任何内容，请检查欢迎程序是否关闭了扩展：

```bash
sudo env DCONF_PROFILE=gdm XDG_CONFIG_HOME=/var/lib/gdm/seat0/config \
  gsettings get org.gnome.shell disable-user-extensions
```

`true` 意味着 GNOME Shell 在欢迎程序中停掉了整个扩展系统，因此无论怎么配置，Gaze 都不会在那里加载。GDM 自己的 dconf 数据库保存这个键，并且优先级高于 Gaze 安装在 `/etc/dconf/db/gdm.d` 下的每一个键文件，因此请从源头清除它并重启：

```bash
sudo rm -f /var/lib/gdm/seat0/config/dconf/user
```

GDM 会用它自己的默认值再次写入该文件。在 Debian 和 Ubuntu 上，路径位于 `/var/lib/gdm3` 下，而拥有多个席位的机器每个席位各有一个目录。`gaze doctor` 会报告这一点并为你点明文件名。

## 验证 GNOME 流程

- 锁屏，然后尝试用面部解锁。
- 如果启用了登录面部认证，请测试一个完整的注销 / 登录周期。
