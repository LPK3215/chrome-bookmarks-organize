#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_workflow.py — 生成 docs/workflow.svg（0→7 带循环主流程示意图）

用途：
    把 README「核心：一条『带循环』的流程」画成一张 SVG，突出三个关键事实：
      1) 准备段（detect → preflight → backup → show）全程只读；
      2) plan / preview 在一个循环区里反复确认，绝不写原文件；
      3) 只有 finalize 一步真正写回；不满意走 restore 回到底牌那一刻，再回到循环区。

依赖：
    仅 Python 标准库，无第三方依赖（与 scripts/bm.py 同一约定）。

运行方式：
    python scripts/visualization/generate_workflow.py

输出路径：
    docs/workflow.svg（自动创建 docs/ 目录）

维护说明：
    改文案/配色/布局请改本脚本后重跑，不要手改 SVG。
"""
import html
import os
import pathlib

# ---------- 画布 ----------
W, H = 1200, 640
OUT = pathlib.Path(__file__).resolve().parents[2] / "docs" / "workflow.svg"

# ---------- 配色 ----------
C_PREP = "#eef2ff"          # 只读准备：indigo-50
C_PREP_S = "#4f46e5"
C_PREP_T = "#312e81"
C_LOOP_BG = "#fffbeb"       # 循环区：amber-50
C_LOOP_S = "#f59e0b"
C_LOOP_T = "#b45309"
C_WRITE_BG = "#fee2e2"      # 唯一写回：red-100
C_WRITE_S = "#dc2626"
C_WRITE_T = "#7f1d1d"
C_VERIFY_BG = "#ecfdf5"     # 校验验收：emerald-50
C_VERIFY_S = "#10b981"
C_VERIFY_T = "#065f46"
C_RESTORE_S = "#e11d48"     # restore 回环
C_ARROW = "#94a3b8"
C_CMD = "#0f172a"
C_DESC = "#475569"
C_CARD = "#ffffff"


def esc(s):
    return html.escape(s, quote=True)


def chip(cx, y_center, w, title, desc, bg, stroke, title_color):
    """宽高 60 的双行信息块；cx 为中心 x。"""
    x0 = cx - w / 2
    return f'''<g>
  <rect x="{x0:.1f}" y="{y_center - 30}" width="{w}" height="60" rx="10" fill="{bg}" stroke="{stroke}" stroke-width="1.5"/>
  <text x="{cx}" y="{y_center - 2}" text-anchor="middle" font-size="14.5" font-weight="700" fill="{title_color}">{esc(title)}</text>
  <text x="{cx}" y="{y_center + 17}" text-anchor="middle" font-size="11" fill="{C_DESC}">{esc(desc)}</text>
</g>'''


def line(x1, y1, x2, y2, color=C_ARROW, width=2, dash=None, marker="arw"):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{width}"{d} marker-end="url(#{marker})"/>')


def polyline(pts, color, width=2, dash="7 5", marker=None):
    m = f' marker-end="url(#{marker})"' if marker else ""
    return (f'<polyline points="{pts}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-dasharray="{dash}"{m}/>')


def body():
    parts = []
    a = parts.append

    # ============ 第 1 行：准备段（只读） ============
    a('<text x="150" y="58" font-size="12.5" font-weight="600" fill="#64748b">① 定位 · 底牌 · 读结构（全程只读）</text>')
    a(chip(225, 108, 150, "detect", "按 OS 定位 Bookmarks", C_PREP, C_PREP_S, C_PREP_T))
    a(line(305, 108, 326, 108))
    a(chip(415, 108, 180, "preflight", "体检 → GO / NO-GO", C_PREP, C_PREP_S, C_PREP_T))
    a(line(510, 108, 531, 108))
    a(chip(610, 108, 150, "backup", "底牌 + sha256 + 还原命令", C_PREP, C_PREP_S, C_PREP_T))
    a(line(690, 108, 711, 108))
    a(chip(795, 108, 150, "show", "读结构 · 逐条标重复", C_PREP, C_PREP_S, C_PREP_T))

    # show → 进入循环区
    a(line(795, 140, 795, 181))

    # ============ 循环区 ============
    a(f'<rect x="40" y="190" width="1040" height="150" rx="16" fill="{C_LOOP_BG}" stroke="{C_LOOP_S}" stroke-width="1.6" stroke-dasharray="8 5"/>')
    a(f'<text x="560" y="219" text-anchor="middle" font-size="14.5" font-weight="700" fill="{C_LOOP_T}">② 循环区 · 改到满意才放行（全程不写原文件）</text>')
    a(chip(255, 275, 175, "plan", "重排 → 候选文件", "#ffffff", C_LOOP_S, C_LOOP_T))
    a(chip(625, 275, 195, "preview", "渲染本地 HTML 肉眼核对", "#ffffff", C_LOOP_S, C_LOOP_T))
    a(f'<text x="470" y="264" text-anchor="middle" font-size="24" font-weight="700" fill="{C_LOOP_S}">⇄</text>')
    a(f'<text x="470" y="300" text-anchor="middle" font-size="11" fill="{C_DESC}">与用户反复确认</text>')

    # 用户拍板 → finalize
    a(line(405, 340, 405, 372, color=C_VERIFY_S))
    a(f'<text x="500" y="364" font-size="11.5" fill="{C_VERIFY_S}">用户拍板「就这版」↓</text>')

    # ============ 第 3 行：唯一写回 + 校验验收 ============
    a(f'<text x="150" y="425" font-size="12.5" font-weight="600" fill="#64748b">③ 写回 · 校验 · 验收</text>')
    a(chip(405, 410, 205, "finalize", "唯一写回 · 原子替换 · 自动兜底", C_WRITE_BG, C_WRITE_S, C_WRITE_T))
    a(line(510, 410, 568, 410))
    a(chip(668, 410, 195, "verify / diff", "结构 · 数量 · 变更分类对账", C_VERIFY_BG, C_VERIFY_S, C_VERIFY_T))
    a(line(770, 410, 818, 410))
    a(chip(920, 410, 200, "重启浏览器验收", "肉眼确认新结构生效", C_VERIFY_BG, C_VERIFY_S, C_VERIFY_T))

    # ============ restore：回到底牌 → 回到循环区 ============
    a(line(920, 442, 920, 497, color=C_RESTORE_S))
    a(f'<rect x="560" y="505" width="600" height="90" rx="14" fill="#fff1f2" stroke="{C_RESTORE_S}" stroke-width="1.6" stroke-dasharray="8 5"/>')
    a(f'<text x="860" y="536" text-anchor="middle" font-size="14" font-weight="700" fill="#be123c">不满意 → restore 一键还原</text>')
    a(f'<text x="860" y="562" text-anchor="middle" font-size="12.5" fill="#9f1239">回退到底牌那一刻；回到 ② 循环区，换规则重新 plan / preview</text>')
    # 卡片右上角沿右侧空档绕回循环区底部
    a(polyline("1120,505 1120,430 990,346", C_RESTORE_S, width=2, dash="7 5", marker="arw-red"))

    return "\n".join(parts)


def render():
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="'Segoe UI', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif">
  <defs>
    <marker id="arw" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="{C_ARROW}"/>
    </marker>
    <marker id="arw-red" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="{C_RESTORE_S}"/>
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
