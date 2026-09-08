# chrome-bookmarks-organize

> 直接编辑 Chrome/Edge 的 Bookmarks JSON 文件，让 AI Agent 帮你整理浏览器书签——**完全绕开"导出 HTML → 导入"的重复追加问题**。

一个遵循 [Agent Skills](https://agentskills.io) 开放标准的技能（SKILL.md），可直接用于 Claude Code、OpenCode、QwenWork 等支持该标准的 AI 编程工具。

## 为什么做这个

整理浏览器书签的常规路线是：导出 HTML → 手工/AI 整理 → 导入。但浏览器书签的**导入是追加不是替换**，整理完永远多出一个"已导入"文件夹，还得手工去重合并，整理 100 个书签有 30 分钟浪费在流程上。

实际上，浏览器书签的底层存储就是一个**纯 JSON 文件，无加密**。直接改它 = 改正式数据，重启浏览器即生效，开启同步时自动同步到账号。这条路社区博客早有验证，但一直没人把它封装成 AI 可执行的规范——本仓库补上这一环。

## 它能做什么

把这个 SKILL.md 装进你的 AI 工具后，说一句"帮我整理收藏夹"，AI 会按规范执行：

- 🔍 自动定位正确的 Profile（多用户防呆）
- 💾 修改前强制备份，并明确告知备份路径
- 📂 重排目录树 / 改名 / 按 URL 去重 / 排序
- 🧹 自动处理 `checksum` 校验字段（Chrome 会自动重建）
- ✅ 写回后 JSON 合法性校验 + 书签数量对账

## 使用前提（硬性）

1. **浏览器必须完全退出**（不是关窗口，托盘后台进程也要退干净）——运行时书签缓存在内存里，退出时会用旧数据覆盖磁盘修改，这是最常见的失败原因。
2. 整理规则先和 AI 确认，**不自作主张删除任何一条书签**（已写死在 SKILL.md 中）。

## 安装

把本仓库的 `SKILL.md` 放进你工具的技能目录即可：

| 工具 | 技能目录 |
|---|---|
| Claude Code | `~/.claude/skills/chrome-bookmarks-organize/` |
| QwenWork | `~/.qwenworkcn/skills/chrome-bookmarks-organize/` |
| OpenCode | `.opencode/skills/chrome-bookmarks-organize/` |

## 文件位置速查

| 浏览器 | Bookmarks 文件路径 |
|---|---|
| Chrome (Windows) | `%LOCALAPPDATA%\Google\Chrome\User Data\<Profile>\Bookmarks` |
| Edge (Windows) | `%LOCALAPPDATA%\Microsoft\Edge\User Data\<Profile>\Bookmarks` |
| Chrome (macOS) | `~/Library/Application Support/Google/Chrome/<Profile>/Bookmarks` |
| Chrome (Linux) | `~/.config/google-chrome/<Profile>/Bookmarks` |

> `<Profile>` 通常为 `Default`，多用户场景可能是 `Profile 1`、`Profile 2`…

## 已知边界

- 没有"热编辑"：改文件时浏览器必须关着，这是机制限制，任何工具都绕不开。
- `date_added` 是 Chrome 时间戳（自 1601-01-01 起的微秒数），按时间排序需先转换。
- 无法判断书签内容好坏——它只管结构整理，不管链接是否失效。

## License

[MIT](LICENSE)
