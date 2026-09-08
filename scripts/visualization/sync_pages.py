#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_pages.py — 把 project_overview/（全景观览站源目录）同步到 docs/（GitHub Pages 经典模式部署源）

用途：
    Pages 经典模式只认仓库根 `/` 或 `/docs`，本项目用 `main/docs`；
    而全景观览页的源目录是 project_overview/。改完源目录后跑本脚本，
    即可把站点文件复制成 docs/ 下的部署副本，避免手工 cp 漏文件。

依赖：
    仅 Python 标准库，无第三方依赖（与 scripts/bm.py 同一约定）。

运行方式：
    python scripts/visualization/sync_pages.py

输出路径：
    docs/index.html、docs/style.css、docs/script.js、docs/charts.js
    docs/assets/*（示意图副本）
    docs/.nojekyll（不存在时自动创建，禁用 Jekyll 处理下划线文件）

维护说明：
    - 只复制 SYNC_FILES 里列出的文件与 assets/ 目录；不会自动删除 docs/ 里的其它文件，
      发现"源目录已没有但 docs/ 还在"的旧文件时会打印提示，由人决定删不删。
    - docs/*.svg（README 引用的白底示意图）由 generate_workflow.py / generate_deliverables.py
      生成，不归本脚本管。
"""
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "project_overview"
DST = ROOT / "docs"

SYNC_FILES = ["index.html", "style.css", "script.js", "charts.js"]

# 本地预览面板（可视化编辑）会在 HTML 上注入 data-page-node-id 标记，
# 部署副本不需要它：复制 HTML 时统一剔除，保证 docs/ 始终是干净产物。
_JUNK_ATTR = re.compile(r'\s+data-page-node-id="[^"]*"')


def copy_html(src, dst):
    text = src.read_text(encoding="utf-8")
    cleaned = _JUNK_ATTR.sub("", text)
    dst.write_text(cleaned, encoding="utf-8", newline="\n")
    return len(text) - len(cleaned)


def main() -> int:
    if not SRC.is_dir():
        print(f"✗ 源目录不存在：{SRC}")
        return 1
    DST.mkdir(parents=True, exist_ok=True)

    copied = []
    stripped = 0
    for name in SYNC_FILES:
        s = SRC / name
        if not s.is_file():
            print(f"! 跳过（源目录没有）：{name}")
            continue
        if name.endswith(".html"):
            stripped += copy_html(s, DST / name)
        else:
            shutil.copy2(s, DST / name)
        copied.append(name)

    src_assets = SRC / "assets"
    if src_assets.is_dir():
        dst_assets = DST / "assets"
        dst_assets.mkdir(parents=True, exist_ok=True)
        for f in sorted(src_assets.glob("*")):
            if f.is_file():
                shutil.copy2(f, dst_assets / f.name)
                copied.append(f"assets/{f.name}")

    nojekyll = DST / ".nojekyll"
    if not nojekyll.exists():
        nojekyll.write_text("", encoding="utf-8")
        copied.append(".nojekyll")

    # 提示 docs/ 里"源目录已没有"的旧站点文件
    stale = []
    for f in sorted(DST.glob("*")):
        if f.name in {".nojekyll", "assets"} or f.suffix == ".svg":
            continue
        if f.is_file() and (not (SRC / f.name).exists()):
            stale.append(f.name)

    print(f"✓ 已同步 {len(copied)} 个文件到 {DST.relative_to(ROOT)}/")
    for c in copied:
        print(f"    · {c}")
    if stripped:
        print(f"  （剔除预览面板注入的 data-page-node-id 标记 {stripped} 字符）")
    if stale:
        print("! docs/ 中存在源目录已移除的旧文件（本脚本不自动删，请人工确认）：")
        for s in stale:
            print(f"    · {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
