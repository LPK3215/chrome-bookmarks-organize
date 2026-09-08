#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_deliverables.py — 生成 docs/deliverables.svg（三份交付物 · 从轻到全）

用途：
    把仓库「同一套逻辑做成三份交付物」可视化：PROMPT.md（一段话）→ SKILL.md（流程与纪律）
    → scripts/bm.py（默认执行层），并点明默认路径判定：工作区有 bm.py 一律走脚本，禁止手改 JSON。

依赖：
    仅 Python 标准库 + 同目录 theme.py（共享配色 / 字体 / 明暗自适应）。

运行方式：
    python scripts/visualization/generate_deliverables.py

输出路径：
    docs/deliverables.svg 与  project_overview/assets/deliverables.svg（同一份内容，双写）

维护说明：
    改文案/配色/布局请改本脚本（或 theme.py）后重跑，不要手改 SVG。
"""
import pathlib

from theme import C, box, esc, line, note, svg_doc, write_outputs

W, H = 1200, 620

# 三档：从轻到全，逐档加重（tone 与全景观览页阶梯卡一致）
TIERS = [
    {
        "name": "PROMPT.md",
        "sub": "一段话 · 零安装",
        "tag": "轻路径 · 无闸门",
        "tone": "blue",
        "lines": [
            "整段复制给任意聊天 AI 即可跑",
            "备份 / 退浏览器 / 删 checksum 全靠自觉",
            "给一次性整理 · 先体验 · 分享给别人",
        ],
    },
    {
        "name": "SKILL.md",
        "sub": "流程与纪律 · Skill 化",
        "tag": "中间层 · 人肉守闸",
        "tone": "purple",
        "lines": [
            "同一条 0→7 流程 + 硬约束 + Pitfalls",
            "拿不到脚本时自动降级执行",
            "可单独加载当提示词 / 装成 skill",
        ],
    },
    {
        "name": "scripts/bm.py",
        "sub": "默认执行层 · 闸门锁进代码",
        "tag": "正式用法（唯一推荐）",
        "tone": "green",
        "badge": "默认",
        "lines": [
            "10 个子命令：detect → restore",
            "体检 / 底牌 / 预览 / 原子写回 / 还原",
            "1010 行单文件、仅标准库、零依赖",
            "一次写对、每次一样 —— 对真实书签动手",
        ],
    },
]


def card(t, x, y, w, h):
    """竖排卡片：顶部色条 + 文件名 + 副标题 + 徽章 + 特性列表。"""
    tone = t["tone"]
    parts = [
        box(x, y, w, h, tone=tone, fill=tone + "-bg", radius=16, width=1.6 if t.get("badge") else 1.3),
        # 顶部色条
        f'  <rect x="{x}" y="{y}" width="{w}" height="6" rx="3" fill="{C[tone]}"/>',
        note(x + 24, y + 46, t["name"], tone=tone + "-fg", size=21, weight=800, mono=True),
        # 副标题左侧竖条
        f'  <rect x="{x + 24}" y="{y + 60}" width="4" height="16" rx="2" fill="{C[tone]}"/>',
        note(x + 36, y + 73, t["sub"], tone="tx", size=13.5, weight=600),
    ]
    # 徽章
    tag = t["tag"]
    tw = len(tag) * 7.6 + 20
    parts.append(
        f'  <rect x="{x + 24}" y="{y + 92}" width="{tw:.0f}" height="24" rx="12" '
        f'fill="{C[tone]}" opacity="0.14"/>'
    )
    parts.append(note(x + 34, y + 108, f"〔{tag}〕", tone=tone, size=11.5, weight=800))

    ty = y + 150
    for ln in t["lines"]:
        parts.append(f'  <circle cx="{x + 30}" cy="{ty - 4}" r="3" fill="{C[tone]}"/>')
        parts.append(note(x + 42, ty, ln, tone="tx", size=13, weight=500))
        ty += 28
    if t.get("badge"):
        bw = len(t["badge"]) * 12 + 22
        bx = x + w - bw - 18
        parts.append(
            f'  <rect x="{bx:.0f}" y="{y - 11}" width="{bw}" height="24" rx="12" fill="{C[tone]}"/>'
        )
        parts.append(
            f'  <text x="{bx + bw / 2:.0f}" y="{y + 5.5}" text-anchor="middle" font-size="12" '
            f'font-weight="800" fill="#ffffff">{esc(t["badge"])}</text>'
        )
    return "\n".join(parts)


def body():
    p = []
    a = p.append

    a(note(600, 48, "同一套逻辑，三份交付物 —— 从轻到全", tone="tx", size=20, weight=800, anchor="middle"))
    a(note(600, 74, "跑的是同一条「带循环」的 0→7 流程，差别只在闸门由谁守",
           tone="dim", size=13.5, weight=500, anchor="middle"))

    cw, gap, y, ch = 340, 30, 108, 330
    x = (W - (3 * cw + 2 * gap)) / 2
    for t in TIERS:
        a(card(t, x, y, cw, ch))
        x += cw + gap

    # 卡片间「递进」箭头
    ax = (W - (3 * cw + 2 * gap)) / 2
    a(line(ax + cw, 273, ax + cw + gap - 4, 273, width=2.4))
    a(line(ax + 2 * cw + gap, 273, ax + 2 * cw + 2 * gap - 4, 273, width=2.4))

    # 底部判定条
    bx, by, bw, bh = (W - (3 * cw + 2 * gap)) / 2, 472, 3 * cw + 2 * gap, 108
    a(box(bx, by, bw, bh, tone="gray", fill="panel2", radius=14))
    a(note(bx + 24, by + 34, "判定（动手前先看工作区）", tone="tx", size=15, weight=800))
    a(note(bx + 24, by + 62, "① 有", tone="tx", size=13.5, weight=500))
    a(note(bx + 58, by + 62, "scripts/bm.py", tone="green", size=13.5, weight=800, mono=True))
    a(note(bx + 176, by + 62, "→ 一律走脚本（默认）· 禁止绕开它手改 JSON", tone="tx", size=13.5, weight=600))
    a(note(bx + 24, by + 90, "② 拿不到脚本 → 降级「仅提示词」（SKILL.md 流程，AI 人肉守闸）",
           tone="tx", size=13.5, weight=500))
    a(note(bx + 560, by + 90, "③ 只是临时体验 → 复制 PROMPT.md", tone="tx", size=13.5, weight=500))

    return "\n".join(p)


def render():
    svg = svg_doc(W, H, body(), title="三份交付物 · 从轻到全")
    write_outputs("deliverables.svg", svg)


if __name__ == "__main__":
    render()
