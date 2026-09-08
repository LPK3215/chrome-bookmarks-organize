# sample/ — 合成样例（入库 · 零隐私）

这里的两份数据是**纯虚构**的，目的是让任何人 clone 之后**立刻有靶子可练**。

> 为什么需要它：本目录之外的 `scripts/test/Bookmarks.*` 是**真实书签快照**，含隐私、
> 被 `.gitignore` 屏蔽不入库。若没有这份样例，clone 的人第一次跟着 README 跑就会撞空。

## 文件

| 文件 | 含义 |
|---|---|
| `Bookmarks.before` | 18 条虚构书签：三层嵌套、带 `checksum` |
| `Bookmarks.after` | 在 before 上做了**改目录名 + 移动 1 条 + 删 2 条 + 增 2 条**，且去掉 `checksum` |
| `make_sample.py` | 重新生成上面两份的脚本（想重造就跑它） |

## 刻意埋的点（用来验证工具箱各条能力）

| 埋点 | 验证什么 |
|---|---|
| 同目录内两条相同链接 | `plan --dedup` 会合并成 1 条，`diff` 报「副本减少」而不是「删除」 |
| 跨目录两条相同链接 | `plan` **不会**去重（Chrome 允许一条归多处） |
| 一对重复 id | `verify` 能报出「重复id」 |
| before 有 checksum / after 没有 | `finalize` 的删 checksum 分支、`verify` 的提示分支 |
| 移动 + 改名 + 增删 | `diff` / `preview --base` 的路径感知对账 |

## 试跑

```bash
# 在仓库根目录
python scripts/bm.py show    --file scripts/test/sample/Bookmarks.before
python scripts/bm.py plan    --file scripts/test/sample/Bookmarks.before --out /tmp/cand --sort --dedup
python scripts/bm.py preview --file /tmp/cand --base scripts/test/sample/Bookmarks.before --out /tmp/p.html
python scripts/bm.py diff    --a scripts/test/sample/Bookmarks.before --b scripts/test/sample/Bookmarks.after
```

预期：`plan` 报告去重删除 1 条；`diff` 报 **删 2 / 增 2 / 移动 2**；
`verify sample/Bookmarks.after` 会报出一组重复 id（这也是埋好的）。
