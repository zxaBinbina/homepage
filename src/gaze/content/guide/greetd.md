<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# greetd

greetd 是一个极简的登录管理器，它将登录界面交给一个独立的 greeter，例如 tuigreet、ReGreet 或 noctalia-greeter。Gaze 通过共享 PAM 栈在其中进行认证，方式与在 LightDM 上相同。

## 配置

greetd 的 PAM 服务包含了共享认证栈，因此按常规方式启用 Gaze 就足够了：

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

:::

某些发行版还会附带一个 `greetd-greeter` 服务。该栈运行的是 greeter 程序本身，而非你的登录过程，Gaze 绝不会向其释放密钥环凭据。

用 `gaze doctor` 确认，然后注销并用你的面孔认证。

## 解锁 GNOME 密钥环

面部登录不提供密码，因此 `pam_gnome_keyring.so` 没有可用于解锁密钥环的凭据，并在桌面就绪后提示一次。Gaze 可以改为向它提供一份受 TPM 保护的密码副本，就像它针对 [GDM](/projects/gaze/guide/gnome#optional-tpm-backed-keyring-unlock) 所做的那样。

在 `gaze config` 中开启模板加密、活体检测与 GNOME 密钥环解锁，然后录入密码：

```bash
sudo gaze config
sudo systemctl restart gazed
gaze keyring
```

在 TPM 清除或账户/密钥环密码变更后重新录入。

### PAM 修改

`/etc/pam.d/greetd` 已有一行密钥环配置，但它不会接收令牌：

```pam
auth       optional    pam_gnome_keyring.so
```

添加 `use_authtok`，并将该行留在原处：

```pam
auth       optional    pam_gnome_keyring.so use_authtok
```

保留已有的 `session optional pam_gnome_keyring.so auto_start` 行。Gaze 不会为你编辑此文件，因为它属于发行版。

与 `gdm-face` 不同，greetd 对面部登录和密码登录使用同一个栈，因此没有 `pam_deny` 闸门。密钥环行只需位于 `system-auth` 之后即可。面部匹配会向它提供所存储的密码，输入的密码则提供你输入的内容，两者皆无则不做任何事。

对于 greetd，请使用此处展示的 PAM 配置，而不要从 `gdm-face` 或 hyprlock 复制 `pam_gaze.so` 行。`[success=1 ...]` 控制会跳过密钥环行，而 `sufficient` 或 `[success=done ...]` 会在它运行之前就结束 auth 段。

`sudo gaze doctor` 会检查顺序，而不仅仅是选项。

### 这对你的安全意味着什么

[GNOME 的安全说明](/projects/gaze/guide/gnome#what-this-changes-about-your-security) 中的全部内容均适用。此外，greetd 的栈是完整的会话栈，而非仅限面部的栈，因此在面部匹配之后，密码对位于密钥环行之后的模块可见。在 Fedora 上是 `postlogin`，在 KDE 安装中是 `pam_kwallet5.so` 与 `pam_kwallet.so` 行。

### SELinux

在 Fedora 上，greeter 需要 `gaze-greeter-keyring` 策略模块才能读取所存储的记录。`gaze keyring` 会加载它，而 `sudo gaze doctor` 会将其报告为 **Keyring SELinux policy（密钥环 SELinux 策略）**。若没有它，登录仍然成功，且密钥环会像之前一样提示。

## 故障排除

`journalctl -b` 中出现的 `gkr-pam: no password is available for user` 表示密钥环行缺少 `use_authtok`、位于 `system-auth` 之前，或被其上方的 `pam_gaze.so` 行跳过。`sudo gaze doctor` 会在 **Keyring** 下报告这三种情况。
