# MAINTENANCE — AI/脚本分工合同 & 脚本质量台账

> 这份文档**长期维护**：每次改 `SKILL.md` 的流程、或改/加 `scripts/bm.py` 的子命令后，回来更新第 2、3、5 节。它回答三个问题：**什么动作归 AI 判断、什么动作归脚本执行、脚本现在写得对不对。**

## 1. 一条主线

书签整理 = 一份"分工合同"：
- **判断题 → AI 做**（每次临场定，写在 `SKILL.md`，不固化）：需要常识/语境/品味/跟用户拉扯的。
- **算术题 → 脚本做**（一次写对永久对，锁进 `bm.py`）：有唯一机械答案、不容手滑的。
- **接缝 = 命令行参数**：AI 决定"选哪个开关、传什么路径"，脚本保证"这个开关的执行永远一致"。例：*要不要去重 / 跨目录同链接算不算重复*是 AI 的判断；`--dedup` 一旦按下，*遍历、比 `date_added` 取最新、删多余节点*全是脚本的活。

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
| backup | 底牌+manifest | 合成靶子跑通；**微秒时间戳防同秒碰撞 + 复制后 sha256 校验**（不一致即丢弃并报错） | 2026-09-08 | 真实文件仅做只读快照，未跑写操作（符合预期） |
| show | 读结构+体检 | 合成靶子识别重复URL/checksum；真实快照报 3276 条；缺文件/损坏 JSON 现走 main 兜底给干净中文 | 2026-09-08 | 超大全树（>3000条）输出刷屏，考虑加 `--depth` |
| plan | 内存重排到候选 | sort+dedup 跑通，原文件 0 改动已证明；真实快照 3276→3275（并掉 1 条同目录重复） | 2026-09-08 | 仅 `--sort/--dedup`；改名/移动/新建目录尚未脚本化（暂靠 AI 改 JSON） |
| preview | 本地HTML嵌套树预览 | 合成+真实快照渲染成功；真·嵌套 `<ul>` 树；**目录已可折叠（原生 `<details>`，无 JS）**；带 `--base` 列增删 | 2026-09-08 | 折叠默认全展开；如需"默认收起深层"再加开关 |
| diff | 两份书签增删对账 | 控制台列被删/新增 URL + 净变化数 | 2026-09-08 | **按 (name,url) 集合比对（非多重集）**：删掉多份同名同链中的一份不会计为"删除"；同名改 URL 计为 1 删 1 增 |
| finalize | 唯一动真身 | **Chrome 开着时拒绝写回（干净中文提示，rc=1）；`--force` 放行并自动 prescript 兜底 + 改名陈旧 .bak**；只读/占用写失败给人话且保留兜底件 | 2026-09-08 | 真实浏览器 Profile 仍未 finalize（测试期只打 `scripts/test/` 副本） |
| verify | 校验+对账 | 合成+真实文件跑通；BOM 文件也能读；损坏 JSON 自身捕获报错 | 2026-09-08 | `--before` 对账依赖传对底牌路径 |
| restore | 一键还原 | 合成靶子验证可退回改动前；真实快照退回 3276+checksum | 2026-09-08 | 还原后 `.bak.stale-*`/`.prescript-*` 不自动清理，是否纳入待定 |

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
| 超大全树刷屏 | `preview` 嵌套树；`show` 待加 `--depth` | 部分 |
| Windows 中文控制台乱码 | stdout + stderr 均 `reconfigure(utf-8)` | ✅（本会话修 bug） |

## 6. 测试案例 `scripts/test/`（常驻 · 勿删）

- 内容：`Bookmarks.before`（真实书签裁剪到 ~99 条、保留目录骨架、含 checksum）、`Bookmarks.after`（在 before 上做改名+新增+删除、去 checksum）、`preview-before.html`、`preview-after.html`。**2 数据 + 2 预览**，一眼对比整理前后。
- 定位：脚本对不对，先拿它对这份案例跑一遍、比对预览；预览与预期一致，才允许对真实数据落地。
- **测试铁律**：`finalize` 的 `--target` 永远只指 `scripts/test/` 里的副本，**绝不指向真实 Chrome/Edge Profile**。真实 Profile 仅在最终正式整理、且浏览器完全退出时才当 target。
- 隐私：数据源自真实书签（虽已裁剪），被 `.gitignore` 屏蔽、不入库。将来换成彻底脱敏/虚构数据后，可解除忽略、纳入仓库当公开样例。详见 `scripts/test/README.md`。

## 7. 变更日志

- 2026-09-08 v1.1.0：SKILL 线性流程→带循环版；新增 `bm.py` 7 子命令并在合成靶子端到端跑通；加 `.gitignore` 隔离真实快照；建 `_test/chrome-default/` 只读测试目录。
- 2026-09-08 v1.1.1：建 `_test/README.md`，定"验证靶场常驻勿删 + finalize 测试期只打副本"铁律；补本节分工台账。
- 2026-09-08 v1.2.0：加 `detect`——按 OS 环境变量自动定位 Bookmarks（根路径不再写死，`--root` 兜底自定义 user-data-dir）；"定位文件"从 AI 猜升级为脚本确定性动作、人仍负责挑哪个；同步更新 SKILL 第 0 步与本台账。
- 2026-09-08 v1.2.1：`preview` 由 `&nbsp;` 假缩进（长链接一换行层级就塌）重写为真·嵌套 `<ul>` 树（CSS 竖线引导 + 每目录递归条数）。印证分工好处：格式是脚本决定的，改一次、以后每次预览全跟着变。
- 2026-09-08 v1.3.0：为真实世界加固——加 `preflight`(GO/NO-GO 闸门) 与 `diff`；`load` 容错 BOM/缺失、`main()` 统一兜异常；`backup` 微秒时间戳+复制后 sha256 校验；`finalize` 检测浏览器在跑即拒(除非 `--force`)+自动 prescript 兜底+写失败给人话；`detect` 扩 Chromium/Brave/Vivaldi/Opera；**修 stderr 未切 UTF-8 致中文报错乱码的 bug**；跑通边界测试电池；SKILL 升 v1.2.0、preflight 入第 0 步。
- 2026-09-08 v1.3.2：文档对齐——`README` 重写以反映 10 子命令工具箱 + 带循环流程 + detect/preflight，`SKILL` Verification 更新。**在真实导出快照上跑完整 E2E**：preflight 因浏览器开着判 NO-GO；finalize 无 `--force` 被拒、加 `--force` 放行并自动 prescript + 改名 .bak；verify 全绿；diff 在"总数不变(3276→3276)但组成变了"的增删改下仍报"删2/增2"；restore 后与 .bak sha256 一致、满血复原。**结论：工具箱可用。**
- 2026-09-08 v1.4.0：`preview` 目录改为**原生 `<details>` 可折叠**（无 JS）。**结构大清理**：删 `_demo`/`_test`/`_scratch`/`__pycache__`，合并为单一 `scripts/test/` 对比案例——`Bookmarks.before`(真实数据裁剪到 ~99、含 checksum) + `Bookmarks.after`(改名+新增+删除、去 checksum) + `preview-before.html` + `preview-after.html`；同步改 `.gitignore` 与全部文档引用。在裁剪数据上**重跑完整流程全绿**。发现并记录 `diff` 集合语义局限（删重名重链中的一份不计为删除）。
