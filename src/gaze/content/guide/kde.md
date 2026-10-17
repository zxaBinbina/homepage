<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# KDE Plasma

在 KDE Plasma 的**锁屏**上，`gaze-kde` 软件包会自动启动面部解锁，无需按键。而**登录欢迎程序**是一个独立的程序，工作方式不同；那里的面部认证默认是关闭的。详情参见[登录欢迎程序](#login-greeter)。

一行式安装程序在检测到 KDE Plasma 会话时会安装 `gaze-kde`，因此这些步骤只在手动安装后才需要。

## 安装

::: code-group

```bash [Debian/Ubuntu]
sudo apt-get install gaze-kde
```

```bash [Fedora and compatible]
sudo dnf install gaze-kde
```

```bash [openSUSE Tumbleweed]
sudo zypper install gaze-kde
```

```bash [Arch]
yay -S gaze-kde-bin
```

:::

`gaze-kde` 会接好锁屏，并添加一个“系统设置”条目。一行式安装程序在检测到 KDE Plasma 会话时会安装它。

锁定屏幕并看向摄像头。面部认证会在密码字段等待期间运行；谁先成功谁获胜。`gaze doctor` 会在“KDE lock screen（KDE 锁屏）”项下报告它是否已接好。

## 系统设置

在 Plasma 6 上，`gaze-kde` 会在“系统管理”下添加一个用 Kirigami 构建的 **Gaze** 页面。它列出已录入的面部，以实时预览进行添加、重命名和删除，测试认证，并显示 Gaze 的每一项设置。在你按下 **Unlock（解锁）** 并用管理员密码授权之前，这些设置是锁定的。应用菜单里的 **Gaze Settings（Gaze 设置）** 启动器会在它自己的窗口中打开同一个页面。

该页面管理运行它的那个用户的面部。同一时间只能有一个应用使用摄像头，因此在 `gaze-gui` 或另一个客户端正在录入时，添加或测试面部会失败，而且一次登录或 `sudo` 提示会取消它。

Ubuntu 24.04 搭载的是 Plasma 5，无法加载该页面，因此在那里 `gaze-kde` 添加的是一个会打开 `gaze-gui` 的 **Gaze** 条目。请务必安装 `gaze-gui` 以使该条目工作；一行式安装程序已包含它。

## 锁屏如何工作

KScreenLocker 的欢迎程序会为一次解锁同时启动三个 PAM 服务：用于密码字段的交互式 `kde` 服务，加上两个*非交互式*、为生物识别提前启动的槽位 `kde-fingerprint` 与 `kde-smartcard`。这正是指纹读取器所使用的同一个槽位，也正是这里之所以能实现无感面部解锁的原因。

`gaze-kde` 把 Gaze 放在这两个槽位之一中，位于一个带标记的块内：

```
# BEGIN gaze (managed by gaze-kde; remove with `gaze-kde-pam disable`)
-auth       requisite                                    pam_nologin.so
-auth       requisite                                    pam_faillock.so    preauth
-auth       [success=done default=ignore]                pam_gaze.so
# END gaze
```

前导的 `-` 表示缺失的模块会被跳过而不是中止整个栈，因此卸载 Gaze 不会留下一个接收输入却从不响应的欢迎程序。那两道门控在[账户锁定](#account-locking)一节说明。

1. 欢迎程序在锁屏一出现、你还没碰任何东西时就调用该服务。
2. Gaze 通过 `gazed` 占用摄像头并验证你的面部。
3. 一旦匹配，`success=done` 结束整个栈，屏幕解锁。
4. 其他任何情况，`default=ignore` 落到栈的其余部分、你若有的指纹读取器，而密码字段始终在持续等待。

### Gaze 占用哪个槽位

通常情况下是 `kde-fingerprint`，其提示文字是锁屏上最接近生物识别标签的东西。

如果指纹读取器已经占用了那个文件，`gaze-kde` 会改用 `kde-smartcard`。对 KScreenLocker 而言这两个槽位是同一套机制，因此移动不会损失什么，反而能换来真正的并发：`pam_fprintd` 会阻塞它完整的 30 秒超时，因此共用一个槽位意味着后运行的模块会被饿死。Gaze 会先占用前十二秒，读取器之后才能轮到。在分开的槽位里两者同时启动，先匹配者获胜。

代价只是外观上的。Plasma 把那个槽位标注为“(or scan your smartcard)（或刷你的智能卡）”，对摄像头而言是错的，不过只要有话可说，Gaze 会立即用一条真实的信息替换它。`gaze doctor` 会报告正在使用哪个槽位，而 `gaze-kde-pam` 绝不会同时接好两个。

要让这一点触发，读取器必须真的存在，而不仅仅是被提及：每个发行版的 `kde-fingerprint` 都会命名 `pam_fprintd`，无论 `fprintd` 是否存在，因此检查的是磁盘上的模块以及 `fprintd` 报告的设备。libfprint 不支持的读取器会让 Gaze 留在 `kde-fingerprint`。

在 openSUSE 和 Gentoo 上，智能卡槽位自带 `pam_pkcs11 wait_for_card`，它会无超时地阻塞。Gaze 在它上方运行，因此面部解锁不受影响，但在一次面部未匹配之后，该模块会为本次锁屏的剩余时间继续占用该槽位。

### 每次锁定只尝试一次

欢迎程序给一个非交互式槽位每次锁定只一次认证：它会刻意忽略生物识别失败，只有在一次*密码*尝试失败时才会重新武装所有东西。由于守护进程在失去对一张脸的视线几秒后就会停止寻找，Gaze 会在它的整个预算内持续内部重试，而不是在第一帧空画面时就放弃。稍后唤醒屏幕并抬头看一眼仍然能解锁。

### 状态消息

锁屏根本没有任何处理来自生物识别槽位的*信息性*消息的处理器，因此任何你需要阅读的内容（“Face not recognized（无法识别面部）”、“Too dark for face authentication（光线太暗，无法进行面部认证）”）都是作为*错误*消息发送的，它会短暂地替换该槽位的提示标签。Gaze 仍然会在它开始寻找时发送一条信息性消息，尽管没有任何东西显示它：这正是告诉欢迎程序这次解锁有过一个提示，没有它的话，一次面部匹配会落在一个额外的“Unlock（解锁）”按钮上，而不是直接进入桌面。

### 每次解锁只运行一个 Gaze

在 Fedora、Debian 和 openSUSE 上，Gaze 会被安装进共享认证栈（`password-auth` 或 `common-auth`），而 `/etc/pam.d/kde` 也包含它。一旦某个生物识别槽位运行了 Gaze，通过那种方式到达它的服务中的模块就会退场，因此单个锁屏不会把面部认证运行两三次，并让那些客户端争抢同一个摄像头。`kde` 会让位给任一个槽位，而如果两者不知何故都各有一行，`kde-smartcard` 会让位给 `kde-fingerprint`。

移除 `gaze-kde` 会自动恢复之前的行为，因为该模块是在认证时通过读取槽位文件来决定，而不是通过一个构建标志。

### 账户锁定

一次 `success=done` 的匹配会结束整个认证栈，因此 Gaze 下方的任何东西都会被跳过，包括本应拒绝你的那些检查。因此 Gaze 会放在该栈门控的**下方**而不是顶端，并在它自己的块内携带 `pam_nologin` 与 `pam_faillock preauth`，以便那些把这两道门控放在 `include` 之后、从而无法在它们下方插入的发行版也能使用。被锁定或被 `nologin` 阻止的账户无法通过面部解锁。

在槽位能到达 `pam_faillock authfail` 的地方（Fedora，经由 `substack fingerprint-auth`），Gaze 在未匹配时会直接让该槽位失败，而不是落到它上面，因此转几次头不会耗尽你的登录尝试并锁住账户。Gaze 绝不会在一个同样服务密码的栈里这么做，因为在那种栈里直接失败会在守护进程宕机时拒绝一个正确的密码。

::: warning 一个无关的上游 bug 仍可能把你锁在外面
在 6.7 之前的 Plasma（以及 6.5.x 和 6.6.x 回移植版本之前），一次*成功*的生物识别解锁会让密码服务中的 `pam_unix` 报告一次失败，因此快速地连续解锁可能会触发 `pam_faillock` 并锁住账户。该问题已在 [kscreenlocker 29d01bf7](https://invent.kde.org/plasma/kscreenlocker/-/commit/29d01bf74958b96b41d1726b5ff6b133a7a0e402) 中修复，并且它对指纹读取器和 Gaze 的影响完全一样。`faillock --user "$USER"` 会显示已记录的内容，而 `faillock --reset` 会清除它。
:::

## require_confirmation_lock_screen

当 `require_confirmation_lock_screen = true` 时，Gaze 会在 KDE 生物识别槽位（`kde-fingerprint`、`kde-smartcard`）以及 Plasma Login Manager 或 SDDM 欢迎程序中返回 `PAM_IGNORE`。这些服务无法呈现一个确认提示，因此 Gaze 不会在你所请求的同意之外进行扫描或静默解锁。改用你的密码；当该开关为一个已接好的 KDE 服务启用时，`gaze doctor` 会报告这个回退。

要在这些界面上实现无感面部解锁，请显式禁用 `require_confirmation_lock_screen`。要获得一个真正的确认步骤，请使用支持它的界面，例如终端或 polkit 对话框。同时模式（`pam_gaze.so simultaneous`）无法在锁屏的非交互式槽位中运行。

## 登录欢迎程序

登录欢迎程序（Plasma Login Manager，或 SDDM）不同于锁屏，是一个独立的程序，并且在今天发布的每个版本上，它都只在你提交登录表单时才启动 PAM。因此那里的面部认证并非无感：请在密码字段为空时按 Enter，并看向摄像头。

这一行为来自欢迎程序，而非来自 Gaze。作为对比，**指纹读取器在这个屏幕上的表现完全相同。** `pam_fprintd` 进入同一个 `plasmalogin` 或 `sddm` 栈，那个栈在提交时运行，并且每个发行版的指纹说明都告诉你在刷卡之前先在空字段上按 Enter。两种方法都不会在你输入之前扫描，因为两者都无法决定欢迎程序何时调用 PAM。

它默认是关闭的。要打开它：

```bash
sudo gaze-kde-pam enable-login
```

这会把 Gaze 插入 `/etc/pam.d/plasmalogin` 与 `/etc/pam.d/sddm`（以实际存在的为准），位置在该栈的门控模块（`pam_nologin`、对 `user != root` 的检查、`pam_selinux_permit`）之后，这样一次面部匹配就无法跳过它们。用 `sudo gaze-kde-pam disable-login` 把它关回去。

一个服务只要在 `/usr/lib/pam.d` 中也有文件就算存在，Fedora 的 `plasma-login-manager` 就是把 `plasmalogin` 放在那里的：在那里、在有人自定义该栈之前，`/etc/pam.d` 下什么都不会出现，而 PAM 在此期间会回退到供应商副本。`enable-login` 会读取欢迎程序真正会使用两者中的哪一个，因此它在那些系统上既不会报告缺失的登录栈，也不会在没有可添加块的地方写入一个 `/etc` 文件。

在 Fedora、Debian 和 openSUSE 上，共享认证栈可能已经在运行 Gaze。`enable-login` 会添加一个受管理的顺序登录记录，以便 KWallet 在认证结束前收到凭据。该记录会在 PAM 中标记它的尝试；在密码回退期间，共享栈中后面的 Gaze 记录会退场，从而避免第二次扫描。该辅助脚本还会在发行版的 session 设置之后追加一个 KWallet session 钩子。重新运行它会刷新较旧的受管理块；不受管理的自定义 Gaze 记录留给管理员去更新。

### 欢迎程序处的无感解锁

上游正在 Plasma Login Manager 中修复这一点，而不是在 SDDM 中。相关工作是 [plasma-login-manager!185](https://invent.kde.org/plasma/plasma-login-manager/-/merge_requests/185)，它把密码认证与生物识别认证作为两个独立的辅助进程来运行：生物识别的那个在欢迎程序选好一个用户和一个会话后立即启动，一个错误的密码不会让它停下，而先成功的方法会启动会话。它会安装一个专用的 `plasmalogin-fingerprint` PAM 服务，正是锁屏上 `kde-fingerprint` 的对等物。

`enable-login` 已经处理了这一点。如果 `plasmalogin-fingerprint` 存在于 `/etc/pam.d` 或供应商目录中，Gaze 就会进入那里，并为了与锁屏上相同的原因排在 `pam_fprintd` 之前，于是面部认证会在你碰任何东西之前就运行。如果它不存在，则什么都不写入，你会得到上面那种由提交触发的路径。这个选择会被记住，因此当你的发行版发布一个带有该变更的 Plasma Login Manager 时，下一次 `gaze-kde` 升级无需你运行任何命令就会接好它。

即便如此，有两件事依然成立：

- 它只扫描**预选**的用户。PAM 需要先有一个用户名才能验证任何人，因此在配置为要求你输入用户名的欢迎程序上，在你提交之前没有可扫描的人。这与 Gaze 在 GDM 登录界面上所受的约束相同。
- 在 Gaze 也处于 `plasmalogin` 栈中的地方（无论是直接还是通过 `password-auth`），一旦前端服务运行了它，该模块就会在那里退场，因此一次提交不会启动两个争抢摄像头的扫描。

这里没有任何东西适用于 SDDM。上游的答复一直是：这一点要在 Plasma Login Manager 中解决。

### 可选的 TPM 支持 KWallet 解锁

KWallet 通常会复用你的登录密码。在面部登录之后，除非你手动解锁或录入一个可选的 TPM 保护凭据，否则它会保持锁定。这在 `sddm`、`plasmalogin` 与 `plasmalogin-fingerprint` 的顺序 PAM 模式下有效。锁屏解锁不需要、也不会释放钱包密码。

在 **NixOS** 上，请改用 [`services.gaze.kde.unlockKwallet`](/projects/gaze/guide/nixos#kde-plasma)，而不是下面的 PAM 辅助脚本；该模块以声明式管理这些钩子。

1. 安装你的发行版中提供 `pam_kwallet5.so` 的 KWallet PAM 软件包（通常是 `kwallet-pam` 或 `libpam-kwallet5`）。请使用一个密码加密的 `kdewallet`；KWallet 的 PAM 集成不支持 GPG 加密的钱包。
2. 在 `gaze config` 中启用 TPM 模板加密、活体检测以及 **KWallet unlock（KWallet 解锁）**。GUI 暴露的是同一个存储开关。这会设置 `storage.unlock_kwallet = true`；其默认值为 `false`。
3. 录入你的钱包密码并刷新登录 PAM 集成：

   ```bash
   gaze keyring --kwallet
   sudo gaze-kde-pam enable-login
   gaze doctor
   ```

该凭据独立于 GNOME Keyring 录入，因此两个钱包可以有不同的密码。它加密存储在 `/var/lib/gaze/kwallet` 下，从不通过 DBus 发送。在面部认证与活体检测都成功后，PAM 模块把它提供给 KWallet 的认证钩子；session 钩子打开钱包。

在 SELinux 系统上，欢迎程序的 PAM worker 是受限的，无法读取解锁所需的 `/etc/shadow` 或 TPM。`gaze keyring --kwallet` 会加载 `gaze-greeter-keyring` 策略模块以允许这一点，而 `sudo gaze doctor` 会把它报告为 **Keyring SELinux policy（keyring SELinux 策略）**。
该辅助脚本会保留发行版的密码回退与 session 设置。没有录入凭据的用户仍能用面部登录，并在自己的会话中解锁钱包，而无需额外的欢迎程序密码提示。

在更改你的账户或钱包密码或重置 TPM 之后，请重新录入。一条不可读或无效的存储记录会请求密码回退。Gaze 无法在录入期间校验钱包密码，也无法检测到仅改钱包的密码变更：一个不正确或过期的密码会让钱包保持锁定。如果你在欢迎程序中输入了非空密码，那个已有的 PAM 令牌将优先。

```bash
gaze keyring --kwallet --forget          # remove only the KWallet credential
sudo gaze keyring --kwallet --user alice # enroll for another user
```

`gaze clear-user` 会同时移除 GNOME Keyring 与 KWallet 记录。同时模式与 grosshack 认证不会释放钱包凭据。受管理的 KDE 登录记录使用顺序模式，并在密码回退期间防止共享 Gaze 栈中的第二次扫描。

这个选择项会让任何能通过你的面部与活体检测检查的人都能访问该钱包。它具有与 [GNOME Keyring 解锁相同的 TPM 与生物识别安全限制](/projects/gaze/guide/gnome#optional-tpm-backed-keyring-unlock)。

该交接遵循 [KWallet PAM 的 auth/session 实现](https://github.com/KDE/kwallet-pam/blob/master/pam_kwallet.c)。


## 手动管理

`gaze-kde-pam` 就是该软件包的安装与卸载脚本所调用的同一个辅助脚本：

```bash
sudo gaze-kde-pam enable         # lock screen
sudo gaze-kde-pam disable
sudo gaze-kde-pam enable-login   # login greeter (opt-in)
sudo gaze-kde-pam disable-login
gaze-kde-pam status
```

它在带标记的块内就地编辑该槽位，因为在大多数发行版上那个文件属于 `plasma-workspace`，覆盖它会让你的指纹读取器丢失。你自己添加在标记块之外的 `pam_gaze` 行则原样保留。

在发行版把该服务放在 `/usr/lib/pam.d` 而不是 `/etc` 下的地方（Arch、Debian、Ubuntu、Fedora 和 openSUSE 都至少对一个服务如此），`enable` 会先把它复制到 `/etc/pam.d` 再编辑副本，因为在 `/etc` 中的文件会遮蔽供应商文件，而在那里写一个全新文件会静默丢弃发行版配置的任何内容。`disable` 会再次删除那个副本，从而让供应商栈恢复权威，除非它自 Gaze 写入后被改动过，那样的话只会移除 Gaze 块。在任何一个地方都不存在这种文件时，`enable` 会创建一个，`disable` 会移除它。`enable-login` 与 `disable-login` 对欢迎程序的栈做同样的事，并且只在有可写的块时才制作副本。

那些供应商文件没有一个被打包为配置文件，因此后来的发行版更新不会产生 `.pacnew` 或 `.rpmnew` 来告诉你你的 `/etc` 副本已经过时。`gaze doctor` 与 `gaze-kde-pam status` 会把供应商文件与所复制的内容进行比较，并在它已演进时发出警告。

`gaze-kde-pam disable` 会被记住，因此软件包升级不会悄悄地把面部解锁重新打开。请用 `enable --force` 来撤销它。

## 前置条件

- `gazed` 正在运行（`systemctl status gazed`）
- 至少一个已录入的面部：`gaze add-face default`
- 可用的摄像头（用 `gaze auth` 测试）

## 登录欢迎程序上的摄像头

锁屏运行在你的会话内部，因此摄像头在那里的工作方式与在 `sudo` 处完全一样。登录欢迎程序不在你的会话内部运行：SDDM 与 Plasma Login Manager 的欢迎程序账户没有用户会话，因此也就没有 PipeWire，这与 GDM 不同。这对认证没有任何影响，因为认证总是直接捕获内核的 V4L2 设备，因此 `rgb = "primary"` 在欢迎程序处仍然有效。

如果那里的摄像头没有被识别到，请显式指名：

```toml
[cameras]
rgb = "usb:046d:085e"   # hex VID:PID from `lsusb`
```

有关摄像头选项的完整集合，请参见[配置](/projects/gaze/guide/configuration)。

## 禁用

::: code-group

```bash [Debian/Ubuntu]
sudo apt-get remove gaze-kde
```

```bash [Fedora and compatible]
sudo dnf remove gaze-kde
```

```bash [openSUSE Tumbleweed]
sudo zypper remove gaze-kde
```

```bash [Arch]
yay -R gaze-kde-bin
```

:::

## 故障排查

- **面部解锁仍在等待提交密码。** `kde-fingerprint` 没有在运行 Gaze。请检查 `gaze doctor` 中的 “KDE lock screen（KDE 锁屏）” 行，然后运行 `sudo gaze-kde-pam enable`。
- **`gaze doctor` 警告 `kde-fingerprint` 以同时模式运行 `pam_gaze.so`。** 该模式会等待一个欢迎程序永远无法应答的密码提示。请在那里改用普通的 `pam_gaze.so` 行；重新安装 `gaze-kde` 可以修复它。
- **每次都回退到密码。** 请检查 `systemctl status gazed` 与 `gaze list-faces`。最常见的原因是守护进程没有运行，或者当前用户没有录入的面部。
- **摄像头忙。** 另一个 Gaze 客户端（GUI，或混合安装中的 GNOME 扩展）占用了摄像头。请关闭它并重试。
- **Gaze 条目没有出现在系统设置中。** 请重启系统设置；它只在启动时扫描模块。如果仍不出现，请检查 `gaze-kde` 是否已安装。在 Ubuntu 24.04 上，还要检查 `/usr/share/plasma/systemsettings/externalmodules/gaze-face-unlock.desktop` 是否存在，以及 `gaze-gui` 是否已安装。
- **摄像头在登录欢迎程序处从未开启。** 那条路径是选择加入的；请运行 `sudo gaze-kde-pam enable-login`。请记住它只在你提交表单时才启动。
