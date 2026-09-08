#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_deliverables.py — 生成 docs/deliverables.svg（三份交付物 · 从轻到全）

用途：
    把仓库「同一套逻辑做成三份交付物」的可视化：PROMPT.md（一段话）→ SKILL.md（流程与纪律）
    → scripts/bm.py（默认执行层），并点明默认路径判定：工作区有 bm.py 一律走脚本，禁止手改 JSON。

依赖：
    仅 Python 标准库，无第三方依赖（与 scripts/bm.py 同一约定）。

运行方式：
    python scripts/visualization/generate_deliverables.py

输出路径：
    docs/deliverables.svg（自动创建 docs/ 目录）

维护说明：
    改文案/配色/布局请改本脚本后重跑，不要手改 SVG。
"""
import html
import os
import pathlib

W, H = 1200, 600
OUT = pathlib.Path(__file__).resolve().parents[2] / "docs" / "deliverables.svg"

# 三档配色：从轻到全，逐档加深
TIERS = [
    {
        "name": "PROMPT.md",
        "sub": "一段话 · 零安装",
        "tag": "轻路径",
        "bg": "#e0f2fe", "head": "#0284c7", "ink": "#0c4a6e", "bar": "#38bdf8",
        "lines": [
            "复制给任意聊天 AI 就能跑",
            "无闸门：备份/写回全靠临场做对",
            "给一次性整理 · 先体验 · 分享",
        ],
    },
    {
        "name": "SKILL.md",
        "sub": "流程与纪律 · 技能化",
        "tag": "中间层",
        "bg": "#eef2ff", "head": "#4f46e5", "ink": "#312e81", "bar": "#818cf8",
        "lines": [
            "同一条 0→7 流程 + 硬约束",
            "拿不到脚本时自动降级执行",
            "可单独加载当提示词 / 装 skill",
        ],
    },
    {
        "name": "scripts/bm.py",
        "sub": "默认执行层 · 闸门锁进代码",
        "tag": "正式用法（推荐）",
        "bg": "#fde68a", "head": "#b45309", "ink": "#451a03", "bar": "#fbbf24",
        "lines": [
            "10 个子命令：detect → restore",
            "体检 / 底牌 / 预览 / 原子写回 / 还原",
            "一次写对、每次一样 —— 唯一推荐对",
            "真实书签动手的方式",
        ],
    },
]


def esc(s):
    return html.escape(s, quote=True)


def card(t, x, y, w, h):
    """竖排卡片：顶部色条 + 标题 + 特性列表。"""
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{t["bg"]}" stroke="{t["head"]}" stroke-width="1.5"/>',
        # 顶部色条
        f'<rect x="{x}" y="{y}" width="{w}" height="7" rx="3.5" fill="{t["bar"]}"/>',
        f'<text x="{x + 24}" y="{y + 44}" font-size="21" font-weight="800" fill="{t["ink"]}">{esc(t["name"])}</text>',
        f'<rect x="{x + 24}" y="{y + 58}" width="4" height="16" rx="2" fill="{t["bar"]}"/>',
        f'<text x="{x + 36}" y="{y + 71}" font-size="13.5" font-weight="600" fill="{t["head"]}">{esc(t["sub"])}</text>',
        f'<text x="{x + 24}" y="{y + 98}" font-size="11.5" fill="{t["head"]}" opacity="0.9">〔{esc(t["tag"])}〕</text>',
    ]
    ty = y + 132
    for ln in t["lines"]:
        parts.append(f'<text x="{x + 24}" y="{ty}" font-size="13" fill="{t["ink"]}">· {esc(ln)}</text>')
        ty += 27
    return "\n".join(parts)


def arrow(x1, y1, x2, y2):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#94a3b8" stroke-width="2.4" marker-end="url(#arw)"/>')


def body():
    parts = []
    # 标题
    parts.append('<text x="600" y="50" text-anchor="middle" font-size="20" font-weight="800" fill="#0f172a">同一套逻辑，三份交付物 —— 从轻到全</text>')
    parts.append('<text x="600" y="78" text-anchor="middle" font-size="13.5" fill="#64748b">跑的是同一条「带循环」的 0→7 流程，差别只在闸门由谁守</text>')

    # 三张卡片（左→右），右侧留出默认执行层的强调条空间
    x = 60
    w = 330
    gap = 30
    y = 118
    h = 300
    for t in TIERS:
        parts.append(card(t, x, y, w, h))
        x += w + gap
    # 卡片间「递进」箭头
    parts.append(arrow(60 + w, 220, 60 + w + gap - 4, 220))
    parts.append(arrow(60 + w + gap + w, 220, 60 + w + gap + w + gap - 4, 220))

    # 底部默认路径判定条
    bx, by, bw, bh = 60, 458, 1080, 104
    parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="14" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5"/>')
    parts.append(f'<text x="{bx + 24}" y="{by + 34}" font-size="15" font-weight="700" fill="#0f172a">判定（动手前先看工作区）：</text>')
    parts.append(f'<text x="{bx + 24}" y="{by + 62}" font-size="13.5" fill="#0f172a">① 有 <tspan font-weight="700" fill="#b45309">scripts/bm.py</tspan> → 一律走脚本（默认）· 禁止绕开它手改 JSON</text>')
    parts.append(f'<text x="{bx + 24}" y="{by + 86}" font-size="13.5" fill="#0f172a">② 拿不到脚本 → 降级「仅提示词」（SKILL.md 流程，AI 人肉守闸）　③ 只是临时体验 → 复制 PROMPT.md</text>')
    return "\n".join(parts)


def render():
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="'Segoe UI', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif">
  <defs>
    <marker id="arw" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>
{body()}
</svg>
'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8", newline="\n")
    print(f"written: {OUT} ({os.path.getsize(OUT)} bytes)")


if __name__ == "__main__":
    render()
