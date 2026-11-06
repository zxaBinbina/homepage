#!/usr/bin/env python3
"""盘点站点内间距与圆角的硬编码声明（一次性审计脚本，留档复用）。

扫描范围：
- src/style.css（排除 .freemium-workbench 与 .jay-* 上游作用域规则）
- src/HomePage.vue、src/ProjectDirectory.vue、src/components/*.vue
- src/rdp/、src/gaze/、src/games/、src/errors/、src/loading/
- src/tools/ 中除 freemium/、jaytools/ 之外的页面级文件

排除值（白名单）：50%、inherit、0、auto、none、calc() 内部、var() 引用。
999px 单独计数（阶段一将替换为 --radius-pill）。

输出：
- artifacts/spacing-radius-inventory.json  逐条清单
- artifacts/spacing-radius-frequency.json  值频次统计
- 控制台摘要
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGET_PROPS = (
    "margin",
    "margin-top",
    "margin-right",
    "margin-bottom",
    "margin-left",
    "margin-inline",
    "margin-block",
    "padding",
    "padding-top",
    "padding-right",
    "padding-bottom",
    "padding-left",
    "padding-inline",
    "padding-block",
    "gap",
    "row-gap",
    "column-gap",
    "border-radius",
)
PROP_RE = re.compile(
    r"^\s*(" + "|".join(TARGET_PROPS) + r")\s*:\s*([^;]+);",
)

UPSTREAM_SELECTOR_RE = re.compile(r"freemium-workbench|\.jay[-.]")
AT_RULE_RE = re.compile(r"@(media|supports|container)\b")


def scan_css_text(text: str, path: str, selector_prefix: str = ""):
    """逐行扫描 CSS 文本（花括号栈跟踪作用域，正确处理媒体查询内嵌规则）。"""
    records = []
    stack = []  # 每个未闭合 '{'：(是否上游作用域, 是否 @media, 选择器文本)
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip("\n")
        opens = line.count("{")
        closes = line.count("}")
        if stack and not stack[-1][0] and opens == 0:
            decl_part = line
            if closes:
                decl_part = line.split("}")[0]
            m = PROP_RE.match(decl_part)
            if m:
                prop, value = m.group(1), m.group(2).strip()
                records.append(
                    {
                        "file": path,
                        "line": lineno,
                        "property": prop,
                        "value": value,
                        "selector": (selector_prefix + " " + _last_selector(stack)).strip()
                        if _last_selector(stack)
                        else selector_prefix or "(inline)",
                        "in_media": any(s[1] for s in stack),
                    }
                )
        for _ in range(closes):
            if stack:
                stack.pop()
        if opens:
            sel = line.split("{")[0].strip()
            is_media = bool(AT_RULE_RE.match(sel))
            stack.append((bool(UPSTREAM_SELECTOR_RE.search(sel)), is_media, sel))
    return records


def _last_selector(stack):
    # 找最近的非 @media 作用域名（用于记录归属选择器）
    for entry in reversed(stack):
        if not entry[1]:
            return entry[2]
    return ""


VUE_STYLE_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.S)
INLINE_STYLE_RE = re.compile(r"""[:\s]style\s*=\s*["']([^"']+)["']""")


def scan_vue_file(path: Path):
    text = path.read_text(encoding="utf-8")
    records = []
    for m in VUE_STYLE_RE.finditer(text):
        block = m.group(1)
        offset = text[: m.start(1)].count("\n") + 1
        base = path.relative_to(ROOT).as_posix()
        sub = scan_css_text(block, base)
        for r in sub:
            r["line"] += offset
            r["source"] = "style-block"
        records.extend(sub)
    # 模板内联 style 属性
    for m in INLINE_STYLE_RE.finditer(text):
        block = m.group(1)
        if not any(p in block for p in ("margin", "padding", "gap", "radius")):
            continue
        offset = text[: m.start(1)].count("\n") + 1
        for part in block.split(";"):
            part = part.strip()
            if not part:
                continue
            if ":" not in part:
                continue
            prop, value = part.split(":", 1)
            prop = prop.strip()
            value = value.strip()
            if prop not in TARGET_PROPS:
                continue
            records.append(
                {
                    "file": path.relative_to(ROOT).as_posix(),
                    "line": offset,
                    "property": prop,
                    "value": value,
                    "selector": "(template inline style)",
                    "in_media": False,
                    "source": "inline-style",
                }
            )
    return records


def collect_files():
    files = []
    files.append(ROOT / "src" / "style.css")
    files.append(ROOT / "src" / "HomePage.vue")
    files.append(ROOT / "src" / "ProjectDirectory.vue")
    files.extend(sorted((ROOT / "src" / "components").glob("*.vue")))
    for sub in ("rdp", "gaze", "games", "errors", "loading"):
        d = ROOT / "src" / sub
        if d.exists():
            files.extend(sorted(d.rglob("*.vue")))
            files.extend(sorted(d.rglob("*.css")))
    # src/tools 排除上游目录
    tools = ROOT / "src" / "tools"
    if tools.exists():
        for p in sorted(tools.rglob("*")):
            if p.is_dir():
                continue
            rel = p.relative_to(tools).as_posix()
            if rel.startswith("freemium/") or rel.startswith("jaytools/"):
                continue
            if p.suffix in (".vue", ".css", ".ts"):
                files.append(p)
    return files


def parse_value_terms(value: str):
    """把简写值拆成逐个值项，返回 (terms, flags)。"""
    flags = set()
    v = value.strip()
    if "!important" in v:
        flags.add("important")
        v = v.replace("!important", "").strip()
    for fn in ("calc(", "clamp(", "min(", "max("):
        if fn in v:
            flags.add("function")
    if "var(" in v:
        flags.add("var")
    if flags & {"function", "var"}:
        return [], flags
    terms = [t for t in re.split(r"\s+", v) if t]
    return terms, flags


def main():
    all_records = []
    for f in collect_files():
        rel = f.relative_to(ROOT).as_posix()
        if f.suffix == ".css":
            all_records.extend(scan_css_text(f.read_text(encoding="utf-8"), rel))
        elif f.suffix == ".vue":
            all_records.extend(scan_vue_file(f))
        elif f.suffix == ".ts":
            # ts 中偶有注入样式字符串，扫描文本形式的属性行
            text = f.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), start=1):
                m = PROP_RE.match(line)
                if m:
                    all_records.append(
                        {
                            "file": rel,
                            "line": lineno,
                            "property": m.group(1),
                            "value": m.group(2).strip(),
                            "selector": "(ts injected)",
                            "in_media": False,
                            "source": "ts",
                        }
                    )

    # 频次统计：逐值项，按属性组分开
    radius_freq = Counter()
    space_freq = Counter()
    prop_freq = Counter()
    whitelist_counter = Counter()
    pill_counter = 0
    for r in all_records:
        prop_freq[r["property"]] += 1
        terms, flags = parse_value_terms(r["value"])
        if flags & {"function", "var"}:
            whitelist_counter[f"{r['property']}: {r['value']}"] += 1
            continue
        for t in terms:
            if t in ("50%", "inherit", "0", "auto", "none", "0px"):
                whitelist_counter[f"{t}"] += 1
                continue
            if t == "999px":
                pill_counter += 1
                continue
            if r["property"] == "border-radius":
                radius_freq[t] += 1
            else:
                space_freq[t] += 1

    out_dir = ROOT / "artifacts"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "spacing-radius-inventory.json").write_text(
        json.dumps(all_records, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (out_dir / "spacing-radius-frequency.json").write_text(
        json.dumps(
            {
                "radius_value_frequency": dict(radius_freq.most_common()),
                "space_value_frequency": dict(space_freq.most_common()),
                "property_frequency": dict(prop_freq.most_common()),
                "whitelist_counts": dict(whitelist_counter.most_common()),
                "pill_999px": pill_counter,
                "total_declarations": len(all_records),
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )

    print(f"共扫描到 {len(all_records)} 条相关声明")
    print("按属性：", dict(prop_freq.most_common()))
    print(f"999px（将替换为 --radius-pill）：{pill_counter} 处")
    print("白名单值统计：", dict(whitelist_counter.most_common()))
    print("\n=== 圆角值频次 ===")
    for val, n in radius_freq.most_common():
        print(f"  {val:>10} × {n}")
    print("\n=== 间距值频次 ===")
    for val, n in space_freq.most_common():
        print(f"  {val:>10} × {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
