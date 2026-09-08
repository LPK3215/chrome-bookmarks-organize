#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
theme.py — 全仓库可视化资产的共享主题（配色 / 字体 / 明暗自适应 / 通用绘制件）

用途：
    让 README 示意图（docs/*.svg）、项目全景观览站（project_overview/）、
    GitHub 社交预览图（docs/social-preview.svg）用同一套视觉语言：
      · Chrome 四色点缀（蓝 / 绿 / 黄 / 红）+ 紫，中性色走冷灰蓝；
      · 圆角 12-16、1.5px 描边、克制的虚线循环框；
      · 命令名用等宽字体，其余用 Inter / 系统中文字体栈。

关键机制（明暗自适应）：
    每个图形元素都同时写「浅色 presentation attribute」+「语义 class」。
    SVG 内嵌 <style> 只在 prefers-color-scheme: dark 时用 class 覆盖颜色，
    因此 GitHub（浅色为主）显示浅色版，开启深色模式的浏览器自动切换深色版；
    即使宿主把 <style> 剥掉，也只会退回浅色版，不会变成黑块。

依赖：
    仅 Python 标准库，无第三方依赖（与 scripts/bm.py 同一约定）。

运行方式：
    本模块不直接运行，由 generate_*.py 导入：
        from theme import svg_doc, chip, arrow, write_outputs

维护说明：
    改配色 / 圆角 / 字体请改这里，一次改动全仓资产同步生效；不要手改 SVG。
"""
import html
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
ASSETS = ROOT / "project_overview" / "assets"

# ---------- 字体 ----------
FONT = "'Inter', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
FONT_MONO = "'JetBrains Mono', 'SFMono-Regular', Consolas, 'Microsoft YaHei Mono', monospace"

# ---------- 浅色配色（presentation attribute 的 fallback，也是 GitHub 默认显示效果） ----------
C = {
    "bg": "#ffffff",
    "panel": "#ffffff",
    "panel2": "#f8fafc",
    "bd": "#d7e0ee",
    "tx": "#0d1626",
    "dim": "#55677f",
    "dim2": "#8494ab",
    # 语义主色
    "blue": "#4285f4", "blue-bg": "#e8f0fe", "blue-fg": "#1a56c4",
    "green": "#34a853", "green-bg": "#e6f5ea", "green-fg": "#1e7e34",
    "yellow": "#f5a623", "yellow-bg": "#fef6e4", "yellow-fg": "#a35c00",
    "red": "#ea4335", "red-bg": "#fdeceb", "red-fg": "#c5221f",
    "purple": "#8b5cf6", "purple-bg": "#f3edff", "purple-fg": "#6d28d9",
    "gray": "#94a3b8", "gray-bg": "#f1f4f9",
}

# ---------- 深色覆盖（只在 prefers-color-scheme: dark 生效） ----------
_DARK_FILL = {
    "f-bg": "#0a0f1a",
    "f-panel": "#0f1728",
    "f-panel2": "#141f33",
    "f-blue-bg": "#16294a", "f-green-bg": "#123021", "f-yellow-bg": "#33280f",
    "f-red-bg": "#36161a", "f-purple-bg": "#241a44", "f-gray-bg": "#172032",
    "f-dim": "#7c8ea8", "f-dim2": "#63748d",
    "t-tx": "#e9eefb", "t-dim": "#93a5c2", "t-dim2": "#6e809d",
    "t-blue": "#8ab4ff", "t-green": "#6ee79b", "t-yellow": "#fbd25c",
    "t-red": "#ff8a80", "t-purple": "#b9a5ff",
}
_DARK_STROKE = {
    "s-bd": "#2a3a58",
    "s-blue": "#5b9bff", "s-green": "#4ade80", "s-yellow": "#fbc531",
    "s-red": "#ff6b5e", "s-purple": "#a78bfa",
    "s-dim": "#7c8ea8", "s-dim2": "#5b6c85",
}

TONES = ("blue", "green", "yellow", "red", "purple", "gray")


def esc(s):
    return html.escape(str(s), quote=True)


def dark_style():
    """生成只在深色模式下生效的 <style> 覆盖块。"""
    rules = [f"    .{k} {{ fill: {v}; }}" for k, v in _DARK_FILL.items()]
    rules += [f"    .{k} {{ stroke: {v}; }}" for k, v in _DARK_STROKE.items()]
    return (
        "  <style>\n"
        "    text { font-family: " + FONT + "; }\n"
        "    .mono { font-family: " + FONT_MONO + "; }\n"
        "    @media (prefers-color-scheme: dark) {\n"
        + "\n".join(rules) + "\n"
        "    }\n"
        "  </style>"
    )


def defs():
    """多色箭头 marker；颜色同样跟随明暗主题（class f-* 覆盖 marker path 的 fill）。"""
    out = ["  <defs>"]
    for name, cls, color in (
        ("arw", "f-dim", C["gray"]),
        ("arw-blue", "f-dim", C["blue"]),
        ("arw-green", "f-dim", C["green"]),
        ("arw-red", "f-dim", C["red"]),
        ("arw-yellow", "f-dim", C["yellow"]),
    ):
        out.append(
            f'    <marker id="{name}" viewBox="0 0 10 10" refX="8.5" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" class="{cls}" fill="{color}"/></marker>'
        )
    out.append("  </defs>")
    return "\n".join(out)


def svg_doc(w, h, body, title="", subtitle=""):
    """包装成完整 SVG 文档：样式 + defs + 背景 + 可选标题区 + body。"""
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT}">',
        f"  <title>{esc(title or 'chrome-bookmarks-organize')}</title>",
        dark_style(),
        defs(),
        f'  <rect x="0" y="0" width="{w}" height="{h}" rx="0" class="f-bg" fill="{C["bg"]}"/>',
    ]
    return "\n".join(head) + "\n" + body + "\n</svg>\n"


# ---------- 通用绘制件 ----------
def chip(cx, cy, w, h, title, desc, tone="blue", mono=True, badge=None):
    """圆角信息块：命令名（等宽）+ 一行说明；tone 决定语义色。可选右上角徽章。"""
    x, y = cx - w / 2, cy - h / 2
    cls = "green" if tone == "green" else tone
    parts = [
        f'  <rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="12" '
        f'class="f-{cls}-bg s-{cls}" fill="{C[cls + "-bg"]}" stroke="{C[cls]}" stroke-width="1.5"/>',
        f'  <text x="{cx}" y="{cy - 3}" text-anchor="middle" font-size="15" font-weight="800" '
        f'class="t-{cls}" fill="{C[cls + "-fg"]}"' + (' font-family="' + FONT_MONO + '"' if mono else '') + f'>{esc(title)}</text>',
        f'  <text x="{cx}" y="{cy + 16}" text-anchor="middle" font-size="11.5" '
        f'class="t-dim" fill="{C["dim"]}">{esc(desc)}</text>',
    ]
    if badge:
        bw = len(badge) * 11 + 16
        bx = x + w - bw - 10
        parts.append(
            f'  <rect x="{bx:.1f}" y="{y - 9:.1f}" width="{bw}" height="19" rx="9.5" '
            f'fill="{C[cls]}" stroke="none"/>'
        )
        parts.append(
            f'  <text x="{bx + bw / 2:.1f}" y="{y + 4.5:.1f}" text-anchor="middle" font-size="11" '
            f'font-weight="800" fill="#ffffff">{esc(badge)}</text>'
        )
    return "\n".join(parts)


def section_label(x, y, no, text, tone="blue"):
    """阶段标签：编号圆点 + 说明文字。"""
    return "\n".join([
        f'  <circle cx="{x + 9}" cy="{y - 4}" r="9" fill="{C[tone]}"/>',
        f'  <text x="{x + 9}" y="{y}" text-anchor="middle" font-size="11" font-weight="800" fill="#ffffff">{esc(no)}</text>',
        f'  <text x="{x + 26}" y="{y}" font-size="12.5" font-weight="700" class="t-dim" fill="{C["dim"]}">{esc(text)}</text>',
    ])


def line(x1, y1, x2, y2, marker="arw", tone=None, dash=None, width=2):
    color = C[tone] if tone else C["gray"]
    cls = f' s-{tone}' if tone else ' s-dim'
    mk = f' marker-end="url(#{marker})"' if marker else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls.strip()}" '
            f'stroke="{color}" stroke-width="{width}"{da}{mk}/>')


def path(d, marker="arw", tone=None, dash=None, width=2):
    color = C[tone] if tone else C["gray"]
    cls = f' s-{tone}' if tone else ' s-dim'
    mk = f' marker-end="url(#{marker})"' if marker else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'  <path d="{d}" fill="none" class="{cls.strip()}" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round"{da}{mk}/>')


def note(x, y, text, tone="dim", size=12.5, anchor="start", weight=600, mono=False):
    return (f'  <text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" '
            f'class="t-{tone}" fill="{C[tone]}"'
            + (' font-family="' + FONT_MONO + '"' if mono else '') + f'>{esc(text)}</text>')


def box(x, y, w, h, tone="gray", dash=None, fill="bg", radius=14, width=1.5):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
            f'class="f-{fill} s-{tone}" fill="{C[fill]}" stroke="{C[tone]}" '
            f'stroke-width="{width}"{da}/>')


def write_outputs(filename, svg_text):
    """同一份 SVG 同时写入 docs/（README + Pages 引用）与 project_overview/assets/（站点副本）。"""
    targets = []
    if filename.startswith("social"):
        targets = [DOCS / filename]
    else:
        targets = [DOCS / filename, ASSETS / filename]
    for t in targets:
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text(svg_text, encoding="utf-8", newline="\n")
        print(f"written: {t} ({os.path.getsize(t)} bytes)")
