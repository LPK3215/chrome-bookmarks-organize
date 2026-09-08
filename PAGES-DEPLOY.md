# GitHub Pages 部署：经典模式 vs Actions 模式

> 本文档长期有效。记录本项目 Pages 部署方式的选型、区别、操作步骤，以及一段可直接复制给 AI 的提示词——以后部署 Pages 就让 AI 按这段提示词跑，不用手敲命令。

## 一句话结论

**本项目固定使用经典模式（legacy）部署，不用 Actions 模式（workflow）。**

理由：经典模式不走 Actions 引擎，不怕账号账单锁定，公开仓库零成本、零依赖、push 即自动构建。Actions 模式更灵活但多一层依赖——账号一旦被锁，Actions 跑不起来，Pages 就跟着断。

## 两种模式到底什么区别

| 维度 | 经典模式（legacy） | Actions 模式（workflow） |
|---|---|---|
| 构建引擎 | GitHub 内置服务（Jekyll / 纯静态） | GitHub Actions（你写的 workflow YAML） |
| 需要 Actions 运行？ | ❌ 不需要 | ✅ 必须 |
| 账号被锁（账单问题）时 | ✅ 照常部署 | ❌ 直接卡死 |
| 部署源 | 仓库分支的 `/` 或 `/docs` 目录 | workflow 里 `upload-pages-artifact` 指定的路径 |
| 可做的事 | 放静态文件，GitHub 自动发布 | 可先跑测试、构建 React/Vue、自定义处理后再发布 |
| 配置方式 | `gh api -X PUT .../pages -f build_type=legacy -f "source[branch]=main" -f "source[path]=/docs"` | 仓库 Settings → Pages → Source 选「GitHub Actions」+ 写 `.github/workflows/pages.yml` |
| push 后 | GitHub 内部自动构建，无需你做任何事 | 触发 workflow，workflow 跑完才部署 |
| 灵活性 | 低（只能放静态文件） | 高（可以在部署前做任何 CI 的事） |
| 费用（公开仓库） | 免费 | 免费（但账号被锁时无法运行） |

### 为什么一个能跑一个不能

就一句话：**经典模式不经过 Actions 引擎，Actions 模式必须经过 Actions 引擎**。

GitHub 账号被锁的是 **Actions 的执行权限**，不是 Pages 服务本身。经典模式走的是 GitHub 内部固定的构建服务，和 Actions 完全无关；Actions 模式走的是你写的 workflow YAML，必须由 Actions 引擎执行——引擎被锁了，链条就断了。

本项目是纯静态 HTML/CSS/JS，不需要任何构建步骤，经典模式完全够用。

## 当前配置

| 配置项 | 值 |
|---|---|
| 构建模式 | `legacy`（经典部署） |
| 部署源 | `main` 分支的 `/docs` 目录 |
| 站点 URL | `https://LPK3215.github.io/chrome-bookmarks-organize/` |
| `pages.yml` workflow | 已禁用（`gh workflow disable`），不再触发 Actions |
| `docs/` 与 `project_overview/` 的关系 | `docs/` 是部署副本，内容与 `project_overview/` 同步 |

### 维护约定

- 改 `project_overview/` 的内容后，**同步复制到 `docs/`** 再 push
- 或者直接改 `docs/` 下的文件（两处保持一致即可）
- push 到 main 后，GitHub 经典模式自动构建 `docs/` 并发布，无需手动操作

## 手动操作命令（参考用，一般让 AI 跑提示词即可）

```bash
# 查看当前 Pages 配置
gh api repos/<owner>/<repo>/pages

# 切换到经典模式（本项目固定使用）
gh api -X PUT /repos/<owner>/<repo>/pages -f build_type=legacy -f "source[branch]=main" -f "source[path]=/docs"

# 手动触发一次经典构建
gh api -X POST /repos/<owner>/<repo>/pages/builds

# 查看最新构建状态
gh api /repos/<owner>/<repo>/pages/builds/latest

# 禁用 Actions 版 pages.yml（避免每次 push 都触发一个注定失败的 workflow）
gh workflow disable pages.yml --repo <owner>/<repo>

# 如果以后要切回 Actions 模式（不推荐，除非有特殊需求）
gh workflow enable pages.yml --repo <owner>/<repo>
gh api -X PUT /repos/<owner>/<repo>/pages -f build_type=workflow
```

---

## 提示词：让 AI 帮你配置 GitHub Pages（经典模式）

> 把下面代码块整段复制给 AI（Claude / Codex / GPT…），再补一句你的仓库名（如 `LPK3215/chrome-bookmarks-organize`），AI 就会按这套流程跑完。

```text
你是"GitHub Pages 部署助手"。帮我用经典模式（legacy）把仓库的 docs/ 目录部署到 GitHub Pages。

关键原则：用经典模式，不用 Actions 模式。经典模式不走 Actions 引擎，不怕账号账单锁定，公开仓库零成本。

我的仓库是：<在这里填你的 owner/repo，如 LPK3215/chrome-bookmarks-organize>

按以下步骤操作，每一步做完告诉我结果：

1. 检查仓库是否为公开仓库（私有仓库 Pages 需付费，公开仓库免费）：
   gh api /repos/<owner>/<repo> --jq '{visibility: .visibility, has_pages: .has_pages}'

2. 确认 docs/ 目录存在且有 index.html。如果没有，先把 project_overview/（或其他宣传页源目录）的内容复制到 docs/。

3. 检查当前 Pages 配置：
   gh api /repos/<owner>/<repo>/pages
   记下 build_type：如果是 legacy 且 source 已指向 main/docs，说明已配好，跳到第 6 步。

4. 如果当前是 workflow 模式，或还没配过 Pages，切换到经典模式：
   gh api -X PUT /repos/<owner>/<repo>/pages -f build_type=legacy -f "source[branch]=main" -f "source[path]=/docs"
   （如果返回 404 说明 Pages 还没开启，先开启：gh api -X POST /repos/<owner>/<repo>/pages -f build_type=legacy -f "source[branch]=main" -f "source[path]=/docs"）

5. 如果仓库里有 .github/workflows/pages.yml，禁用它（防止每次 push 触发一个注定失败的 Actions workflow）：
   gh workflow disable pages.yml --repo <owner>/<repo>

6. 手动触发一次构建（不用等 push，立刻验证能不能跑通）：
   gh api -X POST /repos/<owner>/<repo>/pages/builds

7. 等 30 秒后检查构建结果：
   gh api /repos/<owner>/<repo>/pages/builds/latest --jq '{status: .status, error: .error.message}'
   如果 status 是 "built" 且 error 是 null，说明部署成功。

8. 告诉我最终的站点 URL：
   gh api /repos/<owner>/<repo>/pages --jq '.html_url'

注意：
- 经典模式只支持部署源路径为 /（仓库根）或 /docs（docs 目录）。如果宣传页不在 docs/ 下，先复制过去。
- 私有仓库的 Pages 需要 GitHub Pro 以上套餐，公开仓库免费。
- 以后改了 docs/ 的内容，push 到 main 就会自动构建发布，不需要再手动触发。
- 如果 docs/ 的内容是从别处同步来的（如 project_overview/），每次改完源目录记得同步到 docs/。
```

> 这段提示词里的 `<owner>/<repo>` 占位符，你可以在复制时直接替换成你的仓库名，也可以在提示词后面补一句"我的仓库是 LPK3215/chrome-bookmarks-organize"让 AI 自己填。
