#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 scripts/test/sample/ 下的演示书签样例（Bookmarks.before / .after）。

这套数据长什么样
----------------
用**真实存在的通用网站**（淘宝/京东/GitHub/澎湃新闻……）模拟一个「多年随手收藏、
从未分类」的书签栏：`Bookmarks.before` 是一团乱（链接平铺、目录叫"新建文件夹"、
同一条链接收藏了两遍、还躺着一条失效旧链接）；`Bookmarks.after` 是 AI 整理后
的样子——全部归入「购物 / 新闻资讯 / 技术开发 / 学习资源 / 视频娱乐 / 生活工具」等
目录，重复链接合并、失效链接删掉。

为什么用真实站点而不是 example.test
------------------------------------
1. 一眼能看懂整理效果：目录名「购物」里放着「淘宝网」「京东」，预览/对拍时无需脑补；
2. 仍然零隐私：**没有一条是你的收藏**，全是公开的通用站点，clone 即用、放心入库。

刻意埋的点（验证工具箱能力，与 run_tests.py 的分工：这里看"长什么样"，
单测管"细节对不对"）
---------------------
- before 顶部平铺 + 多个"新建文件夹"          → 模拟真实乱象，preview 前后对比明显
- before 同一条「大众点评」在同一目录出现两次 → plan --dedup 会合并成 1 条
- before 躺着一条失效旧链接                    → after 里被删掉，diff 报「删除」
- before 带 checksum、after 不带               → finalize / verify 的 checksum 分支
- after 全部重新归类进目录                      → diff / preview --base 报大量「移动」

用法
----
    python scripts/test/sample/make_sample.py
"""
import json
import os
from datetime import datetime

EPOCH = datetime(1601, 1, 1)


def ts(y, m, d):
    """Chrome 时间戳：自 1601-01-01 起的微秒。"""
    return str(int((datetime(y, m, d) - EPOCH).total_seconds() * 1_000_000))


# ------------------------- 通用站点目录（唯一事实来源） -------------------------
# 每个站点：(名称, url, 收藏日期 y-m-d)
SITES = {
    "购物": [
        ("淘宝网", "https://www.taobao.com/", 2023, 5, 3),
        ("京东", "https://www.jd.com/", 2023, 5, 3),
        ("拼多多", "https://www.pinduoduo.com/", 2024, 1, 12),
        ("天猫", "https://www.tmall.com/", 2023, 9, 21),
        ("苏宁易购", "https://www.suning.com/", 2023, 6, 8),
        ("亚马逊中国", "https://www.amazon.cn/", 2024, 3, 15),
    ],
    "新闻资讯": [
        ("新浪新闻", "https://news.sina.com.cn/", 2022, 11, 2),
        ("网易新闻", "https://news.163.com/", 2022, 12, 30),
        ("澎湃新闻", "https://www.thepaper.cn/", 2023, 2, 17),
        ("新华社", "https://www.news.cn/", 2023, 4, 9),
        ("BBC 中文", "https://www.bbc.com/zhongwen/simp", 2023, 8, 24),
        ("纽约时报中文网", "https://cn.nytimes.com/", 2024, 6, 1),
    ],
    "技术开发": [
        ("GitHub", "https://github.com/", 2022, 9, 14),
        ("Stack Overflow", "https://stackoverflow.com/", 2023, 1, 5),
        ("MDN Web 文档", "https://developer.mozilla.org/zh-CN/", 2023, 3, 20),
        ("掘金", "https://juejin.cn/", 2024, 2, 28),
        ("阮一峰的网络日志", "https://www.ruanyifeng.com/blog/", 2023, 7, 11),
        ("LeetCode", "https://leetcode.cn/", 2024, 4, 18),
    ],
    "学习资源": [
        ("中国大学MOOC", "https://www.icourse163.org/", 2023, 2, 10),
        ("Coursera", "https://www.coursera.org/", 2023, 6, 25),
        ("学堂在线", "https://www.xuetangx.com/", 2023, 9, 3),
        ("知乎", "https://www.zhihu.com/", 2022, 10, 19),
        ("维基百科", "https://zh.wikipedia.org/", 2023, 5, 30),
        ("可汗学院", "https://zh.khanacademy.org/", 2024, 1, 7),
    ],
    "视频娱乐": [
        ("bilibili", "https://www.bilibili.com/", 2022, 8, 22),
        ("YouTube", "https://www.youtube.com/", 2022, 11, 11),
        ("爱奇艺", "https://www.iqiyi.com/", 2023, 3, 8),
        ("腾讯视频", "https://v.qq.com/", 2023, 4, 27),
        ("芒果TV", "https://www.mgtv.com/", 2023, 12, 2),
        ("网易云音乐", "https://music.163.com/", 2022, 9, 1),
    ],
    "生活工具": [
        ("铁路12306", "https://www.12306.cn/", 2023, 1, 1),
        ("高德地图", "https://www.amap.com/", 2023, 5, 6),
        ("大众点评", "https://www.dianping.com/", 2023, 10, 12),
        ("中国天气网", "https://www.weather.com.cn/", 2024, 2, 14),
        ("百度翻译", "https://fanyi.baidu.com/", 2023, 8, 2),
        ("顺丰速运", "https://www.sf-express.com/", 2024, 5, 20),
    ],
    "博客与阅读": [
        ("少数派", "https://sspai.com/", 2023, 7, 19),
        ("即刻", "https://web.okjike.com/", 2023, 11, 8),
    ],
}

# before 里额外埋的失效旧链接（after 中删除，验证 diff 的「删除」分类）
DEAD_LINK = ("失效-个人主页(已打不开)", "https://dead.example.net/old", 2021, 4, 3)


def flatten():
    """按目录顺序摊平为 [(category, name, url, y, m, d), ...]，保证目录排序稳定。"""
    out = []
    for cat, items in SITES.items():
        for name, url, y, m, d in items:
            out.append((cat, name, url, y, m, d))
    return out


# ------------------------- 节点构造（id/guid 全确定性） -------------------------
_NODE = [0]          # 每造一个节点自增，id/guid 都从它派生，保证全树唯一且可复现
_ROOT = [("bookmark_bar", "书签栏"), ("other", "其他书签"), ("synced", "移动设备书签")]


def _url(name, url, y, m, d):
    _NODE[0] += 1
    return {
        "date_added": ts(y, m, d),
        "guid": "demo-%04d" % _NODE[0],
        "id": str(_NODE[0]),
        "name": name,
        "type": "url",
        "url": url,
    }


def _folder(name, children, y=2024, m=1, d=1):
    _NODE[0] += 1
    return {
        "children": children,
        "date_added": ts(y, m, d),
        "date_last_used": "0",
        "guid": "demo-%04d" % _NODE[0],
        "id": str(_NODE[0]),
        "name": name,
        "type": "folder",
    }


def build_doc(bar_kids, other_kids=None, synced_kids=None, checksum=None):
    """按 Chrome 的固定骨架拼出整份 Bookmarks 文档。
    roots 的三个根节点也走 _folder 计数，保证 id 不与子树冲突。"""
    roots = {}
    for key, label in _ROOT:
        kids = {"bookmark_bar": bar_kids, "other": other_kids or [],
                "synced": synced_kids or []}[key]
        roots[key] = _folder(label, kids)
    doc = {"roots": roots, "version": 1}
    if checksum is not None:
        doc["checksum"] = checksum
    return doc


def build_after():
    """AI 整理后：按 SITES 的目录逐类归档，重复/失效已清，去掉 checksum。"""
    children = [_folder(cat, [_url(name, url, y, m, d) for name, url, y, m, d in items])
                for cat, items in SITES.items()]
    return build_doc(children)


def build_before():
    """AI 整理前：目录平铺/新建文件夹乱放 + 同目录重复 + 失效旧链接，带 checksum。"""
    flat = flatten()
    # 摊成四个去处，模拟"随手丢"：一部分平铺在书签栏，其余丢进三个"新建文件夹"
    buckets = [[] for _ in range(4)]
    where = {}
    for i, (cat, name, url, y, m, d) in enumerate(flat):
        b = i % 4
        buckets[b].append(_url(name, url, y, m, d))
        where[name] = b

    # 埋点①：同一条「大众点评」在同一目录里被收藏了两次（duplicate 日期更旧，
    # 验证 plan --dedup 保留 date_added 最新的那条；注意必须与原件同目录，
    # 否则变成跨目录重复、plan 反而不会去重）
    buckets[where["大众点评"]].append(_url("大众点评", "https://www.dianping.com/", 2022, 6, 6))
    # 埋点②：失效旧链接（after 里没有，验证 diff 的「删除」分类）
    buckets[1].append(_url(*DEAD_LINK))

    bar_kids = buckets[0] + [
        _folder("新建文件夹", buckets[1], 2023, 1, 15),
        _folder("新建文件夹 (1)", buckets[2], 2023, 2, 20),
        _folder("新建文件夹 (2)", buckets[3], 2023, 3, 25),
    ]
    return build_doc(bar_kids, checksum="0" * 40)


def walk(node):
    yield node
    for c in node.get("children", []):
        yield from walk(c)


def count_urls(data):
    return sum(1 for root in data["roots"].values() for n in walk(root) if n.get("type") == "url")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    data = {"Bookmarks.before": build_before(), "Bookmarks.after": build_after()}
    for name, bookmarks in data.items():
        path = os.path.join(here, name)
        # newline="\n"：强制 LF，避免 Windows 默认写 CRLF 导致跨平台产物不一致
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(bookmarks, f, ensure_ascii=False, indent=3)
        print("written: " + path)
    b = data["Bookmarks.before"]
    a = data["Bookmarks.after"]
    print("url 数: before=%d（含 1 条同目录重复 + 1 条失效旧链）  after=%d"
          % (count_urls(b), count_urls(a)))
    print("after 分类目录：%s" % "、".join(SITES.keys()))


if __name__ == "__main__":
    main()
