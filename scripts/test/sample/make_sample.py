#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 scripts/test/sample/ 下的**合成**书签样例（Bookmarks.before / .after）。

为什么需要它
------------
scripts/test/ 里那份对比案例是**真实书签快照**，含隐私、被 .gitignore 屏蔽、不入库。
于是别人 clone 之后仓库里一份能跑的数据都没有 —— 照 README 第一步就会撞空。
本样例全部虚构，零隐私，可以安全入库。

刻意埋了什么（用来验证工具箱的各条能力）
---------------------------------------
- 三层嵌套目录                    → 验证 preview 嵌套树 / show --depth
- 同一目录内的重复链接（新旧两条）  → 验证 plan --dedup 会合并成 1 条
- 跨目录的重复链接                → 验证 plan 不去重（Chrome 允许一条归多处）
- 一对重复 id                     → 验证 verify 能报出「重复id」
- before 带 checksum、after 不带   → 验证 finalize 的删 checksum 分支
- after 相对 before 有 改名/移动/增2/删2 → 验证 diff 的路径感知对账

用法
----
    python scripts/test/sample/make_sample.py
"""
import copy
import json
import os
from datetime import datetime
from itertools import count

EPOCH = datetime(1601, 1, 1)
_ids = count(1)


def ts(y, m, d):
    """Chrome 时间戳：自 1601-01-01 起的微秒。"""
    return str(int((datetime(y, m, d) - EPOCH).total_seconds() * 1_000_000))


def url(name, link, y, m, d, node_id=None):
    return {
        "date_added": ts(y, m, d),
        "guid": "sample-guid-%d" % (abs(hash((name, link))) % 9973),
        "id": str(node_id if node_id is not None else next(_ids)),
        "name": name,
        "type": "url",
        "url": link,
    }


def folder(name, children, y=2024, m=1, d=1):
    return {
        "children": children,
        "date_added": ts(y, m, d),
        "date_last_used": "0",
        "guid": "sample-folder-%d" % (abs(hash(name)) % 9973),
        "id": str(next(_ids)),
        "name": name,
        "type": "folder",
    }


def build_before():
    bar = folder("书签栏", [
        folder("开发", [
            url("MDN Web 文档", "https://developer.mozilla.org/", 2024, 3, 1),
            url("MDN Web 文档", "https://developer.mozilla.org/", 2023, 8, 12),  # 同目录重复 → 会被 --dedup 合并
            folder("前端", [
                url("CSS Tricks", "https://css-tricks.com/", 2024, 5, 2),
                url("Can I use", "https://caniuse.com/", 2024, 5, 3),
            ], 2024, 5, 1),
            folder("后端", [
                url("Python 官方文档", "https://docs.python.org/", 2024, 4, 10),
                url("Go by Example", "https://gobyexample.com/", 2024, 4, 11),
            ], 2024, 4, 1),
        ], 2024, 1, 2),
        folder("AI", [
            url("示例论文站", "https://example-papers.test/", 2025, 2, 1),
            url("示例模型卡", "https://example-models.test/", 2025, 2, 2),
        ], 2025, 1, 5),
        folder("常读", [
            url("示例新闻站", "https://example-news.test/", 2025, 6, 1),
            url("示例论坛", "https://example-forum.test/", 2025, 6, 2),
            # 跨目录重复：「工具箱」里还有同一条 → plan 不去重
            url("示例工具站", "https://example-tools.test/", 2025, 6, 3),
        ], 2025, 5, 1),
        folder("工具箱", [
            url("示例工具站", "https://example-tools.test/", 2025, 7, 1),  # 跨目录重复的另一份
            url("待删除-A", "https://example-drop-a.test/", 2025, 3, 1),   # after 里删
            url("待删除-B", "https://example-drop-b.test/", 2025, 3, 2),   # after 里删
            url("待移动", "https://example-move.test/", 2025, 3, 3),       # after 里挪到「AI」
        ], 2025, 3, 1),
    ], 2024, 1, 1)

    other = folder("其他书签", [
        url("示例归档文章", "https://example-archive.test/", 2024, 11, 1),
        folder("旧杂物", [
            url("示例旧链接", "https://example-old.test/", 2023, 12, 1),
        ], 2023, 12, 1),
    ], 2024, 10, 1)

    synced = folder("移动设备书签", [
        url("手机上存的示例页", "https://example-mobile.test/", 2025, 1, 1),
    ], 2025, 1, 1)

    return {
        "checksum": "0000000000000000000000000000000000000000",
        "roots": {"bookmark_bar": bar, "other": other, "synced": synced},
        "sync_metadata": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
        "version": 1,
    }


def walk_nodes(node):
    stack = [node]
    while stack:
        n = stack.pop()
        yield n
        stack.extend(n.get("children", []))


def build_after(before):
    """在 before 基础上做出可见改动：改名 + 移动 + 增 2 + 删 2，并去掉 checksum。"""
    a = copy.deepcopy(before)
    a.pop("checksum", None)
    bar = a["roots"]["bookmark_bar"]
    by_name = {c.get("name"): c for c in bar["children"] if c.get("type") == "folder"}
    toolbox, ai = by_name["工具箱"], by_name["AI"]

    # ① 目录改名
    toolbox["name"] = "工具箱-已重命名"

    # ② 移动一条链接：工具箱 → AI
    for c in list(toolbox["children"]):
        if c.get("name") == "待移动":
            toolbox["children"].remove(c)
            ai["children"].append(c)

    # ③ 删两条
    toolbox["children"] = [c for c in toolbox["children"]
                           if c.get("name") not in ("待删除-A", "待删除-B")]

    # ④ 新增一个目录（含 2 条）
    next_id = max(int(n.get("id", "0") or 0) for n in walk_nodes(a)) + 1
    bar["children"].append(folder(
        "新增-归档",
        [url("新增示例A", "https://example-added-a.test/", 2026, 1, 1, next_id),
         url("新增示例B", "https://example-added-b.test/", 2026, 1, 2, next_id + 1)],
        2026, 1, 1))

    # ⑤ 埋一对重复 id，用来验证 verify 的重复 id 检测
    flat = [n for n in walk_nodes(a) if n.get("type") == "url"]
    if len(flat) >= 2:
        flat[-1]["id"] = flat[0]["id"]
    return a


def count_urls(data):
    return sum(1 for root in data["roots"].values()
               for n in walk_nodes(root) if n.get("type") == "url")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    before = build_before()
    after = build_after(before)
    for name, data in (("Bookmarks.before", before), ("Bookmarks.after", after)):
        path = os.path.join(here, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=3)
        print("written: " + path)
    print("url 数: before=%d  after=%d" % (count_urls(before), count_urls(after)))


if __name__ == "__main__":
    main()
