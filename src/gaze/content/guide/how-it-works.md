<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# Gaze 的工作原理

本页说明 Gaze 的人脸认证流水线是如何工作的。使用 Gaze 并不需要了解这些，但它有助于理解其行为。

## 安全性与活体检测

Gaze 在本地执行活体检测，并支持红外（IR）相机以帮助抵御欺诈攻击。

将 IR 相机与 RGB 活体检测结合使用，有助于 Gaze 抵御打印照片、屏幕回放与视频等呈现式攻击。在高安全环境中，请保留你惯用的系统认证方式（例如密码）作为回退。

## 隐私模型

- Gaze 在你的机器本地处理人脸；它不会将人脸数据发送到云服务。
- 不需要任何云账户。
- 人脸嵌入向量存储在 Gaze 的本地数据目录中，该目录仅 root 可读。
- 模板加密默认启用，并且需要一个可用的 TPM 2.0；既有的显式选择退出仍会被尊重。AES-GCM 将每个加密嵌入向量与其账户名和文件名绑定。TPM 封存保护的是被带到另一台机器的磁盘，而不是同一台机器上的另一次启动：因此还需启用全盘加密。参见[模板加密与旧版迁移](/projects/gaze/guide/configuration#encrypt-face-templates-with-the-tpm)。
- 如果你启用了[GNOME Keyring 解锁](/projects/gaze/guide/gnome#optional-tpm-backed-keyring-unlock)，你的账户密码会额外保存在一个受 TPM 保护的记录中，以便人脸登录能够解锁密钥环。该记录在本机可由 root 恢复；开启前请阅读安全说明。

## 认证流水线

```text
Camera frame -> Face detection (SCRFD) -> Face alignment -> Embedding (ArcFace: MobileFaceNet by default, ResNet50 at high/maximum security) -> Similarity match -> Liveness check (MiniFASNet-V2 / eye-motion on IR)
```

从高层来看，认证过程如下：

1. Gaze 从你配置的 GStreamer 相机来源捕获一帧。
2. 检测器定位人脸及其关键点。
3. Gaze 将人脸对齐为标准输入形状。
4. 识别模型将人脸转换为嵌入向量。
5. Gaze 将嵌入向量与你已登记的档案进行对比。如果 RGB 与 IR 相机都处于活动状态，它会根据配置的混合策略合并两者结果。根据该策略，可能需要其中一个或两个相机都匹配，或者当场景较暗时 Gaze 可以回退到 IR。
6. 如果启用了活体检测，MiniFASNet-V2 检查人脸裁剪区域是否存在欺诈。在 IR 相机路径上，Gaze 改为跨帧检查眼球运动。

当最佳相似度分数与活体分数都达到其配置阈值时，认证即成功。

## 一次认证尝试

以下所有内容在每次 `gaze auth`、PAM 提示或锁屏解锁时各发生一次。同一套守护进程代码在所有界面上运行，因此你用 `gaze auth --verbose` 能复现的问题，正是锁屏所遇到的问题。

### 相机开启之前

1. 客户端通过 DBus 认领（claim）守护进程。一次认领将该次运行绑定到单个用户，客户端在完成时释放它。从未被释放的认领会在 5 分钟后被回收，这样被遗弃的认领就无法一直占用相机。
2. Gaze 按顺序检查三项拒绝条件：自启动以来未挂起或恢复过（`auth.abort_before_first_resume`）、调用方位于 SSH 会话内（`auth.abort_if_ssh`）、以及笔记本盖已合上（`auth.abort_if_lid_closed`）。其中任意一项都会在触及相机之前结束本次尝试。当 logind 设置为合盖即挂起时，合盖是例外：参见[认证过程中的挂起](#suspend-during-an-attempt)。
3. Gaze 计算出哪些光谱可以运行。当 `cameras.rgb` 已设置*并且*你已登记 RGB 模板时，RGB 才会运行；IR 遵循相同规则。如果两者都无法运行，或者 `security.hybrid_policy = "and"` 要求两者但只登记了其一，本次尝试会在此结束，而不是在证据不完整的情况下继续。
4. `auth.start_delay_ms` 与 `auth.resume_grace_ms` 会推迟捕获。屏幕已锁定的时长会计入该延迟，因此锁定时间长于 `start_delay_ms` 的屏幕会立即开始。延迟之后会再次检查盖子，因为它可能在 Gaze 等待期间合上。

### 认证过程中的挂起

在合盖时启动的锁屏程序（例如来自 hypridle 的 `before_sleep_cmd` 的 hyprlock），会在机器睡眠前的一刻请求人脸认证。若没有特殊处理，该尝试会因合盖或黑屏而失败，锁屏在恢复后显示密码提示，且 Gaze 不再扫描。

Gaze 会监听 logind 的 `PrepareForSleep` 信号，从而将此类尝试挂起而非失败：

- 如果请求到达时系统已在挂起中，该请求会等待恢复。
- 如果盖子已合上，且 logind 的盖子动作（`HandleLidSwitch`，或其 `ExternalPower` 与 `Docked` 变体）为挂起或休眠，Gaze 会等待最多 3 秒让挂起开始，然后才拒绝。已接入扩展坞的笔记本，或被设置为 `ignore` 或 `lock` 的笔记本，会像之前一样立即被拒绝。
- 如果挂起在启动延迟期间或捕获中途开始，相机会被释放，本次尝试暂停。

恢复之后，本次尝试以 `auth.resume_grace_ms` 作为延迟重新开始。如果那时盖子仍然合上，`auth.abort_if_lid_closed` 会拒绝它。在尝试被挂起期间取消的客户端会像往常一样结束本次尝试。

### 打开相机

5. 配置的来源会解析为内核 `/dev/videoN` 节点，并直接使用 `v4l2src` 捕获。`primary` 表示第一个彩色节点，PipeWire 目标会解析为该同一相机背后的节点，而 `/dev/videoN` 路径或 USB `vid:pid` 会直接指定其节点。用户会话的 PipeWire 套接字永远不会被连接：它由被认证的用户控制。没有内核节点（包括手写 GStreamer 流水线）的来源会被拒绝。唯一的例外是仅能由 libcamera 驱动的相机上的 `primary`，例如 Intel IPU MIPI 相机：当所选节点只能经由 libcamera 驱动，或没有任何彩色节点可见时，守护进程会自行运行 `libcamerasrc`。
6. 流水线有 500 ms 时间达到播放（playing）状态。较慢的相机不被视为失败：帧循环会报告之后出现的任何错误。
7. 非特权预览（例如 GUI 相机视图）仍可在用户自己的会话中打开 `pipewiresrc` 流水线，在那里信任该会话是正确的。认证与登记永远不会这样做。

### 读取帧

8. **预热。** 自带自动曝光功能的传感器在流水线启动后会短暂输出黑帧，因此早期的暗帧并不能说明房间状况。最多 2 秒内这些帧被忽略而非上报。该宽限期是有条件的：如果画面在 1 秒且至少 8 帧后仍未变亮，Gaze 会判定没有任何东西在预热，并立即上报黑暗。一旦画面曾有过亮度，该宽限期即被用尽，因此扫描中途被遮挡的镜头会立即上报。当暗的 RGB 帧会直接把相机交给 IR 时，预热会被完全跳过，从而让混合设置保持即时切换。
9. **暗帧闸门。** 平均亮度低于 `cameras.dark_luma_threshold`（默认 20）的帧为 `TooDark`，永远不会到达检测器。
10. **检测与匹配。** 检测器找到人脸与关键点，人脸被对齐，识别模型生成嵌入向量，并将嵌入向量与已登记模板对比。嵌入向量仅针对 `Usable` 帧计算，因此偏暗或构图不佳的帧只消耗一次检测，仅此而已。
11. **活体检测。** 匹配时，反欺诈模型对人脸裁剪区域打分，并跨帧运行眼球运动检测。两者都必须通过。匹配但活体检测未通过的人脸会报告 `Face matched, but the liveness check did not pass`。
12. **IR。** 默认情况下（`cameras.parallel_capture = "never"`），IR 阶段会等待 RGB 释放相机，然后（若已配置）开启发射器。Windows Hello 发射器会频闪，因此 IR 路径容忍一段暗帧，仅在连续 8 帧后上报黑暗。

### 判定

结果是一个判定，加上每个光谱的最后捕获状态。当两个光谱都运行时，`security.hybrid_policy` 决定它们如何合并。判定通过 DBus 返回给客户端，PAM 将其转为消息与返回码。

## 超时与预算

看门狗每 250 ms 检查一次截止时间，因此一台完全停止输送帧的相机仍会被限制住。

| 截止时间 | 取值 | 计时起点 | 行为 |
| --- | --- | --- | --- |
| 启动延迟 | `auth.start_delay_ms`，在恢复后至少为 `auth.resume_grace_ms`（两者默认均为 0） | 请求到达时 | 捕获被推迟。可取消。 |
| 流水线启动 | 500 ms | `Playing` 状态请求时 | Gaze 停止等待状态变化，但保留流水线。 |
| 相机预热 | 最长 2 秒；若画面始终未变亮，则在 1 秒且 8 帧后提前结束 | 首帧 | 暗帧被忽略而非上报。 |
| 暗帧流 | 1 秒 | 预热后首个 `TooDark` | 认证尝试结束。"Need more light"。 |
| 无人脸 | 5 秒 | 最后一个包含人脸的帧 | 认证尝试结束。"Face not detected"。 |
| 无可用帧 | 8 秒 | 最后一个生成了嵌入向量的帧 | 认证尝试结束。限制住一直构图不佳的人脸。 |
| RGB 串行预算 | 4 秒 | RGB 阶段开始 | 即使未匹配，RGB 也将相机交给 IR。仅当 IR 同时运行且 `parallel_capture = "never"` 时。 |
| 帧预算 | `liveness.max_seconds` × 相机 fps，最少 6 帧（默认 2.0 秒，即 30 fps 下 60 帧） | 仅对每个光谱中可用人脸在画面内时计数的帧 | 认证尝试结束。记录为 `frame budget spent`。 |
| PAM 兜底 | 12 秒再加上启动延迟 | PAM 提示 | PAM 停止等待。"Face authentication timed out"。 |
| 客户端兜底 | 20 秒 | DBus 调用 | CLI 或 GUI 停止等待守护进程。 |
| 认领 | 5 分钟 | 认领 | 未释放的认领会被回收。 |

这些截止时间是刻意嵌套的：每个守护进程截止时间都在 PAM 兜底之前触发，而 PAM 兜底又在客户端兜底之前触发，因此你总能获得具体原因，而不是一个笼统的超时。

## 运行时相机的报告内容

每一帧产生一个状态。GUI 与 CLI 会显示其文字，守护进程通过 DBus 以 `FaceStatus` 形式发出。

| 状态 | 显示文字 | 含义 |
| --- | --- | --- |
| `Unused` | Camera is not in use... | 该光谱未运行。 |
| `NoFace` | Please look at the camera... | 检测器未找到任何人脸。 |
| `TooDark` | Need more light... | 该帧或其内的人脸区域低于 `cameras.dark_luma_threshold`。 |
| `Clipped` | Face is clipped. Please move back... | 人脸触碰到画面边缘。 |
| `Ready` | Hold still... | 已检测到人脸且本帧偏暗，但最近 5 帧的滚动平均值并非如此。属于瞬时下降，而非判定结果。 |
| `Usable` | Hold still... | 已检测到人脸且亮度足以匹配。仅这些帧会生成嵌入向量。 |

`NotCentered`、`TooFar` 与 `TooClose` 也存在，但只有登记时会检查居中与距离。在认证过程中你永远不会看到它们。

`Ready` 与 `Clipped` 算作"有人脸在画面内"，因此会推迟无人脸截止时间，但不会推迟无可用帧截止时间。这正是为何一个在场但始终不够可用的人脸会在 8 秒结束，而不是永远运行。

## 认证尝试如何结束

| 结束方式 | CLI | PAM 消息 | PAM 代码 |
| --- | --- | --- | --- |
| 匹配 | `Authenticated as: <face>` | Face Verified. | success |
| 人脸被判定但不匹配 | `Authentication failed` | Face not recognized. Enter your password. | `PAM_AUTH_ERR` |
| 匹配，但活体检测未通过 | `Authentication failed` 加上活体检测说明 | Face not recognized. Enter your password. | `PAM_AUTH_ERR` |
| 因过暗结束 | `Authentication failed` | Too dark for face authentication. Enter your password. | `PAM_AUTHINFO_UNAVAIL` |
| 因人脸缺失结束 | `Authentication failed` | Face not detected. Enter your password. | `PAM_AUTHINFO_UNAVAIL` |
| 相机从未运行，或无法联系到守护进程 | `Authentication failed` | Face authentication unavailable. Enter your password. | `PAM_AUTHINFO_UNAVAIL` |
| PAM 预算耗尽 | 不适用，仅 PAM | Face authentication timed out. Enter your password. | `PAM_AUTHINFO_UNAVAIL` |

只有真正被判定过的人脸才会返回 `PAM_AUTH_ERR`。所有其他结束方式都返回 `PAM_AUTHINFO_UNAVAIL`，它告诉 PAM 是 Gaze 没有得出任何结论，而不是你尝试失败，因此一个黑暗的房间或被其他程序占用的相机都不会算到你头上。因硬件错误结束的运行也会以同样方式上报。

## 在日志中查看

`journalctl -u gazed -b` 记录了每次尝试的形态。映射到上述截止时间的日志行如下：

| 日志行 | 含义 |
| --- | --- |
| `VerifyStart: sensing faces for user ...` | 捕获正在开始。会列出光谱、活体检测设置，以及捕获是否为串行。 |
| `Attempting to open GStreamer camera: ...` | 确切的流水线。有助于确认实际使用了哪个来源。 |
| `Opening the PipeWire camera failed ...; trying a direct V4L2 device` | 一个 PipeWire 来源（非特权预览路径）未能打开，接下来会重试 V4L2。特权认证直接捕获 V4L2，永远不会记录这一行。 |
| `RGB stream never brightened: mean_luma=0` | 画面是纯黑的。隐私快门已关闭、镜头盖未取下，或房间确实很暗。 |
| `RGB face region: mean_luma=..., threshold=..., status=...` | 某个状态背后的亮度读数。每种不同状态的首帧会被记录。 |
| `VerifyStart: giving up after 1000ms of dark frames` | 暗帧截止时间。 |
| `VerifyStart: giving up after 5s without a detected face` | 无人脸截止时间。 |
| `VerifyStart: giving up after 8s without a usable frame` | 无可用帧截止时间。 |
| `VerifyStart: frame budget spent` | 帧预算。同一行上的 `matched=true` 表示人脸匹配但活体检测未通过。 |

## 为什么多次采集有帮助

每次登记都会存储跨越略微不同角度的多个样本。

这让认证对以下情况更具鲁棒性：

- 头部小幅转动
- 轻微的光线变化
- 外观变化（例如戴眼镜）

## 数据储存位置

默认情况下，Gaze 将数据存储在这些位置：

- 用户嵌入向量：`/var/lib/gaze/users`
- TPM 封存的加密密钥（启用模板加密时）：`/var/lib/gaze/tpm/dek.blob`
- 受 TPM 保护的 GNOME Keyring 凭据（仅当运行过 `gaze keyring` 时）：`/var/lib/gaze/keyring`
- 模型文件：`/var/cache/gaze`
- 配置文件：`/etc/gaze/config.toml`

## 组件

- `gazed`：执行检测与识别的守护进程（crate：`gaze`）
- `gaze`：CLI 客户端（crate：`gaze-cli`，保持独立以便客户端二进制不链接 ONNX Runtime）
- `gaze-gui`：GTK 应用
- `pam_gaze.so`：PAM 模块。它本身不含任何相机或推理代码；它通过 DBus 询问 `gazed`，并把答案回报给 PAM。它链接 `gaze-security`，以便在成功登录后能够解封已存储的 GNOME Keyring 凭据
- PAM 集成、GNOME 与 Cinnamon 扩展，以及 KDE 用于登录/锁屏流程的生物识别 PAM 槽位

CLI 与 GUI 通过 DBus（`com.gundulabs.Gaze`）与守护进程通信。
