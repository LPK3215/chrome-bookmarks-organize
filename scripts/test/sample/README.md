# sample/ — 通用站点演示样例（入库 · 零隐私）

这里的两份数据是**用真实存在的通用网站合成的演示数据**，目的是让任何人 clone 之后**立刻有靶子可练**，
并且一眼就能看懂「整理前 vs 整理后」的区别。

> 为什么需要它：本目录之外的 `scripts/test/Bookmarks.*` 是**真实书签快照**，含隐私、
> 被 `.gitignore` 屏蔽不入库。若没有这份样例，clone 的人第一次跟着 README 跑就会撞空。
>
> 为什么不干脆用 `example.test`：那样的链接整理前后看不出意义。这里选用**人人都认得的通用站点**
> （淘宝/京东、新浪/澎湃、GitHub/MDN、B站/YouTube、12306/高德……）按类目归好，
> preview 出来的效果就是你想看到的真实整理效果。它依然**零隐私**——没有一条是你个人的收藏。

## 文件

| 文件 | 含义 |
|---|---|
| `Bookmarks.before` | **AI 整理前**：40 条通用站点乱放——平铺在书签栏 + 三个「新建文件夹」，带 `checksum` |
| `Bookmarks.after` | **AI 整理后**：38 条全部归入 7 个类目目录（购物/新闻资讯/技术开发/学习资源/视频娱乐/生活工具/博客与阅读），去 `checksum` |
| `make_sample.py` | 重新生成上面两份的脚本（想重造就跑它） |

两份之间的净变化是 `40 → 38`（`-2` = 去重掉 1 条 + 删掉 1 条失效旧链接）。

## 数据长什么样

**after（AI 整理后）** 的目录一眼可读：

```
书签栏
├── 购物          淘宝网 / 京东 / 拼多多 / 天猫 / 苏宁易购 / 亚马逊中国
├── 新闻资讯      新浪新闻 / 网易新闻 / 澎湃新闻 / 新华社 / BBC 中文 / 纽约时报中文网
├── 技术开发      GitHub / Stack Overflow / MDN Web 文档 / 掘金 / 阮一峰的网络日志 / LeetCode
├── 学习资源      中国大学MOOC / Coursera / 学堂在线 / 知乎 / 维基百科 / 可汗学院
├── 视频娱乐      bilibili / YouTube / 爱奇艺 / 腾讯视频 / 芒果TV / 网易云音乐
├── 生活工具      铁路12306 / 高德地图 / 大众点评 / 中国天气网 / 百度翻译 / 顺丰速运
└── 博客与阅读    少数派 / 即刻
```

**before（AI 整理前）** 则是"随手丢"的样子：10 条平铺在书签栏，其余散落在
`新建文件夹 / 新建文件夹 (1) / 新建文件夹 (2)` 里，还有两条埋点。

## 刻意埋的点（验证工具箱各能力）

| 埋点 | 在 before 里的位置 | 验证什么 |
|---|---|---|
| 「大众点评」同目录收藏了两次（2023-10-12 与 2022-06-06） | 书签栏平铺区 | `plan --dedup` 保留日期最新的一条、并掉旧条，`diff` 报「副本减少」而不是「删除」 |
| 「失效-个人主页(已打不开)」 | `新建文件夹` | `diff` 报「删除」——真实的清理动作 |
| 40 条全被挪进 7 个类目目录 | 全部 | `diff` / `preview --base` 的路径感知「移动」对账 |
| before 有 checksum / after 没有 | 顶层 | `finalize` 删 checksum、`verify` 的提示分支 |

> 曾经这里埋过"重复 id"，后来撤了：重复 id 的检出已由 `run_tests.py` 的
> `TestVerifyAndShow.test_verify_reports_structural_issues` 单独锁住，
> 演示样例保持"干净结构"，避免误导（after 本应是整理好的结果）。

## 试跑（对照下面的预期输出）

```bash
# 在仓库根目录
python scripts/bm.py show    --file scripts/test/sample/Bookmarks.before --stats   # 40 条，1 组同目录重复 URL
python scripts/bm.py plan    --file scripts/test/sample/Bookmarks.before --out cand --sort --dedup   # 40 -> 39
python scripts/bm.py preview --file scripts/test/sample/Bookmarks.after --base scripts/test/sample/Bookmarks.before --out preview-sample.html
python scripts/bm.py diff    --a scripts/test/sample/Bookmarks.before --b scripts/test/sample/Bookmarks.after
python scripts/bm.py verify  --file scripts/test/sample/Bookmarks.after
```

> `cand`、`preview-sample.html` 是中间产物（后者匹配 `.gitignore` 的 `preview-*`，前者不是）——练完手记得删掉 `cand`，别把它一起提交。

预期：

- `show`：`url 总数: 40`，重复 URL 1 组（`https://www.dianping.com/ ×2`，标注**同目录 → --dedup 会并入 1 条**）；
- `plan --sort --dedup`：`url 40 -> 39 (去重删除 1 条)`，且原文件未动；
- `diff before → after`：`删 1 / 增 0 / 移动 38 / 改名 0 / 副本减少 1`，净变化 `-2`；
- `preview --base`：同一套差异，绿色「移动」行把每条通用站点标出"从哪挪到哪"；
- `verify after`：`JSON 合法 / checksum 已无 / url 总数 38 / 重复id 无 / 结构问题 无`。

`make_sample.py` 全确定性、可复现：重跑一次产物逐字节一致。
