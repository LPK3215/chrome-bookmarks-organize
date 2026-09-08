---
name: chrome-bookmarks-organize
description: 直接编辑 Chrome/Edge 的 Bookmarks JSON 文件，让 AI 整理浏览器书签（重排目录/改名/去重/排序），完全绕开"导出HTML→导入"的重复追加问题。用户要求整理收藏夹、批量修改书签结构时使用。
version: 1.4.0
---

# Chrome 书签直改整理

## 原理

浏览器书签底层是纯 JSON 文件（无加密）。直接改文件 = 改正式数据，重启浏览器后生效，开启同步时自动同步到账号。**唯一硬性要求：浏览器必须完全退出后再改**——运行时书签缓存在内存里，退出时会用旧数据覆盖磁盘上的修改。

配套一个离线、零第三方依赖的小工具 `scripts/bm.py`（Python 3，仅需标准库）。**流程不是直线跑到底，而是"读准结构 →〔反复沟通改方案，全程不动真身〕→ 确认后才写回 → 校验 → 不满意一键还原回循环"**。只有 `finalize` 一步会真正改文件，其余都在内存/候选文件里折腾。

## 步骤

> **路径不写死**：先跑 `python scripts/bm.py detect` 让脚本按当前 OS 的环境变量自动定位所有 Profile 的 `Bookmarks`（列修改时间 / url 数 / 标"疑似在用"，并从 `Local State` 读出 Profile 显示名），**与用户确认整理哪一个**再往下。若浏览器用 `--user-data-dir` 挪过位置：`python scripts/bm.py detect --root "<你的根>"`，或给任何命令直接显式传 `--file`。
> 原理（"相对死"而非"直接死"）：`Bookmarks` 这个文件名 + `<根>/<Profile>/Bookmarks` 的相对结构是 Chrome 固定契约，用户改不了，故写死合理；唯一会变的是"根"——Windows `%LOCALAPPDATA%`、macOS `~/Library/Application Support`、Linux `~/.config`——交给 `detect` 从环境变量探，不烙进脚本。手动兜底路径：Chrome(Windows) `%LOCALAPPDATA%\Google\Chrome\User Data\<Profile>\Bookmarks`（Edge 把 `Google\Chrome` 换 `Microsoft\Edge`；macOS 在 `.../Google/Chrome/<Profile>/Bookmarks`、无 `User Data` 层）。本仓 `scripts/test/` 是常驻对比测试案例（原版/修改后两份数据 + 两份预览，见其 README，含隐私不入库）。

0. **定位 + 体检（GO/NO-GO 闸门）**
   - 定位：`python scripts/bm.py detect`（按 OS 环境变量扫出候选，标"疑似在用"）→ 与用户确认整理哪一个，得到 `<Bookmarks>`。
   - 体检：`python scripts/bm.py preflight --file "<Bookmarks>"`（**只读**）→ 检查文件存在/可读可写/JSON 合法/是否有 `.bak`/**浏览器是否在跑**，末行给 `GO ✅` 或 `NO-GO`。
   - **NO-GO 不许往下走**。浏览器没退干净＝白改（退出时内存旧数据覆盖磁盘）；preflight 报"浏览器在跑"就让用户彻底退出（含托盘后台）再重跑。

1. **备份底牌**（并把备份路径与还原命令记清告知用户）
   `python scripts/bm.py backup --file "<Bookmarks>"`
   → 生成同目录时间戳底牌 `Bookmarks.backup-<时间>`，打印 `sha256 / url 数量 / restore_cmd`，并追加到 `_backup_manifest.txt`。这是还原底牌，**不等于** Chrome 自动维护的 `Bookmarks.bak`。

2. **读取真实结构（地基，不能读错）**
   `python scripts/bm.py show --file "<Bookmarks>"`
   → 打印目录树、url 总数、重复 id、重复 URL、是否带 checksum。**把结构呈现给用户、由其确认"对，这就是我现在的书签"** 再往下；地基歪了方案必歪。

3. **【循环区 · 绝不碰原文件 · 可反复】** 定/调方案 → 内存重排 → 预览 → 用户再看再提，直到用户**明确拍板"就这版"**：
   - 重排到候选：`python scripts/bm.py plan --file "<Bookmarks>" --out "<候选>" --sort --dedup`（原文件不动；`--sort` 目录优先按名排、`--dedup` 仅在**同目录内**按 url 去重保留最新）
   - 肉眼核对：`python scripts/bm.py preview --file "<候选>" --base "<Bookmarks>" --out preview.html` → 双击 `preview.html`，顶部看结构、底部看与原版"增/删"差异
   - 不满意就换规则/改需求**重跑本步**，这一步没有次数上限。归类规则、哪些删、哪些合并，全部在此与用户确认，**不自作主张删任何一条**。

4. **【唯一动真身 · 未获第 3 步"就这版"前禁止执行】**
   `python scripts/bm.py finalize --from "<候选>" --target "<Bookmarks>"`
   → 删除顶层 `checksum`（改数据后校验和必失配，删掉 Chrome 会自动重建、不报错）+ 把陈旧 `Bookmarks.bak` 改名 `.stale-*`（防加载时静默回滚）+ 原地写回候选。
   → **内置双保险**：finalize 自己会再查一次浏览器进程，在跑就拒绝（除非 `--force`）；写回前自动把当前真身兜一份 `<target>.prescript-<时间>`，即使用户漏了第 1 步也能救；写失败（只读/被占用）给一句人话而非崩栈。

5. **机器校验**
   `python scripts/bm.py verify --file "<Bookmarks>" --before "<第1步底牌>"`
   → 三项：JSON 合法、结构合法（folder 有 `children`、url 有非空 `url`、id 全树唯一）、数量对账（改动前后差额应＝去重数）。
   → 想逐条看增删：`python scripts/bm.py diff --a "<第1步底牌>" --b "<Bookmarks>"` 列出被删/新增的具体 URL。

6. **重开浏览器验收**：结构生效、书签能正常打开。前面对话没退浏览器/没重启验过的都不算数。

7. **定夺**：
   - 不满意 → `python scripts/bm.py restore --backup "<第1步底牌>" --target "<Bookmarks>"` 一键回退到底牌那一刻（**语义不是"只撤销最后一步"**，见 Pitfalls），**回到第 3 步继续循环**。
   - 满意 → 清理 `preview.html`/候选等临时产物；底牌保留一段时间确认稳了再清。

## Pitfalls

- **第 3 步是循环，不是直线**：AI 不得按字面顺序一路冲到写回。没拿到用户明确的"就这版"，绝不执行第 4 步 `finalize`。
- 浏览器没退干净 = 白改（退出时被内存旧数据覆盖，最常见失败原因）。**现由 `preflight`/`finalize` 自动拦截**（检测到 chrome/edge 等在跑即拒绝）；确已退出仍被拦才用 `--force`，平时别拿它绕闸。
- **动手前先 `preflight`**：它给 GO/NO-GO；NO-GO（文件缺失/损坏/只读/浏览器在跑）一律先解决再往下，别硬跑 backup/finalize。
- 目标文件**只读或被占用**时，`preflight` 会标"不可写"、`finalize` 写失败给一句人话并保留自动兜底件，不会把真身写坏。
- **路径不写死**：靠 `detect` 从 OS 环境变量解析（跨 Win/mac/Linux、换用户名）；用户用 `--user-data-dir` 挪过位置就 `detect --root`，或任何命令直接传 `--file`。绝不把 `C:\Users\某名\...` 烙进脚本或文档。
- **自建底牌 ≠ `Bookmarks.bak`**：后者是 Chrome 自动备份，改数据若有瑕疵时会被用来**静默回滚**，让你以为改的东西丢了；`finalize` 已主动把它改名，别手动恢复它。
- checksum 不要试图重算，删字段最稳（`finalize` 已代劳）。
- 动手前必须先 `backup` 并**把底牌路径与 `restore_cmd` 告知用户**；改坏了用它退回即可（即便漏了这步，`finalize` 也会自动兜一份 prescript）。
- **`restore` 是"回退到底牌那一刻"，不是"只撤销最后一步"**：若开了浏览器同步，底牌拍摄之后由其他设备同步过来的书签会被**一并退回**。所以尽量缩短 `backup → finalize` 的间隔——别昨晚备份、今晚才写回。
- 去重只在同目录内合并重复链接，跨目录同链接保留（Chrome 允许一条归多处，跨目录删＝误伤）。
- 多 Profile 机器改错 Profile 是常见事故，先确认哪个在用。
- `date_added` 是 Chrome 时间戳（自 1601-01-01 的微秒），`bm.py` 已自动转成日期显示，勿手推。

## Verification

- 第 5 步 `verify` 三项全绿，且 `--before` 对账差额＝预期去重数。
- 用户重启 Chrome/Edge 后结构生效、链接可点。
- 改真实数据前，先在 `scripts/test/`（对比案例）上把 `preflight→backup→show→plan→preview→finalize→verify→diff→restore` 整条跑一遍，确认手感再上。
