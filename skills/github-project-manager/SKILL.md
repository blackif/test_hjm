---
name: github-project-manager
description: >
  当用户提到要管理 GitHub 的 project 或 issues、自动处理 issues 标签和回答、创建定时作业自动维护仓库、生成进度周报等时，立即触发此 skill。
  适用场景：用户想要自动分类 issues、自动回答问题、追踪修改进度、维护 GitHub Project 看板、或设置定时自动化维护任务。
  即使用户只是说"帮我管理一下 issues"、"自动处理 github 的问题"、"设置定时维护仓库"也应触发此 skill。
---

# GitHub Project & Issues Manager Skill

自动管理 GitHub 仓库的 Project 看板与 Issues，包括标签分类、自动回答、修改追踪、进度日报，并支持定时作业模式。

---

## ⛔ 严格禁止事项（最高优先级，任何情况下均不得违反）

```
严格禁止删除 仓库
严格禁止删除 Project
严格禁止删除 Issues
严格禁止删除任何 Label 属性
```

---

## 📁 定时作业配置文件规范

所有定时作业统一写入 `cron/jobs.json`，格式如下：

```json
{
  "jobs": [
    {
      "id": "github-project-manager-20260317143000",
      "skill": "github-project-manager",
      "enabled": true,
      "status": "active",
      "schedule": {
        "cron": "0 9 * * *",
        "description": "每天 09:00 执行"
      },
      "config": {
        "owner": "GitHub 用户名",
        "repo": "仓库名",
        "project_id": 1,
        "daily_report": true
      },
      "created_at": "2026-03-17T14:30:00Z",
      "last_run": null,
      "last_status": null
    }
  ]
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 严格遵循 `skill 名字-YYYYMMDDHHMMSS` 格式 |
| `skill` | string | 固定值 `github-project-manager` |
| `enabled` | boolean | `true`=启用，`false`=暂停 |
| `status` | string | `active` / `paused` / `error` |
| `schedule.cron` | string | 标准 cron 表达式 |
| `schedule.description` | string | 人类可读的执行频率描述 |
| `config.owner` | string | GitHub 用户名或组织名 |
| `config.repo` | string | 仓库名 |
| `config.project_id` | number | 绑定的 Project ID（首次手动执行后自动写入） |
| `config.daily_report` | boolean | 是否启用进度日报 |
| `created_at` | string | ISO 8601 创建时间 |
| `last_run` | string/null | 最后执行时间，初始为 `null` |
| `last_status` | string/null | `success` / `error` / `null` |

**错误处理原则：**
- 网络或 API 失败 → 将 `status` 改为 `paused`，`last_status` 改为 `error`，**不删除作业**，记录错误日志，等待人工确认后手动改回 `active`
- 不得因单次失败自动删除定时作业

---

## 前置流程

### STEP 0 — 判断触发来源

```
IF 用户手动输入提示词
  → 进入 STEP 0.1

IF 定时作业触发
  → 跳过 STEP 0.1，直接进入 STEP 1
```

---

### STEP 0.1 — 用户输入时的定时作业询问

检查用户提示词中是否包含创建定时作业相关词汇：
> 关键词示例：定时、自动执行、每天、每周、scheduled、cron、定期、自动运行 等

```
IF 用户提示词包含上述关键词
  → 直接进入 STEP 0.1.1

IF 用户提示词不包含上述关键词
  → 询问用户：
    「是否需要创建定时作业？
      A) 是，请告诉我执行频率（如：每天 09:00 / 每周一 / 每小时等）
      B) 否，本次为一次性执行」

  IF 用户选 A → 进入 STEP 0.1.1
  IF 用户选 B → 记录为一次性作业，进入 STEP 1
```

---

### STEP 0.1.1 — 创建或更新定时作业

```bash
# 检查 cron/jobs.json 是否存在
mkdir -p cron
[ -f cron/jobs.json ] || echo '{"jobs":[]}' > cron/jobs.json
```

检查 `cron/jobs.json` 中是否已存在 `skill` 为 `github-project-manager` 的作业：

```
IF 已存在同 skill 的作业
  → 询问用户：
    「已存在一个定时作业（ID: XXX，当前设置：XXX）
      A) 覆盖旧作业（使用新的时间设置）
      B) 新增一个作业（旧作业保留）
      C) 取消，不创建」

  IF 用户选 A → 将旧作业 enabled 改为 false，新建作业
  IF 用户选 B → 新建作业，旧作业保留
  IF 用户选 C → 记录为一次性作业，进入 STEP 1

IF 不存在同 skill 的作业
  → 直接创建新作业
```

新作业 ID 格式：`github-project-manager-YYYYMMDDHHMMSS`（使用当前时间）

创建完成后确认告知用户，然后进入 STEP 1。

---

## 主流程

### STEP 1 — GitHub 连接检查

```bash
# 检查 GitHub CLI 认证状态
gh auth status

# 检查是否能访问目标仓库（在确定仓库后执行）
gh repo view "$OWNER/$REPO" --json name,id > /dev/null
```

```
IF 认证失败或无法连接
  → 输出错误信息：「GitHub 连接失败：[错误详情]」
  → IF 定时作业 → 将 jobs.json 中对应作业的 status 改为 paused，last_status 改为 error，不删除
  → 终止本次执行

IF OK
  → 继续 STEP 1.1
```

---

### STEP 1.1 — 确认目标仓库

```
IF 用户提示词中包含仓库信息（仓库名 / owner/repo / GitHub URL）
  → 解析并确认仓库，继续 STEP 2

IF 用户提示词中不包含仓库信息
  → 列出当前用户可访问的仓库供选择，或让用户输入仓库名
  → 用户确认后继续 STEP 2
```

```bash
# 解析仓库信息
# 支持以下格式：
# https://github.com/owner/repo
# owner/repo
# repo（owner 从 gh auth status 取）
OWNER=$(gh api user --jq '.login')
REPO="用户输入或解析的仓库名"
```

---

### STEP 2 — 权限检查

```bash
# 检查当前 token 对目标仓库的权限
gh api repos/$OWNER/$REPO --jq '.permissions'
```

需要确认以下权限均为 `true`：
- `push`（用于修改文件）
- `issues`（用于操作 issues）
- `projects`（用于操作 project）

```
IF 权限不足
  → 输出具体缺失的权限信息
  → IF 定时作业 → 将 jobs.json 中对应作业的 status 改为 paused
  → 终止本次执行

IF OK → 继续 STEP 3
```

---

### STEP 3 — Project 确认

```
IF 本次作业是定时作业
  → 从 jobs.json 中读取 config.project_id
  → IF project_id 存在 → 跳过 STEP 3，直接进入 STEP 4
  → IF project_id 不存在 → 输出错误：「定时作业缺少 project 绑定，请先手动执行一次」→ 终止
```

#### STEP 3.1 — 获取账号下所有 project 并过滤无效项

```bash
# 获取账号下所有 project
gh project list --owner "$OWNER" --format json \
  | jq '[.projects[] | select(
      (.title != null) and
      (.title | gsub("^ +| +$";"") | ascii_downcase) != "" and
      (.title | gsub("^ +| +$";"") | ascii_downcase) != "untitled project"
    )]' \
  > /tmp/projects_all.json
```

**无效 project 过滤规则（同时满足以下全部条件才过滤）：**
- title 为空、纯空格、或不区分大小写等于 `untitled project`
- 该 project 下 items 数量为 0

> 两个条件必须同时满足，防止误过滤用户真实使用的同名 project。

#### STEP 3.2 — 进一步筛选：只保留已关联当前仓库的 project

GitHub Projects (v2) 是账号级别资源，需通过 GraphQL API 查询哪些 project 已关联当前仓库：

```bash
# 通过 GraphQL 查询已关联当前仓库的 project 列表
gh api graphql -f query='
  query($owner: String!, $repo: String!) {
    repository(owner: $owner, name: $repo) {
      projectsV2(first: 20) {
        nodes {
          id
          number
          title
          items {
            totalCount
          }
        }
      }
    }
  }
' -f owner="$OWNER" -f repo="$REPO" \
  | jq '[.data.repository.projectsV2.nodes[] | select(
      (.title != null) and
      (.title | gsub("^ +| +$";"") | ascii_downcase) != "" and
      (.title | gsub("^ +| +$";"") | ascii_downcase) != "untitled project"
    )]' \
  > /tmp/projects_linked.json
```

#### STEP 3.3 — 根据筛选结果决策

```
IF 关联当前仓库的有效 project 为 0 个
  → 询问用户：
    「当前仓库没有关联任何 project。
      A) 新建一个 project 并关联到当前仓库（project name 默认为 "default"）
      B) 从账号现有 project 中选一个关联到当前仓库
      C) 取消」

  IF 用户选 A
    → 创建新 project，关联到当前仓库，继续 STEP 4
  IF 用户选 B
    → 列出账号下所有有效 project（来自 /tmp/projects_all.json）供用户选择
    → 用户选定后，将该 project 关联到当前仓库，继续 STEP 4
  IF 用户选 C
    → 终止本次执行

IF 关联当前仓库的有效 project 只有 1 个
  → 直接使用该 project，继续 STEP 4

IF 关联当前仓库的有效 project 有多个
  → 列出这些 project 供用户选择（不显示未关联或已过滤的 project）
  → 用户确认后继续 STEP 4
```

```bash
# 创建新 project 并关联仓库（如需要）
PROJECT_ID=$(gh project create --owner "$OWNER" --title "default" --format json | jq '.number')

# 将 project 关联到仓库（GraphQL）
gh api graphql -f query='
  mutation($projectId: ID!, $repoId: ID!) {
    linkProjectV2ToRepository(input: { projectId: $projectId, repositoryId: $repoId }) {
      repository { name }
    }
  }
' -f projectId="$PROJECT_NODE_ID" -f repoId="$REPO_NODE_ID"
```

確認 project 後，将 project_id 写入 `jobs.json` 对应作业的 `config.project_id`（如为定时作业）。

---

### STEP 3.5 — QA 代码检查

遍历仓库内所有文件，调用大模型逐文件进行检查。检查分三轮依次执行，全部完成后再进入 STEP 4。

**创建 issue 通用规则（本 STEP 全程遵守）：**
- 一个问题对应一个 issue，严禁将多个问题合并到同一 issue
- 允许一个问题涉及多个文件，此时在 body 中逐一列出
- Assignees：当前账户（`$OWNER`）
- Projects：STEP 3 确认的 project
- Status：open

```bash
# 获取仓库所有文件列表
git ls-files > /tmp/qa_files.txt
```

---

#### STEP 3.5.1 — 第一轮：简单错误检查

对每个文件调用大模型，检查以下类型的简单错误：

| 检查项 | 说明 |
|--------|------|
| 拼写错误 | 变量名、函数名、关键字手误（如 `funciton` / `retrun`） |
| 括号/引号未闭合 | 成对符号缺少另一半 |
| 缩进不一致 | 同文件内混用 tab 和空格，或层级混乱 |
| 未使用的 import | import 了但代码中从未引用 |
| 硬编码敏感信息 | 密码、token、IP 等直接写在代码里 ※见注 |
| 遗留调试代码 | `console.log` / `print` / `debugger` 等残留 |
| 空的 catch 块 | 异常被捕获后什么都没做，错误被吞掉 |
| 死代码 | 永远不会被执行到的分支或语句 |
| 文件末尾缺少换行 | 最后一行没有 `\n` |

※ 硬编码敏感信息属于隐私安全问题 → 跳过此处，交由 **STEP 3.5.3** 处理

```
FOR 每个发现的简单错误（隐私安全类除外）：
  → 创建 issue，格式如下：

  Labels：question
  Title：QA: [问题简单描述]
  Body：
  [问题内容详细说明]
  - agent 的 QA
```

```bash
gh issue create --repo "$OWNER/$REPO" \
  --title "QA: [问题简单描述]" \
  --body "[问题内容详细说明]
- agent 的 QA" \
  --assignee "$OWNER" \
  --label "question" \
  --project "$PROJECT_NUMBER"
```

全部文件的简单错误检查完毕后，进入 STEP 3.5.2。

---

#### STEP 3.5.2 — 第二轮：复杂错误检查

对每个文件再次调用大模型，检查以下类型的复杂错误：

| 检查项 | 说明 |
|--------|------|
| 逻辑错误 | 条件判断方向反了、边界值处理错误、永远为真/假的条件 |
| 潜在 null/undefined 崩溃 | 未做空值检查就直接访问属性或调用方法 |
| 异步处理问题 | async/await 使用错误、未处理的 Promise rejection |
| 循环依赖 | 模块 A 依赖 B，B 又依赖 A |
| 重复逻辑不一致 | 相同功能在多处实现，但实现内容存在差异 |
| 接口不匹配 | API 接口定义的参数与实际调用方传入的不一致 |
| 缺少错误处理 | 只写了 happy path，异常情况没有任何处理 |
| 性能隐患 | 循环内做不必要的重复计算、N+1 查询等 |
| 隐私 & 安全问题 | 敏感数据未加密、权限校验缺失、SQL/命令注入风险 ※见注 |

※ 隐私 & 安全问题 → 跳过此处，交由 **STEP 3.5.3** 处理

```
FOR 每个发现的复杂错误（隐私安全类除外）：
  → 创建 issue，格式与 STEP 3.5.1 相同：

  Labels：question
  Title：QA: [问题简单描述]
  Body：
  [问题内容详细说明]
  - agent 的 QA
```

全部文件的复杂错误检查完毕后，进入 STEP 3.5.3。

---

#### STEP 3.5.3 — 第三轮：隐私 & 安全问题 + 隐藏问题

**3.5.3.A — 隐私 & 安全问题汇总**

将 STEP 3.5.1 和 STEP 3.5.2 中标记为「隐私 & 安全」的所有发现，在此统一创建 issue：

```
FOR 每个隐私或安全问题：
  → 创建 issue：

  Labels：help wanted
  Title：QA: [问题简单描述]
  Body：
  [需求详细说明，仅描述问题，不含解决建议]
  - agent 的 QA
```

```bash
gh issue create --repo "$OWNER/$REPO" \
  --title "QA: [问题简单描述]" \
  --body "[需求详细说明]
- agent 的 QA" \
  --assignee "$OWNER" \
  --label "help wanted" \
  --project "$PROJECT_NUMBER"
```

**3.5.3.B — 隐藏问题 & 更优方案**

在 STEP 3.5.1 和 STEP 3.5.2 全部结果的基础上，再次调用大模型进行整体审视，思考：
- 前两轮未发现但可能存在的隐藏问题
- 是否有更好的实现方案或架构改善点

```
IF 发现隐藏问题或更优方案（隐私安全类除外）：
  → 遵循 STEP 3.5.1 的 issue 格式创建（Labels：question）

IF 发现隐藏的隐私 & 安全问题：
  → 遵循 STEP 3.5.3.A 的 issue 格式创建（Labels：help wanted）

IF 没有新发现：
  → 无需创建任何 issue，直接进入 STEP 4
```

---

### STEP 4 — Issues 处理

---

#### STEP 4.1 — 处理无标签的 Open Issues

```bash
# 获取所有 open 状态且无 label 的 issues
gh issue list --repo "$OWNER/$REPO" \
  --state open \
  --json number,title,body,comments,labels \
  | jq '[.[] | select(.labels | length == 0)]' \
  > /tmp/issues_unlabeled.json
```

对每个无标签 issue，阅读 title + body + 所有 comments，按以下规则判断并添加 label：

| 判断条件 | 添加 Label | 附加操作 |
|----------|-----------|----------|
| 内容是提问、疑问、询问、求解答等 | `question` | 无 |
| 内容是求助、寻求协助、帮帮我等 | `help wanted` | 无 |
| 内容与已有 issue（含已关闭）高度相似且无追问 | `duplicate` | 追加回复：「此问题与 #XX 重复，请参考 [链接]」 |
| 内容描述了某个错误、异常、非预期行为 | `bug` | 无 |
| 内容描述了新功能需求、改善请求 | `enhancement` | 无 |

**Label 不存在时先创建：**
```bash
# 创建 label（如不存在）
gh label create "label 名" --repo "$OWNER/$REPO" \
  --color "随机颜色 hex" --description "描述" 2>/dev/null || true
```

**Duplicate 判断原则：**
- 同时检索 open 和 closed 状态的 issues
- 相似度判断基于语义理解（不要求完全相同，重点看核心问题是否一致）
- 如存在多个相似 issue，回复中列出所有相关 issue 链接

遍历全部无标签 issue 后，进入 STEP 4.2。

---

#### STEP 4.2 — 处理有标签的 Open Issues

```bash
# 获取所有 open 状态且有 label 的 issues
gh issue list --repo "$OWNER/$REPO" \
  --state open \
  --json number,title,body,comments,labels \
  | jq '[.[] | select(.labels | length > 0)]' \
  > /tmp/issues_labeled.json
```

---

##### STEP 4.2.1 — 处理含 `question` / `help wanted` 标签的 Issues

阅读 issue 的完整对话链（body + 所有 comments），判断：

```
IF 最后一条回复是用户的追问
  → 追加回答（格式见下方）

IF 最后一条回复是 agent 的回答，且之后没有追问
  → 无需操作，跳过

IF 没有任何回答
  → 追加回答（格式见下方）
```

**回答格式：**
```
回答：
[回答内容]
- agent の回答

根据以上回答，判断是否需要修改：
- 需要修改：[简要说明修改方向和范围] → 执行 STEP 4.2.1.1
- 不需要修改：[说明理由] → 执行 STEP 4.2.1.2
```

**追加回答格式（针对追问）：**
```
追加回答：
[回答内容]
- agent の回答

根据以上回答，判断是否需要修改：
- 需要修改：[简要说明修改方向和范围] → 执行 STEP 4.2.1.1
- 不需要修改：[说明理由] → 执行 STEP 4.2.1.2
```

**STEP 4.2.1.1 — 需要修改的处理：**
```bash
# 添加 bug 或 enhancement label（根据性质判断）
gh issue edit $ISSUE_NUMBER --repo "$OWNER/$REPO" --add-label "bug"   # 或 enhancement
```
→ 继续进入 STEP 4.2.2 范畴（该 issue 将在下一轮或本轮后续被 4.2.2 处理）

**STEP 4.2.1.2 — 不需要修改的处理：**
无需添加任何新 label，回答已在上方追加，无需进一步操作。

---

##### STEP 4.2.2 — 处理含 `bug` / `enhancement` 标签的 Issues

阅读完整问题链，分析是否有完整的修改方案：

```
IF 问题链完整且能给出具体修改方案
  → 直接创建 sub-issue（无需再向用户确认）
  → 执行 STEP 4.2.2.A

IF 问题链不完整或无法给出修改方案
  → 遵循 STEP 4.2.1.2 原则
  → 追加回答（格式遵循 4.2.1 的回答格式），说明缺少哪些信息
  → 不添加任何新 label
```

**STEP 4.2.2.A — 创建 Sub-Issue：**

Sub-issue Title 格式：
```
CHANGING: issue#XXX-简短描述
```

Sub-issue Body 格式（单文件）：
```
文件名:
path/to/file.ext

修改前
[修改前的内容]

修改后
[修改后的内容]
```

Sub-issue Body 格式（多文件）：
```
改修点 1：
文件名:
path/to/file1.ext

修改前
[修改前的内容]

修改后
[修改后的内容]

------------------------------------------------------

改修点 2：
文件名:
path/to/file2.ext

修改前
[修改前的内容]

修改后
[修改后的内容]
```

Sub-issue Labels：添加 `Revision`

```bash
# 创建 sub-issue
gh issue create --repo "$OWNER/$REPO" \
  --title "CHANGING: issue#XXX-简短描述" \
  --body "[按上方格式生成的 body]" \
  --label "Revision"
```

---

##### STEP 4.2.3 — 处理含 `Revision` 标签的 Issues

阅读 issue 的所有 comments，找到**最新一条非 agent 的回复**（即人类用户的回复），按以下逻辑判断：

```
IF 最新用户回复包含确认修改意图
  关键词：确认修改 / 可以改 / OK go ahead / LGTM / 请改 / 对的改吧 等
  → 直接执行修改，无需再向用户确认
  → 按 sub-issue body 中的修改方案修改本地文件
  → 确认本地文件与远程同步（git pull）
  → 修改完成后推送，并追加回复：
    「回答：
     √ 修改完成，等待确认 :)
     - agent の回答」

IF 最新用户回复是确认完成 / OK / 看起来没问题 等含义
  → 关闭该 sub-issue
  → 查找 sub-issue 对应的父 issue（从 title 中解析 issue# 编号）
  → 检查父 issue 下是否还有其他 open 状态的 sub-issue
  → IF 所有 sub-issue 均已关闭
    → 追加父 issue 回复：
      「回答：
       所有相关修改均已完成并确认，即将关闭本 issue。如有疑问请重新 open。
       - agent の回答」
    → 关闭父 issue

IF 最新用户回复是暂停指令（如：等等 / 请暂停 / 停止改修 等）
  → 无需修改任何内容，跳过

IF 最新用户回复是疑问 / 修改有误 / 不对等含义
  → 重新确认本地文件是否按 sub-issue 的修改内容正确修改
  → 确认本地文件与远程文件同步（git pull / git diff）
  → 再次修改并推送
  → 追加回复：
    「回答：
     √ 再次修改完成，等待确认 :)
     - agent の回答」

IF 最后一条回复是 agent 自己的回复（等待确认中）
  → 无需任何操作，跳过
```

```bash
# 关闭 issue
gh issue close $ISSUE_NUMBER --repo "$OWNER/$REPO"

# 添加 issue 评论
gh issue comment $ISSUE_NUMBER --repo "$OWNER/$REPO" --body "[回复内容]"
```

---

### STEP 5 — Stale Issue 检查（定时作业时执行）

```bash
# 获取所有 open issues，找出超过 30 天无任何回复的
gh issue list --repo "$OWNER/$REPO" \
  --state open \
  --json number,title,labels,comments,updatedAt \
  > /tmp/issues_all.json
```

判断条件：距离最后一条 comment（或 issue 创建时间，如无 comment）超过 **30 天**，且不含 `stale` label。

```
IF 符合条件的 issue
  → 添加 stale label（如不存在则先创建）
  → 追加回复：
    「此 issue 已超过 30 天没有新的回复，请确认问题是否仍然存在。
     如问题已解决请关闭此 issue；如仍需帮助请回复以继续讨论。」
  → ⚠️ 严格禁止自动关闭 issue
```

```bash
gh label create "stale" --repo "$OWNER/$REPO" \
  --color "ededed" --description "超过 30 天无回复" 2>/dev/null || true

gh issue edit $ISSUE_NUMBER --repo "$OWNER/$REPO" --add-label "stale"
gh issue comment $ISSUE_NUMBER --repo "$OWNER/$REPO" --body "[提醒内容]"
```

---

### STEP 6 — 进度日报（定时作业且 daily_report: true 时执行）

```bash
# 获取今天（过去 24 小时）的 issues 统计
SINCE=$(date -d '1 day ago' --utc +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
        || date -v-1d -u +%Y-%m-%dT%H:%M:%SZ)

# 新增的 issues
gh issue list --repo "$OWNER/$REPO" --state all \
  --json number,title,state,labels,createdAt \
  | jq --arg since "$SINCE" '[.[] | select(.createdAt >= $since)]' \
  > /tmp/report_new.json

# 今天关闭的 issues
gh issue list --repo "$OWNER/$REPO" --state closed \
  --json number,title,state,labels,closedAt \
  | jq --arg since "$SINCE" '[.[] | select(.closedAt >= $since)]' \
  > /tmp/report_closed.json

# 当前 open issues 总数
gh issue list --repo "$OWNER/$REPO" --state open --json number | jq length \
  > /tmp/report_open_count.json
```

**日报格式：**
```
📊 Daily Report｜[YYYY-MM-DD]

📥 今日新增 Issues：N 件
  - #XX 标题
  - #XX 标题

✅ 今日关闭 Issues：N 件
  - #XX 标题
  - #XX 标题

📌 当前 Open Issues 总数：N 件

🏷️ 标签分布（Open Issues）
  - bug: N
  - enhancement: N
  - question: N
  - help wanted: N
  - Revision: N
  - stale: N
  - 其他：N
```

日报写入位置：**在指定 Project 下创建一个新 Issue**，标题为：
```
[Daily Report] YYYY-MM-DD
```
Labels：`report`（不存在则先创建）

```bash
gh issue create --repo "$OWNER/$REPO" \
  --title "[Daily Report] $(date +%Y-%m-%d)" \
  --body "[日报内容]" \
  --label "report"
```

---

## 执行结果摘要输出

每次执行完成后，向用户输出摘要：

```
✅ 执行完成｜[执行时间]

仓库：owner/repo
Project：[project name]

STEP 4.1 无标签 Issues 处理：N 件
  - #XX 添加了 [label]
  - #XX 标记为 duplicate（参考 #YY）

STEP 4.2.1 question/help wanted Issues 处理：N 件
  - #XX 追加了回答（需要修改 → 已添加 bug label）
  - #XX 追加了回答（无需修改）

STEP 4.2.2 bug/enhancement Issues 处理：N 件
  - #XX 创建了 sub-issue #YY

STEP 4.2.3 Revision Issues 处理：N 件
  - #XX 修改完成，等待确认
  - #YY 关闭（对应父 issue #ZZ 也已关闭）

STEP 5 Stale 检查：N 件提醒
STEP 6 日报：已创建 issue #XX
```

---

## 注意事项

- **所有 label 操作只添加，不删除**
- **所有 issue 操作只追加 comment，不编辑或删除已有 comment**
- **修改本地文件前必须先 git pull，确保与远程同步**
- **定时作业失败时修改 status 为 paused，不删除作业**
- **发现任何不确定的情况，优先追加 comment 询问，不擅自决定**
