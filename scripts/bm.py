#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bm.py — Chrome/Edge 书签 Bookmarks JSON 直改工具箱（本地、离线、零第三方依赖）。

设计原则（对应整理流程）：
  detect   读环境变量自动定位各浏览器 Profile 的 Bookmarks（不写死根路径，跨 OS/换盘）
  preflight 只读体检：文件存在/可读写/JSON合法/浏览器是否在跑 → 给 GO/NO-GO
  backup   改前强制时间戳底牌 + 记录备份信息（可还原）
  show     读取并打印真实结构（目录树 / 数量 / 重复URL / 是否有checksum）——地基，不能读错
  plan     在【内存】里按规则重排(排序/去重)，写到 --out，绝不碰原文件（循环区用）
  preview  把某份书签渲染成本地 HTML（嵌套树），双击即可肉眼核对（循环区用）
  diff     两份书签文件的增/删/净变化对账（控制台）
  finalize 真正落地：删 checksum、改名 .bak、把 --from 写回目标（唯一动真身的步骤）
  verify   JSON 合法性 + url 数量对账（可 --before 比对）
  restore  用 backup 生成的底牌一键还原

约定：所有文件路径都显式传 --file/--target；detect 只负责"探"，探完仍由人确认后再传。
"""
import argparse
import glob
import hashlib
import json
import os
import platform
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

_SCRIPT = os.path.abspath(__file__)  # 用于生成「拿到就能直接粘贴运行」的还原命令

# Windows 控制台默认 GBK，中文/符号易崩，stdout 与 stderr 都切 UTF-8
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

CHROME_EPOCH = datetime(1601, 1, 1)
SHOW_TREE_WARN = 300  # 超过这个条数，show 打印前提醒一句"全树很长"，建议 --depth/--stats


def roots_of(data):
    """取 roots 容器；缺失时给一句人话，而不是让 KeyError 冒到顶层变成"未预期错误"。"""
    if not isinstance(data, dict) or not isinstance(data.get("roots"), dict):
        sys.exit("✗ 这不是一个书签文件：缺少 roots 容器（是不是 --file 指错了文件？）")
    return data["roots"]


def load(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件不存在: {path}")
    with open(path, "r", encoding="utf-8-sig") as f:  # utf-8-sig 容忍 BOM
        return json.load(f)


def chrome_ts_to_date(raw):
    try:
        us = int(raw)
    except (TypeError, ValueError):
        return "?"
    if us <= 0:
        return "-"
    return (CHROME_EPOCH + timedelta(microseconds=us)).strftime("%Y-%m-%d")


def walk(node):
    """深度优先遍历，产出 (depth, node, parent_folder_name)。"""
    def rec(n, depth, parent):
        yield depth, n, parent
        if n.get("type") == "folder":
            for child in n.get("children", []):
                yield from rec(child, depth + 1, n.get("name", ""))
    roots = node["roots"] if "roots" in node else node
    for key, label in (("bookmark_bar", "书签栏"), ("other", "其他书签"), ("synced", "移动设备书签")):
        if key in roots:
            yield from rec(roots[key], 0, None)
            # label 仅用于顶层提示
            _ = label


def iter_urls(node):
    for _d, n, _p in walk(node):
        if n.get("type") == "url":
            yield n


def count_urls(node):
    return sum(1 for _ in iter_urls(node))


def all_ids(node):
    return [n.get("id") for _d, n, _p in walk(node)]


def duplicate_ids(node):
    """全树重复 id。用 Counter 一次扫出（O(n)）；旧写法在列表里反复 count() 是 O(n²)，大书签会卡。"""
    counts = Counter(i for i in all_ids(node) if i is not None)
    return sorted((i for i, c in counts.items() if c > 1), key=str)


def iter_urls_with_parent(node):
    """产出 (url节点, 所属目录路径)。路径敏感后才能识别「移动/改名」，也能判断重复是否跨目录。"""
    out = []

    def rec(n, parts):
        if n.get("type") == "folder":
            for c in n.get("children", []):
                rec(c, parts + [c.get("name", "?")] if c.get("type") == "folder" else parts)
        else:
            out.append((n, "/".join(parts)))

    roots = node["roots"] if "roots" in node else node
    for key, label in (("bookmark_bar", "书签栏"), ("other", "其他书签"), ("synced", "移动设备书签")):
        if key in roots:
            rec(roots[key], [label])
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------- backup ---------------------------
def cmd_backup(args):
    src = args.file
    if not os.path.isfile(src):
        sys.exit(f"[backup] 源文件不存在: {src}")
    out_dir = args.dir or os.path.dirname(os.path.abspath(src))
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")  # 微秒，防同秒碰撞
    base = os.path.basename(src)
    dst = os.path.join(out_dir, f"{base}.backup-{stamp}")
    shutil.copy2(src, dst)
    if sha256(src) != sha256(dst):  # 复制完整性校验
        try:
            os.remove(dst)
        except OSError:
            pass
        sys.exit(f"[backup] ✗ 备份校验失败（sha256 不一致），已丢弃 {dst}，请检查磁盘/权限")

    # 即使源 JSON 坏了也要留下可还原的底牌+记录：解析失败不应吞掉已成功生成的备份
    try:
        data = load(src)
        url_count, has_ck = count_urls(data), "checksum" in data
    except Exception as e:
        url_count, has_ck = -1, None
        print(f"[backup] ⚠ 源文件无法解析（{e}），底牌已生成但无法统计 url 数")

    abs_src, abs_dst = os.path.abspath(src), os.path.abspath(dst)
    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "original": abs_src,
        "backup": abs_dst,
        "sha256_original": sha256(src),
        "url_count": url_count,
        "has_checksum": has_ck,
        # 绝对路径：底牌常生成在浏览器目录里，`python bm.py` 这种相对写法用户照抄必然跑不通
        "restore_cmd": f'"{sys.executable}" "{_SCRIPT}" restore --backup "{abs_dst}" --target "{abs_src}"',
    }
    manifest = os.path.join(out_dir, "_backup_manifest.txt")
    with open(manifest, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("[backup] 已生成底牌，还原命令随时可用：")
    for k, v in record.items():
        print(f"  {k:>16}: {v}")
    print(f"  {'manifest':>16}: {manifest}")


# --------------------------- show ---------------------------
def cmd_show(args):
    data = load(args.file)
    roots = roots_of(data)
    total = count_urls(data)
    print(f"=== {args.file} ===")
    print(f"顶层键: {list(data.keys())}  |  version={data.get('version')}  |  checksum={'有(待删)' if 'checksum' in data else '无(可直接加载)'}")

    if args.stats:
        print("[show] --stats 只看体检，已跳过目录树。")
    elif args.depth is None and total > SHOW_TREE_WARN:
        print(f"[show] ⚠ 本文件有 {total} 条书签，全树打印很长；"
              f"想要概览可加 --depth 2 / --stats。")
    max_depth = args.depth

    if not args.stats:
        def rec(n, depth):
            pad = "  " * depth
            name = n.get("name", "?")
            if n.get("type") == "folder":
                kids = n.get("children", [])
                child_urls = sum(1 for c in kids if c.get("type") == "url")
                print(f"{pad}[目录] {name}  (直属URL {child_urls} 条)")
                if max_depth is not None and depth >= max_depth:
                    if kids:
                        print(f"{pad}  …（更深 {len(kids)} 项已省略，调大 --depth 展开）")
                    return
                for c in kids:
                    rec(c, depth + 1)
            else:
                print(f"{pad}- {name}  <{n.get('url')}>  [{chrome_ts_to_date(n.get('date_added'))}]")

        for key, label in (("bookmark_bar", "书签栏"), ("other", "其他书签"), ("synced", "移动设备书签")):
            if key in roots:
                print(f"\n## {label} ({key})")
                rec(roots[key], 0)

    ids = all_ids(data)
    dup_ids = duplicate_ids(data)
    print("\n--- 体检 ---")
    print(f"url 总数: {total}")
    print(f"id 总数: {len(ids)}  |  重复id: {dup_ids if dup_ids else '无'}")

    # 关键：标出每条重复是「同目录」还是「跨目录」。
    # plan --dedup 只在同目录内合并；跨目录重复是 Chrome 允许的"一条归多处"，不会被删。
    # 不标的话，AI 会拿这张表向用户承诺"这些都给你去重"，结果 plan 一条没删。
    where = defaultdict(list)
    dates = {}
    for n, path in iter_urls_with_parent(data):
        u = n.get("url", "")
        where[u].append(path)
        dates.setdefault(u, []).append(chrome_ts_to_date(n.get("date_added")))
    dups = {u: ps for u, ps in where.items() if len(ps) > 1}
    if dups:
        print(f"重复URL {len(dups)} 组（口径提示：plan --dedup **只在同目录内**合并，跨目录会保留）:")
        for u, ps in sorted(dups.items()):
            same_dir = len(set(ps)) == 1
            verdict = "同目录 → --dedup 会并入 1 条" if same_dir else "跨目录 → plan 不去重（一条归多处）"
            print(f"  - {u}  ×{len(ps)}  [{', '.join(dates[u])}]  {verdict}")
    else:
        print("重复URL: 无")


# --------------------------- detect (只读·自动定位，不写死) ---------------------------
def _default_roots():
    """按当前 OS 与环境变量返回候选 (浏览器标签, User Data 根目录)。绝不写死机器路径。"""
    sysname = platform.system()
    env = os.environ
    home = os.path.expanduser("~")
    out = []
    if sysname == "Windows":
        local = env.get("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
        roam = env.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
        out += [
            ("Chrome", os.path.join(local, "Google", "Chrome", "User Data")),
            ("Edge", os.path.join(local, "Microsoft", "Edge", "User Data")),
            ("Chromium", os.path.join(local, "Chromium", "Chromium", "User Data")),
            ("Brave", os.path.join(local, "BraveSoftware", "Brave-Browser", "User Data")),
            ("Vivaldi", os.path.join(local, "Vivaldi", "User Data")),
            ("Opera", os.path.join(roam, "Opera Software", "Opera Stable")),
        ]
    elif sysname == "Darwin":
        base = os.path.join(home, "Library", "Application Support")
        out += [
            ("Chrome", os.path.join(base, "Google", "Chrome")),
            ("Edge", os.path.join(base, "Microsoft Edge")),
            ("Chromium", os.path.join(base, "Chromium")),
            ("Brave", os.path.join(base, "BraveSoftware", "Brave-Browser")),
            ("Vivaldi", os.path.join(base, "Vivaldi")),
            ("Opera", os.path.join(base, "com.operasoftware.Opera")),
        ]
    else:  # Linux 等
        cfg = env.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
        out += [
            ("Chrome", os.path.join(cfg, "google-chrome")),
            ("Edge", os.path.join(cfg, "microsoft-edge")),
            ("Chromium", os.path.join(cfg, "chromium")),
            ("Brave", os.path.join(cfg, "BraveSoftware", "Brave-Browser")),
            ("Vivaldi", os.path.join(cfg, "Vivaldi")),
            ("Opera", os.path.join(cfg, "opera")),
        ]
    return out


def _browser_processes_running():
    """返回 (在跑的浏览器标签列表, 探测是否成功)。探测失败→([], False)，调用方据此告警。"""
    sysname = platform.system()
    running, ok = [], True
    try:
        import subprocess
        if sysname == "Windows":
            res = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                                 capture_output=True, text=True, timeout=15)
            blob = (res.stdout or "").lower()
            table = {"Chrome": ["chrome.exe"], "Edge": ["msedge.exe"],
                     "Brave": ["brave.exe"], "Chromium": ["chromium.exe"],
                     "Vivaldi": ["vivaldi.exe"], "Opera": ["opera.exe"]}
            for label, exes in table.items():
                if any(e in blob for e in exes):
                    running.append(label)
        else:
            names = {"Chrome": ["Google Chrome", "google-chrome", "chrome"],
                     "Edge": ["Microsoft Edge", "msedge", "microsoft-edge"],
                     "Brave": ["Brave Browser", "brave-browser", "brave"],
                     "Chromium": ["Chromium", "chromium"],
                     "Vivaldi": ["Vivaldi", "vivaldi"],
                     "Opera": ["Opera", "opera"]}
            for label, cands in names.items():
                for c in cands:
                    r = subprocess.run(["pgrep", "-ix", c], capture_output=True, text=True, timeout=10)
                    if r.returncode == 0 and r.stdout.strip():
                        running.append(label)
                        break
    except FileNotFoundError:
        ok = False  # tasklist/pgrep 不可用
    except Exception:
        ok = False
    return running, ok


def _profile_friendly_names(base):
    """尽力从 <base>/Local State 读 profile 显示名，失败返回空字典。"""
    names = {}
    try:
        with open(os.path.join(base, "Local State"), "r", encoding="utf-8") as f:
            state = json.load(f)
        cache = state.get("profile", {}).get("info_cache", {})
        for prof_dir, info in cache.items():
            nm = info.get("name")
            if nm:
                names[prof_dir] = nm
    except Exception:
        pass
    return names


def cmd_detect(args):
    want = args.browser
    rows = []
    seen = set()

    def scan(browser, base):
        if not base or not os.path.isdir(base):
            return
        names = _profile_friendly_names(base)
        for bm in glob.glob(os.path.join(base, "*", "Bookmarks")):
            prof = os.path.basename(os.path.dirname(bm))
            rows.append((browser, prof, names.get(prof, ""), bm))
            seen.add(bm)

    for browser, base in _default_roots():
        if want in ("all", browser.lower()):
            scan(browser, base)
    if args.root:
        for bm in glob.glob(os.path.join(args.root, "**", "Bookmarks"), recursive=True):
            if bm in seen:
                continue
            prof = os.path.basename(os.path.dirname(bm))
            rows.append(("custom", prof, "", bm))
            seen.add(bm)

    if not rows:
        print("[detect] 没在任何标准根目录下找到 Bookmarks 文件。")
        print("[detect] 若你用 --user-data-dir 改过位置：detect --root \"<那个根>\"，或直接给各命令传 --file。")
        return

    def info(bm):
        st = os.stat(bm)
        try:
            d = load(bm)
            return count_urls(d), ("有" if "checksum" in d else "无"), st.st_mtime
        except Exception:
            return None, "-", st.st_mtime

    enriched = []
    for browser, prof, disp, bm in rows:
        cnt, ck, mtime = info(bm)
        enriched.append((mtime, browser, prof, disp, bm, cnt, ck))
    enriched.sort(reverse=True)  # 新的在前

    # 每个浏览器里 mtime 最新者标为"疑似在用"
    active = {}
    for mtime, browser, *_ in enriched:
        active.setdefault(browser, mtime)

    print(f"[detect] 系统={platform.system()}  共找到 {len(enriched)} 个 Bookmarks（按修改时间新→旧）")
    print("-" * 100)
    for mtime, browser, prof, disp, bm, cnt, ck in enriched:
        when = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        tag = "  ◀ 疑似在用" if mtime == active.get(browser) else ""
        cnt_s = f"{cnt}条" if cnt is not None else "读取失败"
        disp_s = f"「{disp}」" if disp else ""
        print(f"{when}  {browser:<6} {prof}{disp_s}  url={cnt_s}  checksum={ck}{tag}")
        print(f"          → {bm}")
    print("-" * 100)
    print("[detect] 确认哪个是你要整理的，再把它当 --file/--target 传给后续命令（detect 只读、不改任何东西）。")


# --------------------------- plan (非破坏 · 循环区) ---------------------------
def _safety_gate(force, action):
    """统一的安全闸：浏览器在跑就拒绝写类操作。返回是否继续。"""
    if force:
        return True
    running, ok = _browser_processes_running()
    if running:
        sys.exit(f"[{action}] ✗ 检测到浏览器进程在跑：{', '.join(running)}。"
                 f"运行时书签缓存在内存里，退出时旧数据会覆盖本次写入。"
                 f"请完全退出浏览器（含托盘后台）后重试；确认已退可加 --force。")
    if not ok:
        print(f"[{action}] ⚠ 无法探测浏览器进程（tasklist/pgrep 不可用），请自行确保已完全退出浏览器。")
    return True


def _prescript_snapshot(target, action, suffix):
    """写类操作前，先把当前真身兜一份——即便用户漏了 backup 也能救。"""
    if not os.path.exists(target):
        return None
    safety = f"{target}.{suffix}-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
    shutil.copy2(target, safety)
    print(f"[{action}] 已自动兜底当前真身 → {safety}")
    return safety


def _sort_children(folder):
    """每层：目录在前、同层按名称排序。"""
    def key(n):
        return (0 if n.get("type") == "folder" else 1, n.get("name", ""))
    folder["children"] = sorted(folder.get("children", []), key=key)


def _dedup_children(folder):
    """仅在同一目录内，按 url 去重，保留 date_added 最新的一条。返回被删节点列表。

    这里记「下标」而不是 kept_children.index(节点)：后者是按 dict **值**比较的，
    若同目录恰有两个内容完全相同的节点，会替换错对象。
    """
    removed = []
    buckets = {}   # url -> (在 kept 中的下标, 节点, 时间戳)
    kept_children = []
    for c in folder.get("children", []):
        if c.get("type") != "url":
            kept_children.append(c)
            continue
        u = c.get("url", "")
        try:
            cur_ts = int(c.get("date_added") or 0)
        except (TypeError, ValueError):
            cur_ts = 0
        if u not in buckets:
            buckets[u] = (len(kept_children), c, cur_ts)
            kept_children.append(c)
        else:
            pos, old_node, old_ts = buckets[u]
            if cur_ts >= old_ts:
                removed.append(old_node)
                kept_children[pos] = c
                buckets[u] = (pos, c, cur_ts)
            else:
                removed.append(c)
    folder["children"] = kept_children
    return removed


def _apply_rules(node, do_sort, do_dedup):
    removed_total = 0
    def rec(folder):
        nonlocal removed_total
        if do_dedup:
            removed_total += len(_dedup_children(folder))
        if do_sort:
            _sort_children(folder)
        for c in folder.get("children", []):
            if c.get("type") == "folder":
                rec(c)
    roots = roots_of(node)
    for key in ("bookmark_bar", "other", "synced"):
        if key in roots and roots[key].get("type") == "folder":
            rec(roots[key])
    return removed_total


def cmd_plan(args):
    """在内存里按规则重排，写到 --out，绝不改动 --file。"""
    data = load(args.file)
    before = count_urls(data)
    removed = _apply_rules(data, do_sort=args.sort, do_dedup=args.dedup)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=3)
    print(f"[plan] 规则: sort={args.sort} dedup={args.dedup}")
    print(f"[plan] url {before} -> {count_urls(data)}  (去重删除 {removed} 条)")
    print(f"[plan] 候选写入 {args.out} —— 原文件 {args.file} 未动。请 preview 肉眼核对后再 finalize。")


# --------------------------- preview (非破坏 · 循环区) ---------------------------
def url_index(node):
    """{(路径, 名称, url): 条数} —— 路径敏感 + 计重数。

    为什么不再只用 (名称,url) 的集合：那样「把链接从 A 目录挪到 B 目录」两端集合完全不变，
    整理完会得到"删 0 / 增 0"，用户以为脚本没干活——而结构整理恰恰几乎全是移动。
    """
    idx = Counter()
    for n, path in iter_urls_with_parent(node):
        idx[(path, n.get("name", ""), n.get("url", ""))] += 1
    return idx


def diff_report(base_node, cand_node):
    """base → cand 对账。返回 dict，值都是 [(基础端key, 对照端key或None), ...]。
    key 形如 (路径, 名称, url)。分类：改名 / 移动 / 真删除 / 真新增 / 副本减少。"""
    ia, ib = url_index(base_node), url_index(cand_node)
    list_a = list((ia - ib).elements())
    list_b = list((ib - ia).elements())
    used_b = [False] * len(list_b)

    def take(match, expect):
        for i, k2 in enumerate(list_b):
            if not used_b[i] and match(k2) == expect:
                used_b[i] = True
                return k2
        return None

    out = {"renamed": [], "moved": [], "removed": [], "added": [], "deduped": []}
    pending = []
    for k in list_a:
        k2 = take(lambda x: (x[0], x[2]), (k[0], k[2]))   # 同目录 + 同链接，名字变了 → 改名
        (out["renamed"].append((k, k2)) if k2 else pending.append(k))
    still = []
    for k in pending:
        k2 = take(lambda x: (x[1], x[2]), (k[1], k[2]))   # 同名 + 同链接，目录变了 → 移动
        (out["moved"].append((k, k2)) if k2 else still.append(k))
    kept_nu = {(x[1], x[2]) for x in ib}
    for k in still:
        # 该 (名称,URL) 在 B 里仍然存在 → 不是真删除，只是某处副本少了一份（如同目录去重）
        (out["deduped"] if (k[1], k[2]) in kept_nu else out["removed"]).append((k, None))
    for i, k2 in enumerate(list_b):
        if not used_b[i]:
            out["added"].append((None, k2))
    return out


def cmd_preview(args):
    """把书签渲染成本地 HTML（真·嵌套树，层级清晰）；带 --base 时附增删差异。"""
    data = load(args.file)
    out = args.out or (args.file + ".preview.html")

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def rc(n):
        return 1 if n.get("type") == "url" else sum(rc(c) for c in n.get("children", []))

    def render(n):
        if n.get("type") == "folder":
            kids = "".join(render(c) for c in n.get("children", []))
            return (f"<li><details open><summary><span class='dir'>📁 {esc(n.get('name'))}"
                    f"<span class='cnt'> ({rc(n)})</span></span></summary><ul>{kids}</ul></details></li>")
        d = chrome_ts_to_date(n.get("date_added"))
        return (f"<li><a class='u' href='{esc(n.get('url'))}'>🔖 {esc(n.get('name'))}</a>"
                f"<span class='d'> [{d}]</span></li>")

    body = []
    for key, label in (("bookmark_bar", "书签栏"), ("other", "其他书签"), ("synced", "移动设备书签")):
        root = roots_of(data).get(key)
        if root:
            body.append(f"<li><details open><summary><span class='root'>🗂 {esc(label)}"
                        f"<span class='cnt'> ({rc(root)})</span></span></summary><ul>{render(root)}</ul></details></li>")
    tree = "<ul class='tree'>" + "".join(body) + "</ul>"

    diff_summary = ""
    if args.base:
        base = load(args.base)
        rep = diff_report(base, data)

        def item(cls, txt):
            return f"<li class='{cls}'>{txt}</li>"

        items = ""
        for k, k2 in rep["renamed"]:
            items += item("ren", f"✏ 改名: <a href='{esc(k[2])}'>{esc(k[1])}</a> → 「{esc(k2[1])}」<span class='d'> [{esc(k[0])}]</span>")
        for k, k2 in rep["moved"]:
            items += item("mov", f"⇄ 移动: <a href='{esc(k[2])}'>{esc(k[1])}</a><span class='d'> {esc(k[0])} → {esc(k2[0])}</span>")
        for k, _ in rep["deduped"]:
            items += item("ded", f"⧉ 副本减少: <a href='{esc(k[2])}'>{esc(k[1])}</a><span class='d'> [{esc(k[0])}]（该链接仍保留）</span>")
        for k, _ in rep["removed"]:
            items += item("rm", f"❌ 删除: <a href='{esc(k[2])}'>{esc(k[1])}</a><span class='d'> [{esc(k[0])}]</span>")
        for _, k2 in rep["added"]:
            items += item("add", f"➕ 新增: <a href='{esc(k2[2])}'>{esc(k2[1])}</a><span class='d'> [{esc(k2[0])}]</span>")
        summary = " / ".join(f"{v} {n}" for n, v in
                             (("删", len(rep["removed"])), ("增", len(rep["added"])),
                              ("移动", len(rep["moved"])), ("改名", len(rep["renamed"])),
                              ("副本减少", len(rep["deduped"]))) if v)
        diff_summary = summary or "无差异"
        diff_html = (f"<div class='diff'><h3>与原版差异（{diff_summary}）</h3>"
                     f"<ul>{items or '<li>无差异</li>'}</ul></div>")

    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>书签结构预览</title>
<style>
body{{font-family:system-ui,"Segoe UI","Microsoft YaHei",sans-serif;padding:22px 28px;color:#222;line-height:1.5}}
h2{{margin:0 0 6px}}
.hint{{color:#888;font-size:12px;margin:0 0 16px}}
ul.tree,ul.tree ul{{list-style:none;margin:0;padding:0}}
ul.tree ul{{margin-left:18px;border-left:1px solid #d7dbe0;padding-left:16px}}
ul.tree li{{margin:1px 0}}
details{{margin:1px 0}}
summary{{cursor:pointer;outline:none;list-style:revert}}
summary:hover .dir,summary:hover .root{{text-decoration:underline}}
.root{{font-weight:700;font-size:16px;color:#17375e}}
.dir{{font-weight:600;color:#2b2b2b}}
.cnt{{color:#9aa0a6;font-weight:normal;font-size:12px}}
a.u{{color:#1a73e8;text-decoration:none}}
a.u:hover{{text-decoration:underline}}
.d{{color:#b3b3b3;font-size:11px}}
.diff{{border:1px solid #ddd;border-radius:8px;padding:10px 20px;margin-top:26px}}
.diff li{{margin:4px 0}}
.diff .rm{{color:#c5221f}}
.diff .add{{color:#188038}}
.diff .mov,.diff .ren{{color:#a5601a}}
.diff .ded{{color:#70757a}}
</style></head><body>
<h2>🗂 书签结构预览 <small style="color:#888;font-weight:normal">（{count_urls(data)} 条 url）</small></h2>
<p class="hint">点目录前的三角可折叠 / 展开（默认全展开）</p>
{tree}
{diff_html}
</body></html>"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[preview] 已生成本地嵌套树预览 {out}")
    if args.base:
        print(f"[preview] 与原版差异：{diff_summary}")
    else:
        print("[preview] 未比对差异（可加 --base 原文件）")


# --------------------------- finalize (唯一动真身) ---------------------------
def cmd_finalize(args):
    """把候选 --from 安装到 --target：删 checksum + 处理陈旧 .bak，然后原子写回。"""
    _safety_gate(args.force, "finalize")  # 安全闸①：浏览器在跑就拒绝

    data = load(args.file_from)
    if not isinstance(data, dict) or not isinstance(data.get("roots"), dict) \
            or not any(k in data["roots"] for k in ("bookmark_bar", "other", "synced")):
        sys.exit("[finalize] ✗ 候选文件结构非法（缺 roots / bookmark_bar|other|synced），拒绝写回目标。"
                 "请检查 --from 是否指向正常的书签 JSON。")

    had_ckpt = "checksum" in data
    data.pop("checksum", None)  # 删字段 → Chrome 自动重建校验

    _prescript_snapshot(args.target, "finalize", "prescript")  # 安全闸②：自动兜底当前真身

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    bak = args.target + ".bak"
    if os.path.exists(bak):
        moved = f"{bak}.stale-{stamp}"
        os.replace(bak, moved)
        print(f"[finalize] 陈旧 {bak} → 改名 {moved}（防止 Chrome 加载时回滚）")

    # 原子写回：先落 .tmp 再 os.replace，避免"写到一半失败 → 真身变成半个 JSON"
    tmp = f"{args.target}.tmp-{stamp}"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=3)
        os.replace(tmp, args.target)
    except (PermissionError, OSError) as e:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        sys.exit(f"[finalize] ✗ 写回失败：{e}\n"
                 f"        常见原因：浏览器没退干净占用文件 / 文件被设为只读 / 需要更高权限。"
                 f"（真身未被破坏，自动兜底件已生成）")
    print(f"[finalize] 已写回 {args.target}（url {count_urls(data)} 条）| checksum {'已删除' if had_ckpt else '本就无'}")


# --------------------------- verify ---------------------------
def _structural_issues(node):
    issues = []
    def rec(n):
        if n.get("type") == "folder":
            if not isinstance(n.get("children"), list):
                issues.append(f"目录缺 children 数组: {n.get('name')}")
            for c in n.get("children", []):
                rec(c)
        elif n.get("type") == "url":
            if not n.get("url"):
                issues.append(f"url 节点 url 为空: id={n.get('id')} name={n.get('name')}")
    roots = roots_of(node)
    for key in ("bookmark_bar", "other", "synced"):
        if key in roots:
            rec(roots[key])
    return issues


def cmd_verify(args):
    try:
        data = load(args.file)
    except Exception as e:
        print(f"[verify] ✗ JSON 解析失败: {e}")
        sys.exit(1)
    ids = all_ids(data)
    dup_ids = duplicate_ids(data)
    issues = _structural_issues(data)
    print(f"[verify] ✓ JSON 合法")
    print(f"[verify] checksum: {'仍存在(应删!)' if 'checksum' in data else '已无(Chrome 会重建)'}")
    print(f"[verify] url 总数: {count_urls(data)}  | 重复id: {sorted(dup_ids) if dup_ids else '无'}")
    print(f"[verify] 结构问题: {issues if issues else '无'}")
    if args.before:
        b = count_urls(load(args.before))
        a = count_urls(data)
        print(f"[verify] 对账 {args.before}: {b} -> {a}（差额 {b - a}）")


# --------------------------- restore ---------------------------
def cmd_restore(args):
    """拿底牌盖回目标。语义是「回退到底牌那一刻」，不是「只撤销最后一步」——
    开了浏览器同步时，底牌拍摄之后由其他设备同步来的书签会被一并退回（已在 SKILL Pitfalls 写明）。"""
    if not os.path.isfile(args.backup):
        sys.exit(f"[restore] 底牌不存在: {args.backup}")
    _safety_gate(args.force, "restore")  # 与 finalize 同等级：浏览器在跑就拒绝
    _prescript_snapshot(args.target, "restore", "prerestore")  # 还原前也兜一份当前状态

    shutil.copy2(args.backup, args.target)
    data = load(args.target)  # 解析校验，坏文件立刻暴露
    took = datetime.fromtimestamp(os.path.getmtime(args.backup)).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[restore] 已回退 {args.target} 到底牌拍摄时刻 {took}"
          f"（url {count_urls(data)} 条），文件可正常解析")
    print("[restore] 注意：若开了浏览器同步，底牌之后由其他设备同步来的书签也会被一并退回。")


# --------------------------- preflight (只读·GO/NO-GO) ---------------------------
def cmd_preflight(args):
    f = args.file
    problems = []
    print(f"[preflight] 体检目标: {f}")
    print("-" * 60)

    if not os.path.exists(f):
        print(f"  ✗ 文件不存在")
        print("  结论：NO-GO —— 先 detect 定位正确路径")
        sys.exit(2)
    print("  ✓ 文件存在")

    try:
        data = load(f)
        print(f"  ✓ JSON 合法，url {count_urls(data)} 条，checksum {'有(待删)' if 'checksum' in data else '无'}")
    except Exception as e:
        problems.append("JSON 无法解析")
        print(f"  ✗ JSON 解析失败: {e}")

    try:
        with open(f, "r", encoding="utf-8-sig"):
            pass
        print("  ✓ 可读")
    except Exception as e:
        problems.append("不可读")
        print(f"  ✗ 不可读: {e}")

    print(f"  {'✓' if os.access(f, os.W_OK) else '✗'} 可写: {os.access(f, os.W_OK)}")
    if not os.access(f, os.W_OK):
        problems.append("目标不可写(只读/权限)")

    print(f"  · 同目录 Bookmarks.bak: {'存在(finalize 会改名防回滚)' if os.path.exists(f + '.bak') else '无'}")

    running, ok = _browser_processes_running()
    if running:
        problems.append("浏览器在跑")
        print(f"  ✗ 浏览器进程在跑: {', '.join(running)} —— finalize 会被拒绝(除非 --force)")
    elif not ok:
        print("  ⚠ 无法探测浏览器进程，请自行确保已完全退出")
    else:
        print("  ✓ 未检测到浏览器进程")

    print("-" * 60)
    if problems:
        print(f"[preflight] 结论：NO-GO —— {', '.join(problems)}")
        sys.exit(2)
    print("[preflight] 结论：GO ✅ 可安全执行 backup/finalize")


# --------------------------- diff (两份书签对账) ---------------------------
def cmd_diff(args):
    a, b = load(args.a), load(args.b)
    ca, cb = count_urls(a), count_urls(b)
    rep = diff_report(a, b)
    print(f"[diff] {args.a} ({ca}条)  →  {args.b} ({cb}条)   净变化 {cb - ca}")
    print(f"[diff] 删 {len(rep['removed'])} / 增 {len(rep['added'])} / "
          f"移动 {len(rep['moved'])} / 改名 {len(rep['renamed'])} / 副本减少 {len(rep['deduped'])}")
    for k, k2 in rep["renamed"]:
        print(f"  ✏ 改名: {k[1]} → 「{k2[1]}」  <{k[2]}>   [{k[0]}]")
    for k, k2 in rep["moved"]:
        print(f"  ⇄ 移动: {k[1]}  {k[0]} → {k2[0]}")
    for k, _ in rep["deduped"]:
        print(f"  ⧉ 副本减少: {k[1]}  <{k[2]}>   [{k[0]}]（该链接仍存在于别处）")
    for k, _ in rep["removed"]:
        print(f"  ❌ 删除: {k[1]}  <{k[2]}>   [{k[0]}]")
    for _, k2 in rep["added"]:
        print(f"  ➕ 新增: {k2[1]}  <{k2[2]}>   [{k2[0]}]")


# --------------------------- main ---------------------------
def build_parser():
    p = argparse.ArgumentParser(description="Chrome/Edge 书签 Bookmarks JSON 直改工具箱")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("backup", help="改前时间戳备份 + 记录还原信息")
    b.add_argument("--file", required=True)
    b.add_argument("--dir", help="备份存放目录，默认与源同目录")
    b.set_defaults(func=cmd_backup)

    s = sub.add_parser("show", help="读取并打印真实结构（地基确认）")
    s.add_argument("--file", required=True)
    s.add_argument("--depth", type=int, help="只打印到第 N 层（大书签用它做概览）")
    s.add_argument("--stats", action="store_true", help="只打印体检结果，不打印目录树")
    s.set_defaults(func=cmd_show)

    dt = sub.add_parser("detect", help="按 OS 环境变量自动定位 Bookmarks（只读，不写死路径）")
    dt.add_argument("--browser", choices=["chrome", "edge", "brave", "chromium", "vivaldi", "opera", "all"], default="all")
    dt.add_argument("--root", help="额外搜索的根目录（如自定义 --user-data-dir）")
    dt.set_defaults(func=cmd_detect)

    pl = sub.add_parser("plan", help="内存重排到 --out，绝不改原文件（循环区）")
    pl.add_argument("--file", required=True)
    pl.add_argument("--out", required=True)
    pl.add_argument("--sort", action="store_true", help="每层子节点目录优先、按名排序")
    pl.add_argument("--dedup", action="store_true", help="同目录内按 url 去重，保留最新")
    pl.set_defaults(func=cmd_plan)

    pv = sub.add_parser("preview", help="渲染成本地 HTML 肉眼核对（循环区）")
    pv.add_argument("--file", required=True)
    pv.add_argument("--out", help="输出的 .html，默认 <file>.preview.html")
    pv.add_argument("--base", help="原文件，用于高亮增删差异")
    pv.set_defaults(func=cmd_preview)

    fz = sub.add_parser("finalize", help="唯一动真身：删checksum+处理.bak，把候选写回目标")
    fz.add_argument("--from", dest="file_from", required=True, help="循环区确认好的候选文件")
    fz.add_argument("--target", required=True, help="正式 Bookmarks 路径")
    fz.add_argument("--force", action="store_true", help="浏览器在跑时也强行写回（危险，通常应先退出浏览器）")
    fz.set_defaults(func=cmd_finalize)

    vf = sub.add_parser("verify", help="校验 JSON 合法 + 结构 + 数量对账")
    vf.add_argument("--file", required=True)
    vf.add_argument("--before", help="改动前文件，用于数量对账")
    vf.set_defaults(func=cmd_verify)

    rs = sub.add_parser("restore", help="用底牌回退到底牌那一刻（浏览器在跑会拒绝）")
    rs.add_argument("--backup", required=True)
    rs.add_argument("--target", required=True)
    rs.add_argument("--force", action="store_true", help="浏览器在跑时也强行还原（危险）")
    rs.set_defaults(func=cmd_restore)

    pf = sub.add_parser("preflight", help="只读体检：存在/读写/JSON/浏览器进程 → GO/NO-GO")
    pf.add_argument("--file", required=True)
    pf.set_defaults(func=cmd_preflight)

    df = sub.add_parser("diff", help="两份书签增删对账（控制台）")
    df.add_argument("--a", required=True, help="改动前文件")
    df.add_argument("--b", required=True, help="改动后文件")
    df.set_defaults(func=cmd_diff)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except FileNotFoundError as e:
        sys.exit(f"✗ {e}")
    except json.JSONDecodeError as e:
        sys.exit(f"✗ JSON 解析失败（文件可能已损坏或正被浏览器写入）：{e}")
    except SystemExit:
        raise
    except Exception as e:
        sys.exit(f"✗ 未预期错误：{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
