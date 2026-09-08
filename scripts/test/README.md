# test/ — 练手与验证靶子（请勿删除）

本目录是 `bm.py` 的验证场所，里面住着**两套数据**，性质完全不同：

## A. `sample/` —— 通用站点演示样例（**入库**，零隐私）

用**真实通用网站**合成的演示数据（淘宝/京东、新浪/澎湃、GitHub/MDN、B站/12306……），
before 乱放、after 按「购物/新闻资讯/技术开发/学习资源/视频娱乐/生活工具/博客与阅读」
七类归好。随仓库分发，任何人 clone 之后立刻有靶子可练。**没有一条是个人收藏**。
详见 [sample/README.md](sample/README.md)。

```bash
python scripts/bm.py show --file scripts/test/sample/Bookmarks.before --stats
python scripts/bm.py diff --a scripts/test/sample/Bookmarks.before --b scripts/test/sample/Bookmarks.after
```
预期输出：`diff` 报 **删 1 / 增 0 / 移动 38 / 改名 0 / 副本减少 1**（净变化 `40 -> 38`）。

## B. 本目录下的 `Bookmarks.*` —— 真实书签快照（**不入库**）

从真实浏览器**只读复制**而来，裁剪过但仍含真实标题/链接，用来验证脚本在真实结构上的手感。

- 已被仓库根 `.gitignore` 的 `scripts/test/**` 屏蔽（只有 `README.md` 与 `sample/` 被显式放行）→ **绝不入库、绝不外推**。
- 想换成自己的数据：直接把自己的 `Bookmarks` 复制过来覆盖同名文件即可——**工具箱只认路径，不关心数据从哪来**。
- 将来要做**公开展示案例**：把这两份换成彻底脱敏/虚构的数据，再解除 ignore 即可。

| 文件 | 含义 |
|---|---|
| `Bookmarks.before` | 原版（裁剪后的真实结构，带 `checksum`） |
| `Bookmarks.after` | 修改后（改名 + 增 2 + 删 2，去 `checksum`） |
| `preview-*.html` | 对应的本地预览（可 `preview` 命令重造，也已被忽略） |

## 复现 / 重造对拍流程（不改交付数据）

```bash
# ① 备份到你自己的临时目录再折腾，原两份永远别动
python ../bm.py backup --file Bookmarks.before --dir %TEMP%/bm
# ② 按你要的规则重排 → 只产候选，绝不动原文件
python ../bm.py plan --file Bookmarks.before --out cand --sort --dedup
# ③ 肉眼核对（带相对原版的增删改差异）
python ../bm.py preview --file cand --base Bookmarks.before --out preview-after.html
```

`finalize` 的 `--target` 在"联调阶段"**永远只指临时目录里的副本**，
绝不指向真实浏览器 Profile。真实 Profile 只在最终正式整理、且浏览器完全退出时才当 target。
