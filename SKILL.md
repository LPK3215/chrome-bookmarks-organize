---
name: chrome-bookmarks-organize
description: 直接编辑 Chrome/Edge 的 Bookmarks JSON 文件，让 AI 整理浏览器书签（重排目录/改名/去重/排序），完全绕开"导出HTML→导入"的重复追加问题。用户要求整理收藏夹、批量修改书签结构时使用。
version: 1.0.0
---

# Chrome 书签直改整理

## 原理

浏览器书签底层是纯 JSON 文件（无加密）。直接改文件 = 改正式数据，重启浏览器后生效，开启同步时自动同步到账号。**唯一硬性要求：浏览器必须完全退出后再改**——运行时书签缓存在内存里，退出时会用旧数据覆盖磁盘上的修改。

## 步骤

1. **确认浏览器与 Profile**：Chrome 路径 `%LOCALAPPDATA%\Google\Chrome\User Data\<Profile>\Bookmarks`（Edge 同理把 Google\Chrome 换成 Microsoft\Edge）。Profile 可能是 `Default` 或 `Profile 1`…，按修改时间/内容确认。文件无扩展名，就叫 `Bookmarks`。
2. **让用户完全退出浏览器**：不是关窗口，托盘后台也要退，必要时任务管理器确认无 chrome.exe/msedge.exe 进程。
3. **备份**：把原 `Bookmarks` 文件复制一份到安全位置（用户指定目录或输出目录），并明确告知备份路径。同目录的 `Bookmarks.bak` 不可靠（Chrome 会滚动覆盖），必须自建备份。
4. **读取并理解结构**：顶层 `roots` 下 `bookmark_bar`（收藏夹栏）/ `other`（其他收藏夹）/ `synced`（移动设备）。每个节点：`type` 为 `folder` 或 `url`，folder 有 `children` 数组，url 有 `url` 字段；`date_added` 是 Chrome 时间戳（自 1601-01-01 起的微秒数），比较新旧需先转换。
5. **按用户规则重排**：新建目录树、改名、按 URL 去重（一般保留 date_added 最新的）、排序。保持结构合法：folder 必有 `children`（可为空数组），url 必有非空 `url`；节点 `id` 保持字符串且全树唯一；`guid` 缺失时 Chrome 能自动补。
6. **删除顶层 `checksum` 字段**（整字段删掉）：数据改动后校验和必然不匹配，删掉后 Chrome 视为需重建，会自动重算并正常加载，不报错不拒载。
7. **写回**：UTF-8 编码写回原路径。
8. **验证**：用 Python `json.load` 校验文件合法；让用户重开 Chrome 验收——新结构生效、总书签数与预期一致。

## Pitfalls

- 浏览器没退干净 = 白改，退出时被内存旧数据覆盖（最常见的失败原因）。
- checksum 不要试图重算，直接删字段最稳。
- 动手前必须先备份并告知用户位置；改坏了原样放回即满血复活。
- 收藏夹可能含隐私条目，整理规则（哪些保留/删除/归类）先跟用户确认再动手，不要自作主张删任何一条。
- 多 Profile 机器（Chrome 多用户）改错 Profile 是常见事故，先确认哪个 Profile 是用户在用的。

## Verification

- 写回后 `python -c "import json;json.load(open(r'<path>','r',encoding='utf-8'))"` 不抛异常。
- 统计重排前后 url 节点总数一致（去重场景除外，差额应等于去重数）。
- 用户重启 Chrome 后结构生效、书签可正常打开。
