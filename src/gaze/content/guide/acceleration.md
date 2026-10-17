<!-- SPDX-FileCopyrightText: 2026 Gundu Labs -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# 硬件加速

Gaze 可以在其标准守护进程中使用 Intel OpenVINO（NPU、GPU 或 CPU）以及 AMD Ryzen AI/Vitis AI（NPU），无需重新编译 Gaze，也无需替换 CLI 或 GUI。默认情况下，Gaze 在 CPU 上运行推理，因此即使不进行任何加速设置也可以使用。如果你想使用受支持的加速硬件，请先安装对应的驱动与厂商运行时。

## Intel 设置

对于 Intel NPU 加速，首先安装发行版提供的 NPU 固件、内核支持（`intel_vpu`）以及用户态 Level Zero 驱动。在 Fedora 上，安装：

```bash
sudo dnf install intel-npu-driver oneapi-level-zero intel-npu-firmware
```

在其他发行版上，请[按照 Intel 的 Linux NPU 驱动说明操作](https://github.com/intel/linux-npu-driver)。接下来，将支持 OpenVINO 的 ONNX Runtime（1.21 或更新版本）安装到由 root 拥有的位置（例如 `/opt/onnxruntime-openvino`），然后[将其注册](/projects/gaze/guide/acceleration#register-a-runtime)为 `openvino` 运行时。

## AMD 设置

[AMD 当前的 Linux 指南](https://ryzenai.docs.amd.com/en/latest/linux.html)记录了面向 STX/KRK 平台（Strix、Strix Halo、Krackan Point）的 Ryzen AI 1.8，使用 Ubuntu 24.04 驱动包。较旧的 Phoenix/Hawk Point NPU 以及其他 Linux 发行版不在该文档化的 Linux 支持目标之内。

要设置 AMD 加速，请遵循该指南，将 AMD 的 XRT/NPU 驱动包与 Ryzen AI SDK 安装到由 root 拥有的系统位置（例如 `/opt/ryzen-ai`）。然后[注册运行时](/projects/gaze/guide/acceleration#register-a-runtime)为 `vitis`，并在其库路径中包含 `/opt/xilinx/xrt/lib`。

Ryzen AI 可以[将 FP32 模型编译为 BF16](https://ryzenai.docs.amd.com/en/latest/model_quantization.html)。Gaze 从现有的 ONNX 模型出发，并将符号化输入维度冻结为流水线实际使用的图像尺寸。模型编译、算子支持以及数值精度仍需要在具体的 NPU 与 SDK 版本上进行验证。

## 注册运行时

`gazed` 会在 `/usr/lib/gaze/runtimes/<provider>` 中查找每个厂商运行时，其中 `<provider>` 为 `openvino` 或 `vitis`。该目录包含两项内容：

- `libonnxruntime.so`：指向厂商 ONNX Runtime 库的符号链接
- `library-path`：以冒号分隔的绝对目录列表，保存 SDK 的其他共享库

例如，对于 AMD：

```bash
sudo mkdir -p /usr/lib/gaze/runtimes/vitis
sudo ln -sf /opt/ryzen-ai/onnxruntime/lib/libonnxruntime.so \
    /usr/lib/gaze/runtimes/vitis/libonnxruntime.so
echo /opt/ryzen-ai/onnxruntime/lib:/opt/xilinx/xrt/lib \
    | sudo tee /usr/lib/gaze/runtimes/vitis/library-path
```

注册运行时后，在 `/etc/gaze/config.toml` 中启用加速：

```toml
[inference]
execution_provider = "auto"
device = "npu"
```

最后，重启守护进程并检查每个模型是否使用了预期的 provider：

```bash
sudo systemctl restart gazed
gaze doctor --benchmark
```

## 配置与恢复

你可以显式选择 `openvino/npu` 或 `vitis/npu`，而不是自动选择。若要改用 Intel GPU，注册 `openvino` 运行时并设置为 `openvino/gpu`；`auto` 仅选择 NPU。GUI 与 `gaze config` 都提供了这两种 provider。在切换不同厂商时请重启守护进程：每个进程只加载一个 ONNX Runtime 库。

Gaze 根据 `/sys/class/accel` 与绑定的 NPU 驱动（而非 CPU 品牌名）来选择自动模式。`gaze doctor` 会报告检测到的设备以及缺失的注册项。缺失或不兼容的厂商运行时、不可用的驱动、失败的模型编译或失败的启动推理探测，都会回退到 CPU，并在 `gaze doctor --benchmark` 与守护进程日志中给出原因：

```bash
journalctl -u gazed -b
```

成功的 provider 会话中可能包含 CPU 图分区。计时与 provider 标签并不衡量算子驻留情况或功耗。请针对相同的模型和设置，与 `cpu/cpu` 基线进行对比。

编译缓存位于 `/var/cache/gaze/inference`，以模型内容、运行时标识/版本以及内核发行版本为键。在升级某个厂商的用户态驱动或 SDK 后，使用 `sudo rm -rf /var/cache/gaze/inference/<provider>` 清除该厂商的缓存。首次编译耗时可能长于后续的守护进程启动。

出于安全考虑，请将运行时库及其依赖项保持为 root 所有，放在 `/home` 与 `/root` 之外（这些目录被 `gazed.service` 隐藏），且不可被其他用户写入。Gaze 在加载前会校验库的 ONNX Runtime API，并在启动线程之前仅使用所选厂商的 `library-path` 重新执行守护进程。

要切换回 CPU 推理，请在 `gaze config` 中选择 `cpu/cpu` 并重启 `gazed`。

对于 NixOS，请使用 Nix 管理的驱动/运行时包，并通过服务环境设置 `ORT_DYLIB_PATH` 与 `LD_LIBRARY_PATH`，同时采用相同的推理设置。`/usr/lib/gaze/runtimes` 注册方式适用于常规发行版包。

## 硬件验证

对于每个厂商，请同时测试两种模型质量、RGB 与 IR 识别器、MiniFASNet 活体检测，以及（若已启用）睁眼状态模型。检查启动与预热行为、冷启动与缓存启动时间，以及每个模型的平均延迟和 p95 延迟。在具有代表性的真实样本与欺诈样本上，将识别与活体分数与 CPU 结果进行对比，包括启用加速之前登记的人脸档案。除非验证结果支持更改，否则保留现有阈值。

请演练以下场景：缺失驱动、缺失 SDK 依赖、不支持的模型算子、驱动/SDK 升级，以及切换回 CPU。验证密码回退与恢复，同时不要放宽服务的沙箱限制。CI 会在没有物理 NPU 的情况下测试配置、发现、原生 API 校验与推理回退；它不会对任一厂商硬件上的模型精度或性能进行认证。
