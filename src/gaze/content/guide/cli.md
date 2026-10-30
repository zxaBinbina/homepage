<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# CLI 指南

`gaze` 命令让你可以录入和管理面孔、测试认证，并检查你的安装。

人脸管理、认证与配置命令通过 DBus 与 `gazed` 守护进程通信；诊断还会检查本地系统，密钥环凭据录入与卸载也包含本地操作。

::: tip 中文界面版本
`v0.5.1` 补齐 CLI 帮助、配置向导、诊断、PAM 认证反馈和操作提示的中文；命令名、参数、配置键值与 JSON 字段保持兼容。使用 `gaze --help` 或 `gaze help <命令>` 查看帮助。
:::

## 需要特权的命令

一份已录入的面孔是一项登录凭据，因此创建、更改或删除它都需要 root 特权，即便是你自己的账户也不例外。你无需自己运行 `sudo`：`gaze add-face`、`gaze refine-face`、`gaze remove-face`、`gaze rename-face`、`gaze clear-user`、`gaze config` 以及 `gaze keyring` 等命令会请求提权，并在需要时提示你的密码。它们仍然作用于调用它们的账户，而非 `root`，因此 `gaze add-face default` 为你录入一张面孔。要管理 root 的录入数据，请传入 `-u root`。

`gaze auth`、`gaze list-faces`、`gaze doctor`、`gaze config --show` 以及 `gaze config get` 是只读的，保持非特权状态。`gaze config set` 会像向导一样请求特权。

`gazed` 守护进程独立于 CLI 强制执行这一点：非 root 的 DBus 调用方必须通过 `com.gundulabs.gaze.manage-faces` 或 `com.gundulabs.gaze.manage-config` 的 polkit 检查。这正是 [GUI](/projects/gaze/guide/gui) 授权相同操作的方式，也意味着直接调用 DBus 方法并不能绕过该要求。当其中一个提示打开时，`gazed` 会拒绝为 polkit 对话框进行面部认证，因此更改 Gaze 的面孔或设置始终需要密码。

## 最常见的工作流

```bash
gaze add-face default
gaze auth --verbose
gaze refine-face default
gaze list-faces
gaze doctor
```

## 诊断安装

从你本地的图形会话运行只读诊断命令：

```bash
gaze doctor
```

它会检查：

- CPU 与 systemd 服务的兼容性
- `/etc/gaze/config.toml` 的解析、权限以及不安全的值
- 守护进程与系统 DBus 的响应性
- 对当前 PipeWire 会话的访问，以及已配置的 RGB/IR 相机的可见性
- 当前用户的面部录入情况，以及 RGB/IR 捕获覆盖情况
- PAM 模块的安装、权限，以及活动 PAM 栈的引用
- 在运行 GNOME、KDE 或 hyprlock 这些桌面时，相应的集成情况（在 KDE 上会报告哪个生物识别槽运行 Gaze，以及登录 greeter 是在你输入之前还是提交时扫描）
- 启用加密模板存储时的 TPM 可用性
- GNOME 密钥环解锁：是否已开启、其前置条件是否满足、`/etc/pam.d/gdm-face` 是否仍传递令牌，以及用户是否已录入凭据

每一条警告或错误都包含建议的后续步骤。可能导致 Gaze 无法工作的错误会使命令以状态 `1` 退出；警告仅为建议性，退出状态保持为 `0`。

要检查另一个用户的录入情况（受常规 DBus 授权规则约束）：

```bash
gaze doctor --user alice
```

相机检查会枚举设备，但不会捕获帧。当你需要端到端的相机与识别测试时，请使用 `gaze auth`。

要测量当前硬件上的模型推理速度：

```bash
gaze doctor --benchmark
```

对于脚本，`gaze doctor --json` 会将每一项检查打印为 JSON，而非通常的列表形式。

提交 bug 时，请运行：

```bash
gaze doctor --report
```

它会将一份 `gaze-report-<time>.txt` 文件写入当前目录（若不可写则写入临时目录）。该文件包含 doctor 的结果、Gaze 版本、操作系统发行信息、内核、桌面会话、已安装的 Gaze 软件包、每一行提及 Gaze 的 PAM 配置、`gazed` 服务状态及其最后 200 行日志，以及 `/etc/gaze/config.toml`。你的用户名与主机名会被替换为 `<user>` 与 `<host>`。在将其附到 issue 之前请先阅读。

这会请求正在运行的 `gazed` 守护进程在合成输入上分别运行每个已加载的模型（检测器、RGB/IR 识别器，以及若启用则为活体检测）若干次，并报告每个模型的平均延迟、p95 延迟、最小延迟以及 FPS。它不需要画面中有面孔，也不会触碰相机。

## 认证

```bash
gaze auth
```

有用的选项：

```bash
gaze auth -v          # 显示详细的认证指标（简写形式）
gaze auth --verbose   # 同上
gaze auth -s          # 静默运行，并通过退出码报告结果（简写形式）
gaze auth --silent    # 同上
```

`--verbose` 与 `--silent` 互斥。

结果含义：

- `✓ 认证通过：<face>（XX.X%，XXX毫秒）`：匹配到的面孔名称、得分百分比以及耗时
- `✗ 认证失败（XXX毫秒）`：未通过认证；若有摄像头或服务诊断，会附带原因

使用 `--verbose` 时，会在结果前打印一张逐面孔的表，显示每个已录入面孔按光谱（RGB 与 IR）划分的相似度得分、匹配百分比以及通过/失败。

### 退出码

`gaze auth` 通过退出状态报告其结果，因此可直接用于脚本和 `if` 条件中：

| 码    | 含义                                             |
| ----- | ------------------------------------------------ |
| `0`   | 有面孔匹配且用户已通过认证                       |
| `1`   | 认证失败、没有录入任何面孔，或无法联系到守护进程 |
| `130` | 从终端 UI 取消                                   |

无论是否使用 `--silent` 均适用。较早的版本在认证失败时以 `0` 退出，因此仅检查退出状态的脚本需要重新核对。

### 静默模式

`gaze auth --silent` 完全跳过终端 UI，不向 stdout 或 stderr 写入任何内容；退出码是唯一的结果。请在 PAM 辅助程序、脚本，以及其他没有附加 TTY 的无界面上下文中使用：

```bash
if gaze auth --silent; then
  echo "欢迎回来"
fi
```

由于静默模式是非交互式的，它无法从终端 UI 取消，也不会启动 polkit 代理，因此用 `--user` 认证另一个用户时会失败，而不是提示。静默模式与交互模式均会在开始验证后最多等待守护进程结果 20 秒；如果调用方需要更短的整体截止时间，可用 `timeout(1)` 包裹它（被该工具终止时通常返回 `124`）：

```bash
timeout 15 gaze auth --silent
```

## 录入新面孔

```bash
gaze add-face <name>
```

示例：

```bash
gaze add-face default
gaze add-face glasses
```

当你的外貌经常变化时，请使用独立的档案。

## 改善档案

```bash
gaze refine-face <name>
```

如果在昏暗光线或侧角下识别不一致，请使用此命令。它还会捕获并添加缺失的相机光谱（例如，如果在初次录入之后配置了 IR 相机，则为仅 RGB 的面孔添加 IR 捕获）。

## 列出、重命名与移除

```bash
gaze list-faces
gaze rename-face <old> <new>
gaze remove-face <name>
```

`gaze list-faces` 打印为该用户录入的所有面孔，显示每个面孔拥有的模板捕获数量，并展示该档案已录入相机光谱的 `[RGB]` 与 `[IR]` 徽标：

| 徽标   | 含义                                                                                   |
| ------ | -------------------------------------------------------------------------------------- |
| 绿色   | 该档案拥有该光谱的捕获数据。                                                           |
| 琥珀色 | 已为该光谱配置了相机，但该档案没有来自它的捕获数据。请运行 `gaze refine-face <name>`。 |
| 灰色   | 未为该光谱配置相机，因此没有可录入的内容。                                             |

因此一台仅 RGB 的机器会显示一个绿色的 `[RGB]` 和一个灰色的 `[IR]`，而非失败。`gaze list-faces --json` 会以 JSON 形式打印同一列表。

`gaze remove-face` 与 `gaze rename-face` 在面孔不存在时以状态 `1` 退出。

## 删除当前用户的所有面孔

```bash
gaze clear-user
```

这会永久移除当前用户所有已录入的面孔，以及任何已存储的 GNOME 密钥环或 KWallet 凭据。它会先请求确认；在脚本中传入 `--yes` 可跳过提示。在没有终端且没有 `--yes` 的情况下，它会拒绝执行。

## 检查或清除胁迫锁定

当 [胁迫检测](/projects/gaze/guide/configuration#duress-signal) 锁定面部认证时，一次密码登录会重新启用它。要手动检查或清除它：

```bash
gaze duress          # 显示面部认证是否被锁定
gaze duress --clear  # 重新启用面部认证
```

手动清除锁定需要一次全新的管理员认证，即便是你自己的账户也不例外。root 的 PAM 调用方会在一次成功的非面部登录之后清除它。

## 在一次 GDM 或 greetd 面部登录后解锁 GNOME 密钥环

面部登录不提供密码，因此 GNOME 登录密钥环通常会保持锁定。`gaze keyring` 将账户密码存储在一个仅 root 可读、受 TPM 保护的记录中，`pam_gaze.so` 会在一次成功的面部与活体检测之后将其重放给 `pam_gnome_keyring`：

```bash
gaze keyring                    # 录入或替换凭据
gaze keyring --forget           # 移除已存储的 GNOME 凭据
gaze keyring --kwallet          # 录入或替换 KDE 钱包凭据
gaze keyring --kwallet --forget # 仅移除 KDE 钱包凭据
sudo gaze keyring --user alice  # 对另一个账户操作
```

对于 KDE，请将 `--kwallet` 与 `storage.unlock_kwallet = true` 以及 [受管理的 KDE 登录 PAM 钩子](/projects/gaze/guide/kde#optional-tpm-backed-kwallet-unlock) 配合使用。两种后端拥有独立的凭据；`gaze clear-user` 会同时移除两者。

GNOME 录入需要 `storage.unlock_gnome_keyring = true`，而它又需要 `storage.encrypt_templates = true` 与 `liveness.enabled = true`。`gaze clear-user` 会随该用户其余数据一起移除该记录。

在启用它之前，请先阅读 [它对你的安全意味着什么](/projects/gaze/guide/gnome#what-this-changes-about-your-security)：所存储的密码可被本机上的 root 恢复。

## 完全卸载 Gaze

```bash
gaze uninstall              # 交互式
gaze uninstall --yes        # 跳过确认
gaze uninstall --keep-data  # 保留 /var/lib/gaze 中已录入的面孔
gaze uninstall --dry-run    # 预览计划，不执行任何操作
```

移除已安装的软件包、仓库配置、GNOME/GDM 锁屏与登录设置、PAM/authselect 集成、SELinux 策略、模型缓存（`/var/cache/gaze`）、系统配置（`/etc/gaze`），以及（除非设置了 `--keep-data`）已录入的面孔数据（`/var/lib/gaze`）。每一步都是尽力而为，并使用 `sudo`，因此会提示你的密码。

如果你更想手动运行这些步骤，请参阅 [卸载指南](/projects/gaze/guide/uninstallation)。

## 交互式配置

使用交互式向导通过 DBus 编辑守护进程配置：

```bash
gaze config
```

仅显示模式：

```bash
gaze config --show
```

以 TOML 形式打印每一项设置，布局与 `/etc/gaze/config.toml` 相同，后附注释说明预设所解析到的值（检测器、识别器、阈值、混合策略、并行捕获，以及启动延迟作用范围）。

要在不使用向导的情况下读取或更改某一项设置：

```bash
gaze config get security.level
gaze config set liveness.enabled true
gaze config set cameras.dark_luma_threshold 40
```

`set` 会针对设置类型以及守护进程使用的相同校验规则检查该值，然后通过 `gazed` 应用它。

## Shell 补全

`gaze` 在运行时自行生成补全，包括接受面孔名称的命令所对应的已录入面孔名称。将对应你所用 shell 的那一行添加到其启动文件中：

::: code-group

```bash [bash]
echo 'source <(COMPLETE=bash gaze)' >> ~/.bashrc
```

```zsh [zsh]
echo 'source <(COMPLETE=zsh gaze)' >> ~/.zshrc
```

```fish [fish]
echo 'COMPLETE=fish gaze | source' >> ~/.config/fish/config.fish
```

:::

启动一个新的 shell 以使其生效。没有任何内容被安装到磁盘上，因此在你录入或重命名面孔时，无需维护任何需要同步的补全文件。

## 管理另一个用户

大多数命令支持 `-u`：

```bash
gaze list-faces -u alice
gaze add-face work -u alice
```

## 故障排除命令

```bash
gaze doctor
systemctl status gazed
journalctl -u gazed -n 100 --no-pager
gaze auth --verbose
```

如果你需要诊断失败的帮助，请参阅 [故障排除指南](/projects/gaze/guide/troubleshooting)。
