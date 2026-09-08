# GitHub Pages 部署笔记：经典模式 vs Actions 模式

> 通用文档，不绑定任何具体项目。复制到任何仓库都适用。以后部署 Pages 直接按这份笔记操作，或把末尾提示词复制给 AI 让它跑。

## 一句话结论

**纯静态页面（HTML/CSS/JS）一律用经典模式。需要构建步骤（React/Vue/Hexo 等编译后才出 HTML）才用 Actions 模式。**

---

## 先理清三个容易混的概念

| 概念 | 是什么 | 和部署模式的关系 |
|---|---|---|
| **站点类型** | 个人主页（`username.github.io`）vs 项目主页（`username.github.io/repo`） | 无关——两种仓库都能用两种模式 |
| **部署模式** | 经典模式（legacy）vs Actions 模式（workflow） | 本文核心 |
| **要不要编译** | 纯静态 vs 需要构建（`npm build` / `generate` / `tsc`） | **这才是选哪种模式的决定因素** |

> 很多人说"个人主页用 Actions 模式、项目主页用经典模式"——**不准确**。决定用哪种模式的是"你的项目要不要编译"，不是"你是个人主页还是项目主页"。

### 维度一：站点类型

| 类型 | 仓库名 | 站点 URL | 用途 |
|---|---|---|---|
| **个人主页** | `username.github.io`（必须是这个精确名字） | `https://username.github.io/` | 个人主页、博客、作品集 |
| **项目主页** | 任意名字 | `https://username.github.io/项目名/` | 给项目做宣传页、文档站 |

### 维度二：部署模式

| 模式 | 谁来构建 | 需要 Actions？ | 配置位置 |
|---|---|---|---|
| **经典模式** | GitHub 内置服务，拿到文件直接发布 | ❌ 不需要 | Settings → Pages → Source 选「Deploy from a branch」 |
| **Actions 模式** | 你写的 workflow YAML，先跑再发布 | ✅ 必须 | Settings → Pages → Source 选「GitHub Actions」+ 写 workflow 文件 |

### 维度三：你的项目需不需要编译

| 你的项目长什么样 | 需要编译吗 | 用哪种模式 |
|---|---|---|
| 纯 HTML/CSS/JS，写完就能直接打开 | ❌ 不需要 | **经典模式** |
| React / Vue / Next.js，要 `npm run build` | ✅ 需要 | **Actions 模式** |
| Hexo / Hugo 等静态站点生成器 | ✅ 需要 | **Actions 模式**（或 GitHub 内置 Jekyll） |
| TypeScript 要编译成 JS | ✅ 需要 | **Actions 模式** |

### 简单决策流程

```
你的项目需要编译吗（npm build / generate / tsc）？
├── 不需要 → 经典模式，放 docs/ 里 push 就完事
└── 需要 → Actions 模式，写 workflow 先编译再发布
```

---

## 两种模式详细对比

| 维度 | 经典模式（legacy） | Actions 模式（workflow） |
|---|---|---|
| 构建引擎 | GitHub 内置服务 | GitHub Actions（你写的 workflow YAML） |
| 需要 Actions 运行？ | ❌ 不需要 | ✅ 必须 |
| 账号被锁（账单问题）时 | ✅ 照常部署 | ❌ 直接卡死 |
| 部署源 | 仓库分支的 `/` 或 `/docs` 目录 | workflow 里 `upload-pages-artifact` 指定的路径 |
| 可做的事 | 放静态文件，GitHub 自动发布 | 可先跑测试、构建、自定义处理后再发布 |
| 配置方式 | API 或 Settings 选分支 + 目录 | 写 workflow YAML + Settings 选「GitHub Actions」 |
| push 后 | GitHub 内部自动构建，无需你做任何事 | 触发 workflow，workflow 跑完才部署 |
| 灵活性 | 低（只能放静态文件） | 高（可以在部署前做任何 CI 的事） |
| 费用（公开仓库） | 免费 | 免费（但账号被锁时无法运行） |
| 维护成本 | 极低——放好文件就行 | 中——要维护 workflow YAML |

### 为什么一个能跑一个不能

就一句话：**经典模式不经过 Actions 引擎，Actions 模式必须经过 Actions 引擎**。

GitHub 账号被锁的是 **Actions 的执行权限**，不是 Pages 服务本身。经典模式走的是 GitHub 内部固定的构建服务，和 Actions 完全无关；Actions 模式走的是你写的 workflow YAML，必须由 Actions 引擎执行——引擎被锁了，链条就断了。

---

## 适用场景

### 经典模式适合谁

- ✅ 纯静态页面（HTML/CSS/JS，写完直接能浏览器打开的）
- ✅ 项目宣传页、文档站、展示页
- ✅ 不需要编译、不需要跑测试才部署的项目
- ✅ 想省心、不想维护 workflow YAML 的人
- ✅ 账号可能有账单风险、不想依赖 Actions 的人

**典型场景**：你有一个项目，想给它做个宣传页。你写了 `index.html` + `style.css` + 几张图，往仓库 `docs/` 目录一放，push 到 main，GitHub 自动发布。完事。

### Actions 模式适合谁

- ✅ React / Vue / Next.js 等需要 `npm run build` 编译后才能出 HTML 的项目
- ✅ Hexo / Hugo / Jekyll 等静态站点生成器
- ✅ TypeScript 需要编译成 JavaScript 的项目
- ✅ 部署前要跑测试、做自定义处理（压缩、加密、生成 sitemap）

**典型场景**：你用 React 做了一个个人博客，代码是 JSX/TSX，不能直接当网页打开。你写一个 workflow：`npm install → npm run build → 把 dist/ 目录发布到 Pages`。每次 push 代码，Actions 自动编译并部署。

---

## 经典模式：完整操作步骤

### 前提条件

- 仓库是 **public**（公开仓库 Pages 免费；私有仓库需 GitHub Pro 以上套餐）
- 仓库里有 `docs/` 目录且包含 `index.html`（或你想把仓库根 `/` 当部署源也行）
- 已安装 `gh`（GitHub CLI）并登录

### 操作命令

```bash
# 1. 查看当前 Pages 配置（如果返回 404 说明 Pages 还没开启）
gh api repos/<owner>/<repo>/pages

# 2. 切换到经典模式（或首次开启 Pages）
#    如果 Pages 已存在但 build_type 是 workflow，用 PUT 切换：
gh api -X PUT /repos/<owner>/<repo>/pages -f build_type=legacy -f "source[branch]=main" -f "source[path]=/docs"
#    如果返回 404（Pages 还没开启），用 POST 首次开启：
gh api -X POST /repos/<owner>/<repo>/pages -f build_type=legacy -f "source[branch]=main" -f "source[path]=/docs"

# 3. 如果仓库里有 .github/workflows/pages.yml，禁用它
#    （防止每次 push 触发一个注定失败的 Actions workflow）
gh workflow disable pages.yml --repo <owner>/<repo>

# 4. 手动触发一次构建（不用等 push，立刻验证能不能跑通）
gh api -X POST /repos/<owner>/<repo>/pages/builds

# 5. 等 30 秒后检查构建结果
gh api /repos/<owner>/<repo>/pages/builds/latest --jq '{status: .status, error: .error.message}'
#    status 为 "built" 且 error 为 null = 成功

# 6. 查看站点 URL
gh api /repos/<owner>/<repo>/pages --jq '.html_url'

# 以后每次改了 docs/ 的内容，push 到 main 就会自动构建发布，不需要再手动触发。
```

### 经典模式部署源可选值

经典模式只支持两种部署源路径：

| 路径 | 含义 |
|---|---|
| `/` | 仓库根目录（所有文件直接当网站内容） |
| `/docs` | 仓库下的 `docs/` 子目录 |

> 如果你的静态页面在别的目录（如 `site/`、`dist/`），先复制到 `docs/` 再部署。

---

## Actions 模式：完整操作步骤 + workflow 模板

### 前提条件

- 仓库是 public（公开仓库 Actions 免费；私有仓库每月有免费分钟数限制）
- 仓库里有一份 `.github/workflows/pages.yml`（模板见下方）
- 仓库 Settings → Pages → Source 已选「GitHub Actions」

### Actions 模式 workflow 文件模板

直接复制以下内容到 `.github/workflows/pages.yml`，按需修改 `path` 字段：

```yaml
name: pages

# GitHub Pages 部署 workflow（Actions 模式）。
# 适用于需要编译步骤的项目（React/Vue/Hexo 等）。
# 纯静态页面不需要这个文件——用经典模式（legacy）即可。
#
# 使用前提：
#   1. 仓库 Settings → Pages → Source 选「GitHub Actions」
#   2. 下方 path 改成你的构建产物目录（如 dist/、build/、public/）
#
# 如果项目不需要编译，直接删掉这个文件，改用经典模式：
#   gh api -X PUT /repos/<owner>/<repo>/pages -f build_type=legacy -f "source[branch]=main" -f "source[path]=/docs"

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/configure-pages@v5

      # ↓↓↓ 如果需要编译，在下面加构建步骤，例如： ↓↓↓
      # - uses: actions/setup-node@v4
      #   with:
      #     node-version: 20
      # - run: npm ci
      # - run: npm run build
      # ↑↑↑ 然后把下面的 path 改成构建产物目录（如 dist） ↑↑↑

      - name: 上传站点内容
        uses: actions/upload-pages-artifact@v3
        with:
          path: .          # ← 改成你的站点文件目录（. 表示仓库根，或 dist、build、public 等）

      - name: 部署到 GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### 操作命令

```bash
# 1. 把上面的 workflow 模板复制到 .github/workflows/pages.yml，按需修改 path

# 2. 切换到 Actions 模式
gh api -X PUT /repos/<owner>/<repo>/pages -f build_type=workflow

# 3. 如果之前禁用过这个 workflow，重新启用
gh workflow enable pages.yml --repo <owner>/<repo>

# 4. push 到 main 会自动触发部署；也可以手动触发
gh workflow run pages.yml --repo <owner>/<repo>

# 5. 查看运行状态
gh run list --workflow=pages.yml --repo <owner>/<repo> --limit=3

# 6. 查看站点 URL
gh api /repos/<owner>/<repo>/pages --jq '.html_url'
```

### 两种模式互切

```bash
# 经典 → Actions
gh workflow enable pages.yml --repo <owner>/<repo>
gh api -X PUT /repos/<owner>/<repo>/pages -f build_type=workflow

# Actions → 经典
gh workflow disable pages.yml --repo <owner>/<repo>
gh api -X PUT /repos/<owner>/<repo>/pages -f build_type=legacy -f "source[branch]=main" -f "source[path]=/docs"
```

---

## 提示词：让 AI 帮你配置 GitHub Pages（经典模式）

> 适用于纯静态页面（不需要编译）。把下面代码块整段复制给 AI，再补一句你的仓库名，AI 就会按这套流程跑完。

```text
你是"GitHub Pages 部署助手"。帮我用经典模式（legacy）把仓库的 docs/ 目录部署到 GitHub Pages。

关键原则：用经典模式，不用 Actions 模式。经典模式不走 Actions 引擎，不怕账号账单锁定，公开仓库零成本。只有需要编译的项目（React/Vue/Hexo 等）才用 Actions 模式，我的项目是纯静态页面，不需要编译。

我的仓库是：<在这里填你的 owner/repo>

按以下步骤操作，每一步做完告诉我结果：

1. 检查仓库是否为公开仓库（私有仓库 Pages 需付费，公开仓库免费）：
   gh api /repos/<owner>/<repo> --jq '{visibility: .visibility, has_pages: .has_pages}'

2. 确认 docs/ 目录存在且有 index.html。如果没有，先把源目录（如 project_overview/、site/、dist/ 等）的内容复制到 docs/。

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

> 这段提示词里的 `<owner>/<repo>` 占位符，你可以在复制时直接替换成你的仓库名，也可以在提示词后面补一句"我的仓库是 xxx/yyy"让 AI 自己填。

---

## 提示词：让 AI 帮你配置 GitHub Pages（Actions 模式）

> 适用于需要编译的项目（React/Vue/Hexo 等）。把下面代码块整段复制给 AI，再补一句仓库名和构建命令。

```text
你是"GitHub Pages 部署助手"。帮我用 Actions 模式（workflow）把项目部署到 GitHub Pages。

关键原则：用 Actions 模式，因为项目需要编译后才出 HTML。Actions 模式会先跑构建步骤，再把产物发布到 Pages。

我的仓库是：<在这里填你的 owner/repo>
我的构建命令是：<如 npm run build，填你的构建命令>
构建产物目录是：<如 dist、build、public，填你的输出目录>

按以下步骤操作，每一步做完告诉我结果：

1. 检查仓库是否为公开仓库：
   gh api /repos/<owner>/<repo> --jq '{visibility: .visibility, has_pages: .has_pages}'

2. 检查 .github/workflows/pages.yml 是否存在。如果不存在，创建一份（我会把模板贴在下面）。
   workflow 模板的关键字段：
   - path 改成我的构建产物目录
   - 在 upload-pages-artifact 之前加上构建步骤（checkout → setup-node → npm ci → npm run build）

3. 检查当前 Pages 配置：
   gh api /repos/<owner>/<repo>/pages

4. 切换到 Actions 模式：
   gh api -X PUT /repos/<owner>/<repo>/pages -f build_type=workflow

5. 如果 pages.yml 之前被禁用过，重新启用：
   gh workflow enable pages.yml --repo <owner>/<repo>

6. 手动触发一次部署：
   gh workflow run pages.yml --repo <owner>/<repo>

7. 等约 1 分钟后检查运行状态：
   gh run list --workflow=pages.yml --repo <owner>/<repo> --limit=1

8. 运行成功后查看站点 URL：
   gh api /repos/<owner>/<repo>/pages --jq '.html_url'

注意：
- Actions 模式需要账号 Actions 权限可用。如果账号因账单问题被锁，Actions 无法运行——此时纯静态项目可降级用经典模式。
- 私有仓库每月有免费 Actions 分钟数限制（2000 分钟），公开仓库无限制。
- workflow YAML 模板参考 PAGES-DEPLOY.md 文档中的 Actions 模式 workflow 文件模板。
```
