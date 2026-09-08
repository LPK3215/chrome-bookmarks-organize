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
    仅 Python 标准库 + 同目录 theme.py（共享配色 / 字体 / 明暗自适应）。

运行方式：
    python scripts/visualization/generate_workflow.py

输出路径：
    docs/workflow.svg 与  project_overview/assets/workflow.svg（同一份内容，双写）

维护说明：
    改文案/配色/布局请改本脚本（或 theme.py）后重跑，不要手改 SVG。
"""
from theme import box, chip, line, note, path as svg_path, section_label, svg_doc, write_outputs

W, H = 1200, 700

# 循环区外框
LOOP = (111, 210, 978, 150)
# 写回 / 校验 行
ROW3_Y = 440
# restore 回环框
RES = (600, 530, 560, 110)


def body():
    p = []
    a = p.append

    # ---------- 标题 ----------
    a(note(60, 46, "0→7 主流程：带循环，只有一个写入口", tone="tx", size=19, weight=800))
    a(note(60, 70, "准备段只读 → 循环区反复确认（不碰真身）→ 拍板后唯一写回 → 校验验收 → 不满意回底牌",
           tone="dim", size=12.5, weight=500))

    # ---------- ① 准备段（只读） ----------
    a(section_label(60, 108, "①", "定位 · 体检 · 底牌 · 读结构（全程只读）", tone="blue"))
    cw, gap = 210, 46
    x0 = (W - (4 * cw + 3 * gap)) / 2
    centers = [x0 + cw / 2 + i * (cw + gap) for i in range(4)]
    a(chip(centers[0], 150, cw, 64, "detect", "按 OS 环境变量定位 Bookmarks", "blue"))
    a(line(centers[0] + cw / 2, 150, centers[1] - cw / 2 - 4, 150))
    a(chip(centers[1], 150, cw, 64, "preflight", "体检 → GO / NO-GO", "blue"))
    a(line(centers[1] + cw / 2, 150, centers[2] - cw / 2 - 4, 150))
    a(chip(centers[2], 150, cw, 64, "backup", "时间戳底牌 + sha256 + 还原命令", "blue"))
    a(line(centers[2] + cw / 2, 150, centers[3] - cw / 2 - 4, 150))
    a(chip(centers[3], 150, cw, 64, "show", "读结构 · 逐条标重复（同/跨目录）", "blue"))

    # show → 循环区
    a(line(centers[3], 182, centers[3], LOOP[1] - 4))

    # ---------- ② 循环区 ----------
    a(box(*LOOP, tone="yellow", fill="yellow-bg", dash="8 5", radius=16))
    a(note(LOOP[0] + 26, LOOP[1] + 32, "② 循环区 · 改到满意才放行（全程不写原文件）",
           tone="yellow", size=14, weight=800))
    a(chip(420, 300, 240, 64, "plan", "--sort / --dedup → 候选文件", "yellow"))
    a(chip(790, 300, 260, 64, "preview", "渲染本地 HTML 肉眼核对", "yellow"))
    a(note(600, 296, "⇄", tone="yellow", size=22, weight=800, anchor="middle"))
    a(note(600, 320, "与用户反复确认", tone="dim", size=11, anchor="middle"))

    # ---------- 拍板 → 写回 ----------
    a(line(600, LOOP[1] + LOOP[3], 600, ROW3_Y - 42, tone="red", width=2.2))
    a(note(614, ROW3_Y - 52, "用户拍板「就这版」↓", tone="red", size=12, weight=700))

    # ---------- ③ 写回 · 校验 · 验收 ----------
    a(section_label(196, ROW3_Y - 48, "③", "写回 · 校验 · 验收", tone="red"))
    rw, rgap = 250, 44
    rx0 = (W - (3 * rw + 2 * rgap)) / 2
    rcenters = [rx0 + rw / 2 + i * (rw + rgap) for i in range(3)]
    a(chip(rcenters[0], ROW3_Y, rw, 70, "finalize", "唯一写回 · 原子替换 · 自动兜底", "red", badge="唯一写入口"))
    a(line(rcenters[0] + rw / 2, ROW3_Y, rcenters[1] - rw / 2 - 4, ROW3_Y, tone="green"))
    a(chip(rcenters[1], ROW3_Y, rw, 70, "verify / diff", "结构 · 数量 · 变更分类对账", "green"))
    a(line(rcenters[1] + rw / 2, ROW3_Y, rcenters[2] - rw / 2 - 4, ROW3_Y, tone="green"))
    a(chip(rcenters[2], ROW3_Y, rw, 70, "重启浏览器验收", "肉眼确认新结构生效", "green"))

    # ---------- restore 回环 ----------
    a(line(rcenters[2], ROW3_Y + 35, rcenters[2], RES[1] - 4, tone="red"))
    a(box(*RES, tone="red", fill="red-bg", dash="8 5", radius=14))
    a(note(RES[0] + RES[2] / 2, RES[1] + 34, "不满意 → restore 一键还原",
           tone="red", size=15, weight=800, anchor="middle"))
    a(note(RES[0] + RES[2] / 2, RES[1] + 60, "回退到底牌那一刻，回到 ② 循环区换规则重来",
           tone="dim", size=12.5, anchor="middle"))
    a(note(RES[0] + RES[2] / 2, RES[1] + 86, "与 finalize 同级安全闸：浏览器在跑拒绝 · 覆盖前先校验底牌",
           tone="dim2", size=11, anchor="middle"))
    # 沿右侧空档绕回循环区
    a(svg_path("M1170,585 L1170,320 L1092,320", tone="red", dash="7 5", marker="arw-red", width=2))

    # ---------- 底部图例 ----------
    a(note(60, 678, "虚线框 = 循环 / 回退路径　·　红 = 会真正改动文件的操作　·　绿 = 校验与验收　·　蓝 = 只读准备",
           tone="dim2", size=11.5, weight=500))

    return "\n".join(p)


def render():
    svg = svg_doc(W, H, body(), title="0→7 带循环主流程")
    write_outputs("workflow.svg", svg)


if __name__ == "__main__":
    render()
