<div align="center">

# 🗂️ chrome-bookmarks-organize

**AI 整理浏览器书签栏 / 收藏夹**（Chrome · Edge）

直接编辑 Chrome / Edge 的 Bookmarks JSON —— **完全绕开「导出 HTML → 导入」的重复追加问题**

> **一句话定位：一段提示词打底，一份脚本保底 —— 默认用脚本跑。**

[![version](https://img.shields.io/badge/version-v1.14.4-4285f4?style=flat-square&logo=git&logoColor=white)](SKILL.md)
[![CI](https://github.com/LPK3215/chrome-bookmarks-organize/actions/workflows/test.yml/badge.svg?style=flat-square)](https://github.com/LPK3215/chrome-bookmarks-organize/actions/workflows/test.yml)
[![license](https://img.shields.io/badge/license-MIT-34a853?style=flat-square&logo=opensourceinitiative&logoColor=white)](LICENSE)
[![dependencies](https://img.shields.io/badge/dependencies-0-fbbc05?style=flat-square&logo=python&logoColor=white)](scripts/bm.py)
[![tests](https://img.shields.io/badge/tests-54%20passed-4285f4?style=flat-square&logo=githubactions&logoColor=white)](scripts/test/run_tests.py)
[![pages](https://img.shields.io/badge/pages-overview%20site-ea4335?style=flat-square&logo=githubpages&logoColor=white)](https://LPK3215.github.io/chrome-bookmarks-organize/)

[🏠 全景观览站](https://LPK3215.github.io/chrome-bookmarks-organize/) · [📖 SKILL.md](SKILL.md) · [📝 PROMPT.md](PROMPT.md) · [🧪 回归测试](scripts/test/run_tests.py) · [🛠️ MAINTENANCE.md](MAINTENANCE.md)

</div>

---

## 📑 目录

<table>
<tr>
<td width="33%" valign="top"><b>认识项目</b><br>
<a href="#-整理效果一眼看">✨ 整理效果一眼看</a><br>
<a href="#-为什么做这个">🤔 为什么做这个</a><br>
<a href="#-三条路同一条流程">🚀 三条路，同一条流程</a></td>
<td width="33%" valign="top"><b>怎么用</b><br>
<a href="#-核心流程只有-finalize-真正写回">🔁 核心流程</a><br>
<a href="#-工具箱-scriptsbmpy">🧰 命令速查</a><br>
<a href="#-快速上手">⚡ 快速上手</a><br>
<a href="#-文件位置速查">📍 文件位置速查</a></td>
<td width="33%" valign="top"><b>敢不敢用</b><br>
<a href="#-安全设计">🛡️ 安全设计</a><br>
<a href="#-第一次用不敢放心三层自查">✅ 三层自查</a><br>
<a href="#-回归测试">🧪 回归测试</a><br>
<a href="#-已知边界">🚧 已知边界</a><br>
<a href="#-faq">❓ FAQ</a></td>
</tr>
</table>

---

## ✨ 整理效果一眼看

> 数据来自 `scripts/test/sample/` —— 随仓库入库的**通用站点演示样例**（全是淘宝、GitHub 这类公开站点，零隐私）。

<table>
<tr>
<th width="50%" valign="top">😵 整理前 · 40 条随手乱放</th>
<th width="50%" valign="top">✨ 整理后 · 38 条归入 7 个类目</th>
</tr>
<tr>
<td valign="top">📂 书签栏<br>
&nbsp;&nbsp;├ 🔖 淘宝网<br>
&nbsp;&nbsp;├ 🔖 京东<br>
&nbsp;&nbsp;├ 🔖 GitHub<br>
&nbsp;&nbsp;├ 🔖 新浪<br>
&nbsp;&nbsp;├ 🔖 bilibili<br>
&nbsp;&nbsp;├ 📁 新建文件夹<br>
&nbsp;&nbsp;├ 📁 新建文件夹 (1)<br>
&nbsp;&nbsp;├ 📁 新建文件夹 (2)<br>
&nbsp;&nbsp;└ 📁 新建文件夹 (3)<br>
&nbsp;&nbsp;&nbsp;&nbsp;<sub>↑ 40 条平铺、无分类、重复收藏</sub></td>
<td valign="top">📂 书签栏<br>
&nbsp;&nbsp;├ 📁 购物<sub>&nbsp;&nbsp;淘宝网 · 京东 · 拼多多 · 天猫</sub><br>
&nbsp;&nbsp;├ 📁 新闻资讯<sub>&nbsp;&nbsp;新浪 · 网易 · 澎湃 · 新华社</sub><br>
&nbsp;&nbsp;├ 📁 技术开发<sub>&nbsp;&nbsp;GitHub · Stack Overflow · MDN</sub><br>
&nbsp;&nbsp;├ 📁 学习资源<sub>&nbsp;&nbsp;MOOC · Coursera · 知乎</sub><br>
&nbsp;&nbsp;├ 📁 视频娱乐<sub>&nbsp;&nbsp;bilibili · YouTube · 爱奇艺</sub><br>
&nbsp;&nbsp;├ 📁 生活工具<sub>&nbsp;&nbsp;12306 · 高德 · 大众点评</sub><br>
&nbsp;&nbsp;└ 📁 博客与阅读<sub>&nbsp;&nbsp;少数派 · 即刻</sub><br>
&nbsp;&nbsp;&nbsp;&nbsp;<sub>↑ 同目录重复并入 1 条、失效链接删除</sub></td>
</tr>
</table>

正式整理书签，**默认 clone 本仓库走 `scripts/bm.py`（技能 + 脚本）**：体检 GO/NO-GO、自动备份、HTML 预览、原子写回、一键还原全部锁在代码里。不想 clone 时有两条轻路径——把 [`PROMPT.md`](PROMPT.md) 复制给任意 AI（一段话、无闸门，只适合一次性/先体验/分享），或只加载 [`SKILL.md`](SKILL.md) 走「仅提示词」（流程不变，闸门由 AI 人肉守）。

> [!IMPORTANT]
> **判定铁律：有脚本必用脚本，禁止手改 JSON。**

正式形态遵循 [Agent Skills](https://agentskills.io) 开放标准（`SKILL.md`），并附带一个离线、零第三方依赖的命令行工具箱 `scripts/bm.py`，可直接用于 Claude Code、QwenWork、OpenCode 等支持该标准的 AI 编程工具。

---

## 🤔 为什么做这个

整理浏览器书签的常规路线是：导出 HTML → 手工/AI 整理 → 导入。但浏览器书签的**导入是追加不是替换**，整理完永远多出一个「已导入」文件夹，还得手工去重合并。

实际上书签的底层存储就是一个**纯 JSON 文件，无加密**。直接改它 = 改正式数据，重启浏览器即生效、开同步自动同步到账号。这条路社区博客早有验证。

说实话，让 AI 自由发挥整理书签，效果通常也不差——AI 完全有能力读 JSON、归类、去重、写回去。但「能做」和「每次都做得对」之间差着安全距离：没有强制备份、改了什么不透明、写坏了靠运气。本仓库不是在弥补 AI 的能力不足，而是在补上**完整性、安全性、可靠性**的工程纪律——让每一次整理都可回溯、可校验、可还原，无论交给哪个 AI 跑，结果都一致。因此把同一套逻辑做成**三份交付物，从轻到全**：

| 档位 | 交付物 | 一句话 | 闸门 |
|---|---|---|---|
| ① 轻 | `PROMPT.md` | 任何 AI 都能跑的规范提示词（零安装） | ❌ 无 |
| ② 纪律 | `SKILL.md` | skill 化的完整流程：先看结构 → 先提方案 → 拍板才写 → 复验 → 可还原 | ⚠️ AI 人肉守 |
| ③ 闸门 | `scripts/bm.py` | **默认执行层**：体检、自动备份、原子写回、一键还原锁进代码 | ✅ 代码强制 |

![三份交付物 · 从轻到全](./docs/deliverables.svg)

---

## 🚀 三条路，同一条流程

三条路跑的是**同一条 0→7 流程**（定位 → 备份 → 读结构 →〔循环改方案〕→ 拍板写回 → 校验 → 重启验收），区别只在闸门由谁守：

<table>
<tr>
<th width="22%">方式</th>
<th width="30%">你要做什么</th>
<th width="26%">定位</th>
<th width="22%">边界</th>
</tr>
<tr>
<td valign="top"><b>① 技能 + 脚本</b><br>
<img src="https://img.shields.io/badge/%E9%BB%98%E8%AE%A4%20%C2%B7%20%E6%8E%A8%E8%8D%90-34a853?style=flat-square" alt="默认 · 推荐"></td>
<td valign="top">clone / 下载本仓库，让 AI 调 <code>scripts/bm.py</code>：<br>
<code>detect</code> → <code>preflight</code> → <code>backup</code> → <code>show</code> → <code>plan</code> / <code>preview</code> → <code>finalize</code> → <code>verify</code> / <code>diff</code> → <code>restore</code></td>
<td valign="top">正式整理真实书签。体检、底牌、闸门、写回、校验、还原都锁在代码里，一次写对、每次一样</td>
<td valign="top">✅ 唯一推荐对真实书签动手的方式</td>
</tr>
<tr>
<td valign="top"><b>② 仅技能</b><br>
<img src="https://img.shields.io/badge/%E6%97%A0%E8%84%9A%E6%9C%AC%E9%99%8D%E7%BA%A7-94a3b8?style=flat-square" alt="无脚本降级"></td>
<td valign="top">只把 <code>SKILL.md</code> 加载进 AI（联网装 skill、或直接把文件交给 AI），不下载 <code>scripts/</code>；AI 按同一套 0→7 + 硬约束自己读写 JSON</td>
<td valign="top">拿不到脚本时的兜底：流程不变，闸门由 AI 人肉守</td>
<td valign="top">⚠️ 没有进程探测 / sha256 校验 / HTML 预览 / 一键 restore</td>
</tr>
<tr>
<td valign="top"><b>③ 纯提示词</b><br>
<img src="https://img.shields.io/badge/%E9%9B%B6%E5%AE%89%E8%A3%85-f5a623?style=flat-square" alt="零安装"></td>
<td valign="top">把 <code>PROMPT.md</code> 整段复制给任意聊天 AI（Claude / GPT…），再补一句「我的书签文件路径是 ……」</td>
<td valign="top">不 clone、一次性小改、先体验、拿去分享</td>
<td valign="top">⚠️ 最轻也最裸：备份、退浏览器、删 checksum、写 UTF-8 全靠 AI 临场做对</td>
</tr>
</table>

判定逻辑写死在 `SKILL.md` 里：工作区有 `scripts/bm.py` → 一律走脚本（**默认**），有脚本却手改 JSON = 丢掉护栏，禁止；没有 → 自动降级仅提示词；只是临时体验 → 用 `PROMPT.md`。

---

## 🔁 核心流程：只有 `finalize` 真正写回

<p align="center">
<b>① 定位</b> → <b>② 体检</b> → <b>③ 底牌</b> → <b>④ 读结构</b> → 🔄 <b>⑤ 循环改方案</b>（<sub>全程不动真身</sub>）→ <b>⑥ 写回</b> → <b>⑦ 校验验收</b>
</p>

只有 `finalize` 一步会真正改文件，其余都在内存 / 候选文件里折腾。

![0→7 带循环主流程：只有 finalize 真正写回，不满意走 restore 回到底牌](./docs/workflow.svg)

---

## 🧰 工具箱 `scripts/bm.py`

10 个子命令 · 单文件 · 零第三方依赖。<kbd>🔒 只读</kbd> 不碰真身，<kbd>✍️ 写</kbd> 会改文件（带安全闸）。

| | 命令 | 作用 |
|---|---|---|
| 🔒 | `detect` | 按 OS 环境变量自动定位各浏览器 Profile 的 Bookmarks（**根路径不写死**，跨 Win/mac/Linux） |
| 🔒 | `preflight` | 只读体检：存在/可读写/JSON 合法/**浏览器进程**/**Profile 是否被占用锁**/**是否开着云端同步** → 给 **GO/NO-GO** |
| 🔒 | `backup` | 改前时间戳底牌 + sha256 校验 + 打印**可直接粘贴运行**的还原命令（绝对路径） |
| 🔒 | `show` | 打印真实结构（目录树/数量/重复 id/重复 URL/checksum）；`--depth N` 只看 N 层、`--stats` 只看体检。重复 URL 会**标出同目录还是跨目录** |
| 🔒 | `plan` | 内存里按 `--sort/--dedup` 重排到候选文件，**绝不碰原文件** |
| 🔒 | `preview` | 渲染成**本地嵌套树 HTML**（`<details>` 可折叠、无 JS），双击肉眼核对；`--base` 附「删/增/移动/改名/副本减少」差异 |
| 🔒 | `diff` | **路径感知**对账：除增/删 URL 外，还能识别**移动**（同名链接换目录）、改名、副本减少（删掉多份同名同链中的一份） |
| ✍️ | `finalize` | **唯一动真身**：先验候选与**目标**合法性（目标解析不出 `roots` 也拒，防误盖别的文件）+ 删 checksum + 改名陈旧 `.bak` + **原子写回**（先 .tmp 再 replace）；浏览器在跑/Profile 被占用拒绝（除非 `--force`），写前自动再兜一份；**`--from` 与 `--target` 同一文件则拒（防自我覆盖）**；**候选 0 条拒绝、条数暴跌 <50% 告警**（防 AI 改丢书签） |
| 🔒 | `verify` | JSON 合法性 + 结构合法 + id 唯一 + 数量对账；传 `--before` 时额外给出**变更分类**（删/增/移动/改名/副本减少），与 `diff` 同口径 |
| ✍️ | `restore` | 回退到底牌那一刻；与 `finalize` 同级安全闸（浏览器在跑拒绝）并自动兜底；**覆盖前先校验底牌**，坏底牌不碰真身 |

---

## 🛡️ 安全设计

<sub>为什么敢让它动你的真实数据。</sub>

| | 护栏 | 说明 |
|---|---|---|
| 🪂 | **写操作一律先兜底** | `finalize` 会在写回前自动复制一份 `prescript`，`restore` 也会兜一份 `prerestore`——漏做 `backup` 也不至于裸奔 |
| 🔐 | **两个写操作同等级的安全闸** | `preflight`/`finalize`/`restore` 都有两道防线：① 进程名检测（tasklist/pgrep）；② **Profile 占用锁**（`SingletonLock` 等存在即拒）。后者能回答进程名答不了的关键问题：**跑着的浏览器用的是不是这一个 Profile**，多 Profile 机器上尤其重要 |
| ⚛️ | **写回是原子的** | 先落 `.tmp` 再 `os.replace`，不会留下「半个 JSON」；候选结构非法（`roots` 缺失等）直接拒绝写回 |
| 👁️ | **预览先行** | 任何写回前，先把结构渲染成本地 HTML（目录可折叠）让你肉眼核对；预览和浏览器看到的一致，才证明脚本可信 |
| ✋ | **不自作主张删** | 去重只在同目录内合并，跨目录同链接保留；`show` 会把每条重复标成「同目录（会去重）」还是「跨目录（不去重）」，不让你猜 |
| 🔌 | **全程离线** | 本地、零依赖，不联网、不上传 |

---

## ✅ 第一次用不敢放心？三层自查

不要靠「相信某个工具」，按这三步自己验：

1. **先在假数据上跑一遍** —— `scripts/test/sample/` 是随仓库入库的**通用站点演示样例**（before 乱放 40 条 / after 归好 38 条，全是淘宝、GitHub 这类公开站点，零隐私），跑完整个流程也碰不到你的真实数据——`diff` 的预期输出写在 `sample/README.md` 里，可以先对着看。
2. **`plan` / `preview` / `diff` 一个字节都不写进真身** —— 可以无限次预览到满意为止；`finalize` 是唯一写入口，且必须你明确拍板后才执行。
3. **`backup` 会当场打印一行 `restore_cmd`**（绝对路径）—— 这行命令在你看到它的那一刻就生效了，先把它复制到记事本存好，再继续往下走。

> [!WARNING]
> **云端不是备份，是复制品。**
> Chrome 书签同步是**合并**，本地的删除会跟着传播到所有设备——`preflight` 会在体检时点出这一点。唯一的保险始终是磁盘上那份底牌。
> 同理，`restore` 的语义是**回退到底牌那一刻**，不是「只撤销最后一步」——底牌拍摄之后由其他设备同步来的书签也会被一并退回，所以尽量缩短 `backup → finalize` 的间隔。
> 详见 [阶梯式验收](MAINTENANCE.md#7-真实场景验收阶梯第一次动真-profile-之前)。

---

## ⚡ 快速上手

<details open>
<summary><b>① 技能 + 脚本</b> <img src="https://img.shields.io/badge/%E9%BB%98%E8%AE%A4%20%C2%B7%20%E6%8E%A8%E8%8D%90-34a853?style=flat-square" alt="默认 · 推荐" valign="middle"> — 先 clone 本仓库</summary>

```bash
python scripts/bm.py detect                              # 找到要整理哪个
python scripts/bm.py preflight --file "<Bookmarks>"      # GO/NO-GO
python scripts/bm.py backup    --file "<Bookmarks>"      # 底牌
python scripts/bm.py show      --file "<Bookmarks>"      # 读准结构
python scripts/bm.py plan      --file "<Bookmarks>" --out cand --sort --dedup
python scripts/bm.py preview   --file cand --base "<Bookmarks>" --out preview.html
# 满意后（浏览器已退出）：
python scripts/bm.py finalize  --from cand --target "<Bookmarks>"
python scripts/bm.py verify    --file "<Bookmarks>" --before "<底牌>"
# 不满意：
python scripts/bm.py restore   --backup "<底牌>" --target "<Bookmarks>"
```

</details>

<details>
<summary><b>② 仅技能</b> <img src="https://img.shields.io/badge/%E6%97%A0%E8%84%9A%E6%9C%AC%E9%99%8D%E7%BA%A7-94a3b8?style=flat-square" alt="无脚本降级" valign="middle">（不下载仓库）</summary>

把 `SKILL.md` 加载给 AI，说「帮我整理书签」。AI 会走仅提示词流程——先定位文件、请你关浏览器、自己拷一份备份、改完请你重启验收。细则见 `SKILL.md`「仅提示词时怎么做」。

</details>

<details>
<summary><b>③ 纯提示词</b> <img src="https://img.shields.io/badge/%E9%9B%B6%E5%AE%89%E8%A3%85-f5a623?style=flat-square" alt="零安装" valign="middle">（不下载仓库、不装技能）</summary>

打开 [`PROMPT.md`](PROMPT.md)，把里面代码块整段复制给任意 AI，再补一句「我的书签文件路径是 ……」即可。

</details>

---

## 🧪 回归测试

<sub>改动 `bm.py` 后必跑。</sub>

```bash
python scripts/test/run_tests.py     # 54 项，零第三方依赖，约 1 秒
```

它锁的是**安全不变量**，不是覆盖率：去重是否保留最新、跨目录是否被误删、`plan` 有没有写过源文件、两个安全闸（含 Profile 占用锁）是否还拦得住、写回是否原子、结构闸门是否还生效、移动/改名/副本减少的分类对不对、**每个命令最省参数的组合还能不能跑到底**，以及**脏输入边界**——超大门户时间戳、非 UTF-8 垃圾文件、含引号/尖括号的名称与 URL、残缺节点结构都不会让脚本崩成「未预期错误」。

最后这条不是凑数的：`preview` 不带 `--base` 时曾因变量缺初值直接崩溃，藏了两个版本没人发现——因为手工验证时总带着 `--base`。现在 `TestMinimumArgumentPaths` 会把每种最小参数组合都跑一遍。

这套断言做过变异验证：故意把「保留最新一条」改反，测试立刻变红——它是真的有约束力，不是摆设。`.github/workflows/test.yml` 会在 **Windows / macOS / Linux × Python 3.9 / 3.11** 上跑同一套。

---

## 📁 仓库结构

<details>
<summary><b>展开完整结构（10 个顶层项）</b></summary>

| 路径 | 说明 |
|---|---|
| `PROMPT.md` | **零安装轻路径**：一段可直接复制给任意 AI 的纯文本提示词（`SKILL.md` 流程的压缩版，**无闸门**）。不 clone、一次性、想先体验或分享时用它 |
| `SKILL.md` | 给 AI 看的操作规范（默认脚本 + 无脚本降级 + 流程 + Pitfalls + 验证）。可单独加载当提示词，不必下载整仓 |
| `scripts/bm.py` | 上述工具箱（单文件、零第三方依赖，10 个子命令） |
| `scripts/visualization/` | 可视化资产的**共享主题 + 生成/同步脚本**（零第三方依赖） |
| `docs/` | **GitHub Pages 部署源**（经典模式 `main/docs`）：示意图成品 + 社交卡片 + 全景观览站副本 + `.nojekyll` |
| `project_overview/` | **项目全景观览站源目录**：静态多文件单页（11 章节、深浅色主题、内联 SVG、图表），`docs/` 是其部署副本 |
| `scripts/test/sample/` | **入库**的通用站点演示样例：真实公开网站合成的 before（乱 40 条）/ after（归好 38 条）一对 + 生成脚本，零隐私、`clone` 后立刻有靶子可练 |
| `scripts/test/run_tests.py` | 零依赖回归测试（54 项），改完 `bm.py` 请跑它 |
| `scripts/test/` | **不入库**的真实书签快照（裁剪过的 `Bookmarks.before`/`after`，含隐私，已被 `.gitignore` 屏蔽），本地验证脚本手感用 |
| `MAINTENANCE.md` | 长期维护文档：**AI 判断 vs 脚本执行**的分工合同、脚本质量台账、边界矩阵、变更日志 |

</details>

<details>
<summary><b>scripts/visualization/ 内部结构</b> — 视觉真源，改配色只改 <code>theme.py</code></summary>

- `theme.py` — 全仓视觉主题：Chrome 四色语义色板、字体栈、**明暗自适应**（`prefers-color-scheme`）、通用绘制件（chip / box / 箭头 / 标签）。改配色只改这里，所有 SVG 同步生效。
- `generate_workflow.py` / `generate_deliverables.py` / `generate_social_preview.py` — 生成 `docs/*.svg`（双写到 `project_overview/assets/`，站点与 README 共用同一份）。
- `sync_pages.py` — 把 `project_overview/` 同步成 `docs/` 部署副本。
- 图上文案或站点内容有变时，改脚本后重跑即可再生成，不要手改 SVG / 手工 cp。

</details>

<sub><code>social-preview.svg</code> 需到仓库 <b>Settings → Social preview</b> 手动上传一次。<code>docs/</code> 由 <code>scripts/visualization/</code> 生成并入库。GitHub Pages 走经典模式部署（<code>build_type=legacy</code>，<code>source=main/docs</code>），不依赖 Actions——push main 后自动构建 <code>docs/</code> 发布到 Pages，不是 skill 运行时的组成部分。在线预览：<a href="https://lpk3215.github.io/chrome-bookmarks-organize/">lpk3215.github.io/chrome-bookmarks-organize</a>。<code>.github/workflows/pages.yml</code> 是已禁用的备用 workflow。</sub>

---

## ⚠️ 使用前提（硬性）

> [!CAUTION]
> 1. **整理真实书签时浏览器必须完全退出**（含托盘后台）—— 这是机制限制。脚本模式由 `preflight`/`finalize` 拦截；仅提示词模式没有自动探测，必须开口确认。
> 2. 整理规则先与 AI 确认，**不自作主张删除任何一条书签**。

---

## 📍 文件位置速查

<sub>也可直接 `detect` 自动找。</sub>

| 浏览器 | Bookmarks 路径 |
|---|---|
| Chrome (Windows) | `%LOCALAPPDATA%\Google\Chrome\User Data\<Profile>\Bookmarks` |
| Edge (Windows) | `%LOCALAPPDATA%\Microsoft\Edge\User Data\<Profile>\Bookmarks` |
| Chrome (macOS) | `~/Library/Application Support/Google/Chrome/<Profile>/Bookmarks`（无 `User Data` 层） |
| Chrome (Linux) | `~/.config/google-chrome/<Profile>/Bookmarks` |

> [!NOTE]
> `<Profile>` 通常为 `Default`，多用户是 `Profile 1`…；`detect` 还能识别 Chromium / Brave / Vivaldi / Opera。

---

## 🚧 已知边界

- 没有「热编辑」：改文件时浏览器必须关着。
- `date_added` 是 Chrome 时间戳（自 1601-01-01 的微秒），`bm.py` 已自动转日期。
- 只管结构整理，不判断链接是否失效 / 内容好坏。
- `detect` 的 macOS / Linux 分支与更多浏览器内核已实现，但**尚未在非 Windows 机器上实测**。

---

## ❓ FAQ

<details>
<summary><b>为什么一定要先关掉浏览器？</b></summary>

浏览器运行时书签缓存在内存里，退出时才写盘；没退干净就改 = 白改（退出时旧数据覆盖磁盘）。这是机制限制，不是脚本矫情。

</details>

<details>
<summary><b>改完重启了，结构没变？</b></summary>

按顺序排查：① 改的是不是当前在用的 Profile（多 Profile 机器最常见）；② 有没有被 `Bookmarks.bak` 静默回滚（脚本已自动改名 `.stale-*`）；③ `finalize` 的 `--target` 是不是真的指向那个 `Bookmarks`。

</details>

<details>
<summary><b>开着云端同步安全吗？</b></summary>

同步是**合并**不是备份：本地的删除会传播到所有设备。`preflight` 会点出这一点，但唯一的保险是磁盘上那份底牌——不要靠「反正云端还有一份」。

</details>

<details>
<summary><b><code>restore</code> 会把我后来新增的书签弄丢吗？</b></summary>

会。它的语义是*回退到底牌那一刻*，底牌拍摄之后（包括其他设备同步过来的）新增会被一并退回。所以尽量缩短 `backup → finalize` 的间隔。

</details>

<details>
<summary><b>不 clone 仓库能用吗？</b></summary>

能。把 [`PROMPT.md`](PROMPT.md) 整段复制给任意 AI，或只加载 [`SKILL.md`](SKILL.md)。但这两条路没有脚本闸门，正式整理真实书签请 clone 后走 `scripts/bm.py`。

</details>

<details>
<summary><b>支持哪些浏览器？</b></summary>

Chrome / Edge 为主，`detect` 另覆盖 Chromium / Brave / Vivaldi / Opera。macOS / Linux 的路径分支已实现但尚未在非 Windows 机器上实测。

</details>

<details>
<summary><b>能自动判断链接是否失效吗？</b></summary>

不能。本项目只做**结构整理**——归类、重排、改名、去重、排序；是否删除某条失效链接由你拍板。

</details>

<details>
<summary><b>为什么要三份交付物，一段提示词不就够？</b></summary>

一次整理够用，长期整理要的是*不翻车*。三份是同一套逻辑的三个台阶：轻（提示词）→ 纪律（SKILL）→ 闸门（脚本）。详见上文「为什么做这个」。

</details>

---

## 📌 最近更新

<table>
<tr><td width="70" valign="top"><b>v1.14.4</b></td>
<td valign="top">README 排版系统重构：顶部居中 Hero（统一 <code>flat-square</code> 徽章 + 导航行）、三栏目录、中文对齐永不崩的 HTML 对比表（替换原 ASCII 块）、流程步进条、GitHub 原生告警块（<code>[!IMPORTANT]</code> / <code>[!WARNING]</code> / <code>[!CAUTION]</code> / <code>[!NOTE]</code>）、命令表读/写标记、FAQ 与仓库结构折叠。内容为纯排版改动，一字未删。行为零变化，54 项回归不增删。</td></tr>
<tr><td width="70" valign="top"><b>v1.14.3</b></td>
<td valign="top">展示资产统一换肤：抽出共享主题 <code>scripts/visualization/theme.py</code>（配色 / 字体 / 明暗自适应 / 通用绘制件），<code>workflow.svg</code> 与 <code>deliverables.svg</code> 按同一套视觉语言重绘，新增 <code>docs/social-preview.svg</code>（GitHub 社交卡片）与其生成脚本；全景观览页「架构」章新增示意图折叠区，与 README 共用同一份资产。</td></tr>
<tr><td width="70" valign="top"><b>v1.14.2</b></td>
<td valign="top">项目全景观览站重写为多文件结构（11 章节、深浅色主题、内联 SVG 架构 / 流程图、回归增长与样例分布图表）；新增 <code>scripts/visualization/sync_pages.py</code> 把 <code>project_overview/</code> 同步到 <code>docs/</code>。</td></tr>
</table>

<sub>完整变更历史见 <a href="MAINTENANCE.md#8-变更日志">MAINTENANCE.md §8 变更日志</a>。</sub>

---

## 👤 作者

**LPK3215** — <17538703215@163.com> · GitHub [@LPK3215](https://github.com/LPK3215)

欢迎提 Issue 反馈真实场景（尤其是 macOS / Linux 上的 `detect` 实测结果，以及更多 Chromium 内核的路径验证）。

---

## 📄 License

[MIT](LICENSE) © 2026 LPK3215
