# GitHub Pages 部署：经典模式 vs Actions 模式

> 本文档长期有效。记录 GitHub Pages 两种部署模式的区别、适用场景、选型理由、操作步骤，以及一段可直接复制给 AI 的提示词——以后部署 Pages 就让 AI 按这段提示词跑，不用手敲命令。

## 一句话结论

**纯静态页面（HTML/CSS/JS）一律用经典模式。需要构建步骤（React/Vue/Hexo 等编译后才出 HTML）才用 Actions 模式。**

本项目是纯静态宣传页，固定使用经典模式。

---

## 先理清三个容易混的概念

很多人把这三个概念搅在一起说，越说越乱。它们其实是**三个独立的维度**：

### 维度一：Pages 站点类型——你建的是哪种仓库

| 类型 | 仓库名 | 站点 URL | 用途 |
|---|---|---|---|
| **个人主页**（User/Organization Pages） | `username.github.io`（必须是这个精确名字） | `https://username.github.io/` | 个人主页、博客、作品集 |
| **项目主页**（Project Pages） | 任意名字，如 `my-project` | `https://username.github.io/my-project/` | 给项目做宣传页、文档站 |

**关键**：这两种仓库都可以用经典模式，也都可以用 Actions 模式。站点类型不决定部署模式。

> 你目前的仓库全是项目主页类型（没有 `LPK3215.github.io` 这个个人主页仓库）。这跟部署模式无关。

### 维度二：部署模式——GitHub 怎么把你的文件变成网站

| 模式 | 谁来构建 | 需要 Actions？ | 配置位置 |
|---|---|---|---|
| **经典模式**（legacy） | GitHub 内置服务，拿到文件直接发布 | ❌ 不需要 | 仓库 Settings → Pages → Source 选「Deploy from a branch」 |
| **Actions 模式**（workflow） | 你写的 workflow YAML，先跑再发布 | ✅ 必须 | 仓库 Settings → Pages → Source 选「GitHub Actions」+ 写 `.github/workflows/pages.yml` |

**关键**：经典模式 = GitHub 帮你直接发文件，不需要任何额外运行。Actions 模式 = 你写一个自动化流程，先处理文件再发布，但这个流程必须由 Actions 引擎执行。

### 维度三：你的项目需不需要构建

| 你的项目长什么样 | 需要构建吗 | 用哪种模式 |
|---|---|---|
| 纯 HTML/CSS/JS，写完就能直接打开 | ❌ 不需要 | **经典模式** |
| React / Vue / Next.js，要 `npm run build` 才出 HTML | ✅ 需要 | **Actions 模式** |
| Hexo / Hugo / Jekyll 等静态站点生成器 | ✅ 需要 | **Actions 模式**（或 GitHub 内置 Jekyll） |
| TypeScript 要编译成 JS | ✅ 需要 | **Actions 模式** |

**关键**：选哪种模式，取决于你的项目要不要"编译"。纯静态文件不需要编译，经典模式够用；需要编译的，就得靠 Actions 跑编译再发布。

---

## 两种模式的详细对比

| 维度 | 经典模式（legacy） | Actions 模式（workflow） |
|---|---|---|
| 构建引擎 | GitHub 内置服务 | GitHub Actions（你写的 workflow YAML） |
| 需要 Actions 运行？ | ❌ 不需要 | ✅ 必须 |
| 账号被锁（账单问题）时 | ✅ 照常部署 | ❌ 直接卡死 |
| 部署源 | 仓库分支的 `/` 或 `/docs` 目录 | workflow 里 `upload-pages-artifact` 指定的路径 |
| 可做的事 | 放静态文件，GitHub 自动发布 | 可先跑测试、构建、自定义处理后再发布 |
| 配置方式 | API 或 Settings 页面选分支 + 目录 | 写 `.github/workflows/pages.yml` + Settings 选「GitHub Actions」 |
| push 后 | GitHub 内部自动构建，无需你做任何事 | 触发 workflow，workflow 跑完才部署 |
| 灵活性 | 低（只能放静态文件） | 高（可以在部署前做任何 CI 的事） |
| 费用（公开仓库） | 免费 | 免费（但账号被锁时无法运行） |
| 维护成本 | 极低——放好文件就行 | 中——要维护 workflow YAML |

### 为什么一个能跑一个不能

就一句话：**经典模式不经过 Actions 引擎，Actions 模式必须经过 Actions 引擎**。

GitHub 账号被锁的是 **Actions 的执行权限**，不是 Pages 服务本身。经典模式走的是 GitHub 内部固定的构建服务，和 Actions 完全无关；Actions 模式走的是你写的 workflow YAML，必须由 Actions 引擎执行——引擎被锁了，链条就断了。

### 你的实际使用情况

| 仓库 | 模式 | 部署源 | 站点 URL |
|---|---|---|---|
| `chrome-bookmarks-organize` | legacy | `main/docs` | `https://lpk3215.github.io/chrome-bookmarks-organize/` |
| `silver-guardian-v2` | legacy | `main/docs` | `https://lpk3215.github.io/silver-guardian-v2/` |
| `daily-song` | legacy | `main/` | `https://lpk3215.github.io/daily-song/` |
| `LarkReader` | legacy | `main/docs` | `https://lpk3215.github.io/LarkReader/` |

你的 4 个开了 Pages 的仓库**全部用的是经典模式**，从来没有用过 Actions 模式——这就是它们一直能正常部署的原因。

---

## 适用场景总结

### 经典模式适合谁

- ✅ 纯静态页面（HTML/CSS/JS，写完直接能浏览器打开的）
- ✅ 项目宣传页、文档站、展示页
- ✅ 不需要编译、不需要跑测试才部署的项目
- ✅ 想省心、不想维护 workflow YAML 的人
- ✅ 账号可能有账单风险、不想依赖 Actions 的人

**典型场景**：你有一个项目，想给它做个宣传页。你写了 `index.html` + `style.css` + 几张图，往仓库 `docs/` 目录一放，push 到 main，GitHub 自动发布。完事。

### Actions 模式适合谁

- ✅ React / Vue / Next.js 等需要 `npm run build` 编译后才能出 HTML 的项目
- ✅ Hexo / Hugo / Jekyll 等静态站点生成器（需要先 `generate` 再发布）
- ✅ TypeScript 需要编译成 JavaScript 的项目
- ✅ 部署前要跑测试、做自定义处理（比如压缩、加密、生成 sitemap）
- ✅ 需要从外部数据源拉取内容再构建的场景

**典型场景**：你用 React 做了一个个人博客，代码是 JSX/TSX，不能直接当网页打开。你写一个 workflow：`npm install → npm run build → 把 dist/ 目录发布到 Pages`。每次 push 代码，Actions 自动编译并部署。

### 简单的决策流程

```
你的项目需要编译吗（npm build / generate / tsc）？
├── 不需要 → 经典模式，放 docs/ 里 push 就完事
└── 需要 → Actions 模式，写 workflow 先编译再发布
```

> **个人主页 vs 项目主页**和这个选择**无关**。个人主页仓库（`username.github.io`）也可以用经典模式（直接放 HTML），项目主页仓库也可以用 Actions 模式（先编译再发布）。决定用哪种模式的是"你的项目要不要编译"，不是"你是个人主页还是项目主页"。

---

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

---

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

# 如果以后要切回 Actions 模式（仅在需要编译步骤时才用）
gh workflow enable pages.yml --repo <owner>/<repo>
gh api -X PUT /repos/<owner>/<repo>/pages -f build_type=workflow
```

---

## 提示词：让 AI 帮你配置 GitHub Pages（经典模式）

> 把下面代码块整段复制给 AI（Claude / Codex / GPT…），再补一句你的仓库名（如 `LPK3215/chrome-bookmarks-organize`），AI 就会按这套流程跑完。
> 这个提示词适用于所有"纯静态页面、不需要编译"的项目部署。

```text
你是"GitHub Pages 部署助手"。帮我用经典模式（legacy）把仓库的 docs/ 目录部署到 GitHub Pages。

关键原则：用经典模式，不用 Actions 模式。经典模式不走 Actions 引擎，不怕账号账单锁定，公开仓库零成本。只有需要编译的项目（React/Vue/Hexo 等）才用 Actions 模式，我的项目是纯静态页面，不需要编译。

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
- 这套流程只适用于纯静态页面（不需要编译）。如果项目需要 npm run build / generate 等编译步骤，应该用 Actions 模式而非经典模式。
```

> 这段提示词里的 `<owner>/<repo>` 占位符，你可以在复制时直接替换成你的仓库名，也可以在提示词后面补一句"我的仓库是 LPK3215/chrome-bookmarks-organize"让 AI 自己填。
