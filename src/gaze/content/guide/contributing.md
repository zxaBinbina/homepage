<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# 参与贡献

感谢你帮助改进 Gaze。本指南介绍如何提出更改、需要测试什么，以及在处理认证、PAM、打包与文档时应避免什么。

有关源码构建与特定组件的配置，请从[开发指南](/projects/gaze/guide/development)开始。

## 参与方式

- 报告可复现的 bug，附上日志、发行版版本、桌面环境以及失败的命令。参见[提交问题](#opening-an-issue)。
- 在行为描述不清、缺失或特定于某发行版时改进文档。
- 为纯逻辑、边界情况与回归添加聚焦的测试。
- 修复受支持发行版的打包、安装或卸载问题。
- 改进摄像头、DBus、CLI、GUI、PAM 或 GNOME 扩展的行为。

## 开始之前

- 查看已有的 issue 与 pull request，避免重复劳动。
- 对于较大的行为变更、新的配置键、打包策略变更或认证流程变更，先开一个 issue 或讨论。
- 保持改动小而可审阅。每个 pull request 最好只包含一个 bug 修复或一项功能。
- 不要提交下载的 ML 模型、人脸嵌入、本地配置、软件包产物或密钥。
- 如果你使用了 AI 工具，请在开 pull request 之前阅读 [AI 辅助贡献](#ai-assisted-contributions)。

## 许可

Gaze 采用 [GNU 通用公共许可证，版本 3 或更新](https://github.com/zxaBinbina/gaze-zh/blob/main/LICENSE)（`GPL-3.0-or-later`）授权。通过提交 pull request，即表示你同意你的贡献在相同条款下授权。

- 每个新源文件都请以全树统一使用的 SPDX 头开始：

  ```rust
  // SPDX-FileCopyrightText: 2026 Gundu Labs
  // SPDX-License-Identifier: GPL-3.0-or-later
  ```

  Shell 脚本使用 `#` 注释，并将头放在 shebang 正下方。

- 不要将来自与 GPLv3 不兼容许可证项目的代码复制进 Gaze，也不要添加无法与 GPLv3 代码一同分发的依赖。`just audit` 不会检查许可证，因此请自行检查任何新依赖的许可证。
- 新的 crate manifest 通过 `license.workspace = true` 从工作区继承许可证；新的打包文件必须声明 `GPL-3.0-or-later`。
- 在根 `Cargo.toml` 的 `[workspace.dependencies]` 下声明一次依赖版本，然后在 crate 中使用 `name.workspace = true`，并只添加该 crate 所需的特性。

## 本地设置

克隆仓库，从[开发指南](/projects/gaze/guide/development)安装依赖，然后运行：

```bash
just setup-hooks
just --list
```

钩子设置是每次检出本地的。CI 仍会对推送和 pull request 运行必需的检查。

## 工作流程

1. 创建一个带有简短描述性名称的分支。
2. 做出最小且正确的改动。
3. 当行为发生变化时，添加或更新测试。
4. 当用户可见的行为、安装步骤、配置、CLI 输出或打包行为发生变化时，更新文档。
5. 在本地运行相关的检查。
6. 开一个 pull request 并填写模板。参见[开 pull request](#opening-a-pull-request)。

## 必需的检查

在开 pull request 之前运行这些：

```bash
just fmt-check
just lint
just test
just audit
```

如果你更改了 `Justfile`，还需运行：

```bash
just --fmt --check
```

如果你更改了打包文件、脚本、systemd 单元、DBus 策略、PAM 集成或 GNOME 扩展打包，请至少构建受影响的软件包格式：

```bash
just package <deb | rpm | archlinux>
```

如果你更改了 PAM 模块所链接的任何东西，包括 `gaze-core` 的依赖，请检查它们的共享库占用：

```bash
just build-rust
just check-pam-link
```

`just build-rust` 以及每次软件包构建都已经运行此检查，因此那里的失败意味着某个依赖进入了不应出现的 `pam_gaze.so`。参见[开发指南中的警告](/projects/gaze/guide/development#build-and-test-rust-components)。

## 测试

优先选择不需要硬件或系统服务即可在 CI 中运行的测试。

适合测试的目标：

- 配置解析、默认值，以及 DBus map 转换。
- 用户数据库校验、持久化、匹配与错误路径。
- 不下载文件的模型辅助逻辑。
- 对齐、预处理，以及其他纯数学或图像变换。
- CLI 解析与显示辅助行为。

避免需要以下条件的 CI 测试：

- 物理摄像头。
- 正在运行的系统 DBus `gazed` 服务。
- 安装到系统认证文件中的 PAM。
- 图形会话。
- 下载模型包所需的网络访问。

这些方面请改用手动测试说明。

## 手动测试

对于守护进程的更改，请停止已安装的服务，并在前台运行本地构建：

```bash
sudo systemctl stop gazed
just build-rust
sudo RUST_LOG=debug ./target/release/gazed
```

然后针对拥有系统总线的守护进程运行客户端：

```bash
./target/release/gaze list-faces
./target/release/gaze auth --verbose
./target/release/gaze-gui
```

完成后重启已安装的服务：

```bash
sudo systemctl start gazed
```

## PAM 安全

PAM 更改可能让你无法使用认证流程。

- 在编辑 PAM 文件之前，请保持一个拥有活跃 root shell 的第二个终端打开。
- 先使用非关键 PAM 服务进行测试，而不是 `sudo`、`system-auth` 或你的图形登录。
- 在 `pam-gaze` 中谨慎使用不安全的 FFI。
- 在 pull request 中包含精确的手动测试步骤。

## 文档风格

- 首先为使用者写作。把应当运行的命令放在长篇解释之前。
- 当路径或软件包不同时，说明发行版之间的差异。
- 命令与配置片段使用围栏代码块。
- 对于安全、PAM、GDM 与锁定的风险，保留明确的警告。
- 链接到就近页面，而不是重复长篇的设置说明。
- 不要编辑 `docs/.vitepress/dist` 下生成的文件；请编辑 Markdown 或主题文件，然后重新构建文档。

要在本地预览文档：

```bash
bun run docs:dev
```

要验证文档构建：

```bash
bun run docs:build
```

## 提交问题

[开一个新问题](https://github.com/zxaBinbina/gaze-zh/issues/new/choose)，并选择相符的模板：

| 模板 | 用途 |
| --- | --- |
| Bug 报告 | 刷脸认证、摄像头、守护进程、GUI 或某个桌面集成行为不正确。 |
| 安装与打包 | 在 Gaze 运行之前就失败的任何事情：安装器、包管理器、仓库或 GPG 密钥、缺失的共享库、冲突的软件包、损坏的升级。 |
| 功能请求 | 新的能力、配置键、桌面集成或发行版。 |
| 文档 | 错误、缺失、过时或不清晰的文档。 |

请填写表单所要求的详细信息。提前提供你的环境与日志，有助于我们少花时间追问。

### 一份 bug 报告需要什么

bug 表单会收集以下全部内容，但如果你是在已有 issue 上补充，下面这些是值得包含的信息：

- Gaze 版本（`gaze --version`）与安装方式。混用仓库，或在 AUR 包与官方包之间切换，会造成真实故障。
- 发行版与版本、桌面环境与版本、会话类型（Wayland 或 X11），以及若涉及登录管理器或锁屏时的显示管理器。多个 bug 特定于某个 GNOME Shell 或 Plasma 发布。
- `gaze doctor` 的完整输出，以你的桌面用户身份、在图形会话内（而非通过 SSH 或 `sudo` 下）运行，这样它才能看到该用户的 PipeWire 会话与桌面集成。请包含通过的检查，而不仅仅是失败的。
- 覆盖故障的守护进程日志，取自 `journalctl -u gazed -b --no-pager | tail -300`。故障之前的那些行通常能解释原因。
- 哪些界面受影响，哪些正常。在 `gaze auth` 下成功、却在登录管理器处失败的刷脸匹配，与一个在所有地方都失败的匹配指向截然不同的方向。
- 对于摄像头、IR 或识别问题：`gaze config --show`、`gaze auth --verbose`，以及通过 `udevadm info -q property -n /dev/video0` 得到的摄像头厂商与型号 ID。这些 ID 能告诉我们你的硬件是否需要专用的红外发射器配置。
- 对于 KDE：`gaze-kde-pam status` 以及你的 PAM 栈。在 Fedora 上，厂商副本位于 `/usr/lib/pam.d`，只有在有人自定义后才会出现在 `/etc/pam.d` 中，因此请同时包含这两个路径。
- 对于 Omarchy：`gaze-omarchy doctor`、`omarchy-shell lock status`，以及 `/etc/pam.d/gaze-omarchy-face`。
- 你是否在任何时候运行过 `gaze uninstall`。它会故意移除 `/etc/gaze/config.toml`，因此之后的重新安装会给你一个默认配置，看起来与丢失设置的 bug 一模一样。
- 它是否曾经正常过，以及最后一个正常的版本。

分享日志前请移除私人数据。日志可能包含用户名、主机名与设备序列号。人脸模板与嵌入永远不会写入日志，因此这些无需担心。

请通过[私密安全公告](https://github.com/zxaBinbina/gaze-zh/security/advisories/new)报告认证、PAM 或模板存储方面的漏洞，而非公开 issue。

## 开 pull request

[pull request 模板](https://github.com/zxaBinbina/gaze-zh/blob/main/.github/pull_request_template.md) 会自动加载。删除不适用的部分，但保留 **Verification** 与 **AI disclosure**，这两项在每个 pull request 中都是必需的。

请包含：

- 改变了什么以及为什么，以用户会注意到的行为差异开头。
- 对于 bug 修复，说明根本原因。当修复只有一行时，这正是 pull request 中价值所在的一半。
- [必需检查](#required-checks) 的输出，请粘贴而非仅声明。
- 添加或更新的测试，或说明该行为在没有硬件或系统服务的情况下无法在 CI 中测试。
- 足够精确、他人可重复的手动验证步骤，以及你运行它们的环境：发行版、桌面、会话类型、显示管理器、摄像头型号。
- PAM 更改的精确手动测试步骤，以及你所采取的 [PAM 安全](#pam-safety) 防范措施。
- 确认新文件带有 SPDX 头，且未复制任何与许可证不兼容的代码。
- 后续工作与已知限制。说明你因没有 GNOME 机器而无法测试 GDM 路径，比沉默更有用，且不会成为 pull request 的减分项。

## AI 辅助贡献

我们欢迎 AI 辅助的贡献，并会与其他贡献一样按相同标准审阅。请在使用过模型时进行披露，以便审阅者知道哪些部分可能需要更仔细的关注。

要求披露，是因为它改变了审阅者需要检查的内容。一个误读 PAM 句柄生命周期的人，会在周围的推理中留下审阅者可以追溯的痕迹。一个虚构出这种细节的模型，会产生一个从头到尾看起来都正确的 diff，并用自信的注释解释一个从未成立的不变量。两者需要不同方式的关注，而在认证代码中，这种差异至关重要。

pull request 模板要求你从以下选项中选择一项：

- **None.** 手写。
- **Assisted.** AI 在部分环节提供了帮助，例如补全、样板代码、文档措辞、测试脚手架或命名。你主导了设计并通读了每一行。
- **Generated.** AI 根据你的提示生成了大部分 diff。你审阅了全部内容并理解它。
- **Agentic.** 一个智能体在有限的监督下基本独立地生成了它。

写出你使用的工具，并说明模型在哪些地方提供了帮助，包括你不得不纠正的任何内容。例如，指出它处理了正常路径却编造了错误处理，有助于审阅者集中注意力。

无论适用哪一项，以下原则都成立：

- **只报告你实际运行过的检查和测试。** 结果应来自真实运行，而非预测、代码检查或工具的报告。“已通过语法校验”和“测试进行中，稍后更新”都不是测试结果。描述一个未经测试的区域，比报告一次并未发生的通过更有帮助。
- **对贡献负责。** 准备好解释并捍卫 diff 中的每一处改动。如果有些部分你尚未理解，请在开 pull request 之前花时间审阅它们。
- **自行回应审阅意见。** 未经阅读就转发给工具的反馈，会产生对无人提出的问题看似合理的回复。
- **尊重许可。** 不要将专有、机密或与许可证不兼容的代码粘贴进 AI 工具以生成贡献，并确保输出不会复现此类代码。[许可规则](#licensing) 对生成代码与手写代码的适用方式完全相同。

对于在没有通读并理解 diff 的人参与下提交的、由智能体生成的 pull request，我们会将其关闭。请在开 pull request 之前确保有人已审阅这些更改；单靠数量并无帮助。
