#!/usr/bin/env python3
"""阶段二：将 ±2px 以内的 alt 临时档归并入标准刻度（已确认方案）。

- 归并范围：与基准刻度偏差 ≤2px 的临时档（38 个）
- 保留范围：偏差 >2px 的远档（18 个），保留 --*-alt-N 定义与引用
- 同时删除 :root 中已归并临时档的定义行
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FILES = [
    ROOT / "src" / "style.css",
    ROOT / "src" / "components" / "MusicDialog.vue",
    ROOT / "src" / "components" / "MusicPlayer.vue",
    ROOT / "src" / "rdp" / "style.css",
    ROOT / "src" / "rdp" / "wiki.css",
    ROOT / "src" / "rdp" / "downloads.css",
    ROOT / "src" / "rdp" / "components" / "AuthDemo.vue",
    ROOT / "src" / "rdp" / "components" / "ExposureDemo.vue",
    ROOT / "src" / "gaze" / "style.css",
    ROOT / "src" / "gaze" / "components" / "GuidePage.vue",
]

SPACE_SCALE = {4: "--space-2xs", 8: "--space-xs", 12: "--space-sm", 16: "--space-md", 20: "--space-lg", 24: "--space-xl", 32: "--space-2xl", 48: "--space-3xl"}
RADIUS_SCALE = {4: "--radius-2xs", 8: "--radius-xs", 12: "--radius-sm", 16: "--radius-md", 20: "--radius-lg", 24: "--radius-xl", 30: "--radius-2xl", 40: "--radius-shell", 999: "--radius-pill"}


def nearest(n, scale):
    return min(scale, key=lambda s: (abs(n - s), -s))


def build_mapping():
    """从源码引用统计 + 就近原则，返回归并映射 {alt_token: base_token}。"""
    src_texts = [f.read_text(encoding="utf-8") for f in FILES]
    counts = {}
    for text in src_texts:
        for m in re.finditer(r"var\((--(?:space|radius)-alt-(\d+))\)", text):
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    mapping = {}
    for tok in counts:
        kind = "space" if tok.startswith("--space") else "radius"
        n = int(tok.split("-")[-1])
        scale = SPACE_SCALE if kind == "space" else RADIUS_SCALE
        tgt = nearest(n, scale)
        if abs(tgt - n) <= 2:
            mapping[tok] = scale[tgt]
    return mapping


def main():
    mapping = build_mapping()
    print(f"归并映射 {len(mapping)} 项：")
    for k, v in sorted(mapping.items(), key=lambda x: int(x[0].split("-")[-1])):
        print(f"  {k} -> {v}")
    total = 0
    for f in FILES:
        text = f.read_text(encoding="utf-8")
        new = text
        n_file = 0
        for alt, base in mapping.items():
            new, n = re.subn(re.escape(f"var({alt})"), f"var({base})", new)
            n_file += n
        if f.name == "style.css":
            # 删除已归并临时档的定义行
            for alt in mapping:
                new, _ = re.subn(rf"^\s*{re.escape(alt)}:\s*[^;]+;\n", "", new, flags=re.M)
        if new != text:
            f.write_text(new, encoding="utf-8")
        total += n_file
        print(f"{f.relative_to(ROOT)}: 归并 {n_file} 处引用")
    print(f"\n合计归并 {total} 处引用，删除 {len(mapping)} 个临时档定义")
    return 0


if __name__ == "__main__":
    sys.exit(main())
