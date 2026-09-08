#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bm.py 的零依赖回归测试（unittest，仅标准库）。

为什么要有它
------------
这个项目卖的是"敢让它动真实数据"，而每个安全不变量（去重保留最新、跨目录不去重、
浏览器在跑就拒绝、原子写回、候选非法不落地……）过去都只靠手工跑一遍来验证。
人手 IA，一次改动就可能悄悄破坏护栏。这里把它们全部钉成断言。

跑法
----
    python scripts/test/run_tests.py            # 跑全部
    python scripts/test/run_tests.py -v         # 详细
    python -m unittest discover -s scripts/test # 等价

约定
----
- 只碰临时目录，**绝不读写任何真实 Profile**。
- 需要模拟"浏览器在跑/没跑"时，一律 monkeypatch `bm._browser_processes_running`。
"""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))  # 让 import bm 不论从哪个目录运行都成立

import bm  # noqa: E402


# ------------------------------ 造数据的小工具 ------------------------------
def ts(y, m, d):
    """Chrome 时间戳（自 1601-01-01 的微秒），测试里自己造，不依赖 bm 内部实现。"""
    return str(int((datetime(y, m, d) - datetime(1601, 1, 1)).total_seconds() * 1_000_000))


def node(name, url=None, y=2024, m=1, d=1, node_id=None, children=None):
    common = {"date_added": ts(y, m, d), "id": str(node_id or name), "name": name}
    if url is None:  # 目录
        common.update({"children": children or [], "type": "folder"})
        return common
    common.update({"type": "url", "url": url})
    return common


def write(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=3)
    return path


def read(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def sha(path):
    return bm.sha256(path)


def bookmarks(bar_children):
    return {
        "checksum": "f" * 40,
        "roots": {
            "bookmark_bar": {"children": bar_children, "id": "1", "name": "书签栏",
                             "type": "folder"},
            "other": {"children": [], "id": "2", "name": "其他书签", "type": "folder"},
            "synced": {"children": [], "id": "3", "name": "移动设备书签", "type": "folder"},
        },
        "version": 1,
    }


# ------------------------------ 纯函数层 ------------------------------
class TestBasics(unittest.TestCase):
    def test_ts_conversion(self):
        self.assertEqual(bm.chrome_ts_to_date("0"), "-")
        self.assertEqual(bm.chrome_ts_to_date("bad"), "?")
        self.assertEqual(bm.chrome_ts_to_date(None), "?")
        # 1601-01-01 起 0 微秒 = 1601-01-01
        self.assertEqual(bm.chrome_ts_to_date(1), "1601-01-01")

    def test_load_missing_file(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(FileNotFoundError):
                bm.load(os.path.join(t, "nope.json"))

    def test_load_tolerates_bom(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "bom.json")
            with open(p, "w", encoding="utf-8-sig") as f:
                f.write('{"roots": {}}')
            self.assertEqual(bm.load(p), {"roots": {}})

    def test_roots_of_missing_gives_chinese_error(self):
        with self.assertRaises(SystemExit) as ctx:
            bm.roots_of({"not": "bookmarks"})
        self.assertIn("roots", str(ctx.exception))

    def test_duplicate_ids_and_paths(self):
        data = bookmarks([
            node("A", "https://a.test/", 2024, 1, 1, "id-1"),
            node("A2", "https://a2.test/", 2024, 1, 2, "id-1"),  # 重复 id
        ])
        self.assertEqual(bm.duplicate_ids(data), ["id-1"])
        paths = dict((n.get("name"), p) for n, p in bm.iter_urls_with_parent(data))
        self.assertEqual(paths["A"], "书签栏")


class TestDedupAndSort(unittest.TestCase):
    def test_dedup_same_folder_keeps_newest(self):
        folder = {"type": "folder", "name": "f", "children": [
            node("旧", "https://dup.test/", 2020, 1, 1, "old"),
            node("新", "https://dup.test/", 2025, 1, 1, "new"),
        ]}
        folder["children"][0]["date_added"] = "1000"
        folder["children"][1]["date_added"] = "2000"
        removed = bm._dedup_children(folder)
        self.assertEqual(len(folder["children"]), 1)
        self.assertEqual(folder["children"][0]["id"], "new")   # 保留最新那条
        self.assertEqual([r["id"] for r in removed], ["old"])

    def test_plan_never_touches_source(self):
        data = bookmarks([node("A", "https://a.test/", 2024, 1, 1, "1")])
        with tempfile.TemporaryDirectory() as t:
            src, cand = os.path.join(t, "Bookmarks"), os.path.join(t, "cand")
            write(src, data)
            before = sha(src)
            bm.main(["plan", "--file", src, "--out", cand, "--sort", "--dedup"])
            self.assertEqual(sha(src), before)      # 原文件一个字节都没变
            self.assertTrue(os.path.isfile(cand))

    def test_cross_folder_duplicates_survive(self):
        data = bookmarks([
            node("开发", None, children=[node("dup", "https://dup.test/", 2024, 1, 1, "x1")]),
            node("工具", None, children=[node("dup", "https://dup.test/", 2024, 1, 1, "x2")]),
        ])
        with tempfile.TemporaryDirectory() as t:
            src, cand = os.path.join(t, "Bookmarks"), os.path.join(t, "cand")
            write(src, data)
            bm.main(["plan", "--file", src, "--out", cand, "--dedup"])
            self.assertEqual(bm.count_urls(bm.load(cand)), 2)  # 跨目录不去重

    def test_sort_puts_folders_first(self):
        folder = {"type": "folder", "name": "f", "children": [
            node("z-url", "https://z.test/", 2024, 1, 1),
            node("a-folder", None, children=[]),
        ]}
        bm._sort_children(folder)
        self.assertEqual(folder["children"][0]["type"], "folder")


class NoBrowser:
    """把"浏览器进程"的结果固定住，避免测试受本机真实进程影响。"""

    def __init__(self, running):
        self.running = running

    def __enter__(self):
        self._orig = bm._browser_processes_running
        bm._browser_processes_running = lambda: (list(self.running), True)
        return self

    def __exit__(self, *a):
        bm._browser_processes_running = self._orig


def run(cmdline):
    """跑一条 bm 命令；返回 (是否抛出 SystemExit, 抛出的消息)。"""
    try:
        bm.main(cmdline)
        return None
    except SystemExit as e:
        return str(e)


class TestFinalizeSafety(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.target = os.path.join(self.dir.name, "Bookmarks")
        write(self.target, bookmarks([node("A", "https://a.test/", 2024, 1, 1, "1")]))
        self.cand = write(os.path.join(self.dir.name, "cand"),
                          bookmarks([node("A", "https://a.test/", 2024, 1, 1, "1"),
                                     node("B", "https://b.test/", 2024, 1, 2, "2")]))
        write(self.target + ".bak", bookmarks([]))  # 陈旧 bak，应被改名

    def tearDown(self):
        self.dir.cleanup()

    def test_refuses_when_browser_running(self):
        with NoBrowser(["Chrome"]):
            msg = run(["finalize", "--from", self.cand, "--target", self.target])
        self.assertIn("浏览器进程在跑", msg)
        self.assertEqual(bm.count_urls(bm.load(self.target)), 1)  # 真身没被改

    def test_happy_path_prescript_atomic_no_temp_left(self):
        with NoBrowser([]):
            run(["finalize", "--from", self.cand, "--target", self.target])
        data = bm.load(self.target)
        self.assertEqual(bm.count_urls(data), 2)
        self.assertNotIn("checksum", data)                       # 校验和被删
        self.assertTrue(any(f.startswith("Bookmarks.prescript-") for f in os.listdir(self.dir.name)))
        self.assertTrue(any(f.startswith("Bookmarks.bak.stale-") for f in os.listdir(self.dir.name)))
        self.assertFalse(any(".tmp-" in f for f in os.listdir(self.dir.name)))  # 原子替换不残留

    def test_refuses_invalid_candidate(self):
        bad = write(os.path.join(self.dir.name, "bad"), {"hello": "world"})
        with NoBrowser([]):
            msg = run(["finalize", "--from", bad, "--target", self.target])
        self.assertIn("候选文件结构非法", msg)
        self.assertEqual(bm.count_urls(bm.load(self.target)), 1)  # 真身安然无恙

    def test_refuses_overwriting_non_bookmark_target(self):
        weird = os.path.join(self.dir.name, "Preferences")
        write(weird, {"some": "app setting"})
        with NoBrowser([]):
            msg = run(["finalize", "--from", self.cand, "--target", weird])
        self.assertIn("不像书签文件", msg)
        self.assertEqual(read(weird), {"some": "app setting"})   # 没有被盖掉

        with NoBrowser([]):
            run(["finalize", "--from", self.cand, "--target", weird, "--force"])
        self.assertNotEqual(read(weird), {"some": "app setting"})  # --force 才放行


class TestRestoreSafety(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.src = write(os.path.join(self.dir.name, "Bookmarks"),
                         bookmarks([node("A", "https://a.test/", 2024, 1, 1, "1")]))
        self.backup = self.src + ".backup-20260101-000000-000000"
        write(self.backup, bm.load(self.src))

    def tearDown(self):
        self.dir.cleanup()

    def test_restore_refused_when_browser_running(self):
        with NoBrowser(["Chrome"]):
            msg = run(["restore", "--backup", self.backup, "--target", self.src])
        self.assertIn("浏览器进程在跑", msg)   # restore 与 finalize 同等级

    def test_restore_with_force_and_prerestore(self):
        with NoBrowser([]):
            run(["restore", "--backup", self.backup, "--target", self.src, "--force"])
        self.assertEqual(bm.count_urls(bm.load(self.src)), 1)
        self.assertTrue(any(f.startswith("Bookmarks.prerestore-") for f in os.listdir(self.dir.name)))

    def test_restore_missing_backup(self):
        msg = run(["restore", "--backup", os.path.join(self.dir.name, "nope"), "--target", self.src])
        self.assertIn("底牌不存在", msg)


class TestBackup(unittest.TestCase):
    def test_manifest_and_absolute_restore_cmd(self):
        with tempfile.TemporaryDirectory() as t:
            src = write(os.path.join(t, "Bookmarks"), bookmarks([]))
            with NoBrowser([]):
                bm.main(["backup", "--file", src, "--dir", t])
            manifest = os.path.join(t, "_backup_manifest.txt")
            self.assertTrue(os.path.isfile(manifest))
            with open(manifest, encoding="utf-8") as f:
                rec = json.loads(f.read().strip().splitlines()[-1])
            cmd = rec["restore_cmd"]
            self.assertTrue(os.path.isabs(cmd.split('"')[1]))            # 解释器绝对路径
            self.assertTrue(os.path.isfile(rec["backup"]))               # 底牌真的存在
            self.assertIn("restore", cmd)

class TestDiffClassification(unittest.TestCase):
    """diff 的路径感知对账——这类"看不见的移动"过去会报成 删0/增0。"""

    def test_move_between_folders(self):
        base = bookmarks([node("A", None, children=[node("x", "https://x.test/", 2024, 1, 1, "1")]),
                          node("B", None, children=[])])
        cand = bookmarks([node("A", None, children=[]),
                          node("B", None, children=[node("x", "https://x.test/", 2024, 1, 1, "1")])])
        rep = bm.diff_report(base, cand)
        self.assertEqual(len(rep["moved"]), 1)
        self.assertEqual(rep["removed"], [])
        self.assertEqual(rep["added"], [])

    def test_rename_in_place(self):
        base = bookmarks([node("A", None, children=[node("旧名", "https://x.test/", 2024, 1, 1, "1")])])
        cand = bookmarks([node("A", None, children=[node("新名", "https://x.test/", 2024, 1, 1, "1")])])
        rep = bm.diff_report(base, cand)
        self.assertEqual(len(rep["renamed"]), 1)
        self.assertEqual(rep["removed"], [])

    def test_dedup_counts_as_deduped_not_removed(self):
        base = bookmarks([node("A", None, children=[
            node("dup", "https://d.test/", 2020, 1, 1, "1"),
            node("dup", "https://d.test/", 2024, 1, 1, "2")])])
        cand = bookmarks([node("A", None, children=[
            node("dup", "https://d.test/", 2024, 1, 1, "2")])])
        rep = bm.diff_report(base, cand)
        self.assertEqual(len(rep["deduped"]), 1)
        self.assertEqual(rep["removed"], [])   # 链接还在，不是真删除

    def test_true_add_and_remove(self):
        base = bookmarks([node("gone", "https://gone.test/", 2024, 1, 1, "1")])
        cand = bookmarks([node("fresh", "https://fresh.test/", 2024, 1, 1, "2")])
        rep = bm.diff_report(base, cand)
        self.assertEqual(len(rep["removed"]), 1)
        self.assertEqual(len(rep["added"]), 1)


class TestVerifyAndShow(unittest.TestCase):
    def test_verify_reports_structural_issues(self):
        data = {"roots": {"bookmark_bar": {
            "type": "folder", "name": "书签栏", "id": "1",
            "children": [{"type": "url", "name": "空链接", "id": "2", "url": ""},
                         {"type": "url", "name": "同 id", "id": "2", "url": "https://x.test/"}],
        }}}
        with tempfile.TemporaryDirectory() as t:
            p = write(os.path.join(t, "B"), data)
            buf = io.StringIO()
            with redirect_stdout(buf):
                bm.main(["verify", "--file", p])
            out = buf.getvalue()
        self.assertIn("url 节点 url 为空", out)
        self.assertIn("重复id", out)

    def test_show_depth_and_stats(self):
        data = bookmarks([node("A", None, children=[
            node("deep", None, children=[node("leaf", "https://leaf.test/", 2024, 1, 1, "1")])])])
        with tempfile.TemporaryDirectory() as t:
            p = write(os.path.join(t, "B"), data)
            buf = io.StringIO()
            with redirect_stdout(buf):
                bm.main(["show", "--file", p, "--depth", "1"])
            shallow = buf.getvalue()
            buf2 = io.StringIO()
            with redirect_stdout(buf2):
                bm.main(["show", "--file", p, "--stats"])
            stats = buf2.getvalue()
        self.assertIn("已省略", shallow)                 # 深层被截断
        self.assertIn("url 总数: 1", stats)              # 体检照旧给出
        self.assertNotIn("[目录] A", stats)              # --stats 不打印目录树

    def test_show_marks_cross_folder_duplicates(self):
        data = bookmarks([node("P", None, children=[node("d", "https://dup.test/", 2024, 1, 1, "1")]),
                          node("Q", None, children=[node("d", "https://dup.test/", 2024, 1, 1, "2")])])
        with tempfile.TemporaryDirectory() as t:
            p = write(os.path.join(t, "B"), data)
            buf = io.StringIO()
            with redirect_stdout(buf):
                bm.main(["show", "--file", p, "--stats"])
            out = buf.getvalue()
        self.assertIn("跨目录", out)                     # 明确告诉使用者：这条 --dedup 不会动


class TestDetectRoots(unittest.TestCase):
    """根路径不许写死：必须跟着 OS 与环境变量走。"""

    def _roots(self, system, env):
        import platform as _platform
        old_system, old_env = _platform.system, dict(os.environ)
        try:
            _platform.system = lambda: system
            os.environ.clear()
            os.environ.update(env)
            return dict(bm._default_roots())
        finally:
            _platform.system = old_system
            os.environ.clear()
            os.environ.update(old_env)

    def test_windows_follows_localappdata(self):
        roots = self._roots("Windows", {"LOCALAPPDATA": r"X:\Somewhere\AppData\Local",
                                        "APPDATA": r"X:\Somewhere\AppData\Roaming"})
        self.assertTrue(roots["Chrome"].endswith(os.path.join("Google", "Chrome", "User Data")))
        self.assertTrue(roots["Chrome"].startswith(r"X:\Somewhere\AppData\Local"))
        self.assertTrue(roots["Edge"].startswith(r"X:\Somewhere\AppData\Local"))
        self.assertTrue(roots["Opera"].startswith(r"X:\Somewhere\AppData\Roaming"))

    def test_linux_follows_xdg(self):
        roots = self._roots("Linux", {"XDG_CONFIG_HOME": "/home/someone/.config"})
        self.assertEqual(roots["Chrome"], os.path.join("/home/someone/.config", "google-chrome"))

    def test_macos_under_application_support(self):
        roots = self._roots("Darwin", {})
        self.assertTrue(roots["Chrome"].endswith(os.path.join("Google", "Chrome")))
        self.assertIn("Application Support", roots["Chrome"])

    def test_no_hardcoded_windows_user(self):
        roots = self._roots("Windows", {"LOCALAPPDATA": r"D:\Custom\Local", "APPDATA": r"D:\Custom\Roaming"})
        self.assertNotIn("Users", roots["Chrome"])       # 不许出现 C:\Users\某名\... 这种烙死的路径


class TestPreflightSyncAwareness(unittest.TestCase):
    """preflight 要在动手前把"云端不是备份"这件事讲清楚——脚本管不了合并，但能管住认知。"""

    def _profile(self, **with_what):
        d = tempfile.TemporaryDirectory()
        prof = os.path.join(d.name, "Default")
        os.makedirs(prof, exist_ok=True)
        if with_what.get("sync_dir"):
            os.makedirs(os.path.join(prof, "Sync Data"), exist_ok=True)
        if "preferences" in with_what:
            write(os.path.join(prof, "Preferences"), with_what["preferences"])
        self._saved = d
        return os.path.join(prof, "Bookmarks")

    def tearDown(self):
        if getattr(self, "_saved", None):
            self._saved.cleanup()

    def test_detects_sync_dir(self):
        self.assertTrue(any("Sync Data" in r for r in bm.sync_signals(self._profile(sync_dir=True))))

    def test_detects_preferences_sync_key(self):
        reasons = bm.sync_signals(self._profile(preferences={"sync": {"anything": 1}}))
        self.assertTrue(any("sync" in r for r in reasons))

    def test_no_false_claim_on_clean_profile(self):
        self.assertEqual(bm.sync_signals(self._profile()), [])

    def test_preflight_prints_cloud_warning_without_blocking(self):
        d = tempfile.TemporaryDirectory()
        prof = os.path.join(d.name, "Default")
        os.makedirs(os.path.join(prof, "Sync Data"))
        write(os.path.join(prof, "Preferences"), {"sync": {"x": 1}})
        target = write(os.path.join(prof, "Bookmarks"), bookmarks([]))
        try:
            buf = io.StringIO()
            with NoBrowser([]), redirect_stdout(buf):
                bm.main(["preflight", "--file", target])
            out = buf.getvalue()
        finally:
            d.cleanup()
        self.assertIn("云端同步", out)
        self.assertIn("云端不是备份", out)
        self.assertIn("GO", out)   # 提示归提示，不构成 NO-GO


class TestProfileOccupancy(unittest.TestCase):
    """进程名只能说"某处有 Chrome 在跑"；Profile 目录里的 SingletonLock 才说明"用的是不是这一个"。"""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.prof = os.path.join(self.dir.name, "Default")
        os.makedirs(self.prof)
        write(os.path.join(self.prof, "Preferences"), {"sync": {"x": 1}})   # Profile 指纹
        self.target = write(os.path.join(self.prof, "Bookmarks"),
                            bookmarks([node("A", "https://a.test/", 2024, 1, 1, "1")]))
        # 注意：候选必须是非空书签——否则会先撞上 finalize 的"空候选"护栏，
        # 就测不到本类真正要测的「Profile 占用锁」拦截了。
        self.cand = write(os.path.join(self.dir.name, "cand"),
                         bookmarks([node("A", "https://a.test/", 2024, 1, 1, "1")]))

    def tearDown(self):
        self.dir.cleanup()

    def _lock(self):
        open(os.path.join(self.prof, "SingletonLock"), "w").close()

    def test_finalize_refuses_locked_profile(self):
        self._lock()
        with NoBrowser([]):   # 即使进程表里没有浏览器，也要拦得住
            msg = run(["finalize", "--from", self.cand, "--target", self.target])
        self.assertIn("Profile 正在被占用", msg)
        self.assertEqual(bm.count_urls(bm.load(self.target)), 1)  # 真身没动

    def test_finalize_force_still_works_when_lock_is_stale(self):
        self._lock()
        with NoBrowser([]):
            msg = run(["finalize", "--from", self.cand, "--target", self.target, "--force"])
        self.assertIsNone(msg)   # --force 放行，用于崩溃残留的旧锁

    def test_preflight_nogo_on_locked_profile(self):
        self._lock()
        buf = io.StringIO()
        code = None
        with NoBrowser([]), redirect_stdout(buf):
            try:
                bm.main(["preflight", "--file", self.target])
            except SystemExit as e:
                code = e.code
        self.assertEqual(code, 2)          # NO-GO 的约定退出码
        self.assertIn("NO-GO", buf.getvalue())
        self.assertIn("占用", buf.getvalue())

    def test_preview_default_lands_outside_profile(self):
        # 同时回归「不带 --base 的 preview」：diff_html 曾因缺初值而 UnboundLocalError
        cwd = os.getcwd()
        os.chdir(self.dir.name)
        try:
            with NoBrowser([]), redirect_stdout(io.StringIO()) as out:
                bm.main(["preview", "--file", self.target])
            self.assertNotIn("未预期错误", out.getvalue())
        finally:
            os.chdir(cwd)
        self.assertTrue(os.path.isfile(os.path.join(self.dir.name, "preview.html")))
        self.assertFalse(os.path.isfile(os.path.join(self.prof, "Bookmarks.preview.html")))

    def test_plan_warns_when_candidate_lands_in_profile(self):
        buf = io.StringIO()
        with NoBrowser([]), redirect_stdout(buf):
            bm.main(["plan", "--file", self.target,
                     "--out", os.path.join(self.prof, "cand"), "--sort"])
        self.assertIn("Profile 目录", buf.getvalue())


class TestEdgeInputRobustness(unittest.TestCase):
    """专门钉「脏输入不会把脚本搞崩」这一类边界——书签 JSON 是浏览器产物，
    字段值完全可能被用户/网页折腾得不成样子，脚本要优雅降级而非报未预期错误。"""

    def test_huge_chrome_timestamp_returns_question(self):
        # 10^30 微秒远超 datetime 能表示的范围，曾直接 OverflowError 崩掉整个 show/preview
        self.assertEqual(bm.chrome_ts_to_date("9" * 30), "?")
        self.assertEqual(bm.chrome_ts_to_date("1" + "0" * 25), "?")

    def test_preview_escapes_quotes_and_tags_in_name_url(self):
        data = bookmarks([node('say "hi" <b>bold</b>', "https://x.test/a'b&c",
                               2024, 1, 1, "1")])
        with tempfile.TemporaryDirectory() as t:
            p = write(os.path.join(t, "B"), data)
            out = os.path.join(t, "p.html")
            with redirect_stdout(io.StringIO()):
                bm.main(["preview", "--file", p, "--out", out])
            content = open(out, encoding="utf-8").read()
        self.assertIn("&quot;hi&quot;", content)          # " 必须被转义
        self.assertNotIn("<b>bold</b>", content)          # 标签不得原样进 HTML
        self.assertIn("&#x27;", content)                  # ' 必须被转义（否则 href 属性被截断）
        self.assertIn("&amp;c", content)                  # & 必须被转义
        self.assertNotIn("href='https://x.test/a'b", content)  # 不能出现"裸单引号截断 href"

    def test_garbage_binary_file_clean_error_not_crash(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "garbage")
            with open(p, "wb") as f:
                f.write(b"\xff\xfe\x00\x01not json at all")
            msg = run(["show", "--file", p])
        self.assertIsNotNone(msg)
        self.assertNotIn("Traceback", str(msg))
        self.assertNotIn("未预期错误", str(msg))
        self.assertIn("解析失败", str(msg))

    def test_preflight_garbage_file_gives_nogo(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "garbage")
            with open(p, "wb") as f:
                f.write(b"\xff\xfe\x00\x01not json at all")
            code = None
            buf = io.StringIO()
            with redirect_stdout(buf):
                try:
                    bm.main(["preflight", "--file", p])
                except SystemExit as e:
                    code = e.code
        self.assertEqual(code, 2)
        self.assertIn("NO-GO", buf.getvalue())

    def test_folder_with_unnamed_node_and_missing_children(self):
        # Chrome 正常不会产出这种东西，但脏 JSON 里可能缺 children/缺 name——
        # 结构检查应能发现，而不是在遍历时就崩掉
        data = {"roots": {"bookmark_bar": {"type": "folder", "id": "1", "children": [
            {"type": "folder", "id": "2"},           # 缺 children
            {"type": "url", "id": "3", "url": "https://x.test/"},
        ]}}}
        with tempfile.TemporaryDirectory() as t:
            p = write(os.path.join(t, "B"), data)
            buf = io.StringIO()
            with redirect_stdout(buf):
                bm.main(["verify", "--file", p])
            out = buf.getvalue()
        self.assertIn("结构问题", out)                 # 正常跑完并报告，而不是 Traceback
        self.assertNotIn("未预期错误", out)

    def test_show_zero_length_bookmarks(self):
        # 三个根都为空：show/diff/plan 都不该崩
        with tempfile.TemporaryDirectory() as t:
            p = write(os.path.join(t, "B"), bookmarks([]))
            for argv in (["show", "--file", p],
                         ["plan", "--file", p, "--out", os.path.join(t, "c"), "--sort", "--dedup"]):
                msg = run(argv)
                self.assertIsNone(msg, argv)


class TestMinimumArgumentPaths(unittest.TestCase):
    """每个命令的「最省参数」都必须能跑到底。

    起因：preview 不带 `--base` 时 `diff_html` 缺初值 → UnboundLocalError，
    而且藏了两个版本才被发现（因为手工验证时总带着 --base）。
    这一类问题只有靠"把最小参数组合也跑一遍"才能钉住。
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.src = write(os.path.join(self.dir.name, "Bookmarks"),
                         bookmarks([node("A", "https://a.test/", 2024, 1, 1, "1")]))

    def tearDown(self):
        self.dir.cleanup()

    def _must_not_crash(self, argv):
        buf = io.StringIO()
        with NoBrowser([]), redirect_stdout(buf):
            bm.main(argv)
        out = buf.getvalue()
        self.assertNotIn("未预期错误", out)
        self.assertNotIn("Traceback", out)
        return out

    def test_plan_without_rules(self):
        self._must_not_crash(["plan", "--file", self.src, "--out",
                              os.path.join(self.dir.name, "c1")])

    def test_verify_without_before(self):
        self._must_not_crash(["verify", "--file", self.src])

    def test_show_without_switches(self):
        self._must_not_crash(["show", "--file", self.src])

    def test_preview_without_base(self):
        out = self._must_not_crash(["preview", "--file", self.src,
                                    "--out", os.path.join(self.dir.name, "p.html")])
        self.assertIn("未比对差异", out)

    def test_backup_defaults_to_same_dir(self):
        self._must_not_crash(["backup", "--file", self.src])
        self.assertTrue(any(f.startswith("Bookmarks.backup-") for f in os.listdir(self.dir.name)))
        self.assertTrue(os.path.isfile(os.path.join(self.dir.name, "_backup_manifest.txt")))


class TestRestoreCorruptBackup(unittest.TestCase):
    """restore 必须先在覆盖前校验底牌——否则底牌损坏会把真身也写坏，最后一份好副本都没了。"""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.target = write(os.path.join(self.dir.name, "Bookmarks"),
                            bookmarks([node("A", "https://a.test/", 2024, 1, 1, "1")]))
        self.backup = self.target + ".backup-20260101-000000-000000"

    def tearDown(self):
        self.dir.cleanup()

    def test_refuses_corrupt_backup_and_keeps_target(self):
        write(self.backup, "{ 这不是合法的 json ")   # 损坏底牌
        with NoBrowser([]):
            msg = run(["restore", "--backup", self.backup, "--target", self.target])
        self.assertIn("拒绝还原", msg)                      # 解析失败或结构非法都要拒
        self.assertEqual(bm.count_urls(bm.load(self.target)), 1)   # 真身完好

    def test_refuses_non_bookmark_backup(self):
        write(self.backup, {"hello": "world"})    # JSON 合法但不是书签
        with NoBrowser([]):
            msg = run(["restore", "--backup", self.backup, "--target", self.target])
        self.assertIn("结构非法", msg)
        self.assertEqual(bm.count_urls(bm.load(self.target)), 1)


class TestFinalizeSelfTarget(unittest.TestCase):
    """--from 与 --target 指同一文件 = 在唯一副本上自我改写，必须拒绝。"""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.f = write(os.path.join(self.dir.name, "Bookmarks"),
                       bookmarks([node("A", "https://a.test/", 2024, 1, 1, "1")]))

    def tearDown(self):
        self.dir.cleanup()

    def test_refuses_self_target(self):
        with NoBrowser([]):
            msg = run(["finalize", "--from", self.f, "--target", self.f])
        self.assertIn("同一文件", msg)
        self.assertEqual(bm.count_urls(bm.load(self.f)), 1)
        self.assertFalse(any(".prescript-" in x for x in os.listdir(self.dir.name)))

    def test_force_allows_self_target(self):
        with NoBrowser([]):
            run(["finalize", "--from", self.f, "--target", self.f, "--force"])
        self.assertNotIn("checksum", bm.load(self.f))   # --force 放行后确实写回成功

    def test_refuses_empty_candidate(self):
        empty = write(os.path.join(self.dir.name, "empty"), bookmarks([]))
        with NoBrowser([]):
            msg = run(["finalize", "--from", empty, "--target", self.f])
        self.assertIn("0 条书签", msg)
        self.assertEqual(bm.count_urls(bm.load(self.f)), 1)   # 真身没动
        self.assertFalse(any(".prescript-" in x for x in os.listdir(self.dir.name)))

    def test_warns_on_large_count_drop_but_still_writes(self):
        # 真身放 4 条，候选只 1 条 —— 触发 <50% 告警，但不拦截
        big = write(os.path.join(self.dir.name, "big"),
                    bookmarks([node(f"u{i}", f"https://u{i}.test/", 2024, 1, i, str(i)) for i in range(1, 5)]))
        small = write(os.path.join(self.dir.name, "small"),
                      bookmarks([node("A", "https://a.test/", 2024, 1, 1, "1")]))
        buf = io.StringIO()
        with NoBrowser([]), redirect_stdout(buf):
            run(["finalize", "--from", small, "--target", big])
        self.assertIn("远低于真身", buf.getvalue())              # 告警
        self.assertEqual(bm.count_urls(bm.load(big)), 1)        # 仍写回成功（非拦截）


if __name__ == "__main__":
    unittest.main(verbosity=2)

