# chrome-bookmarks-organize

> 直接编辑 Chrome/Edge 的 Bookmarks JSON 文件，让 AI Agent 帮你整理浏览器书签——**完全绕开"导出 HTML → 导入"的重复追加问题**。

一个遵循 [Agent Skills](https://agentskills.io) 开放标准的技能（`SKILL.md`），并附带一个离线、零第三方依赖的命令行工具箱 `scripts/bm.py`，可直接用于 Claude Code、QwenWork、OpenCode 等支持该标准的 AI 编程工具。

## 为什么做这个

整理浏览器书签的常规路线是：导出 HTML → 手工/AI 整理 → 导入。但浏览器书签的**导入是追加不是替换**，整理完永远多出一个"已导入"文件夹，还得手工去重合并。

实际上书签的底层存储就是一个**纯 JSON 文件，无加密**。直接改它 = 改正式数据，重启浏览器即生效、开同步自动同步到账号。这条路社区博客早有验证，但一直没人把它封装成 **AI 可执行 + 有安全护栏** 的规范——本仓库补上这一环。

## 核心：一条"带循环"的流程，不是一路走到底

```
detect 定位 → preflight 体检(GO/NO-GO) → backup 底牌 → show 读准结构
   → 〔循环区：plan 重排 → preview 预览 → 与用户反复确认，全程不动真身〕
   → 用户拍板"就这版" → finalize 写回 → verify/diff 校验 → 重启浏览器验收
   → 不满意 → restore 一键还原 → 回到循环区
```

只有 `finalize` 一步会真正改文件，其余都在内存/候选文件里折腾。

## 工具箱 `scripts/bm.py`（10 个子命令）

| 命令 | 作用 |
|---|---|
| `detect` | 按 OS 环境变量自动定位各浏览器 Profile 的 Bookmarks（**根路径不写死**，跨 Win/mac/Linux） |
| `preflight` | 只读体检：存在/可读写/JSON 合法/浏览器是否在跑 → 给 **GO/NO-GO** |
| `backup` | 改前时间戳底牌 + sha256 校验 + 记录还原命令 |
| `show` | 打印真实结构（目录树/数量/重复 URL/是否有 checksum）——地基确认 |
| `plan` | 内存里按 `--sort/--dedup` 重排到候选文件，**绝不碰原文件** |
| `preview` | 渲染成**本地嵌套树 HTML**，双击肉眼核对（可 `--base` 看增删） |
| `diff` | 两份书签逐条列增/删 URL |
| `finalize` | **唯一动真身**：删 checksum、改名陈旧 `.bak`、写回（浏览器在跑自动拒绝，除非 `--force`；写前自动再兜一份） |
| `verify` | JSON 合法性 + 结构合法 + id 唯一 + 数量对账 |
| `restore` | 用底牌回退到底牌那一刻（非仅撤销最后一步，见 Pitfalls） |

## 安全设计（为什么敢让它动你的真实数据）

- **改前先备份**，且 `finalize` 自己还会再兜一份 `prescript`——漏做备份也能救。
- **浏览器没退就拒绝写回**：`preflight`/`finalize` 用 tasklist/pgrep 自动检测，杜绝"改了被内存覆盖"。
- **预览先行**：任何写回前，先把结构渲染成本地 HTML 让你肉眼核对；预览和浏览器一致，才证明脚本可信。
- **不自作主张删**：去重只在同目录内合并，跨目录同链接保留；归类规则先与你确认。
- 全程**本地、离线、零依赖**，不联网、不上传。

## 快速上手

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

## 仓库结构

- `SKILL.md` — 给 AI 看的操作规范（流程 + Pitfalls + 验证）。
- `scripts/bm.py` — 上述工具箱。
- `scripts/test/` — 常驻**对比测试案例**：从真实书签裁剪的 `Bookmarks.before`/`Bookmarks.after` + 两份预览 HTML（含隐私，已被 `.gitignore` 屏蔽，不入库）。
- `MAINTENANCE.md` — 长期维护文档：**AI 判断 vs 脚本执行**的分工合同、脚本质量台账、边界矩阵、变更日志。

## 使用前提（硬性）

1. **整理真实书签时浏览器必须完全退出**（含托盘后台）——这是机制限制，`preflight`/`finalize` 已强制拦截。
2. 整理规则先与 AI 确认，**不自作主张删除任何一条书签**。

## 文件位置速查（也可直接 `detect` 自动找）

| 浏览器 | Bookmarks 路径 |
|---|---|
| Chrome (Windows) | `%LOCALAPPDATA%\Google\Chrome\User Data\<Profile>\Bookmarks` |
| Edge (Windows) | `%LOCALAPPDATA%\Microsoft\Edge\User Data\<Profile>\Bookmarks` |
| Chrome (macOS) | `~/Library/Application Support/Google/Chrome/<Profile>/Bookmarks`（无 `User Data` 层） |
| Chrome (Linux) | `~/.config/google-chrome/<Profile>/Bookmarks` |

> `<Profile>` 通常为 `Default`，多用户是 `Profile 1`…；`detect` 还能识别 Chromium/Brave/Vivaldi/Opera。

## 已知边界

- 没有"热编辑"：改文件时浏览器必须关着。
- `date_added` 是 Chrome 时间戳（自 1601-01-01 的微秒），`bm.py` 已自动转日期。
- 只管结构整理，不判断链接是否失效/内容好坏。
- `detect` 的 macOS/Linux 分支与更多浏览器内核已实现，但**尚未在非 Windows 机器上实测**。

## License

[MIT](LICENSE)
