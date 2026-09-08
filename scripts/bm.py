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
from datetime import datetime, timedelta

# Windows 控制台默认 GBK，中文/符号易崩，stdout 与 stderr 都切 UTF-8
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

CHROME_EPOCH = datetime(1601, 1, 1)


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


def find_duplicate_urls(node):
    seen = {}
    for n in iter_urls(node):
        seen.setdefault(n.get("url", ""), []).append(n)
    return {u: ns for u, ns in seen.items() if len(ns) > 1}


def all_ids(node):
    return [n.get("id") for _d, n, _p in walk(node)]


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

    data = load(src)
    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "original": os.path.abspath(src),
        "backup": os.path.abspath(dst),
        "sha256_original": sha256(src),
        "url_count": count_urls(data),
        "has_checksum": "checksum" in data,
        "restore_cmd": f'python bm.py restore --backup "{os.path.abspath(dst)}" --target "{os.path.abspath(src)}"',
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
    print(f"=== {args.file} ===")
    print(f"顶层键: {list(data.keys())}  |  version={data.get('version')}  |  checksum={'有(待删)' if 'checksum' in data else '无(可直接加载)'}")

    def rec(n, depth):
        pad = "  " * depth
        name = n.get("name", "?")
        if n.get("type") == "folder":
            child_urls = sum(1 for c in n.get("children", []) if c.get("type") == "url")
            print(f"{pad}[目录] {name}  (直属URL {child_urls} 条)")
            for c in n.get("children", []):
                rec(c, depth + 1)
        else:
            print(f"{pad}- {name}  <{n.get('url')}>  [{chrome_ts_to_date(n.get('date_added'))}]")

    for key, label in (("bookmark_bar", "书签栏"), ("other", "其他书签"), ("synced", "移动设备书签")):
        if key in data["roots"]:
            print(f"\n## {label} ({key})")
            rec(data["roots"][key], 0)

    ids = all_ids(data)
    dup_ids = {i for i in ids if ids.count(i) > 1 and i is not None}
    print("\n--- 体检 ---")
    print(f"url 总数: {count_urls(data)}")
    print(f"id 总数: {len(ids)}  |  重复id: {sorted(dup_ids) if dup_ids else '无'}")
    dups = find_duplicate_urls(data)
    if dups:
        print("重复URL（去重候选，保留 date_added 最新）:")
        for u, ns in dups.items():
            dates = [chrome_ts_to_date(n.get('date_added')) for n in ns]
            print(f"  - {u}  ×{len(ns)}  [{', '.join(dates)}]")
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
def _sort_children(folder):
    def key(n):
        return (0 if n.get("type") == "folder" else 1, n.get("name", ""))
    folder["children"] = sorted(folder.get("children", []), key=key)


def _dedup_children(folder):
    """仅在同一目录内，按 url 去重，保留 date_added 最新的一条。返回被删节点列表。"""
    removed = []
    buckets = {}
    kept_children = []
    for c in folder.get("children", []):
        if c.get("type") != "url":
            kept_children.append(c)
            continue
        u = c.get("url", "")
        if u not in buckets:
            buckets[u] = c
            kept_children.append(c)
        else:
            try:
                cur_ts = int(c.get("date_added", 0) or 0)
                old_ts = int(buckets[u].get("date_added", 0) or 0)
            except ValueError:
                cur_ts, old_ts = 0, 0
            if cur_ts >= old_ts:
                removed.append(buckets[u])
                kept_children[kept_children.index(buckets[u])] = c
                buckets[u] = c
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
    roots = node["roots"]
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
def _collect_url_names(node):
    return {(n.get("name", ""), n.get("url", "")) for n in iter_urls(node)}


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
        root = data["roots"].get(key)
        if root:
            body.append(f"<li><details open><summary><span class='root'>🗂 {esc(label)}"
                        f"<span class='cnt'> ({rc(root)})</span></span></summary><ul>{render(root)}</ul></details></li>")
    tree = "<ul class='tree'>" + "".join(body) + "</ul>"

    diff_html, removed_n, added_n = "", 0, 0
    if args.base:
        base = load(args.base)
        bu, cu = _collect_url_names(base), _collect_url_names(data)
        removed, added = sorted(bu - cu), sorted(cu - bu)
        removed_n, added_n = len(removed), len(added)
        items = "".join(f"<li>❌ 删除: <a href='{esc(u)}'>{esc(nm)}</a></li>" for nm, u in removed)
        items += "".join(f"<li>➕ 新增: <a href='{esc(u)}'>{esc(nm)}</a></li>" for nm, u in added)
        diff_html = (f"<div class='diff'><h3>与原版差异（{removed_n} 删 / {added_n} 增）</h3>"
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
        print(f"[preview] 差异：删 {removed_n} / 增 {added_n}")
    else:
        print("[preview] 未比对差异（可加 --base 原文件）")


# --------------------------- finalize (唯一动真身) ---------------------------
def cmd_finalize(args):
    """把候选 --from 安装到 --target：删 checksum + 处理陈旧 .bak，然后原地写回。"""
    # 安全闸①：浏览器在跑就拒绝（除非 --force）
    if not args.force:
        running, ok = _browser_processes_running()
        if running:
            sys.exit(f"[finalize] ✗ 检测到浏览器进程在跑：{', '.join(running)}。"
                     f"运行时书签缓存在内存里，退出会用旧数据覆盖本次修改。"
                     f"请完全退出浏览器（含托盘后台）后重试；确认已退可加 --force。")
        if not ok:
            print("[finalize] ⚠ 无法探测浏览器进程（tasklist/pgrep 不可用），请自行确保已完全退出浏览器。")

    data = load(args.file_from)
    had_ckpt = "checksum" in data
    data.pop("checksum", None)  # 删字段 → Chrome 自动重建校验

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    # 安全闸②：写回前，先把当前真身再兜一份（即便用户漏了 backup 步也能救）
    if os.path.exists(args.target):
        safety = f"{args.target}.prescript-{stamp}"
        shutil.copy2(args.target, safety)
        print(f"[finalize] 已自动兜底当前真身 → {safety}")

    bak = args.target + ".bak"
    if os.path.exists(bak):
        moved = f"{bak}.stale-{stamp}"
        os.replace(bak, moved)
        print(f"[finalize] 陈旧 {bak} → 改名 {moved}（防止 Chrome 加载时回滚）")

    try:
        with open(args.target, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=3)
    except (PermissionError, OSError) as e:
        sys.exit(f"[finalize] ✗ 写回失败：{e}\n"
                 f"        常见原因：浏览器没退干净占用文件 / 文件被设为只读 / 需要更高权限。"
                 f"（自动兜底件已生成，真身未被破坏）")
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
    for key in ("bookmark_bar", "other", "synced"):
        if key in node["roots"]:
            rec(node["roots"][key])
    return issues


def cmd_verify(args):
    try:
        data = load(args.file)
    except Exception as e:
        print(f"[verify] ✗ JSON 解析失败: {e}")
        sys.exit(1)
    ids = all_ids(data)
    dup_ids = {i for i in ids if ids.count(i) > 1 and i is not None}
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
    if not os.path.isfile(args.backup):
        sys.exit(f"[restore] 底牌不存在: {args.backup}")
    shutil.copy2(args.backup, args.target)
    load(args.target)  # 解析校验
    print(f"[restore] 已用底牌还原 {args.target}（url {count_urls(load(args.target))} 条），文件可正常解析")


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
    sa, sb = _collect_url_names(a), _collect_url_names(b)
    removed, added = sorted(sa - sb), sorted(sb - sa)
    print(f"[diff] {args.a} ({ca}条)  →  {args.b} ({cb}条)   净变化 {cb - ca}")
    print(f"[diff] 删除 {len(removed)} / 新增 {len(added)}")
    for nm, u in removed:
        print(f"  ❌ {nm}  <{u}>")
    for nm, u in added:
        print(f"  ➕ {nm}  <{u}>")


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

    rs = sub.add_parser("restore", help="用底牌一键还原")
    rs.add_argument("--backup", required=True)
    rs.add_argument("--target", required=True)
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
