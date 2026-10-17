<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# PAM（可插拔认证模块）

使用本指南为 `sudo`、polkit 以及共享 PAM 栈配置面部认证。

`gaze auth` 是检查守护进程与摄像头的好办法，但它并不测试 PAM 栈本身。

如果你特别需要 GNOME 锁屏或 GDM 登录的行为，请使用 [GNOME 扩展指南](/projects/gaze/guide/gnome)。

## Gaze 安装的内容

- `pam_gaze.so`（支持顺序、同时、重试三种模式）

`pam_gaze_grosshack.so` 在 openSUSE 上仍作为兼容垫片随包提供，用于兼容旧配置。它已被弃用，每次认证都会打印一条提示，并将被移除；它并不提供 `pam_gaze.so simultaneous` 所不具备的任何功能。

在顺序模式（默认）下，Gaze 先尝试面部认证，随后回退到密码提示。使用 `simultaneous` 选项（例如 `pam_gaze.so simultaneous`）时，面部认证与密码提示同时运行。`retry` 选项（例如 `pam_gaze.so retry`）会在密码模块*下方*再添加一条 Gaze 记录，使密码被拒绝后还能再获得一次面部认证的机会。参见[密码被拒绝后重试](#retry-after-a-rejected-password)。

### 可信守护进程连接

PAM 直接连接 `/run/dbus/system_bus_socket`，忽略 `DBUS_SYSTEM_BUS_ADDRESS`。它会校验 Gaze 的总线名归 UID 0 所有，并将请求绑定到该唯一持有者。守护进程缺失、不可信或断开连接时，会触发密码回退，绝不会完成一次成功的面部登录。

### 仅靠面部的 GDM 锁定

打包的 `gdm-face` 栈（包括 NixOS）会在扫描之前应用 `pam_faillock`，记录明确的面部拒绝，并在面部认证成功时清空计数。系统的 faillock 策略控制尝试次数上限与解锁间隔。摄像头不可用、用户未录入时，仅靠面部的栈会认证失败，但不会增减失败次数，因此自动扫描不会仅仅因为面部认证不可用就锁死密码登录。

### 网络登录会被跳过

连接在本机上的摄像头看不到网络登录另一端的人，因此 Gaze 会为它们让路。当调用服务将 `PAM_RHOST` 设为除回环地址以外的任何值时，`pam_gaze.so` 会立即返回 `PAM_IGNORE`，栈随即落到下一个模块，通常就是密码检查。对远程客户端进行认证的服务会设置此项：`sshd`、`dovecot`、`vsftpd` 以及 Samba 等。

Gaze 还会按 PAM 服务名跳过已知的网络守护进程，即便客户端通过回环地址连接也是如此，例如在同一个机器上、连向 `127.0.0.1` 的邮件客户端。站在摄像头前的一张脸绝不能替那个打开连接的人背书。被跳过的服务包括：`sshd`、`dovecot`、`imap`、`imaps`、`pop3`、`pop3s`、`smtp`、`sieve`、`managesieve`、`vsftpd`、`proftpd`、`pure-ftpd`、`ftp`、`samba`、`cups`、`openvpn`、`radiusd`、`ppp`、`xrdp-sesman` 以及 `cockpit`。

这一点在 Debian 和 Ubuntu 上很重要：通过 `pam-auth-update` 启用一个 Gaze 配置项会把 Gaze 放入 `common-auth`，而 `common-auth` 会被系统中几乎每个服务包含，不只是桌面服务。那些服务仍会像以前一样通过密码进行认证。

### 以 root 身份运行的服务必须确认是本地

一份名单无法覆盖每一个网络守护进程。JupyterHub、Webmin、RStudio Server 以及各类 VNC 服务器都以 root 身份认证，且常常不设置 `PAM_RHOST`，所以一份排除名单会让网络上的人趁你坐在桌前时提交你的用户名、并让摄像头批准他们。因此，以 root 身份运行的 PAM 主机，只会对 Gaze 确认是“为本机前的人服务”的那些服务开放面部认证：

- 提权类：`sudo`、`sudo-i`、`su`、`su-l`、`doas`、`run0`、`systemd-run0`、`polkit-1`、`pkexec`
- 登录欢迎程序：`gdm-password`、`gdm-launch-environment`、`gdm-face`、`sddm`、`plasmalogin`、`plasmalogin-fingerprint`、`lightdm`、`greetd`、`cosmic-greeter`、`ly`、`lemurs`、`lxdm`
- KDE 锁屏槽位以及 Omarchy 的面部服务
- `login`，但仅限于虚拟控制台（`PAM_TTY` 为 `ttyN`），因为 `login` 同时也是 JupyterHub 等 Web 登录的默认服务

其他任何以 root 身份运行的服务都会落到密码认证。以你的身份运行的锁屏（hyprlock、swaylock，以及 KDE 和 Cinnamon 的锁屏）不受影响，因为它们只能询问自己的用户。

如果你使用的某个以 root 运行欢迎程序或锁屏不在列表中，请在 `/etc/pam.d` 下该服务自己的文件中，为 `pam_gaze.so` 那一行加上 `local` 选项，切勿在 `common-auth` 或 `system-auth` 这样的共享文件中添加：

```text
auth    [success=done default=ignore]    pam_gaze.so local
```

未知选项会被忽略，并在系统日志中给出警告，因此如果某个选项似乎没有生效，请运行 `journalctl -g pam_gaze`。

## Debian / Ubuntu

软件包为 `pam-auth-update` 安装了 PAM 配置项。

应用或重新应用它们：

```bash
sudo pam-auth-update --package
```

选择其中一个 Gaze 条目，然后用一个真实的 PAM 提示进行测试：

```bash
sudo -v
```

如果摄像头打开且面部认证运行，说明 PAM 接线已生效。

### 选择性配置：GDM 处用密码，sudo 与 Polkit 处用面部认证

在 GNOME 系统上，一些用户可能希望在初次 GDM 登录时仍使用密码认证，以便 GNOME Keyring 正常解锁（参见[登录警告](/projects/gaze/guide/gnome#login-warning-gnome-keyring)），同时仍用 Gaze 进行提权和图形化的 Polkit 提示。

通过 `pam-auth-update` 启用 Debian/Ubuntu 的 Gaze 配置项会把 Gaze 加入共享的 `common-auth` 栈。由于 `gdm-password` 也包含 `common-auth`，这可能会导致 Gaze 在初次桌面登录时也运行。

以下配置已在 Ubuntu 26.04 配 GNOME 50 上手动机验证通过。

::: warning
PAM 配置错误可能导致无法认证。在编辑这些文件之前，请保持一个活动的 root shell 打开、保持密码认证启用，并先做好备份。
:::

首先禁用共享的 Gaze 配置项：

```bash
sudo pam-auth-update --disable gaze gaze-simultaneous gaze-retry
```

`--disable`（而不是 `--remove`）会记录该选择，因此 Gaze 软件包安装后脚本里的 `pam-auth-update --package` 调用不会在下一次升级时重新启用该配置项。

确认 Gaze 已不在共享栈中：

```bash
grep -n pam_gaze /etc/pam.d/common-auth \
  || echo "Gaze is not enabled in common-auth"
```

保持 GDM 面部登录开关处于关闭状态。该开关位于 Gaze 扩展的首选项里（参见[在 GDM 登录处禁用面部认证](/projects/gaze/guide/gnome#disable-face-at-gdm-login)）；守护进程开启它时会写入下面的覆盖文件，因此如果它已经存在就将其删除：

```bash
sudo rm -f /etc/dconf/db/gdm.d/99-gaze*
sudo dconf update
```

#### sudo

备份 `/etc/pam.d/sudo`，然后紧接在 `@include common-auth` 之前添加这一行：

```text
auth    sufficient    pam_gaze.so
```

相关部分应如下所示：

```text
auth    sufficient    pam_gaze.so
@include common-auth
```

用以下命令测试：

```bash
sudo -k
sudo -v
```

如果想在 `sudo -i` 上也使用面部认证，可对 `/etc/pam.d/sudo-i` 做同样的修改。

这两个文件都是 dpkg 的 conffile，因此 `sudo` 软件包升级时可能会就本地修改进行询问。请保留修改后的版本以保留面部认证。

#### Polkit

如果 `/etc/pam.d/polkit-1` 不存在但供应商文件可用，请创建一个本地覆盖文件：

```bash
sudo install -o root -g root -m 0644 \
  /usr/lib/pam.d/polkit-1 \
  /etc/pam.d/polkit-1
```

在 `@include common-auth` 之前紧接添加这一行：

```text
auth    sufficient    pam_gaze.so
```

重启 Polkit 并测试一个图形化认证请求：

```bash
sudo systemctl restart polkit
pkexec /usr/bin/true
```

`/etc/pam.d` 下的文件会永久遮蔽供应商文件，因此这个覆盖文件不会吸收 Polkit 栈的上游变更。在 Polkit 升级后，请将其与 `/usr/lib/pam.d/polkit-1` 进行 diff 比对。

最后，确认 Gaze 仍看到一个活跃的 PAM 接线。`gaze doctor` 会扫描 `/etc/pam.d` 下的每个文件，因此按服务进行的配置也满足其 PAM 检查：

```bash
gaze doctor
```

在此安排下：

- GDM 登录使用普通的账户密码。
- GNOME Keyring 在登录时被解锁。
- `sudo` 和 `sudo -i` 可以使用面部认证。
- GNOME 设置、软件包管理应用以及其他 Polkit 客户端可以使用面部认证。
- GNOME 扩展可以保持启用，以在锁屏上进行面部解锁。
- 密码认证仍作为回退可用。

## Fedora 及兼容的 RPM 系统

RPM 软件包在以下位置安装了一个 authselect 配置项：

`/usr/share/authselect/vendor/gaze`

该配置项把 Gaze 加入两个共享认证栈：`system-auth`（被 `sudo` 等工具使用）和 `password-auth`（被 KDE 锁屏、SDDM 以及 Plasma Login Manager 使用）。当 Gaze 配置项处于启用状态时，RPM 升级会自动刷新这些生成的 PAM 文件。authselect 会重新生成 `/etc/pam.d/system-auth` 和 `password-auth`，因此请编辑该配置项的特征，而不是编辑那些文件。

启用 `with-fingerprint` 后，Gaze 会在 `pam_fprintd` 之前运行，因此指纹提示只会在面部认证失败后才出现。如果同时还启用了 `with-pam-u2f-2fa`，则安全密钥既在指纹之前、也在面部之前被要求。

::: tip KDE 锁屏需要 `gaze-kde` 才能实现无感解锁
处于 `password-auth` 中意味着 KDE 锁屏认证时会运行 Gaze，但单凭这一点，它只会在你提交密码字段后才发生一次。要实现自动启动的面部解锁，请安装 `gaze-kde`，它会在 KScreenLocker 为生物识别提前启动的槽位中运行 Gaze。它还能避免在同一个锁屏上让 Gaze 运行两次，因为 `/etc/pam.d/kde` 包含了 `password-auth`。参见 [KDE Plasma 指南](/projects/gaze/guide/kde)。
:::

启用它：

```bash
sudo authselect select gaze with-silent-lastlog --force
```

或为同时模式：

```bash
sudo authselect select gaze with-face-simultaneous with-silent-lastlog --force
```

在以上任一基础上添加“密码被拒绝后重试”：

```bash
sudo authselect enable-feature with-face-retry
```

验证配置项 + PAM 行为：

```bash
sudo authselect current
sudo -v
```

## openSUSE Tumbleweed

openSUSE 软件包为 Gaze 附带了一个 `pam-config` 定义，并在其后安装脚本中启用它。这会把 Gaze 加入受管理的 `common-auth` 栈，覆盖 `sudo`、GDM、GNOME 锁屏以及其他包含 `common-auth` 的 PAM 服务。在更改 PAM 模块后若要再次应用，请运行：

```bash
sudo pam-config --add --gaze
sudo pam-config --update
```

`--gaze` 选项由 Gaze 软件包在 `/usr/lib/pam-config.d` 下的定义提供。如果 `pam-config` 报告未知选项，请确认已安装基础的 `gaze` 软件包（而不只是 `gaze-gui` 或 GNOME 扩展）。

### sudo 要求输入 root 密码

openSUSE 的供应商文件 `/usr/etc/sudoers` 设置了 `Defaults targetpw`，因此 `sudo` 认证的是目标用户（root）而不是你。root 没有录入面部，所以摄像头永远不会启动，即便 `gaze auth` 和 `sudo -u "$USER" -v` 能工作，`sudo` 仍会要求输入 root 密码。`gaze doctor` 将这一情况报告为 **Sudo policy（sudo 策略）**。openSUSE 附带了一个让 `wheel` 组成员豁免的 drop-in：

```bash
sudo zypper install sudo-policy-wheel-auth-self
```

此后，`sudo` 会用你自己的密码或面部认证你。在 `wheel` 之外，请用 `visudo` 去掉 `Defaults targetpw`，或用 `Defaults:%<group> !targetpw` 限制其作用范围。

### openSUSE 上的同时模式

没有针对同时模式的 `pam-config` 定义。该软件包只附带 `--gaze`（顺序模式），因此要手动添加 `simultaneous` 选项：先运行 `sudo pam-config --add --gaze && sudo pam-config --update`，然后编辑生成的 `/etc/pam.d/common-auth-pc`，使 Gaze 那一行变为

```text
auth    sufficient    pam_gaze.so simultaneous
```

`pam-config --update` 会重新生成该文件，因此在此后任何一次 `pam-config` 运行之后，都要重新应用该修改。

::: warning `pam_gaze_grosshack.so` 已弃用
较早的 openSUSE 说明使用了 `sudo pam-config --add --gaze_grosshack`。该定义已不再随包提供，它所启用的模块会在每次认证时打印一条弃用提示，并将在未来的版本中被移除。如果 `/etc/pam.d` 仍引用它，请用 `sudo pam-config --delete --gaze_grosshack` 将其移除，并改用 `pam_gaze.so simultaneous`。`gaze doctor` 会报告一个仍在加载它的栈。
:::

### openSUSE 上的重试模式

重试模式在 openSUSE 上不可用。`pam-config` 会把 `pam_unix.so` 写成 `required`，除非同时启用了 LDAP、Kerberos、SSSD 或 Winbind 模块；而一旦某个 `required` 模块失败，后面即使面部匹配也无法把结果变为成功。早期的软件包仍然附带了一个 `--gaze_retry` 定义；它虽显示“Face Verified.”，但 `sudo` 依旧拒绝。升级会从 `/etc/pam.d/common-auth-pc` 中移除那一行。

检查受管理的文件包含 Gaze，并且 common-auth 的链接仍指向生成的文件：

```bash
grep pam_gaze /etc/pam.d/common-auth-pc
readlink -f /etc/pam.d/common-auth
gaze doctor
```

在测试对共享认证栈的改动时，请保持一个 root shell 打开。如果你的安装中 `common-auth` 不由 `pam-config` 管理，请遵循[其他发行版（手动）](#other-distros-manual)，改为把 `pam_gaze.so` 加入特定服务的 PAM 文件。

## Arch Linux / Manjaro

一行式安装程序以及 AUR 软件包的安装后脚本都会自动配置 `/etc/pam.d/sudo`，在原有的 `auth include system-auth` 行之前插入一个 faillock 预认证门控以及 `pam_gaze.so`。该门控先运行，因此被锁定的账户会在面部认证成功之前就被拒绝；它们只做一次：如果你再次移除了这些行，升级时会保留移除的状态。参见[退出 sudo 改动](#opting-out-of-the-sudo-change)。

如果你需要手动应用或重新应用：

```bash
sudo awk '
    /^[[:space:]]*auth[[:space:]]/ && !done {
        print "-auth       requisite     pam_faillock.so preauth"
        print "auth        sufficient    pam_gaze.so"
        done = 1
    }
    { print }
' /etc/pam.d/sudo | sudo tee /tmp/pam-sudo-new && sudo install -m 644 /tmp/pam-sudo-new /etc/pam.d/sudo
```

一次成功的面部认证会跳过栈的其余部分，因此预认证门控必须排在前面：如果没有它，被锁定的账户仍可能通过面部认证。如果该文件的第一条 `auth` 行已经是 faillock 预认证，则只在其下方添加那条 `pam_gaze.so` 行。

然后测试：

```bash
sudo -v
```

::: warning pambase 更新
`/etc/pam.d/system-auth` 归 `pambase` 软件包所有，会在系统升级时被覆盖。Gaze 直接加入 `/etc/pam.d/sudo` 以避开这一点，但如果你曾手动把 `pam_gaze.so` 加入 `system-auth`，它会在 `pambase` 更新时丢失。
:::

### 退出 sudo 改动

`/etc/pam.d/sudo` 属于 `sudo` 软件包，而不是 Gaze。一旦 Gaze 插入了它自己的行，pacman 就会把该文件视为本地修改，并在以后的 `sudo` 更新时写入 `/etc/pam.d/sudo.pacnew` 而不是替换它，因此那些更新需要手动合并。

要把面部认证排除在终端提权之外，请删除 `pam_gaze.so` 那一行以及它上方的 faillock 门控：

```bash
sudo sed -i '/pam_gaze/d; /^-auth       requisite     pam_faillock\.so preauth$/d' /etc/pam.d/sudo
```

Gaze 不会再把它加回来。下一次安装或升级会注意到它写入的那一行已消失，把这一选择记录到 `/etc/gaze/pam-sudo.optout`，此后便不再动该文件。一旦该标记存在，`gaze doctor` 就会把 sudo 槽位报告为已关闭，而不是就此发出警告。

如果想跳过等待，或者想从首次安装起就让 Gaze 远离 `/etc/pam.d/sudo`，可以自己写入该标记：

```bash
sudo mkdir -p /etc/gaze
sudo touch /etc/gaze/pam-sudo.optout
```

要撤销退出，请移除该标记，并用上面的 `awk` 命令手动重新应用那一行：

```bash
sudo rm /etc/gaze/pam-sudo.optout
```

移除 Gaze 软件包会连同 `/etc/gaze` 的其余部分一起删除该标记。

### Polkit（图形化的“需要认证”提示）

Arch 的 `polkit` 软件包不自带 `/etc/pam.d/polkit-1`，因此 `polkit-1` PAM 服务会回退到 `/usr/lib/pam.d/polkit-1` 处的供应商默认值，后者只是 `include system-auth`。由于 Gaze 避免修补 `system-auth`（见上文），图形化 polkit 提示（`pkexec`、GNOME 设置、软件包管理器 GUI 等）不会获得面部认证，除非同时也安装了 `/etc/pam.d/polkit-1` 覆盖文件。Arch 软件包和 `dev-link-system.sh` 会自动创建一个，且仅在 Arch 上：

```text
#%PAM-1.0
-auth       requisite     pam_faillock.so preauth
auth       sufficient   pam_gaze.so
auth       include      system-auth
account    include      system-auth
password   include      system-auth
session    include      system-auth
```

用以下命令验证：

```bash
sudo systemctl restart polkit
pkexec true
```

某些 Arch 衍生版（例如 Omarchy）确实自带自己的 `/etc/pam.d/polkit-1`。在那里，软件包只在第一条 `auth` 行上方添加 `pam_gaze.so` 那一行，并保留文件的其余部分不变；原文件会先被复制到 `/etc/gaze/polkit-1.pam.bak`（`dev-link-system.sh` 也做同样的事，复制到 `polkit-1.pam.dev.bak`）。移除 Gaze 会把那一行剥离并保留该文件，而不是删除一个并非 Gaze 创建的文件。

Debian/Ubuntu 和 Fedora 自带各自的 `polkit-1` PAM 服务，且不像 Arch 那样使用 `system-auth`，因此 Gaze 从不在那里写入此文件。在这些系统上，polkit 通过共享认证栈获得面部认证（Debian/Ubuntu 上的 `pam-auth-update`，Fedora 上的 `gaze` authselect 特征）。较新的 Debian 和 Ubuntu 版本将该文件作为供应商默认值放在 `/usr/lib/pam.d/polkit-1` 而不是 `/etc/pam.d/polkit-1`，但它仍然包含 `common-auth`，因此共享栈的路线两种方式都行得通。只有在你刻意把 Gaze 移出共享栈时（如[选择性配置](#selective-setup-password-at-gdm-face-authentication-for-sudo-and-polkit)中所做的那样），才需要在那里显式添加一个 `/etc/pam.d/polkit-1` 覆盖文件。

## 其他发行版（手动）

编辑你的共享认证栈（例如 Fedora 或 Arch 上的 `/etc/pam.d/system-auth`，或 `pam-config` 不可用时 openSUSE 上的 `/etc/pam.d/common-auth-pc`），把 Gaze 放在 `pam_unix.so` 之前。

顺序模式：

```text
auth    sufficient    pam_gaze.so
auth    sufficient    pam_unix.so try_first_pass nullok
```

同时模式：

```text
auth    sufficient    pam_gaze.so simultaneous
auth    sufficient    pam_unix.so try_first_pass nullok
```

然后用 `sudo -v` 测试。

## 密码被拒绝后重试

默认情况下，键入的密码会结束 Gaze 的尝试。在同时模式下，你一旦提交密码，Gaze 就会退场；如果那个密码最终是错的，整个认证就失败了：不会再有一次看向摄像头的机会。

`retry` 选项补上了这一次。它是放在密码模块*下方*的第二条 `pam_gaze.so` 行，因此只有在密码被拒绝时才会被触及：

```text
auth    sufficient    pam_gaze.so simultaneous
auth    sufficient    pam_unix.so try_first_pass nullok
auth    sufficient    pam_gaze.so retry
```

第一行仍然提供“面部或密码”。第三行才是用来兜住输错的情况：密码被拒绝，Gaze 再看一眼，而不是直接让这次尝试失败。

密码模块不能是 `required`。一旦某个 `required` 模块失败，无论后面那条 `sufficient` 行返回什么，PAM 都会让整个栈失败，因此重试可能匹配到你的脸、而登录却仍被拒绝。

重试可与任一模式组合，因此单独使用 `pam_gaze.so` 作为第一行也同样有效。

### 它不会重复一个已作出的判定

重试记录并非在所有情况下都是第二次完整的摄像头运行。当第一条 Gaze 记录已经看到一张脸并判定那不是你时，重试记录会立即退场，而不是就一个已有答案的问题再耗费一次摄像头超时。它只会在第一次处理“未决”时再看一次：没找到脸、太暗、超时、摄像头不可用，或者摄像头得出判定之前就提交了密码。

### 启用它

在 Debian 和 Ubuntu 上，该配置项随包提供但默认关闭：

```bash
sudo pam-auth-update --enable gaze-retry
```

在 Fedora 上，它是一个 authselect 特征：

```bash
sudo authselect enable-feature with-face-retry
```

### 锁定计数

一次被拒绝的密码仍然就是一次被拒绝的密码。在使用 `pam_faillock` 的发行版上，即便随后的面部重试成功了，这次失败尝试也可能被记入。Fedora 随包提供的配置项把重试记录放在 `pam_faillock.so authfail` 的*上方*，这样一次成功的重试会在计数写入之前短路掉，但你自己手工拼装的栈不会这么做，除非你也按同样的顺序排列。

如果你经常输错密码并依赖重试，请在几次尝试后用 `faillock --user $USER` 检查一下，确认你的栈行为符合预期。

## 通过 Polkit 实现的浏览器扩展（Bitwarden）

浏览器扩展无法直接调用 PAM。Bitwarden 的浏览器扩展通过本地消息机制，把一个解锁请求交给正在运行的 Bitwarden 桌面应用。在 Linux 上，桌面应用会请求 Polkit 授权 `com.bitwarden.Bitwarden.unlock` 动作，而图形化 Polkit 代理会运行普通的 `polkit-1` PAM 服务。因此 Gaze 不需要任何针对 Firefox、Chromium 或 Zen 的特殊钩子：只要 Gaze 在 `polkit-1` 栈中，该请求就会走与其他任何图形化认证提示相同的路径。

按顺序设置并测试各层：

1. 遵循上文针对你的发行版的 Polkit 配置，然后检查一次普通的 Polkit 请求是否会启动 Gaze：

   ```bash
   gaze doctor
   pkexec /usr/bin/true
   ```

2. 在 Bitwarden 桌面应用中，启用 **Unlock with system authentication（使用系统认证解锁）** 与 **Allow browser integration（允许浏览器集成）**。在设置扩展时，保持桌面应用运行、已登录且已解锁。
3. 在浏览器扩展中，打开 **Settings → Account security（设置 → 账户安全）**，启用 **Unlock with biometrics（使用生物识别解锁）**，并在桌面应用中批准该连接。有关浏览器与软件包相关的具体要求，请参见 [Bitwarden 的生物识别解锁指南](https://bitwarden.com/help/biometrics/)。

如果桌面解锁已经使用 Gaze，但浏览器扩展从不弹出 Polkit 对话框，说明该请求没有到达 PAM。请检查本地消息设置、桌面应用是否在运行且已登录，以及 Bitwarden 是否支持该浏览器和安装方式。再添加一条 Gaze PAM 记录无法修复本地消息失败的问题。

如果出现了 Polkit 提示但 Gaze 没有运行，请回到上文针对你的发行版的 Polkit 配置。`pkexec /usr/bin/true` 必须先使用 Gaze。要确认一次 Bitwarden 尝试是否通过预期的服务到达了守护进程，请检查：

```bash
sudo journalctl -u gazed -b --no-pager | grep 'service="polkit-1"'
```

不要添加一条自动授权 Bitwarden 或某个浏览器的 Polkit 规则。那会绕过认证，而不是把它路由到 Gaze。Bitwarden 掌管桌面/本地消息的信任边界；Gaze 只在 Polkit 调用 PAM 时提供面部认证。

## 安全注意事项

- 测试期间保持密码认证启用。
- 在改动 PAM 之前保持一个 root shell 打开。
- 先备份 PAM 文件，以便快速恢复。
