<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# 配置

Gaze 通过 `/etc/gaze/config.toml` 进行配置。

默认值适用于许多环境。常见的调整包括选择相机源或更改安全级别。

GUI 与 `gaze config` 的更改会在校验与模型准备完成后实时生效。一次成功的更新会取消正在进行的捕获，并等待其线程停止，然后再发布新的设置与模型。准备失败则保持当前运行不变。对文件的手工编辑（包括 `[duress]`）在 `sudo systemctl restart gazed` 之后生效；如果文件被编辑或删除，正在运行的守护进程会保留其已应用的配置。

::: tip 编辑配置需要管理员特权
守护进程在保存更改前需要进行授权。`gaze config` 会通过 `sudo` 提示你的密码，而 `gaze config --show` 是只读的，不需要任何特权。GUI 通过 PolicyKit 请求授权，并使用你桌面的密码对话框，因此请确保已安装 `polkit` 软件包。
:::

## 默认配置

```toml
[inference]
execution_provider = "cpu"
device = "cpu"

[security]
level = "medium"

[cameras]
rgb = "primary"
# ir = "/dev/video2"        # 可选红外相机（直接的 /dev/video* 节点或 usb:VVVV:PPPP）
# emitter_enabled = false   # 驱动红外发射器（需要 ir）
# ir_frame_width = 340      # 强制 IR 分辨率；需与 ir_frame_height 一起设置（需要 ir）
# ir_frame_height = 340
# parallel_capture = "never" # "never"、"auto" 或 "always"（需要 ir）
dark_luma_threshold = 20

[auth]
abort_if_ssh = true
abort_if_lid_closed = true
abort_before_first_resume = false
require_confirmation_lock_screen = false
require_confirmation_elevation = false
resume_grace_ms = 0
start_delay_ms = 0
start_delay_scope = "screen_lock"

[enrollment]
max_templates = 2
min_face_size_ratio = 0.25

[liveness]
enabled = true
threshold = 0.8
max_seconds = 2.0

[storage]
encrypt_templates = true
unlock_kwallet = false # 可选的 TPM 支持 KDE 钱包解锁
unlock_gnome_keyring = false

[duress]
enabled = false
closed_threshold = 0.9
hold_ms = 600
```

## 升级

软件包升级永远不会覆盖你编辑过的 `/etc/gaze/config.toml`。如果打包的默认值发生了变化，新的模板会被并排保存为 `config.toml.rpmnew`（RPM）或 `config.toml.pacnew`（Arch）；在 Debian/Ubuntu 上，dpkg 会保留你的文件，并在替换前询问。你的配置中缺失的任何选项都会使用其内置默认值，因此升级后你无需合并新的选项。

## 选择推理设备

Gaze 始终通过 ONNX Runtime 加载其 `.onnx` 模型。缓存的模型会经过校验和验证；损坏的文件会触发一次全新下载，且在验证之后以原子方式发布替换文件。

RGB 与 IR 使用各自独立的检测器会话。IR 检测器与识别器会话只有在配置了 `cameras.ir` 时才会加载。每个 ONNX Runtime 会话最多使用两个 intra-op 线程、顺序图执行，且不进行线程池空转；加速器提供方可能会自行管理额外的线程。

默认使用 ONNX Runtime 的 CPU 执行提供方：

```toml
[inference]
execution_provider = "cpu"
device = "cpu"
```

标准构建还支持 Intel OpenVINO 与 AMD Ryzen AI。要使用其中任何一种，请按 [硬件加速指南](/projects/gaze/guide/acceleration) 安装其驱动与运行时，然后选择自动 NPU 加速：

```toml
[inference]
execution_provider = "auto"
device = "npu"
```

| 提供方 | 设备 | 行为 |
| --- | --- | --- |
| `cpu` | `cpu` | 内置的 ONNX Runtime CPU 推理（默认） |
| `auto` | `npu` | 根据绑定的 NPU 驱动选择 Intel（`intel_vpu`）或 AMD（`amdxdna`） |
| `openvino` | `cpu`、`gpu`、`npu` | 使用已安装的 Intel OpenVINO 运行时 |
| `vitis` | `npu` | 使用已安装的 AMD Ryzen AI/Vitis AI 运行时 |

在安装运行时或更改提供方厂商之后，请重启 `gazed`。ONNX Runtime 在每个守护进程生命周期内只加载一次。在该运行时内更改 OpenVINO 设备仍可以在不重启的情况下重新加载模型。

缺失的库、不可用的驱动、模型编译失败或启动预热失败都会产生一条日志化的原因，并为受影响的模型回退到 CPU 会话。CPU 图分区也可能残留在一个成功的加速器会话内部；仅凭提供方标签并不能证明每个操作都运行在 NPU 上。`gaze doctor --benchmark` 会报告每个模型所选择的提供方、耗时，以及任何会话回退的原因。

OpenVINO 的 NPU 支持面向 Intel。AMD 使用 `vitis`，并带有 AMD 文档化的硬件与操作系统限制。两种提供方都不会把普通的 CPU 或 GPU 变成 NPU。

## 更改安全级别

`level`（位于 `[security]` 下）控制模型选择与匹配的严格程度。

| 级别 | 检测器 | 识别器 | RGB / IR 阈值 | 混合策略 | 说明 |
|---|---|---|---|---|---|
| `low` | SCRFD-500M | MobileFaceNet | 0.30 | `or` | 最快 |
| `medium` | SCRFD-500M | MobileFaceNet | 0.40 | `fallback_on_dark` | 默认 |
| `high` | SCRFD-10G | ResNet50 | 0.50 | `fallback_on_dark` | 更准确 |
| `maximum` | SCRFD-10G | ResNet50 | 0.60 | `and` | 最严格 |

实践建议：

- `medium`：大多数笔记本的最佳起点
- `high`：在无法接受误接受时使用
- `low`：在硬件较弱且速度至关重要时使用

模板只能与录入它们的识别器匹配。在 MobileFaceNet 级别与 ResNet50 级别之间切换后，请重新录入你的面孔。在你这么做之前，那些面孔会显示 0 个模板，且面部登录会回退到你的密码。切换回原始识别器会使旧模板再次可用。

### 自定义级别

```toml
[security]
level = "custom"
detector = "accurate"   # "standard" 或 "accurate"
recognizer = "accurate" # "standard" 或 "accurate"
rgb_threshold = 0.55
ir_threshold = 0.45
hybrid_policy = "or"    # 可选；default、or、fallback_on_dark、and
```

对于自定义级别，RGB 与 IR 相似度阈值是相互独立的。遗留的 `threshold` 键仍被接受，并在缺少按光谱区分的键时为两者提供取值。

### 混合合并策略

`hybrid_policy`（位于 `[security]` 下，仅在 `level = "custom"` 时可配置）控制当两种模式都录入了模板且两台相机都可用时，如何合并 RGB 与 IR（红外）的认证结果。

支持的策略：
- `or`：RGB 或 IR 任一匹配即通过。
- `fallback_on_dark`：两者都需要，除非 RGB 太暗（低于 `dark_luma_threshold`），此时仅需要 IR。
- `and`：仅当 RGB 与 IR 都匹配时才通过。
- `default`：`fallback_on_dark` 的同义词。它不会解析为上方表格中为活动级别列出的策略。

要获得表格中为某级别列出的策略，请完全省略 `hybrid_policy`。该键仅在 `level = "custom"` 时被读取，而缺失该键的自定义级别同样会解析为 `fallback_on_dark`。

`fallback_on_dark` 与 `default` 都会在 RGB 被捕获并测得过暗，或者 RGB 相机无法使用（例如因为视频通话已经占用了它）时，将要求放宽为仅 IR。在这种情况下，Gaze 会记录相机错误，并改用 IR 继续，而不是回退到你的密码。`and` 仍然会失败，因为它始终需要两种光谱。

## 选择相机源

默认的相机源为：

```toml
[cameras]
rgb = "primary"
```

`primary` 选择第一个彩色 `/dev/video*` 节点。要使用特定的 PipeWire 相机，请打开 `gaze config`，或将 `rgb` 设置为一个 GStreamer 源：

```toml
[cameras]
rgb = "pipewiresrc target-object=<pipewire-target>"
```

对于认证与录入，特权守护进程使用 `v4l2src` 直接捕获底层的内核 `/dev/video*` 节点；它从不连接用户会话的 PipeWire 套接字。被认证的用户控制着那个套接字以及它所广告的每个虚拟相机，因此信任它会让注入的帧直达面部认证。Gaze 以同样的方式将一个固定的 PipeWire 目标解析到它自己的 V4L2 节点，并拒绝没有内核节点的源，包括手写的 GStreamer 管道。因此，`primary` 在 greeter 以及没有 PipeWire 会话的纯 TTY 上同样可用。

将 `rgb` 直接固定到相机会立即使用 `v4l2src`，而无需先解析 PipeWire 目标。当机器上有多台相机且你想要特定的某一台时，优先使用这种方式：

```toml
[cameras]
rgb = "usb:046d:085e"   # 解析该 USB VID:PID 的彩色节点
# rgb = "/dev/video0"    # 或一个固定的 V4L2 节点
```

`usb:VVVV:PPPP`（十六进制 VID:PID）会解析为该相机此刻暴露出的任意 `/dev/video*` 节点，并在单一功能的摄像头在同一 id 下同时呈现彩色与 IR 节点时，选择彩色节点。比起原始的 `/dev/video*` 路径，优先使用它，因为后者在相机被重新编号时会静默指向错误的设备。

### 暗帧拒绝

Gaze 会在运行人脸检测之前拒绝过暗的帧：

```toml
[cameras]
dark_luma_threshold = 20
```

使用默认值，当一帧的平均亮度（0-255，BT.601 加权）低于 20 时会被跳过。提高它以拒绝更昏暗的场景，降低它以更宽松。

## 红外（IR）相机

Gaze 支持 Windows Hello 风格的红外（IR）相机，以实现多相机混合认证。`ir` 设置可直接指向 IR 相机的 `/dev/video*` 节点：

```toml
[cameras]
ir = "/dev/video2"
emitter_enabled = false
```

你也可以通过 USB VID:PID 解析节点（此处选择单色/IR 节点），或使用 IR 的 PipeWire/GStreamer 源：

```toml
[cameras]
ir = "usb:046d:085e"
# ir = "pipewiresrc target-object=<pipewire-target>"
```

当你在 RGB 之外配置了 IR 相机时，Gaze 会在录入期间从两者捕获模板，然后根据配置的 `hybrid_policy` 在验证时合并它们的结果。

### 仅 IR

要仅用 IR 相机认证，且从不打开 RGB 相机，请将 `rgb` 设为空字符串。仅注释掉该键是不够的，因为缺失的 `rgb` 意味着 `"primary"`。

```toml
[cameras]
rgb = ""
ir = "/dev/video2"
```

在 GUI 中，将 RGB 相机源选择为 **None (IR only)**（无，仅 IR）。`gaze config` 提供同样的选择。你的档案需要 IR 模板，因此切换后请录入（或添加捕获）。`hybrid_policy` 在单相机下不起作用。

### IR 帧尺寸覆盖

某些笔记本 IR 相机广告了多种分辨率，但只在原生分辨率下输出有效帧。Gaze 会选择它能协商到的最大模式，因此在这些相机上，IR 画面输出为纯绿或 corrupted（损坏）。请改为强制使用原生尺寸：

```toml
[cameras]
ir = "/dev/video2"
ir_frame_width = 340
ir_frame_height = 340
```

- 两个键都要设置，或都不设置。每个值必须在 1 到 4096 之间。留空让 Gaze 协商尺寸，即默认值。
- 如果相机无法以强制尺寸打开，Gaze 会记录一条警告并回退到协商尺寸，因此错误的值绝不会让面部认证在没有相机的情况下进行。
- 该覆盖仅适用于 IR 相机。在被 Gaze 强制设为 640x480 YUY2 模式的 Dell 与 Realtek 模块上，它会替换掉那个 640x480。
- 在 GUI 中，在 Hardware（硬件）下打开 **IR Frame Size Override**（IR 帧尺寸覆盖）。
- 守护进程必须至少与设置该覆盖的 GUI 或 CLI 一样新。较老的守护进程会拒绝它，并保持配置其余部分不变。

### 并行 RGB + IR 捕获

默认情况下，验证会逐一捕获两台相机（先 RGB，后 IR）。顺序而非并发地捕获，使得无法同时流式传输其 RGB 与 IR 传感器的单一功能摄像头（例如 Logitech BRIO 4K，`046d:085e`）仍然可以使用混合认证，代价是延迟：在 `hybrid_policy = "and"` 下，两种光谱始终都会运行，因此两个捕获阶段会累加。

如果你的相机可以同时流式传输两个传感器，`parallel_capture` 会恢复并发行为：

```toml
[cameras]
ir = "/dev/video2"
parallel_capture = "auto"
```

| 值 | 行为 |
| --- | --- |
| `never`（默认） | 始终先捕获 RGB，再捕获 IR。在所有相机上都可用。 |
| `auto` | 仅当 RGB 与 IR 是独立的硬件功能时才并行捕获。 |
| `always` | 始终并行捕获。仅在确认你的相机支持同时流式传输之后才选择此项。 |

`auto` 将每个已配置的源解析到其 `/dev/video*` 节点，并比较其背后的硬件功能（对于 USB 相机，即该节点所依附的 sysfs USB 接口）。同一功能上的两个节点是一个设备对单一模式同一时刻只流式传输一个子流，因此它们即使在节点号不同的情况下也保持串行。这就是 BRIO 的情况，其中 `/dev/video0` 与 `/dev/video2` 共享单一的 UVC 功能。

默认的 `rgb = "primary"` 意味着第一个彩色 `/dev/video*` 节点。与其猜测它是哪一个，`auto` 从 IR 一侧提出问题：IR 相机自身的功能是否也暴露出一个彩色节点？如果是，那么 IR 相机就是一个双传感器设备，`primary` 很可能解析到它，因此捕获保持串行。如果 IR 功能仅限红外，它就不可能是 `primary` 最终解析出的任何东西，于是两者同时流式传输。无法解析的 `rgb` 值以相同方式处理。如果根本无法枚举任何内容，`auto` 会保持串行路径。

并行捕获只改变每个光谱被捕获的*时机*，从不改变两者是否都必须通过。`hybrid_policy` 在两种模式下行为完全相同。提速也受到人脸检测的限制（两种光谱共享它），因此预期是实质性的改进，而非减半。

某些 Windows Hello 摄像头通过一个 USB 视频类功能暴露其 RGB 与 IR 传感器，且无法同时流式传输两者。录入仍然有效，因为它只捕获短促的突发，但并行的 RGB+IR 验证可能在循环中途丢弃 IR 流（`IR camera stream stopped unexpectedly`，IR 相机流意外停止）并回退到你的密码。如果你在启用 `parallel_capture` 之后发生这种情况，请将其切回 `never`。无论此设置如何，录入始终一次只从一台相机捕获。

Logitech BRIO 4K（`046d:085e`）就是一个已知的例子。那是初代 BRIO，而非使用不同产品 ID 的较新 Brio 300/500/100。

### 红外发射器驱动

许多 IR 相机在流式传输开始时会自动点亮其红外 LED。如果你的不会，请设置 `emitter_enabled = true`，在认证期间手动驱动发射器。

Gaze 从 PipeWire 相机解析底层的 `/dev/video*` 节点，按 VID:PID 对照一个小型内置表匹配 USB 相机，并探测标准的 Microsoft Face Authentication UVC 控制。`crates/gaze-core/ir-profiles/` 下的文件仅描述 USB UVC 扩展单元请求。

通过 I2C 驱动的非 USB 发射器使用 `crates/gaze-core/i2c-ir-profiles/` 中经过审查的配置文件，这些文件会被编译进 Gaze，且永远不会从用户配置中读取。目前唯一的例子是 Surface Pro 4 的 OV7251 传感器。它需要：

- 加载 `i2c-dev` 内核模块，使传感器的 `/dev/i2c-*` 总线存在。要在每次启动时加载，运行 `echo i2c-dev | sudo tee /etc/modules-load.d/i2c-dev.conf`。
- 一个用户态桥接，将 IPU3/CIO2 的 IR 流中继到名为 `Surface IR Camera` 的 v4l2loopback 设备 `/dev/video42`，并将 CIO2 源节点的路径写入 `/run/surface_ir_bridge_dev`。将 `cameras.ir` 指向 `/dev/video42`。
- 将 `ov7251` 驱动绑定到 `i2c-INT347E:00`。

Gaze 使用传感器所绑定适配器上的 I2C 总线。在写入之前，它会检查是否有驱动程序已声明该传感器的地址；然后它只更改发射器位，并将寄存器读回。`gaze doctor` 会报告哪个检查失败。该寄存器值仅经过 Surface Pro 4 的接线验证，因此可能无法在其他 Surface 型号或 OV7251 设备上工作。

在 IR 路径上，活体检测使用跨帧的眼球运动分析；RGB 的 MiniFASNet 模型不会应用于红外。

驱动红外发射器需要对该 IR `/dev/video*` 节点的读写访问。守护进程以 root 运行，并且是 `video` 组的成员，因此默认的 `root:video` 设备权限已足够；不需要额外的 udev 规则。

## 认证选项

Gaze 会在相机不太可能或不宜使用的会话中跳过面部认证：

```toml
[auth]
abort_if_ssh = true
abort_if_lid_closed = true
abort_before_first_resume = false
require_confirmation_lock_screen = false
require_confirmation_elevation = false
resume_grace_ms = 0
start_delay_ms = 0
start_delay_scope = "screen_lock"
```

`abort_if_ssh` 会询问 logind，D-Bus 调用方的会话是否为远程，在 logind 不可达时回退到调用方进程的环境与祖先链。`abort_if_lid_closed` 在可用时读取 ACPI 合盖状态，在没有合盖传感器的系统上会被忽略。当 logind 被配置为合盖时挂起时，合盖会将该尝试暂停最多 3 秒，而非直接拒绝：如果挂起开始，面部认证会在唤醒后恢复，而不是在合盖时出现的锁定器中失败。详见 [尝试期间的挂起](/projects/gaze/guide/how-it-works#suspend-during-an-attempt)。

在你输入密码时中止面部认证并不是该文件中的一个键。它是 PAM 栈的一个属性：[simultaneous 模式](/projects/gaze/guide/pam#what-gaze-installs)（`pam_gaze.so simultaneous`）会在你提交密码时立即让 Gaze 退下；而 [retry 模式](/projects/gaze/guide/pam#retry-after-a-rejected-password)（`pam_gaze.so retry`）会在该密码最终错误时给面部认证多一次尝试。

`abort_before_first_resume` 拒绝面部认证，直到机器已挂起并唤醒过至少一次，因此启动后的第一次认证总是回退到密码。在 GNOME 上，那次密码正是解锁登录密钥环的密码；相比之下用面孔认证会让密钥环保持锁定，GNOME 稍后再次索要密码。启用此项后，你会在 GDM 登录时输入一次密码，然后在会话的其余时间里用面孔解锁。

Gaze 从 logind 的 `PrepareForSleep` 信号触发该闸门，这同样是 `resume_grace_ms` 所使用的信号，因此休眠与挂起都算数。该状态存在于 `gazed` 中，不会被持久化：如果守护进程重启，下一次认证会再次被阻断，直到下一次恢复。它适用于所有场景，包括 `gaze auth` 与 GUI 的测试按钮，因此启动后立即进行的测试会报告失败，直到你挂起一次。

`require_confirmation_lock_screen` 与 `require_confirmation_elevation` 各自在成功的面部匹配之后增加一个手动意图检查步骤，并且可以独立切换。`require_confirmation_lock_screen` 覆盖锁屏以及登录/greeter 界面（例如 GDM）；`require_confirmation_elevation` 覆盖提权认证提示（`sudo`、`su`、`doas`、`run0`、polkit、`pkexec`）。两个 PAM 模块都尊重它们。

当确认被禁用时，一次成功的匹配会将相机提示替换为"Face Verified."（面部已验证），并立即继续认证，无需等待输入。

使用标准的顺序 `pam_gaze` 模式（例如 `sudo`、`gdm-face`）：
- 在基于文本（TTY）的环境（如终端中的 `sudo`）中，它会在面部匹配后请求文本确认（"Press Enter to confirm, Esc to cancel"，按 Enter 确认，Esc 取消）。
- 在 GNOME 锁屏、GDM 登录界面以及统一的 Cinnamon 锁屏（在 Gaze 扩展处于活动状态时），它会在密码框下方显示"Face Verified. Press Enter to confirm."（面部已验证。按 Enter 确认）；或呈现一个专门的"Confirm Face Unlock"（确认面部解锁）按钮；按 Enter 或点击按钮即可确认。如果扩展处于非活动状态，登录会被拒绝，因为该扩展是 GNOME 上预期的确认通道，Gaze 不会静默跳过你所要求的确认。
- 在没有控制终端但 PAM 对话仍能提示的情况下（例如 `hyprlock`），它会问"Face Verified. Type 'yes' to confirm."（面部已验证。输入 'yes' 确认）。在那里，空的回答绝不视为同意：否则那些用 `""` 回答未知提示的主机会在用户不做任何操作的情况下自动确认。
- KDE 的生物识别槽（`kde-fingerprint`、`kde-smartcard`、`plasmalogin-fingerprint`）以及 SDDM/Plasma Login Manager 的登录表单无法回答确认提示。当 `require_confirmation_lock_screen` 启用时，Gaze 会在扫描之前返回 `PAM_IGNORE`，并保留密码认证可用，而非绕过确认。`gaze doctor` 会就此回退发出警告。请使用能够显示确认对话框的场景，或者如果本就打算允许未确认的面部解锁，则显式禁用该开关。
- GDM 在 Gaze 扩展下运行 GNOME，因此确认在那里被强制执行，否则登录会被拒绝。

"基于文本（TTY）的环境"意味着 Gaze 可以打开进程的控制终端（`/dev/tty`），这正是 `sudo` 自己找到要提示的终端的方式。被重定向的标准输入不会改变这一点，因此 `echo 1 | sudo tee /tmp/1` 仍然从键盘确认。在完全没有控制终端的情况下（例如通过带帧的 stdio 协议驱动 PAM 的管理控制台 Cockpit，或在没有终端的情况下启动的服务），没有人能按键，因此 Gaze 既不打印终端横幅，也不等待它；面部匹配被拒绝，栈回退到密码。

设置了 PAM `PAM_SILENT` 标志的调用方（其中包括 `sudo`）不会通过它们自己的对话收到任何消息。对于终端服务（`sudo`、`su`、`doas`、`login`），Gaze 仍然将相机提示与判定结果写入控制终端，因此终端用户保留"Please look at the camera"（请看向相机）/ "Face Verified."（面部已验证）的反馈。其他调用方，包括碰巧继承了终端的锁屏，永远不会收到终端输出或终端确认；它们会通过自己的对话框确认。

使用 simultaneous 模式（`pam_gaze.so simultaneous`）：
- 在终端服务（`sudo`、`su`、`doas`、`login`）与 polkit 对话框中，密码提示会立即出现，因此你永远不会被阻塞。锁屏与 greeter 以 Gaze 无法撤回的方式回答提示，因此在那里扫描先运行，密码随后才被询问，与顺序模式完全一样。
- 如果你在完成输入密码之前面部验证成功：
  - 在基于文本（TTY）的环境中，它会取消密码提示，并请求文本确认（"Press Enter to confirm, Esc to cancel"，按 Enter 确认，Esc 取消）。
  - 在图形化的 Polkit 环境中：
    - 在 **GNOME 与 Cinnamon**（Gaze 扩展处于活动状态）上，它会隐藏密码框，将焦点放到"Authenticate"（认证）按钮上，并让你通过按 Enter 或点击按钮来确认。如果扩展处于非活动状态，它会完全绕过确认，以避免将你锁在门外。
    - 在 **KDE Plasma 与 LXQt** 上，它会提示你按"OK"（确定）确认。
    - 在 **Hyprland** 上，它会提示你按"Authenticate"（认证）确认。
    - 在其他图形环境中，它会提示你按"Enter"（回车）确认。

`resume_grace_ms` 将系统恢复后的面部验证延迟指定的毫秒数（例如 `3000` 毫秒），以便较慢的显示器/GPU 完成初始化并重绘，防止验证发生在黑屏背后。设为 `0` 可禁用该延迟。

`start_delay_ms` 将面部验证延迟指定的毫秒数，且不仅仅是在挂起之后。设为 `0` 可禁用该延迟。

如果你的锁屏一锁定就解锁，启动延迟会有帮助。锁定器开始认证的时间各不相同：hyprlock 在启动时启动其 PAM 栈，而 KDE 在其锁屏一出现时就开始扫描。如果你仍在相机前方，Gaze 可能会识别你并立即解锁。延迟 `3000`-`5000` 毫秒可以给你时间走开。GNOME 不需要这个延迟，因为面部认证只有在你解除锁定遮罩后才会开始。

延迟是从会话锁定之时起算的，而非从每次尝试起算，因此在同一次锁定期间的第二次尝试不会再次等待。Gaze 从 logind 的 `LockedHint` 学习锁定时间，GNOME、KScreenLocker 与 hyprlock 都会设置它。在没有设置它的地方，每次尝试都会等待完整的延迟。

`start_delay_scope` 控制哪些提示需要等待：

| 值 | 效果 |
| --- | --- |
| `all` | 每次面部认证提示都会等待，包括 `sudo` 与 polkit 提示。 |
| `screen_lock`（默认） | 只有屏幕锁定器等待。`sudo`、`su`、`doas`、`run0`、polkit、`pkexec` 以及显示管理器 greeter 会立即开始扫描。 |

两种范围都不会延迟 `gaze auth` 或 GUI 的测试按钮。它们直接调用守护进程，没有 PAM 提示，也没有需要走开的锁定器，因此它们总是立即开始扫描。`resume_grace_ms` 的等待仍然适用于它们，因为那一项是关于相机与显示器在挂起后安顿下来。

默认的 `screen_lock` 范围会在你的锁屏上提供延迟，而不会拖慢 `sudo`：

```toml
[auth]
start_delay_ms = 3000
start_delay_scope = "screen_lock"
```

Gaze 通过提示的 PAM 服务名来区分它们，这也是唯一在到处都有效的信号。例如在 GNOME 上，同一个进程同时驱动锁屏与 polkit 对话框，因此调用方本身没有任何东西能区分它们。一个 Gaze 不认识的服务会被算作屏幕锁定，因此一个不常见的锁定器会保留你配置的延迟，而不是静默丢失它。`gdm-face` 按名称算作屏幕锁定，因为 GDM 将它同时用于 greeter 与锁屏；当活动会话是 greeter 时，守护进程会将其重新分类为登录，这样 greeter 就不会等待。

要查看你的提示报告了什么，请在触发一个提示的同时观察守护进程：

```bash
journalctl -u gazed -f | grep 'Face auth requested'
```

需要牢记四件事：

- 该范围只会被足够新、知晓它的守护进程尊重。软件包升级会重启 `gazed`（如果它已在运行），但如果你以其他方式构建或安装了 Gaze，而旧守护进程仍然存活，该延迟会持续应用于每个提示。如果 `screen_lock` 似乎被忽略了，请运行 `sudo systemctl restart gazed`。
- 从挂起恢复时，Gaze 会等待 `start_delay_ms` 与 `resume_grace_ms` 中较长的那一个。两者不会叠加。
- `resume_grace_ms` 忽略 `start_delay_scope`。它的存在是为了显示器能在挂起后重绘，这与正在询问的是哪个提示无关，因此无论该提示是什么，它都仍然适用于恢复后的第一次认证。
- 使用顺序 PAM 栈（`hyprlock-gaze`，默认）时，`pam_gaze.so` 在密码模块之前运行，因此该延迟也会推迟接受所输入密码的时间点。你可以在延迟期间输入，但你的第一次 Enter 可能在 PAM 仍处于 Gaze 内部时被消耗，需要再按一次。这与面部扫描进行中的现有等待行为相同。simultaneous 栈（`hyprlock-gaze-simultaneous`）并不能避免这一点：在锁屏上，simultaneous 模式也会在询问密码之前先扫描。

更新配置后，重启守护进程以应用更改：

```bash
sudo systemctl restart gazed
```

## 存储路径

Gaze 为你管理这些存储位置，因此你无需配置它们：

- 用户嵌入数据：`/var/lib/gaze/users`
- 胁迫锁定：`/var/lib/gaze/duress`
- 已下载的模型：`/var/cache/gaze`

模型在首次运行时会自动下载（如果缺失）。

## 使用 TPM 加密面部模板

对于省略此设置的新安装与配置，模板加密默认**开启**。它需要一个可用的 TPM 2.0 芯片。显式设置 `encrypt_templates = false` 的现有配置仍保持退出状态；它们的嵌入数据以明文形式存放在 `/var/lib/gaze/users` 下，仅 root 可读。要启用加密：

```toml
[storage]
encrypt_templates = true
```

启用后，`gazed` 会将一个随机的 AES-256 密钥封装（seal）到 TPM，并以 AES-256-GCM 在该密钥下加密存储每个嵌入数据。被封装的密钥位于 `/var/lib/gaze/tpm/dek.blob`，且只能由**此** TPM 解封，因此在没有该 TPM 访问权限的情况下，被盗的磁盘（或在另一台机器上恢复的备份）无法被解密。`GZE2` 格式还会对账户名与嵌入数据文件名（包括其 RGB/IR 后缀）进行认证：将密文移动到另一个账户，或更改其光谱，都会导致认证失败。面部标签仍然可以在不重新加密的情况下重命名。这并不能防护运行中的机器上的特权代码、账户名复用，或针对同一账户的较旧有效模板的重放。

需要注意的行为：

- **失败即关闭（Fail-closed）。** 如果 `encrypt_templates = true` 但找不到可用的 TPM，守护进程会拒绝启动，而不是静默写入未受保护的生物识别数据。请检查 `journalctl -u gazed`，要么修复 TPM（例如在固件中启用它），要么显式将该标志设为 `false` 以接受明文存储。禁用模板加密也会禁用密钥环/钱包解锁，因为它需要加密。
- **仅机器绑定。** 密钥被封装到 TPM 的存储层级，没有 PCR 策略，因此固件、内核与 Secure Boot 更新**不会**将你锁在门外。它防护的是磁盘离开机器，而非机器自身的启动链被篡改。守护进程启动、凭据录入以及 `gaze doctor` 会在状态存储看似未加密或其加密无法被验证时发出警告。检测是尽力而为的：可见的 dm-crypt 后端路径会被识别；不可访问的 sysfs、网络、overlay 或不支持的存储布局会产生未知状态的警告。全盘加密必须覆盖状态存储，而不仅仅是你的主目录。Root 在解锁后仍可恢复密钥。
- **显式迁移。** 通过 `gaze config` 或 GUI 启用加密会显式迁移现有的明文存储。如果你通过手工编辑文件启用，或升级一个较旧的明文或混合格式存储，请运行下面的维护流程。启动绝不静默加密被植入的明文，或重新绑定遗留密文。关闭加密会解密当前格式的模板，这同样需要封装了它们的 TPM。迁移会暂存一份完整的替换存储，并原子地交换目录，因此它需要足够容纳第二份副本的空闲空间，以及一个支持原子目录交换的文件系统。不支持的文件系统会失败，而不会发布部分转换。失败的实时配置保存会恢复旧存储。
- **遗留加密模板。** 较旧的 `GZE1` 密文没有账户绑定，在正常启动期间绝不会被接受用于匹配或自动重新绑定。请遵循下方显式的维护流程，或移除旧模板并重新录入。
- **TPM 重置。** 如果 TPM 被清除，被封装的密钥（以及因此的加密模板）变得不可恢复。归档或移除不可读的模板存储与陈旧的 `/var/lib/gaze/tpm`，然后重新录入。守护进程不会以它再也无法解封的被封装密钥启动。

应用更改：

```bash
sudo systemctl restart gazed
```

### 升级遗留加密模板

当通过编辑配置启用加密或升级一个被省略的存储设置时，对较旧的加密、明文或混合格式模板使用此流程。只迁移你信任其现有账户目录所有权的存储。遗留加密无法证明某个模板尚未在用户之间被移动过；如果有疑问，请改为重新录入。在迁移之前，保留 `/var/lib/gaze/users` 与 `/var/lib/gaze/tpm` 两者的受保护备份，并保持一个可用的密码登录。

```bash
sudo systemctl stop gazed
sudo gazed --migrate-legacy-templates
sudo systemctl start gazed
```

维护命令不会加载相机/推理模型。一个进程锁会防止它与守护进程并发运行。它会验证所有加密记录，并在发布一份完整的、绑定所有者的存储之前绑定明文输入；暂存失败会保留原始存储不变。成功升级后，不再需要该命令。正常的启动仍然会拒绝之后引入的任何明文或遗留密文。

旧的 `dek.pub` / `dek.priv` 密钥对会在成功解封后自动升级为单一、仅所有者可读的 `dek.blob`。一份不完整的遗留密钥对是一个错误，而不是创建替换密钥的许可：请从备份中恢复缺失的 blob。格式错误的包绝不会回退到旧文件。

录入同样会在驱逐旧模板之前发布一个完全同步的批次。被中断的暂存与删除目录会被排除在匹配之外，并在启动时清理。以 `.gaze-` 开头的名称保留给内部存储；在迁移之前，具有该前缀的既有标签必须被重命名或移除，而不会被静默丢弃。如果存储回滚本身失败，匹配与变更会以失败关闭的方式停止，直到重启；两份完整的存储副本都会保留以供恢复。

## 在一次 GDM 或 greetd 面部登录后解锁 GNOME 密钥环

`storage.unlock_gnome_keyring` 默认为 `false`。它需要 TPM 模板加密与活体检测；若缺任一，该选项会被忽略，守护进程会记录原因。启用之后，请为每个用户运行 `gaze keyring`。跳过它的用户继续用面孔登录，并像之前一样被提示输入密钥环。请先阅读 [GNOME 密钥环设置](/projects/gaze/guide/gnome#optional-tpm-backed-keyring-unlock) 中的安全说明：所存储的密码可被本机上的 root 恢复。

## 在一次 KDE 面部登录后解锁 KWallet

`storage.unlock_kwallet` 同样默认为 `false`，且需要 TPM 模板加密与活体检测两者。为 KDE 登录钱包解锁启用它，然后运行 `gaze keyring --kwallet` 与 `sudo gaze-kde-pam enable-login`。其凭据独立于 GNOME 密钥环。详见 [KWallet 设置](/projects/gaze/guide/kde#optional-tpm-backed-kwallet-unlock) 了解受支持的登录服务、PAM 设置，以及重新录入的要求。

## 录入行为

```toml
[enrollment]
max_templates = 2
min_face_size_ratio = 0.25
```

如果认证在多变光线下不可靠，请增大 `max_templates`。

`min_face_size_ratio` 控制在录入期间可接受的最小检测到的面孔，以画面较短边的比例表示。默认的 `0.25` 要求面孔至少占据该尺寸的的四分之一。降低它允许从更远处录入；例如 `0.20` 允许比默认大约远 25% 处的面孔。接受 `0.10` 到 `0.75` 之间的值。

此设置仅在录入期间适用；认证不强制执行相同的居中与接近阈值。请选择仍然感觉舒适的最高值，因为较小的面部裁剪为所录入模板提供的细节更少。

### 多相机与混合录入

Gaze 可以录入同时适用于 RGB 与 IR 相机的档案。它捕获的内容取决于你录入时的相机配置：

- **单相机：** 如果只配置了 RGB 相机（默认），Gaze 仅捕获并保存 RGB 模板。
- **双相机（混合）配置：** 如果 RGB 与 IR 相机都已配置，Gaze 会在录入期间从两者捕获。每一步都会等待来自两个传感器的有效、对齐的帧。

### 升级现有档案

如果你在录入面孔之后添加或配置了 IR 相机，你现有的档案将只包含 RGB 捕获。
- 要查看每个档案包含哪些捕获，请运行 `gaze list-faces` 或打开 GUI 设置。`[RGB]` 与 `[IR]` 徽标在档案拥有该光谱的捕获时为绿色，在已配置相机但档案没有捕获时为琥珀色，在未配置相机时为灰色。
- 要向现有档案添加 IR 捕获，请确保 IR 相机已配置，然后运行：
  ```bash
  gaze refine-face <profile-name>
  ```
  你也可以在 GUI 中改善该档案。Gaze 会捕获缺失的光谱，并将新模板添加到现有档案中。

## 活体防欺骗

```toml
[liveness]
enabled = true
threshold = 0.8
max_seconds = 2.0
```

启用后，Gaze 会在识别匹配之后，对检测到的面部裁剪运行一个本地的 MiniFASNet-V2 防欺骗模型。只有当面孔匹配，且单帧达到 `threshold` 或最佳若干帧显示出持续接近阈值的活体状态时，认证才会成功。

除模型之外，Gaze 还会观察你的双眼在帧之间移动了多远，测量相对于两眼间距，因此它不依赖于你坐得有多近。一次已经累积了若干帧对、却从未见过高于该下限的运动会被当作静止物体而拒绝，即使模型很有信心。正常移动（呼吸、眨眼、微小的头部移动）会清除它；一旦有任何一对显示出运动，之后保持静止也不会撤销它。在 IR 相机上，这个运动检查就是整个活体测试，因为防欺骗模型是在彩色帧上训练的。

`max_seconds` 限定了 Gaze 在放弃并回退到你的密码之前检查相机的时长（以可用面部帧的秒数计）。它限定的是整个尝试，而不仅仅是活体阶段：一个未被识别的面孔会消耗同样的预算。Gaze 使用你相机的实际帧率动态计算帧预算（例如 2.0 秒对应于 30fps 摄像头上的 60 帧，或 60fps 摄像头上的 120 帧）。只有当可用面孔在视野中时帧才计数，且 RGB 与 IR 阶段各自获得完整的预算。如果认证在你准备好之前就放弃，请提高它；`gaze auth --verbose` 会在一次运行以此种方式结束时报告。

## 胁迫信号

```toml
[duress]
enabled = false
closed_threshold = 0.9
hold_ms = 600
```

别人可以把你的笔记本举到你面前，但他们无法逼你输入密码。开启胁迫检测后，你可以用眼睛拒绝一次被胁迫的面部解锁：在相机看到你时保持一只（或两只）眼睛闭上。

工作原理：

- 在你的面孔匹配之后，Gaze 会在每只眼睛上运行一个小型本地睁/闭眼分类器（[Intel Open Model Zoo 的 `open-closed-eye-0001`](https://github.com/openvinotoolkit/open_model_zoo/tree/master/models/public/open-closed-eye-0001)，约 46 KB，Apache-2.0）。它会在第一次启用胁迫时下载到 `/var/cache/gaze`。
- 任何一只眼睛闭合的匹配帧永远不会解锁。仅此一点就意味着一次眨眼无法让被胁迫的解锁通过。
- 如果一只眼睛保持闭合达到 `hold_ms`，Gaze 会拒绝该尝试，并锁定该用户的面部认证。在锁定期间，面部解锁报告自身不可用，并直接穿透到密码提示，而不触碰相机。
- 该锁定存储在 `/var/lib/gaze/duress`，因此重启或守护进程重启都不会清除它。
- 它在一次未使用你的面孔的成功登录之后清除，例如以 root 运行且 auth 栈中包含 `pam_gaze.so` 的服务上的你的密码：登录 greeter（`gdm-password`、SDDM、LightDM、greetd）、`login`、`sudo`、`su` 与 polkit。以你身份运行的锁屏（hyprlock、swaylock、KDE 锁屏）无法清除它，因为守护进程无法判断那里是否使用了密码；请用你的密码解锁，然后运行 `sudo -v`，或重新登录。SSH 或 IMAP 等网络登录不会清除它。你也可以用 `gaze duress --clear` 清除它，这需要一次全新的管理员认证。

设置：

- `closed_threshold` 是分类器将一只眼睛算作闭合所需的闭眼概率（0.5 到 0.99）。如果故意的眨眼被漏检，请降低它；如果眯眼或大笑会触发它，请提高它。
- `hold_ms` 是眼睛必须保持闭合的时长（0 到 5000 毫秒）。正常的眨眼需要 100 到 400 毫秒。

胁迫表只存在于 `/etc/gaze/config.toml`。GUI 与 `gaze config` 不会触碰它。编辑后请用 `sudo systemctl restart gazed` 重启。

需要注意的限制：

- 在相机看到你之前闭上眼睛。任何两只眼睛都睁开的匹配帧都会像往常一样解锁。
- 另一种非面部登录方式，例如指纹，也会清除该锁定。
- 该分类器适用于 RGB 与 IR 帧，但它并非完美。在依赖它之前，请用 `gaze auth` 测试：一次保持的眨眼应以锁定结束，而 `gaze duress --clear` 会重置它。以 `RUST_LOG=debug` 运行 `gazed` 会记录逐眼得分。

## 推荐的调优工作流

1. 从 `[security] level = "medium"` 开始
2. 录入一个档案：`gaze add-face default`
3. 使用 `gaze auth --verbose` 测试 5 到 10 次
4. 如果担心照片或屏幕欺骗，保持 `[liveness] enabled = true`
5. 如果误接受过高，切换到 `high`
6. 如果误拒绝过高，运行 `gaze refine-face default`
