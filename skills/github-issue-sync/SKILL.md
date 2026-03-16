---
name: github-issue-sync
description: >
  当用户提到要根据 GitHub Issues 修改本地文件、同步 issue 改修内容、处理 GitHub 仓库的待办修改、或者说"帮我看看 issues 要改什么"时，立即触发此 skill。
  适用场景：用户输入仓库名或 URL，想要自动拉取待确认的 issue，分析改修内容，确认后修改本地文件并推送到 GitHub，最后在 issue 下回复完成通知。
  即使用户只是说"把 issue 的改修做掉"、"按 issues 改代码"、"同步一下 github 的修改需求"也应触发此 skill。
---

# GitHub Issue Sync Skill

根据 GitHub Issues 中已确认的修改需求，分析、整理、执行本地文件改修并自动推送至 GitHub。

---

## 前置条件检查

在开始任何操作前，先验证环境：

```bash
# 检查 git 配置
git config --global user.name
git config --global user.email

# 检查 GitHub CLI 或 gh token
gh auth status 2>/dev/null || echo "gh CLI 未配置"

# 检查 git remote 及仓库访问
git remote -v
```

**若 GitHub 用户信息未配置**，停下来向用户询问：
- GitHub username
- GitHub email  
- Personal Access Token（需要 `repo` + `issues` 权限）

然后执行：
```bash
git config --global user.name "USER_NAME"
git config --global user.email "USER_EMAIL"
gh auth login --with-token <<< "TOKEN"
```

---

## 完整工作流程

### STEP 1 — 解析输入，确认仓库

从用户输入中提取仓库信息：
- 完整 URL 格式：`https://github.com/owner/repo`
- 简写格式：`owner/repo` 或仅 `repo`（owner 从 git config 取）

```bash
OWNER=$(git config --global user.name)  # 或从输入解析
REPO="仓库名"
```

克隆或确认本地仓库存在：
```bash
# 若本地不存在则克隆
if [ ! -d "$REPO" ]; then
  gh repo clone "$OWNER/$REPO"
fi
cd "$REPO"
git pull origin main  # 确保最新
```

---

### STEP 2 — 拉取并筛选 Issues

#### 2.1 获取"待处理"Issues 清单

**条件：**
- 状态为 `open`（未关闭）
- 最新回复中包含**确认改修关键词**（见下方）

**确认改修关键词（满足任一即视为已确认）：**
```
确认 / 同意 / OK / LGTM / approved / 请修改 / 可以改 / 去改吧
please fix / confirmed / go ahead / fix this / 修正してください / 対応お願い
```

```bash
# 获取所有 open issues（含 comments）
gh issue list --repo "$OWNER/$REPO" --state open --json number,title,body,comments,updatedAt \
  > /tmp/issues_raw.json
```

用脚本过滤出最新评论包含确认关键词的 issues，输出 issue 号列表。

#### 2.2 分析每个 Issue 的改修内容

对每个筛选出的 issue，阅读**完整对话链**（包括 body + 所有 comments），判断：
- 需要修改哪个文件（`file`）
- 修改的位置（函数名 / 行范围 / 类名等）
- 修改的具体内容（issue 中讨论的方案）

#### 2.3 冲突检测与改修方案推导

检查所有待处理 issue 之间是否存在冲突：

**冲突类型：**
| 类型 | 说明 |
|------|------|
| 文件冲突 | 两个 issue 修改同一文件同一位置 |
| 逻辑冲突 | A 的改修会使 B 的需求失效 |
| 顺序依赖 | B 依赖 A 完成后才能改 |

**处理规则：**
- 有冲突 → 重新推导合并方案，使两者都能满足
- 无法合并 → 标记为 `⚠️ 需用户确认`，在 STEP 2.4 中说明
- 有顺序依赖 → 调整清单顺序，确保前置 issue 先执行

---

### STEP 2.4 — 向用户展示改修清单（必须用户确认才能继续）

以如下格式输出**改修清单**，顺序即为执行顺序：

```
📋 改修清单（共 N 项）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID: 1
Issue: #42 · 修复登录页面的输入验证
File: src/pages/Login.tsx
Where: validateInput() 函数，第 34–51 行
How:
  [Issue 中的讨论方案] 在提交前检查 email 格式
  [最终改修方案] 新增正则验证 /^[^\s@]+@[^\s@]+\.[^\s@]+$/，验证失败时设置 errorMsg 状态
Risk: 🟢 低（只影响前端验证逻辑）
Status: pending

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID: 2
Issue: #38 · API 返回格式统一
File: src/api/userService.ts
Where: getUser() 和 updateUser() 函数
How:
  [Issue 中的讨论方案] 统一 response wrapper 格式
  [最终改修方案] 所有返回值统一为 { success, data, error } 结构
Risk: 🟡 中（需确认调用方是否有其他依赖）
Status: pending

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID: 3
Issue: #35 · 删除旧版认证逻辑
File: src/utils/auth.ts
Where: legacyAuth() 函数（第 89–120 行）
How:
  [Issue 中的讨论方案] 直接删除
  [最终改修方案] ⚠️ 无法直接删除：src/middleware/session.ts 第 15 行仍有调用。
              建议：先在 #38 完成后，再由用户决定是否一并重构。
              → 此项暂时跳过，请确认处理方式。
Risk: 🔴 高（存在依赖，需额外确认）
Status: ⚠️ 待确认
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

请确认：
A) 没问题，按此清单执行
B) 有问题，我来说明（将重新分析）
C) 放弃修改
```

**清单字段说明：**

| 字段 | 内容 |
|------|------|
| `ID` | 执行顺序（整数） |
| `Issue` | 来源 issue 号和标题 |
| `File` | 需要修改的文件路径 |
| `Where` | 改修的精确位置（函数名/行号/类名） |
| `How` | issue 原始讨论方案 + 最终推导出的改修方案 |
| `Risk` | 🟢低 / 🟡中 / 🔴高（说明原因） |
| `Status` | `pending` / `⚠️ 待确认` / `skipped` |

---

### STEP 2.5 — 处理用户回复

**用户选 A（没问题）** → 进入 STEP 2.6

**用户选 B（有问题）** → 
  - 听取用户的意见或补充
  - 返回 STEP 2.2，重新分析（不需要重新拉 issues）
  - 重新生成清单，再次请用户确认
  - 循环直到用户选 A 或 C

**用户选 C（放弃修改）** → 
  - 回复：「好的，本次修改已取消。如需再次处理请重新发起。」
  - 终止流程

---

### STEP 2.6 — 执行本地文件改修

**严格按照清单顺序执行，逐项操作：**

```bash
# 创建改修分支（推荐，更安全）
BRANCH="issue-sync-$(date +%Y%m%d-%H%M)"
git checkout -b "$BRANCH"
```

每项改修：
1. 读取对应文件当前内容
2. 严格按照清单中 `How` 的最终改修方案执行
3. **不得擅自扩展改修范围**（仅改清单内的内容）
4. 改完后简单验证文件语法（如果有对应工具）

```bash
# 示例：检查 TypeScript/JS 语法
npx tsc --noEmit 2>/dev/null || echo "注意：语法检查失败，请人工确认"
```

所有项完成后：
```bash
git add -A
git commit -m "fix: apply changes from issues #XX, #YY, #ZZ

- Issue #XX: [简要描述]
- Issue #YY: [简要描述]
- Issue #ZZ: [简要描述]"

git push origin "$BRANCH"
```

> ⚙️ **关于推送方式（默认行为）**：
> - 默认推送至独立 branch（`issue-sync-日期`），更安全
> - 如用户希望直接推 main，需在初始输入中明确说明 `--push-main`

---

### STEP 2.7 — 在对应 Issues 下回复通知

对每个已完成的 issue，自动回复：

```bash
gh issue comment $ISSUE_NUMBER --repo "$OWNER/$REPO" \
  --body "✅ 改修完成，请确认！

- 分支：\`$BRANCH\`
- Commit：\`$COMMIT_HASH\`
- 修改内容：[简要说明]

如无问题可关闭此 issue。"
```

---

### STEP 2.8 — 返回结果给用户

输出简洁的结果摘要，例如：

```
✅ 全部完成！

已处理 Issues：#38, #42
跳过：#35（存在依赖，已在 issue 下说明）
推送分支：issue-sync-20260316-1423
已在对应 issues 下回复完成通知。

👉 请前往 GitHub 确认改修内容是否正确，如无问题可合并分支。
```

---

## 注意事项

- **绝对不修改清单以外的内容**，即使看起来顺手也不行
- **Risk 🔴 的项目**，改修前再次向用户口头确认一次
- 若执行过程中报错，立即停止并告知用户，不继续后续项目
- 若仓库没有找到任何符合条件的 open issue，直接告知用户：「未找到含确认关键词的 open issues」
