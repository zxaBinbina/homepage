#!/usr/bin/env python3
"""按映射表机械替换间距/圆角硬编码为 token（阶段一，零视觉偏差）。

用法：python3 scripts/apply-spacing-radius-tokens.py <scope>
scope ∈ style | components | rdp | gaze

规则（与已确认的映射表一致）：
- 刻度值 → 基础 token；非刻度正值 → --*-alt-N 临时档
- 白名单保持字面量：0/0px/auto/none/50%/inherit/百分比/0.06em、
  负值 margin、>60px 单次版式留白、calc()/clamp()/var() 值
- 999px 圆角 → --radius-pill
- 跳过 .freemium-workbench / .jay-* 上游作用域（style.css 内）
- 不处理 src/loading/screen.css（首屏内联样式，早于 token 定义加载）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SPACE_SCALE = {4: "--space-2xs", 8: "--space-xs", 12: "--space-sm", 16: "--space-md", 20: "--space-lg", 24: "--space-xl", 32: "--space-2xl", 48: "--space-3xl"}
RADIUS_SCALE = {4: "--radius-2xs", 8: "--radius-xs", 12: "--radius-sm", 16: "--radius-md", 20: "--radius-lg", 24: "--radius-xl", 30: "--radius-2xl", 40: "--radius-shell", 999: "--radius-pill"}

PROP_RE = re.compile(r"^(\s*)((?:margin|padding)(?:-(?:top|right|bottom|left|inline|block))?|gap|row-gap|column-gap|border-radius)\s*:\s*([^;]+);")
UPSTREAM_SELECTOR_RE = re.compile(r"freemium-workbench|\.jay[-.]")
TERM_WHITELIST = {"0", "0px", "auto", "none", "50%", "inherit", "0.06em"}


def map_term(term: str, is_radius: bool):
    """返回替换后的 term（var 引用）或 None 表示保持字面量。"""
    if term in TERM_WHITELIST:
        return None
    if term.endswith("%"):  # 18%/28% 等椭圆形态
        return None
    m = re.fullmatch(r"(\d+(?:\.\d+)?)px", term)
    if not m:
        return None
    n = float(m.group(1))
    if is_radius:
        if n in RADIUS_SCALE and n == int(n):
            return f"var({RADIUS_SCALE[int(n)]})"
        return f"var(--radius-alt-{m.group(1)})"
    # 间距
    if n < 0 or n > 60:  # 负值与 >60px 单次版式留白：白名单
        return None
    if n in SPACE_SCALE and n == int(n):
        return f"var({SPACE_SCALE[int(n)]})"
    return f"var(--space-alt-{m.group(1)})"


def transform_line(line: str):
    m = PROP_RE.match(line)
    if not m:
        return line, False
    indent, prop, value = m.group(1), m.group(2), m.group(3)
    if any(fn in value for fn in ("calc(", "clamp(", "var(")):
        return line, False
    is_radius = prop == "border-radius"
    important = ""
    v = value
    if "!important" in v:
        important = " !important"
        v = v.replace("!important", "").strip()
    terms = v.split()
    if not terms:
        return line, False
    mapped = [map_term(t, is_radius) for t in terms]
    if all(x is None for x in mapped):
        return line, False
    new_terms = [t if x is None else x for t, x in zip(terms, mapped)]
    trailing = line[m.end():]
    new_line = f"{indent}{prop}: {' '.join(new_terms)};{important}{trailing}"
    # 保持原结尾（可能有注释等）——trailing 已含
    return new_line.rstrip("\n") + ("\n" if line.endswith("\n") else ""), True


def transform_css_text(text: str, path: str):
    """花括号栈跟踪作用域，跳过上游规则（含媒体查询内嵌），逐行替换。"""
    out = []
    changed = 0
    stack = []  # 每个未闭合 '{' 对应：该作用域选择器是否为上游范围
    details = []
    for lineno, raw in enumerate(text.splitlines(keepends=True), start=1):
        rstripped = raw.rstrip("\n")
        opens = rstripped.count("{")
        closes = rstripped.count("}")
        processed = False
        if stack and not stack[-1] and opens == 0:
            new_line, did = transform_line(rstripped)
            if did:
                changed += 1
                details.append((lineno, rstripped.strip(), new_line.rstrip()))
                if raw.endswith("\n") and not new_line.endswith("\n"):
                    new_line += "\n"
                out.append(new_line)
                processed = True
        if not processed:
            out.append(raw)
        # 先闭合后开启（处理 "} .foo {" 这类同行切换）
        for _ in range(closes):
            if stack:
                stack.pop()
        if opens:
            sel = rstripped.split("{")[0]
            stack.append(bool(UPSTREAM_SELECTOR_RE.search(sel)))
    return "".join(out), changed, details


VUE_STYLE_RE = re.compile(r"(<style[^>]*>)(.*?)(</style>)", re.S)


def transform_vue_file(path: Path):
    text = path.read_text(encoding="utf-8")
    total = 0
    all_details = []

    def repl(m):
        nonlocal total
        new_body, n, details = transform_css_text(m.group(2), path.as_posix())
        total += n
        all_details.extend(details)
        return m.group(1) + new_body + m.group(3)

    new_text = VUE_STYLE_RE.sub(repl, text)
    if total:
        path.write_text(new_text, encoding="utf-8")
    return total, all_details


SCOPE_FILES = {
    "style": [ROOT / "src" / "style.css"],
    "components": [
        ROOT / "src" / "components" / "MusicDialog.vue",
        ROOT / "src" / "components" / "MusicPlayer.vue",
        ROOT / "src" / "components" / "AnimatedCursor.vue",
    ],
    "rdp": [
        ROOT / "src" / "rdp" / "style.css",
        ROOT / "src" / "rdp" / "wiki.css",
        ROOT / "src" / "rdp" / "downloads.css",
        ROOT / "src" / "rdp" / "components" / "AuthDemo.vue",
        ROOT / "src" / "rdp" / "components" / "ExposureDemo.vue",
    ],
    "gaze": [
        ROOT / "src" / "gaze" / "style.css",
        ROOT / "src" / "gaze" / "components" / "GuidePage.vue",
        ROOT / "src" / "gaze" / "components" / "HomePage.vue",
    ],
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in SCOPE_FILES:
        print("用法: apply-spacing-radius-tokens.py <style|components|rdp|gaze>")
        return 2
    scope = sys.argv[1]
    grand = 0
    for f in SCOPE_FILES[scope]:
        if not f.exists():
            print(f"跳过不存在的 {f}")
            continue
        rel = f.relative_to(ROOT).as_posix()
        if f.suffix == ".vue":
            n, details = transform_vue_file(f)
        else:
            text = f.read_text(encoding="utf-8")
            new_text, n, details = transform_css_text(text, rel)
            if n:
                f.write_text(new_text, encoding="utf-8")
        grand += n
        print(f"{rel}: 替换 {n} 处")
        for lineno, old, new in details[:5]:
            print(f"    L{lineno}: {old}  ->  {new}")
        if len(details) > 5:
            print(f"    ... 共 {len(details)} 条")
    print(f"\n[{scope}] 合计替换 {grand} 处")
    return 0


if __name__ == "__main__":
    sys.exit(main())
