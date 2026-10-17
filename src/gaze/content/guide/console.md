<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# 控制台登录（TTY）

Gaze 可以认证虚拟终端上的 `login` 提示符——也就是在没有桌面的服务器上，或通过 Ctrl+Alt+F3 切换到空闲 VT 时看到的那个。

输入你的用户名，按 Enter，然后看向相机。`pam_unix` 会打印密码提示，而非 `login` 本身，因此当 Gaze 先认证成功时，该提示不会出现，你会直接进入 shell。

## 配置

`login` 使用共享认证栈，因此在大多数发行版上按常规方式启用 Gaze 即可覆盖它：

::: code-group

```bash [Debian/Ubuntu]
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

Debian 的 `/etc/pam.d/login` 包含 `common-auth`，Fedora 的包含 `system-auth`，openSUSE 的包含 `common-auth`，因此你为 `sudo` 启用的配置文件或模块也会覆盖到控制台。

### Arch Linux

Arch 需要手动步骤。Gaze 刻意不进入 `/etc/pam.d/system-auth`，因为 `pambase` 会在升级时覆盖该文件（见 [PAM](/projects/gaze/guide/pam#arch-linux-manjaro)），而 `/etc/pam.d/login` 只能通过该共享栈访问 Gaze。请改为直接将 Gaze 添加到 `/etc/pam.d/login`：

```bash
staged=$(sudo mktemp /etc/pam.d/login.gaze.XXXXXX) && \
  sudo awk -v out="$staged" '
    /^[[:space:]]*auth[[:space:]]+(include|substack)[[:space:]]/ && !inserted {
        print "-auth       requisite     pam_faillock.so preauth" > out
        print "auth        sufficient    pam_gaze.so" > out
        inserted = 1
    }
    { print > out }
    END { if (!inserted) exit 1 }
' /etc/pam.d/login && \
  sudo install -m 644 "$staged" /etc/pam.d/login
sudo rm -f "$staged"
```

该命令有两个细节很重要，因为一份被破坏的 `/etc/pam.d/login` 会把你锁在所有终端之外：

- Gaze 的两行位于 `auth include system-login`（即引入共享栈的那一行）的正上方。Arch 放在它之前的任何内容（即 `pam_nologin` 以及用到之处 `pam_securetty`）都是必须首先运行的否决项。出于同样的原因，faillock preauth 闸门与 Gaze 行一起加入，只是方向相反：一次充分的面部匹配会从栈中直接返回，因此若没有该闸门，被锁定的账户仍然可能通过面部认证，且在其之后运行的任何内容都不会被打印出来。
- `awk` 自己写入暂存文件，而非通过管道传给 `tee`。管道只报告其最后一条命令的退出状态，因此即使 `awk` 失败，`tee` 仍会报告成功，而 `install` 也会乐呵呵地用一份被截断或空的文件替换你的登录栈。按此写法，`&&` 看到的是 awk 自身的状态，且如果 awk 从未找到 include 行，它会以非零状态退出。

暂存文件是特意由 root 在 `/etc/pam.d` 内创建的。若在 `/tmp` 下的固定路径构建新栈，会让任何其他本地用户预先创建它，而他们留在那里的任何内容都会成为你的认证栈。

注销之前，请用 `cat /etc/pam.d/login` 检查结果。

::: warning
测试此配置时请保持一个 root shell 打开。对 `/etc/pam.d/login` 的失误可能会把你锁在所有虚拟终端之外。
:::

## 登录提示符处的相机

登录之前不存在会话，因此没有可供捕获的 PipeWire，也没有授予你用户相机访问权的 ACL。Gaze 始终直接捕获内核 V4L2 设备用于认证，因此该环境无需特殊处理：`gazed` 打开相机，而非 PAM 模块，因此施加于 `login` 本身的沙箱隔离不会构成阻碍。

将 `cameras.rgb` 保持为 `primary`（第一个彩色 V4L2 节点），将其固定到 `usb:VVVV:PPPP`，或固定到一个 `pipewiresrc target-object=` 值，该值会被解析到同一相机背后的 V4L2 节点。详见 [选择相机源](/projects/gaze/guide/configuration#select-a-camera-source)。

### Gaze 不会使用座位相机的情况

只有当 logind 报告 seat0 没有活动会话 **且** 该座位上没有任何属于其他用户的会话时，Gaze 才会取用座位设备。

两部分都很重要。每当前台虚拟终端不持有会话时，logind 就会清除活动会话，这在其他人登录到后台终端时也同样成立。因此单凭"没有活动会话"并不意味着座位空闲，Gaze 也不会这样处理：如果有其他用户在座位上的任何地方登录，控制台面部认证就会回退到密码。

如果根本无法访问 logind，Gaze 会拒绝而非猜测。

另请注意，当某个会话停止活动后，已打开的相机不会被关闭。在后台会话中遗留运行的程序可能继续占用该设备，因此即使座位看似空闲，捕获也可能因设备忙而失败。

## 时间限制

默认情况下，`login` 为整个尝试允许 60 秒（即 `/etc/login.defs` 中的 `LOGIN_TIMEOUT`），最多三次尝试（`LOGIN_RETRIES`）。每次面部尝试最多可使用 12 秒，且某些发行版会在失败后增加延迟，因此重复的面部失败可能在使用者输入任何内容之前就耗尽预算。如果发生这种情况，`login` 会退出，终端返回到全新的提示符。

在此场景下将 [`auth.start_delay_ms`](/projects/gaze/guide/configuration) 降到最小；如果你经常回退到密码，考虑将 Gaze 移出控制台栈，改为将其用于 `sudo` 和锁屏。

## 密钥环

当你用面孔认证时，没有密码可交给 `pam_gnome_keyring` 或 `pam_kwallet`，因此登录时解锁的密钥环之后会改为提示你。在无界面或服务器控制台上这通常无关紧要；但在你从 TTY 启动桌面的机器上则不然。

## 关闭它

在 Debian 和 Ubuntu 上，从共享栈中移除 Gaze，并仅在你想要的位置重新添加它：

```bash
sudo pam-auth-update --disable gaze gaze-simultaneous
```

然后遵循 [选择性配置](/projects/gaze/guide/pam#selective-setup-password-at-gdm-face-authentication-for-sudo-and-polkit)。在 Arch 上，移除你添加到 `/etc/pam.d/login` 的 `pam_gaze.so` 行。在 openSUSE 上，用 `sudo pam-config --delete --gaze --gaze_grosshack && sudo pam-config --update` 从受管理的栈中移除该模块。
