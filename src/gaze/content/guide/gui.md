<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# GUI 指南

::: tip 在 KDE Plasma 上
`gaze-kde` 会在"系统设置"中添加一个原生的 **Gaze** 页面，功能与此应用相同。详见 [KDE Plasma 指南](/projects/gaze/guide/kde#system-settings)。
:::

使用 `gaze-gui` 来录入人脸、测试识别以及调整 Gaze 设置。

::: tip 中文界面版本
本页对应 `v0.5.1` 的中文界面，窗口尺寸、控件顺序与页面结构沿用上游。
:::

启动它：

```bash
gaze-gui
```

- **录入面孔：** 跟随相机提示。如果同时配置了 RGB 与 IR 相机，Gaze 会从两者捕获。
- **查看档案：** 主窗口列出已录入的面孔、它们的总模板数量，以及 `RGB` 和 `IR` 徽标。当档案拥有该光谱的捕获数据时，徽标为绿色；当配置了相机但档案没有捕获数据时，为琥珀色；当未配置相机时，为灰色。因此一台仅 RGB 的机器会显示一个绿色的 `RGB` 徽标和一个灰色的 `IR` 徽标；灰色并不表示失败。
- **改善面孔：** 选择其改善图标以捕获额外的样本，或添加缺失的光谱。例如，你可以在配置了 IR 相机之后，为仅 RGB 的面孔添加 IR 捕获。
- **测试认证：** 运行一次面部扫描，以检查 Gaze 是否能识别你。
- **移除面孔：** 删除单个面孔。
- **更改守护进程设置：** 调整安全级别、相机、活体检测设置以及混合（hybrid）策略。

## 配置对话框

从头部栏的设置按钮打开配置对话框。

该对话框提供 `/etc/gaze/config.toml` 的常用选项，按以下页面分组显示。解锁需通过 polkit 授权，修改会自动保存到守护进程；未在 GUI 中显示的选项可通过 `gaze config` 或配置文件管理。

**安全**

- 安全级别：低、中、高、最高或自定义（配置值仍为 `low`、`medium`、`high`、`maximum`、`custom`）
- 选择自定义后显示检测器级别、识别器级别、RGB 与 IR 相似度阈值

**硬件**

- 推理执行后端：CPU、自动（NPU）、Intel OpenVINO 或 AMD Ryzen AI
- OpenVINO 推理设备；自动与 AMD 模式使用 NPU
- RGB 摄像头来源、红外摄像头来源
- 指定红外画面尺寸：自动模式下画面偏绿或损坏时，可设置固定宽度与高度
- 强制开启红外发射器：仅在无法自动开启时使用
- 并行采集 RGB 与红外：从不、自动或始终；默认依次采集，自动模式仅在摄像头支持时并行
- 暗光阈值：拒绝平均亮度低于指定值的画面（0–255）

标准构建提供上述推理后端。请按 [硬件加速](/projects/gaze/guide/acceleration) 安装厂商运行时与驱动，并在更改后端后重启守护进程。

**录入**

- 模板上限：每张人脸保存的采集组数
- 最小人脸占比：调低可在更远处录入

**活体防伪**

- 启用活体防伪、活体检测阈值、活体检测最长时长

**认证**

- 若为 SSH 则中止、若为合盖则中止
- 要求先挂起，即拒绝面部认证，直到机器已挂起并恢复过一次
- 锁屏要求确认、提权认证要求确认
- 恢复宽限期与启动延迟，均以毫秒为单位
- 启动延迟应用于：每次面部认证，或仅屏幕锁定器
- 混合匹配策略，在 RGB 与 IR 均录入时使用

**存储**

- 加密人脸模板：使用 TPM 密封密钥加密存储模板。详见 [工作原理](/projects/gaze/guide/how-it-works) 了解它防护了什么。
- 解锁 GNOME 密钥环，它会在一次受活体保护的 GDM 或 greetd 面部登录后重放已录入的密码。它需要开启模板加密与活体检测，且每个用户仍需运行 `gaze keyring`。请先阅读 [它对你的安全意味着什么](/projects/gaze/guide/gnome#what-this-changes-about-your-security)。
- 解锁 KWallet：在通过活体检测的 KDE 人脸登录后使用已录入的密码，同样需要模板加密和活体检测；运行 `gaze keyring --kwallet` 录入凭据，并按 [KDE 指南](/projects/gaze/guide/kde#optional-tpm-backed-kwallet-unlock) 配置。

## 常见任务

1. 录入一个名为 `default` 的档案。
2. 在正常室内光线下多次运行测试认证。
3. 如果你的外貌经常变化（例如戴眼镜），再添加一个档案。

## 何时用 GUI 还是 CLI

- 使用 GUI 进行录入以及快速的通过/失败检查。
- 当你想要详细的认证指标与诊断信息时，使用 CLI（`gaze auth --verbose`）。

## 如果 GUI 无法认证

检查守护进程状态：

```bash
systemctl status gazed
```

如果服务已停止，启用并启动它：

```bash
sudo systemctl enable --now gazed
```

然后从 GUI 重试。
