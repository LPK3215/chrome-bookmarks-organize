#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_social_preview.py — 生成 docs/social-preview.svg（GitHub 社交卡片）

用途：
    仓库分享到 GitHub / 社交平台时的预览大图（1280×640）。
    固定深色版（卡片场景不跟随系统主题），配色与全景观览站、README 示意图同源。

依赖：
    仅 Python 标准库 + 同目录 theme.py（共享配色 / 字体）。

运行方式：
    python scripts/visualization/generate_social_preview.py

输出路径：
    docs/social-preview.svg

使用方法：
    生成后到 GitHub 仓库 Settings → Social preview → Upload an image 上传该 SVG
    （若 GitHub 不接受 SVG，可用任意工具转成 PNG 后上传）。

维护说明：
    改文案 / 配色请改本脚本（或 theme.py）后重跑，不要手改 SVG。
"""
from theme import C, FONT, FONT_MONO, esc, write_outputs

W, H = 1280, 640

BG = "#0a0f1a"
PANEL = "#101a2c"
BORDER = "#25344f"
TEXT = "#e9eefb"
DIM = "#93a5c2"


def body():
    p = []
    a = p.append

    # ---------- 背景光斑 ----------
    a(f'  <rect x="0" y="0" width="{W}" height="{H}" fill="{BG}"/>')
    a(f'  <circle cx="120" cy="80" r="420" fill="url(#glowBlue)"/>')
    a(f'  <circle cx="1180" cy="40" r="380" fill="url(#glowGreen)"/>')
    a(f'  <circle cx="760" cy="620" r="360" fill="url(#glowPurple)"/>')
    # 网格纹理
    a('  <g opacity="0.06" stroke="#e9eefb" stroke-width="1">')
    for x in range(0, W + 1, 64):
        a(f'    <line x1="{x}" y1="0" x2="{x}" y2="{H}"/>')
    for y in range(0, H + 1, 64):
        a(f'    <line x1="0" y1="{y}" x2="{W}" y2="{y}"/>')
    a('  </g>')

    # ---------- 左侧文案 ----------
    a(f'  <rect x="72" y="96" width="330" height="34" rx="17" fill="{C["green"]}" opacity="0.16"/>')
    a(f'  <circle cx="94" cy="113" r="5" fill="{C["green"]}"/>')
    a(f'  <text x="110" y="119" font-size="14.5" font-weight="700" fill="{C["green"]}">'
      f'Agent Skills · MIT · 零第三方依赖</text>')

    a(f'  <text x="72" y="214" font-size="44" font-weight="900" fill="{TEXT}" letter-spacing="-1">'
      f'{esc("chrome-bookmarks-organize")}</text>')
    a(f'  <text x="72" y="272" font-size="30" font-weight="800" fill="{C["blue"]}">'
      f'{esc("AI 整理浏览器书签 · 直改 JSON")}</text>')
    a(f'  <text x="72" y="330" font-size="21" fill="{DIM}">'
      f'{esc("绕开「导出 HTML → 导入」的追加地狱")}</text>')
    a(f'  <text x="72" y="366" font-size="21" fill="{DIM}">'
      f'{esc("一段提示词打底，一份脚本保底 —— 默认用脚本跑")}</text>')

    # ---------- 底部指标 pill ----------
    pills = [("10", "bm.py 子命令", 212), ("54", "项回归护栏", 186), ("0", "第三方依赖", 186)]
    x = 72
    for num, label, w in pills:
        a(f'  <rect x="{x}" y="426" width="{w}" height="60" rx="14" fill="{PANEL}" stroke="{BORDER}"/>')
        a(f'  <text x="{x + 20}" y="462" font-size="26" font-weight="900" fill="{C["blue"]}" '
          f'font-family="{FONT_MONO}">{esc(num)}</text>')
        a(f'  <text x="{x + 20 + len(num) * 16 + 10}" y="461" font-size="15" font-weight="600" '
          f'fill="{DIM}">{esc(label)}</text>')
        x += w + 16

    # ---------- 右侧：整理后书签栏示意 ----------
    px, py, pw, ph = 792, 128, 416, 400
    a(f'  <rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="18" fill="{PANEL}" '
      f'stroke="{BORDER}" stroke-width="1.5"/>')
    # 标题栏
    a(f'  <path d="M{px} {py + 18} a18 18 0 0 1 18 -18 h{pw - 36} a18 18 0 0 1 18 18 v38 h-{pw} z" '
      f'fill="#16223a"/>')
    for i, col in enumerate((C["red"], C["yellow"], C["green"])):
        a(f'  <circle cx="{px + 24 + i * 20}" cy="{py + 19}" r="6" fill="{col}"/>')
    a(f'  <text x="{px + pw / 2}" y="{py + 25}" text-anchor="middle" font-size="13" '
      f'fill="{DIM}" font-family="{FONT_MONO}">chrome://bookmarks</text>')
    # 书签行
    rows = [
        ("购物", C["red"]), ("新闻资讯", C["blue"]), ("技术开发", C["green"]),
        ("学习资源", C["yellow"]), ("视频娱乐", C["purple"]), ("生活工具", C["blue"]),
        ("博客与阅读", C["green"]),
    ]
    ry = py + 82
    for i, (name, col) in enumerate(rows):
        a(f'  <rect x="{px + 24}" y="{ry}" width="{pw - 48}" height="36" rx="9" fill="#16223a"/>')
        a(f'  <rect x="{px + 38}" y="{ry + 12}" width="12" height="12" rx="3" fill="{col}"/>')
        a(f'  <text x="{px + 62}" y="{ry + 24}" font-size="15" font-weight="600" fill="{TEXT}">'
          f'{esc(name)}</text>')
        a(f'  <text x="{px + pw - 40}" y="{ry + 24}" text-anchor="end" font-size="12.5" '
          f'fill="{DIM}" font-family="{FONT_MONO}">{(6 if i < 6 else 2)}</text>')
        ry += 42
    a(f'  <text x="{px + 24}" y="{ry + 8}" font-size="12.5" fill="{C["green"]}">'
      f'38 条 · 同目录重复已合并 · 失效链接已清理</text>')

    # ---------- 底部一行 ----------
    a(f'  <text x="72" y="592" font-size="17" fill="{DIM}">'
      f'{esc("Chrome / Edge 书签栏 · 体检 GO/NO-GO · 自动备份 · 原子写回 · 一键还原")}</text>')
    a(f'  <text x="{W - 72}" y="592" text-anchor="end" font-size="17" font-weight="700" '
      f'fill="{C["blue"]}">{esc("github.com/LPK3215/chrome-bookmarks-organize")}</text>')
    return "\n".join(p)


def render():
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
        f'  <title>chrome-bookmarks-organize · AI 整理浏览器书签</title>\n'
        f'  <defs>\n'
        f'    <radialGradient id="glowBlue" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0" stop-color="{C["blue"]}" stop-opacity="0.42"/>'
        f'<stop offset="1" stop-color="{C["blue"]}" stop-opacity="0"/></radialGradient>\n'
        f'    <radialGradient id="glowGreen" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0" stop-color="{C["green"]}" stop-opacity="0.34"/>'
        f'<stop offset="1" stop-color="{C["green"]}" stop-opacity="0"/></radialGradient>\n'
        f'    <radialGradient id="glowPurple" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0" stop-color="{C["purple"]}" stop-opacity="0.30"/>'
        f'<stop offset="1" stop-color="{C["purple"]}" stop-opacity="0"/></radialGradient>\n'
        f'  </defs>\n'
        + body() + "\n</svg>\n"
    )
    write_outputs("social-preview.svg", svg)


if __name__ == "__main__":
    render()
