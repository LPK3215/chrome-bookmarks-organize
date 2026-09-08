# MAINTENANCE — AI/脚本分工合同 & 脚本质量台账

> 这份文档**长期维护**：每次改 `SKILL.md` 的流程、或改/加 `scripts/bm.py` 的子命令后，回来更新第 2、3、5 节。它回答三个问题：**什么动作归 AI 判断、什么动作归脚本执行、脚本现在写得对不对。**

## 1. 一条主线

书签整理 = 一份"分工合同"：
- **判断题 → AI 做**（每次临场定，写在 `SKILL.md`，不固化）：需要常识/语境/品味/跟用户拉扯的。
- **算术题 → 脚本做**（一次写对永久对，锁进 `bm.py`）：有唯一机械答案、不容手滑的。
- **接缝 = 命令行参数**：AI 决定"选哪个开关、传什么路径"，脚本保证"这个开关的执行永远一致"。例：*要不要去重 / 跨目录同链接算不算重复*是 AI 的判断；`--dedup` 一旦按下，*遍历、比 `date_added` 取最新、删多余节点*全是脚本的活。

`SKILL.md` 本身就是提示词，可单独加载（联网装 skill 即可，不必下载仓库）。无 `bm.py` 时 AI 走「仅提示词」硬约束自己读写 JSON；有脚本时禁止手改真身，判断仍归 AI、执行锁进脚本。脚本模式在安全/准确/合法/一致性上更强，所以推荐下载仓库再整理真实书签。

## 2. 分工总表

| 流程环节 | AI 做动作（判断，写进 SKILL） | 脚本做动作（确定性，bm.py） |
|---|---|---|
| 前置 | 判定"整理哪一个" Profile、看到 NO-GO 时决定怎么排除 | `detect` 扫候选（根路径不写死）+ `preflight` 体检（存在/读写/JSON/浏览器在跑）给 GO/NO-GO |
| 1 备份 | 决定底牌放哪、把路径+还原命令讲清 | `backup`：打时间戳、算 sha256、记 manifest |
| 2 读结构 | **判读**"这结构对不对、是不是用户当前的书签"并请用户确认 | `show`：解析、转日期、数 url/查重复 id |
| 3 循环区 | **核心判断全在这**：怎么归类、哪些并/删/改名、用哪些规则、够不够好、何时可进第 4 步 | `plan`(只执行给定规则、只写候选不碰原文件) / `preview`(渲染 HTML 供肉眼核) |
| 4 写回 | 仅在用户"就这版"后才触发；决定 finalize 的 `--from/--target` | `finalize`：查浏览器在跑即拒(除非--force) + 自动 prescript 兜底 + 删 checksum + 改名陈旧 .bak + UTF-8 写回（唯一动真身） |
| 5 校验 | 判断对账差额是否等于预期、异常要不要回滚 | `verify`（JSON合法+结构+id唯一+数量对账）+ `diff`（逐条列增/删 URL） |
| 6 验收 | 提示用户重启浏览器核对 | ——（要人开浏览器看） |
| 7 定夺 | 决定还原还是清垃圾；保留底牌多久 | `restore`：一键用底牌盖回并复验可解析 |

## 3. 脚本质量台账（每次维护更新"最近核验"列）

| 子命令 | 职责 | 已核验内容 | 最近核验 | 待办/存疑 |
|---|---|---|---|---|
| detect | 按 OS 环境变量自动定位 Bookmarks | 本机重探到 Chrome Default/Profile 1、Edge Default；mtime 排序、"疑似在用"标记、`Local State` 显示名「LPK」均对；`--browser edge` 过滤有效 | 2026-09-08 | 已扩 Chromium/Brave/Vivaldi/Opera 根（**mac/linux 未在本机验**）；"整块 AppData 挪别的盘"仍需 `--root` |
| preflight | 只读体检 → GO/NO-GO | Chrome 开着时正确判 NO-GO(浏览器在跑)、rc=2；chmod 444 时正确判"不可写"NO-GO；缺文件/损坏 JSON 均报 NO-GO | 2026-09-08 | 进程探测靠 tasklist/pgrep，探测不可用时只告警不阻断（交由 finalize） |
| backup | 底牌+manifest | 微秒时间戳防同秒碰撞 + 复制后 sha256 校验（不一致即丢弃并报错）；**`restore_cmd` 已改绝对路径**（解释器+脚本+底牌+目标），任何目录下可直接粘贴运行；源 JSON 损坏时仍会留下底牌与记录，不会被异常吞掉 | 2026-09-08 | 真实文件仅做只读快照，未跑写操作（符合预期） |
| show | 读结构+体检 | 新增 `--depth N`（只打到第 N 层）/ `--stats`（只看体检）；>300 条自动提醒改用这两个开关；重复 URL **逐条标注「同目录→会被去重」还是「跨目录→保留」**，消除"AI 拿着全树重复表向用户承诺去重"的误判；重复 id 改用 Counter 一次扫出（原 O(n²) 写法已删）；缺 `roots` 给干净中文而非 KeyError | 2026-09-08 | 排序为 Unicode 码点序，非中文拼音序（需 locale/第三方库，暂搁） |
| plan | 内存重排到候选 | sort+dedup 跑通，原文件 0 改动已证明；真实快照 3276→3275（并掉 1 条同目录重复） | 2026-09-08 | 仅 `--sort/--dedup`；改名/移动/新建目录尚未脚本化（暂靠 AI 改 JSON） |
| preview | 本地HTML嵌套树预览 | 真·嵌套 `<ul>` 树；**目录可折叠（原生 `<details>`，无 JS）**；`--base` 差异区已与 `diff` 共用同一套分类（删/增/移动/改名/副本减少，按颜色区分） | 2026-09-08 | 折叠默认全展开；如需"默认收起深层"再加开关 |
| diff | 两份书签增删对账 | **重写为「路径+名称+链接」的多重集比对**：能区分真删除/真新增/**移动**/改名/**副本减少**，并把 `(名称,链接)` 仍在对方的条目判为"副本减少"而非"删除"；新增路徑有助于发现"纯整理目录"这种过去会报"删0/增0"的场景 | 2026-09-08 | 改名+移动同时发生时，按"先配改名再配移动"的顺序处理，极端多重重名场景可能配对次序不理想（暂未发现误判） |
| finalize | 唯一动真身 | Chrome 开着拒绝（rc=1）；`--force` 放行 + 自动 prescript 兜底 + 改名陈旧 .bak；**新增：写回前先验候选结构（缺 roots/三根之一即拒），并先验目标（目标存在却解析不出 roots 即拒，防 `--target` 指错盖到别的文件，需 `--force` 放行）**；**写回改为先落 `.tmp` 再 `os.replace` 的原子替换**，中途失败不再留下半个 JSON；安全闸与本表 restore 共用同一实现 | 2026-09-08 | 真实浏览器 Profile 仍未 finalize（测试期只打临时目录副本） |
| verify | 校验+对账 | 合成+真实文件跑通；BOM 文件也能读；损坏 JSON 自身捕获报错；**`--before` 现在额外输出"变更分类"（删/增/移动/改名/副本减少）**，与 `diff` 同口径；`--before` 读不出时给告警而非崩 | 2026-09-08 | `--before` 依赖用户传对底牌路径；发现问题只报告不自动回滚 |
| restore | 回退到底牌那一刻 | **补齐与 finalize 同级的安全闸**：浏览器在跑即拒（需 `--force`）+ 自动 `prerestore` 兜底当前状态；输出明确"回退到底牌拍摄时刻"及同步场景提醒 | 2026-09-08 | 还原后 `.bak.stale-*`/`.prescript-*` 不自动清理，是否纳入待定；同步窗口期内他端新增书签会被一并退回（已写进 SKILL Pitfalls） |

## 4. 已知边界与坑（喂给 SKILL 的 Pitfalls，此处记技术成因）

- **浏览器没退干净 = 白改**：内存旧数据退出时覆盖磁盘。**现由 `preflight`/`finalize` 用 tasklist(Windows)/pgrep(mac/linux) 自动检测并拒绝**；仅当探测工具不可用时降级为告警（此时靠第 0 步人确认）。
- **`Bookmarks.bak` ≠ 自建底牌**：前者 Chrome 自动维护，改数据有瑕疵时会用它**静默回滚**；`finalize` 主动改名 `.stale-*` 堵死。
- **去重只在同目录内**：跨目录同链接保留（Chrome 允许一条归多处）。这是 `plan` 的既定策略，非 bug。
- **Windows 控制台 GBK**：`bm.py` 顶部把 **stdout 与 stderr 都** `reconfigure(utf-8)`——因为 `sys.exit()` 的报错走 stderr，之前只切 stdout 会让中文拒绝信息乱码（本会话发现并修复）。任何临时内联脚本打印中文/emoji 前也要切，否则崩。
- **date_added**：自 1601-01-01 的微秒，`chrome_ts_to_date` 已统一转换。

## 5. 边界矩阵（设备 / 场景 / 意外 × 脚本怎么扛 × 是否已验）

| 场景 / 意外 | 脚本对策 | 已验状态 |
|---|---|---|
| 不同 OS（Win/mac/Linux）根不同 | `detect` 按 `platform` 分支 + 读环境变量 | Win ✅；mac/linux 代码分支未在本机验 |
| 多 Chromium 内核（Chrome/Edge/Chromium/Brave/Vivaldi/Opera） | `detect` 覆盖各家根路径 | Chrome/Edge ✅；余者根未本机验 |
| 用户用 `--user-data-dir` 挪了位置 | `detect --root` 或任何命令直接 `--file` | 逻辑就位 |
| 浏览器没装 / 找不到文件 | `detect` 空结果给提示；`preflight` NO-GO | ✅（缺文件已验） |
| **浏览器没退就写回** | `preflight` 检测进程 NO-GO；`finalize` 拒绝（除非 `--force`） | ✅（Chrome 开着→拒） |
| 文件缺失 / 路径错 | `load` 抛 `FileNotFoundError`→`main` 干净中文；`preflight` NO-GO | ✅ |
| JSON 已损坏 / 半写 | `main` 兜底 + `verify` 捕获报错，不崩栈 | ✅ |
| 文件带 UTF-8 BOM | `load` 用 `utf-8-sig` 容忍 | ✅ |
| 目标只读 / 无权限 | `preflight` 标"不可写"；`finalize` 写失败给人话且保留兜底件 | ✅（chmod 444 已验） |
| 陈旧 `Bookmarks.bak` 会回滚 | `finalize` 改名 `.stale-*` | ✅ |
| 漏做备份就想写回 | `finalize` 自动 `prescript` 兜底当前真身 | ✅ |
| 备份同秒碰撞 | 微秒时间戳 | ✅ |
| 复制不完整（底牌坏） | `backup` 复制后 sha256 校验，不一致即丢弃报错 | 逻辑就位 |
| `finalize` 跑两次（幂等） | 第二次无 `.bak` 可改、checksum 已无，安全 | 逻辑就位 |
| 含 `feature_endpoint` 等新根 | `plan/finalize` 只动已知 roots 子树、整 dict 原样写回，其余键不丢 | 逻辑就位 |
| 超大全树刷屏 | `show --depth N` / `--stats` + >300 条自动提醒 | ✅ |
| Windows 中文控制台乱码 | stdout + stderr 均 `reconfigure(utf-8)` | ✅ |
| **`--target` 指错文件（把候选盖到 Preferences）** | `finalize` 校验目标能解析出 `roots`，否则拒绝，确要覆盖才 `--force` | ✅（有单测） |
| **目标 Profile 开着云端同步，误删会传播** | 脚本管不了浏览器的合并行为 → `preflight` 明确提示（并区分"未发现迹象"而非谎称没开）+ SKILL Pitfalls 写明"云端是复制品不是备份" + 阶梯 L2/L3 要求先做**整个 Profile 目录副本** | 提示已实现；行为保证只能靠阶梯验证 |
| **护栏被后来的改动悄悄破坏** | `scripts/test/run_tests.py` 28 项回归 + CI 三平台；已做变异验证（把去重比较符改反→测试立刻变红） | ✅ |
| **写回写到一半失败（磁盘满/被占用）** | 先写 `.tmp` 再 `os.replace` 原子替换，真身永不为半截 JSON | ✅（代码就位） |
| **候选文件本身是垃圾/结构非法** | `finalize` 先验证 `roots` 与三个根之一，不合法直接拒绝写回 | ✅ |
| **还原时浏览器在跑** | `restore` 与 `finalize` 共用 `_safety_gate`，同样拒绝并提供 `--force` | ✅（Chrome 开着→拒） |
| **clone 后没有任何可用数据** | 新增**入库的合成样例** `scripts/test/sample/`（虚构 18 条 + 生成脚本），真实快照仍被忽略 | ✅ |
| 跨平台行尾打架 | 新增 `.gitattributes`（`* text=auto eol=lf`） | ✅ |
| 装了进程名清单之外的 Chromium 内核浏览器 | 进程名表固定，`--force` 之外会**漏检**（危险方向是漏检不是误报） | 已知风险，建议由人确认 |

## 6. 测试案例 `scripts/test/`（常驻 · 勿删）

本目录住着**两套**数据，别混为一谈：

| 位置 | 性质 | 是否入库 | 用途 |
|---|---|---|---|
| `test/run_tests.py` | 零依赖回归测试（unittest，28 项，~1 秒） | ✅ 入库 | 锁安全不变量；改完 `bm.py` 必跑 |
| `test/sample/` | **纯虚构**合成样例（18 条）+ `make_sample.py` | ✅ 入库 | clone 后立刻有靶子；兼作回归验收基准 |
| `test/Bookmarks.*` | 真实书签裁剪快照（~99 条） | ❌ 被 `.gitignore` 屏蔽 | 本地验证真实结构手感 |

**回归测试怎么组织**：不追求覆盖率，只钉"护栏还在不在"——
`TestFinalizeSafety`（两个安全闸 / 原子写回不留 .tmp / 候选非法不落地 / 目标不是书签文件不盖）、
`TestRestoreSafety`（还原也拒命令行下的浏览器进程 / prerestore 兜底）、
`TestDedupAndSort`（保留最新、跨目录不去重、`plan` 不动源文件）、
`TestDiffClassification`（移动/改名/副本减少/增删）、
`TestDetectRoots`（三平台根路径跟着环境变量走、不许烙死用户名）、
`TestVerifyAndShow`（结构问题检出、`--depth`/`--stats`、跨目录标注）。
浏览器状态一律用 monkeypatch 固定，测试不碰任何真实 Profile。

- **为什么要有 `sample/`**：真实快照含隐私、不入库，若仓库里只留命令文档，clone 的人第一次执行就撞空。`sample/` 埋了同目录重复 / 跨目录重复 / 重复 id / 移动 / 改名 / 增删，一步 `diff` 就能把工具箱的能力全验一遍，预期输出写在 `sample/README.md`。
- **定位**：脚本对不对，先拿 `sample/` 跑一遍、比对输出；一致才允许对真实数据落地。
- **测试铁律**：`finalize` 的 `--target` 永远只指**临时目录里的副本**，绝不指向真实 Chrome/Edge Profile，也不要指向 `test/Bookmarks.*`（那是基准，不是靶子）。真实 Profile 仅在最终正式整理、且浏览器完全退出时才当 target。
- **隐私**：`test/Bookmarks.*` 源自真实书签（虽已裁剪），绝不入库/外推；将来换成彻底脱敏/虚构数据后可解除忽略。详见 `scripts/test/README.md`。

## 7. 真实场景验收阶梯（第一次动真 Profile 之前）

脚本能证明"文件写对了"，但**证明不了浏览器会不会认账**。这部分没有捷径，只能分级试——好消息是：
**前两级的风险是零，而它们已经能回答你绝大部分的担心。**

| 阶梯 | 对象 | 做什么 | 能验证什么 | 风险 |
|---|---|---|---|---|
| **L0 合成样例** | `test/sample/` | 跑完整链路，**不开浏览器** | 脚本逻辑、diff 分类、门禁 | 零 |
| **L1 一次性 Profile** | 新建的临时 Profile | 真实 Chrome 完整跑一遍，**含重启** | **浏览器会不会认账**：重启后结构生效吗、checksum 有没有自动重建、`.bak` 行为、以及最要命的习惯——"彻底退出浏览器再动手" | **零**（里面没有值得丢的东西） |
| **L2 只读动作** | 真实 Profile | 只做 `--sort` 或改一个目录名 | 真实文件权限、多 Profile 识别、同步提示 | 极低（有底牌 + Profile 整目录副本） |
| **L3 完整整理** | 真实 Profile | 去重 / 归类 / 删除 | 全部 | 中（唯一保险＝底牌） |

### L1 怎么做（强烈建议先做这一步）

用 `--user-data-dir` 让 Chrome 在一个**全新的临时目录**里启一个新 Profile：

```bash
# Windows（关掉正在跑的 Chrome 之后）
"C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="C:\bm-drill"
```

在里面随便添加二三十条书签（故意留几条重复链接），**完全退出**，然后走完整流程：

```bash
python scripts/bm.py detect --root "C:\bm-drill"
python scripts/bm.py preflight --file "<探到的 Bookmarks>"
python scripts/bm.py backup    --file "<Bookmarks>"
python scripts/bm.py plan      --file "<Bookmarks>" --out cand --sort --dedup
python scripts/bm.py preview   --file cand --base "<Bookmarks>" --out p.html
python scripts/bm.py finalize  --from cand --target "<Bookmarks>"     # 此时浏览器已退
python scripts/bm.py verify    --file "<Bookmarks>" --before "<底牌>"
```

再**重新打开 Chrome**（同样带 `--user-data-dir`），看结构有没有生效、链接能不能打开。

这一步会得到三样东西，都是 L0 拿不到的：
1. 确认"删字段 + 重启"这条路在你这台机器上走得通；
2. 练熟"必须先彻底退出浏览器"这个最容易翻车的动作；
3. `preflight` 会顺便告诉你这个 Profile 的同步状态提示长什么样。

### L2 / L3 的前提

- **先把整个 Profile 目录复制一份**（`User Data\Default` 整个文件夹，不是只 copy `Bookmarks`）。这比 `bm.py backup` 更彻底，连 `Preferences` 一起保住；几十 MB 到几百 MB 的成本，换的是"最坏情况直接把目录盖回去"。
- **保持浏览器原本的同步状态**，不要为了保险去开关同步——开关本身就会引发数据变动，得不偿失。
- L3 之后别急着关浏览器等着同步：先肉眼核一遍，确认无误再让它同步上去。**一旦同步上线，误删就传播了，那时只能靠底牌 `restore`。**

## 8. 变更日志

- 2026-09-08 v1.1.0：SKILL 线性流程→带循环版；新增 `bm.py` 7 子命令并在合成靶子端到端跑通；加 `.gitignore` 隔离真实快照；建 `_test/chrome-default/` 只读测试目录。
- 2026-09-08 v1.1.1：建 `_test/README.md`，定"验证靶场常驻勿删 + finalize 测试期只打副本"铁律；补本节分工台账。
- 2026-09-08 v1.2.0：加 `detect`——按 OS 环境变量自动定位 Bookmarks（根路径不再写死，`--root` 兜底自定义 user-data-dir）；"定位文件"从 AI 猜升级为脚本确定性动作、人仍负责挑哪个；同步更新 SKILL 第 0 步与本台账。
- 2026-09-08 v1.2.1：`preview` 由 `&nbsp;` 假缩进（长链接一换行层级就塌）重写为真·嵌套 `<ul>` 树（CSS 竖线引导 + 每目录递归条数）。印证分工好处：格式是脚本决定的，改一次、以后每次预览全跟着变。
- 2026-09-08 v1.3.0：为真实世界加固——加 `preflight`(GO/NO-GO 闸门) 与 `diff`；`load` 容错 BOM/缺失、`main()` 统一兜异常；`backup` 微秒时间戳+复制后 sha256 校验；`finalize` 检测浏览器在跑即拒(除非 `--force`)+自动 prescript 兜底+写失败给人话；`detect` 扩 Chromium/Brave/Vivaldi/Opera；**修 stderr 未切 UTF-8 致中文报错乱码的 bug**；跑通边界测试电池；SKILL 升 v1.2.0、preflight 入第 0 步。
- 2026-09-08 v1.3.2：文档对齐——`README` 重写以反映 10 子命令工具箱 + 带循环流程 + detect/preflight，`SKILL` Verification 更新。**在真实导出快照上跑完整 E2E**：preflight 因浏览器开着判 NO-GO；finalize 无 `--force` 被拒、加 `--force` 放行并自动 prescript + 改名 .bak；verify 全绿；diff 在"总数不变(3276→3276)但组成变了"的增删改下仍报"删2/增2"；restore 后与 .bak sha256 一致、满血复原。**结论：工具箱可用。**
- 2026-09-08 v1.4.0：`preview` 目录改为**原生 `<details>` 可折叠**（无 JS）。**结构大清理**：删 `_demo`/`_test`/`_scratch`/`__pycache__`，合并为单一 `scripts/test/` 对比案例——`Bookmarks.before`(真实数据裁剪到 ~99、含 checksum) + `Bookmarks.after`(改名+新增+删除、去 checksum) + `preview-before.html` + `preview-after.html`；同步改 `.gitignore` 与全部文档引用。在裁剪数据上**重跑完整流程全绿**。发现并记录 `diff` 集合语义局限（删重名重链中的一份不计为删除）。
- 2026-09-08：文档写清**两种用法**——仅加载 `SKILL.md` 当提示词（可联网、不下载脚本）vs 下载仓库走 `bm.py`（推荐）。SKILL 增加用法判定 +「仅提示词时怎么做」硬约束；有脚本禁止手改，没脚本禁止空跑 `bm.py`。
- 2026-09-08 v1.5.0：一轮加固与对齐——把"敢让它动真实数据"补严，并让 clone 下来的人也有靶子可练。
  - **安全补齐**：`restore` 补上与 `finalize` 同级的进程安全闸 + 自动 `prerestore` 兜底（此前它是唯一缺闸的写操作）；`backup` 的 `restore_cmd` 改为绝对路径（原来写 `python bm.py`，用户照抄必失败）；`finalize` 写回改为「先验候选结构 → 写 `.tmp` → `os.replace`」的原子替换（原来直接 `open(w)` 截断，中途失败会留下半个 JSON）；`finalize`/`restore` 的闸门抽成同一份实现，不再各写一遍。
  - **`diff`/`preview` 重写为路径感知**：按「路径+名称+链接」多重集对账，能识别**移动 / 改名 / 副本减少**。此前纯整理目录会报"删 0 / 增 0"，用户以为脚本没干活；同目录去重也会被误报成"删除"。
  - **`show` 可用性**：新增 `--depth N` / `--stats`，>300 条自动提醒；重复 URL 逐条标注"同目录（会去重）/ 跨目录（保留）"，堵住"AI 拿着全树重复表向用户承诺去重"的误判；`roots` 缺失给干净中文而非 KeyError。
  - **性能与隐患**：重复 id 由列表 `count()`（O(n²)）改为 Counter；`_dedup_children` 由 `list.index(dict)`（按值比较，可能替换错对象）改为记录下标。
  - **新增入库样例** `scripts/test/sample/`（虚构 18 条 + 生成脚本）并调整 `.gitignore` 放行它——解决"clone 后没有能练手的靶子"；真实快照仍被屏蔽。新增 `.gitattributes` 统一 LF。
  - **文档对齐**：三处 README/SKILL/MAINTENANCE 的表、Pitfalls、边界矩阵、台账全部更新到当前行为；版本号统一到 1.5.0；README 新增「第一次用不敢放心？三层自查」，把信任建立在可自查的事实上而非承诺上。
- 2026-09-08 v1.6.0：把"靠手工跑一遍验证"升级为"可重复执行的断言"。
  - **新增零依赖回归测试** `scripts/test/run_tests.py`（unittest，28 项，约 1 秒）：锁住安全不变量——去重保留最新、跨目录不被误删、`plan` 不写源文件、finalize/restore 两个安全闸、原子写回不留 `.tmp`、候选非法不落地、路径感知对账（移动/改名/副本减少/增删）、`detect` 三平台根路径跟随环境变量且不烙死用户名、`verify` 结构检出、`show --depth/--stats` 与跨目录标注。浏览器状态一律 monkeypatch，测试不碰真实 Profile。
  - **做了变异验证**：故意把"去重保留最新"的比较符改反 → 测试立刻变红 → 证明这套断言不是摆设。这是本项目第一次有能力证明"测试真的能抓住回归"。
  - **`finalize` 补目标闸门**：目标存在却解析不出 `roots`（多半是 `--target` 指到 `Preferences` 之类的文件）时拒绝覆盖，确要强行才 `--force`。补上新闸门后它是唯一会在武力之外防住"盖错文件"的一环。
  - **`verify --before` 补变更分类**：与 `diff` 同口径输出删/增/移动/改名/副本减少，避免"总数没变但组成变了"看不出来。
  - **新增 CI** `.github/workflows/test.yml`：Windows/macOS/Linux × Python 3.9/3.11 跑同一套测试 + 样例端到端冒烟，部分弥补"mac/linux 的 detect 分支无法在本机实测"。
- 2026-09-08 v1.7.0：**把"脚本管不了的浏览器行为"显式化**—— 此前一直担心的那件事，现在会在体检时被点破，并有了一条零风险的试水路线。
  - `preflight` 新增**云端同步感知**：检测 `Sync Data/` 目录与 `Preferences` 里的 `sync`/`account_info`/`signin`，有迹象就明确输出「**云端不是备份，是复制品**：误删会同步传播到所有设备」；没迹象就如实说"未发现"（**不谎称没开同步**），并建议动手前把整个 Profile 目录复制一份。这是提示不构成 NO-GO。
  - SKILL Pitfalls 补两条硬认知：「云端不是备份」与「**不要靠开关同步求安全**」——开关同步本身会引发数据变动，风险大于收益。
  - 新增 **第 7 节「真实场景验收阶梯」**：L0 合成样例 → **L1 用 `--user-data-dir` 起一次性 Profile 完整跑一遍含重启（这是第一次真正让浏览器参与，代价为零，能回答"浏览器会不会认账"）** → L2 真实 Profile 只读动作 → L3 完整整理；并写明 L2/L3 的前提是整 Profile 目录副本。README 与 SKILL 均已挂链。
  - 测试从 28 项增到 **32 项**：新增 `TestPreflightSyncAwareness`（有迹象能识别、干净 Profile 不误报、有同步也不阻塞 GO）。
