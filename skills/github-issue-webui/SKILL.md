---
name: github-issue-webui
description: >
  当用户想通过可视化界面处理、审核或批量操作 GitHub Issues 时，立即触发此 skill。
  适用场景：用户想查看项目 issues 并决定对每个 issue 执行什么操作（确认/修改/方案/分析/关闭/移交等）、
  想通过 WebUI 表单批量处理 issues、想在提交前预览和确认所有操作。
  即使用户只说"帮我看看 issues"、"用界面处理 github 问题"、"批量处理 issues"也应触发此 skill。
---

# GitHub Issue WebUI Skill

通过本地 Gradio WebUI 可视化审核和批量处理 GitHub Project Issues，
所有操作必须经用户在 UI 上确认提交后才能执行，严禁提前操作。

---

## ⛔ 最高优先级禁止事项（任何情况均不得违反）

```
严格禁止  用户提交前 私自修改 project
严格禁止  用户提交前 私自修改 文件
严格禁止  用户提交前 私自修改 issue
严格禁止  用户提交前 私自给出意见
严格禁止  暴露用户仓库文件的隐私内容
严格禁止  暴露自己提交了什么（用户自行去 GitHub 确认）
严格禁止  在本地留下任何 log 文件
```

---

## STEP 1 — GitHub 认证检查

```bash
gh auth status 2>&1
```

```
IF 认证失败或未配置
  → 向用户询问：
    「请提供以下信息以连接 GitHub：
      1. GitHub Personal Access Token（需要 repo + project 权限）
      2. 执行：gh auth login --with-token <<< "YOUR_TOKEN"」
  → 用户配置完成后重新执行 STEP 1

IF OK → 继续 STEP 2
```

---

## STEP 2 — 查询所有 Project 并过滤

```bash
# 获取当前用户
GH_USER=$(gh api user --jq '.login')

# 获取用户所有 projects（最多100个）
gh project list --owner "$GH_USER" --format json --limit 100 > /tmp/giu_projects_raw.json

# 也查询所有可访问的组织 projects（如有）
# gh project list --owner "ORG_NAME" --format json >> /tmp/giu_projects_raw.json
```

对每个 project，查询其关联 issues：

```bash
# 获取 project 内的 items（issues）
gh project item-list PROJECT_NUMBER \
  --owner "$GH_USER" \
  --format json \
  --limit 200 \
  | jq '[.items[] | select(.type == "ISSUE")]' \
  > /tmp/giu_project_items_${PROJECT_NUMBER}.json
```

**过滤规则（以下 project 不参与后续流程）：**
- project 内没有任何 issue 的
- project 内所有 issue 均为 closed 状态的

```
IF 过滤后没有任何 project
  → 输出：「YYYY-MM-DD HH:MM:SS 查询完成，当前所有 project 均无待处理 issues。」
  → 结束本次执行

IF 过滤后有可用 project → 继续 STEP 3
```

---

## STEP 3 — 向用户展示 Project 清单并询问操作对象

输出格式（严格遵守）：

```
YYYY-MM-DD HH:MM:SS 查询到以下结果

project <名称>  issues <N>个  关联仓库 <repo1>, <repo2>
project <名称>  issues <N>个  关联仓库 <repo1>
...

请输入要操作的 project 名称（或编号）：
```

对每个 project 列出的 issues：

```bash
# 获取 project 内 open issues 详情（含 issue 编号、仓库、标题、labels、comments）
gh project item-list PROJECT_NUMBER \
  --owner "$GH_USER" \
  --format json \
  | jq '[.items[] | select(.type=="ISSUE" and .status!="Done" and .status!="Closed")]'
```

```
IF 用户选择了 project → 继续 STEP 4
IF 用户取消 → 结束
```

---

## STEP 4 — 检查或创建 WebUI

### 4.1 检查 WebUI 是否存在

```bash
SKILL_DIR="$(dirname "$0")"   # skill 所在目录
WEBUI_PATH="${SKILL_DIR}/webui/app.py"

ls -la "$WEBUI_PATH" 2>&1
python3 -c "
import ast, sys
with open('${WEBUI_PATH}') as f: src = f.read()
tree = ast.parse(src)
names = [n.name if hasattr(n,'name') else '' for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
# 验证必要组件
required = ['gradio', 'subprocess']
missing = [r for r in required if not any(r in str(n) for n in ast.walk(tree))]
print('OK' if not missing else 'MISSING:'+','.join(missing))
"
```

```
IF app.py 存在且包含 gradio 和 subprocess → 跳转 STEP 5
IF app.py 不存在或格式不符合 → 执行 STEP 4.2
```

### 4.2 创建 WebUI 脚本

参考 `webui/app.py` 模板（见本 skill 的 webui/ 目录）。
如模板文件存在，直接复制并根据当前 project 数据填充；
如模板不存在，按本 SKILL.md 附录的 WebUI 规范从头生成。

**WebUI 必须包含的功能：**

| 区域 | 内容 |
|------|------|
| **Header** | `project: <名称>  YYYY/MM/DD HH:MM:SS` |
| **Body - 列1** | Checkbox 选中=操作对象，不选=忽略 |
| **Body - 列2** | Issue 编号（升序排列） |
| **Body - 列3** | Issue 标题 |
| **Body - 列4** | Labels（多个时显示第一个 + `...`） |
| **Body - 列5** | Comments 折叠按钮（默认收起，点击展开完整内容，仿 GitHub 样式，只读） |
| **Body - 列6** | Require 下拉框（默认空白，选项见下方） |
| **Footer** | 确认按钮（含校验 + 二次确认弹窗） |

**Require 下拉选项及 AI 行为规范：**

| 选项 | AI 行为（严格执行） |
|------|-------------------|
| `确认` | 仅追加 comment 回答，**不得修改任何文件** |
| `修改` | 根据上下文修改相关文件，完成后追加 comment：`已经完成修改，请确认` |
| `方案` | 不修改文件，仅在 comment 中给出完整解决方案 |
| `分析` | 对 issue 内容进行深度分析，在 comment 中输出分析报告 |
| `关闭` | 追加关闭说明 comment 后关闭 issue（需用户在弹窗中再次确认） |
| `移交` | 追加 comment 说明需要人工跟进的原因，添加 `needs-human` label |
| `暂挂` | 追加 comment：「此 issue 暂时挂起，待后续跟进」，添加 `on-hold` label |

**所有 AI comment 末尾必须附加（换行后）：**
```
------请注意这是AI做出的评论内容
```

**Footer 确认按钮逻辑：**
```
1. 检查所有勾选的 issue：
   IF 任何勾选 issue 的 Require 为空白
     → 显示错误提示：「issue#XX 请选择 require」
     → 不继续处理

2. 全部校验通过 → 弹出确认对话框：
   「请确认是否提交：
    issue#XX：XX（require 名称）
    issue#YY：YY（require 名称）
    ...
    [确认] [取消]」

3. 用户点击确认 → 组织提示词 → 调用 AI 执行 task → 关闭 WebUI
4. 用户点击取消 → 返回 UI 画面
```

创建完成后继续 STEP 5。

---

## STEP 5 — 启动 WebUI 并等待用户提交

```bash
# 获取本机 IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

# 查找可用端口（从 7860 开始扫描）
for PORT in $(seq 7860 7900); do
  if ! lsof -i :$PORT > /dev/null 2>&1; then
    AVAILABLE_PORT=$PORT
    break
  fi
done

# 传入 project 数据并启动
ISSUES_JSON='<从 STEP 3 收集的 issues JSON>' \
PROJECT_NAME='<project 名称>' \
python3 "${SKILL_DIR}/webui/app.py" \
  --host 0.0.0.0 \
  --port "$AVAILABLE_PORT" \
  --issues-json "$ISSUES_JSON" &

WEBUI_PID=$!
```

向用户发送链接：

```
WebUI 已启动，请在浏览器中打开：
http://<LOCAL_IP>:<PORT>

等待您在表单中确认提交后自动执行...
```

等待 WebUI 进程提交信号（WebUI 内部通过 flag file 或 callback 通知）。

---

## STEP 6 — 执行 AI Task

WebUI 提交后，根据每个 issue 的 require 依次执行：

### 执行顺序

1. 读取提交的 issue + require 列表
2. 对每个 issue，按 require 类型构建专用 prompt（见下方）
3. 调用 AI 处理，将结果通过 `gh issue comment` 推送到 GitHub
4. 特殊 require（修改/关闭/移交/暂挂）按对应规则执行额外操作

### 各 Require 的 Prompt 模板

**确认：**
```
你是一个 GitHub issue 助手。
请仔细阅读以下 issue 的完整内容（标题、描述、所有 comment），
然后给出一个确认回答。你只能追加 comment，不能修改任何文件。

Issue #<N>：<title>
内容：<body + comments>

请用简洁专业的语言回答这个 issue。
```

**修改：**
```
你是一个代码修改助手。
请仔细阅读以下 issue 的内容，找到需要修改的文件，
执行修改后追加 comment：「已经完成修改，请确认」。

Issue #<N>：<title>
内容：<body + comments>
相关仓库：<owner/repo>

请分析需要修改什么文件，然后执行修改并推送。
```

**方案：**
```
你是一个技术方案规划师。
请基于以下 issue 内容，给出一个完整的解决方案（不执行修改，只输出方案）。

Issue #<N>：<title>
内容：<body + comments>

请输出完整方案，包括：问题分析、解决思路、具体步骤、潜在风险。
```

**分析：**
```
你是一个技术分析师。
请对以下 issue 进行深度分析，输出分析报告。

Issue #<N>：<title>
内容：<body + comments>

请输出：根本原因分析、影响范围、优先级评估、相关 issue 关联。
```

### 推送 Comment

```bash
# 所有 require 类型都通过此命令追加 comment
gh issue comment $ISSUE_NUMBER \
  --repo "$OWNER/$REPO" \
  --body "$AI_RESPONSE

------请注意这是AI做出的评论内容"

# 修改类：执行文件修改后推送
# 关闭类：
gh issue close $ISSUE_NUMBER --repo "$OWNER/$REPO" \
  --comment "根据 require 指示关闭此 issue。

------请注意这是AI做出的评论内容"

# 移交类：
gh issue edit $ISSUE_NUMBER --repo "$OWNER/$REPO" --add-label "needs-human"

# 暂挂类：
gh issue edit $ISSUE_NUMBER --repo "$OWNER/$REPO" --add-label "on-hold"
```

---

## STEP 7 — 输出执行结果

关闭 WebUI 并输出简洁结果（格式严格遵守）：

```
project <名称>  YYYY-MM-DD HH:MM:SS

issues#XX
issues#YY
...

上述所有评论或修改已推送到 GitHub。
```

**注意：结果只列出 issue 编号，不描述具体操作内容。用户自行去 GitHub 确认。**

---

## 附录：WebUI 规范参考

WebUI 的完整实现模板位于本 skill 目录的 `webui/app.py`。

**技术要求：**
- Python 3.8+
- gradio >= 4.0
- 通过环境变量接收数据：`ISSUES_JSON`、`PROJECT_NAME`
- 端口通过命令行参数 `--port` 传入
- 提交完成后通过写入 `/tmp/giu_submit_result.json` 通知主流程
- 启动后主动打印访问地址

**样式要求：**
- 整体风格参考 GitHub Issues 页面（深色/浅色跟随系统）
- Comment 折叠区仿照 GitHub comment 卡片样式（头像占位 + 圆角边框 + 时间戳）
- Require 下拉框使用 Gradio Dropdown 组件
- 确认弹窗使用 Gradio Modal 组件

具体实现详见 `webui/app.py`。
