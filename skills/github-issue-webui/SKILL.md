---
name: github-issue-webui
description: >
  当用户想通过可视化界面处理、审核或批量操作 GitHub Issues 时，立即触发此 skill。
  适用场景：用户想查看项目 issues 并决定对每个 issue 执行什么操作（确认/修改/方案/分析/关闭/移交等）、
  想通过 WebUI 表单批量处理 issues、想在提交前预览和确认所有操作。
  即使用户只说"帮我看看 issues"、"用界面处理 github 问题"、"批量处理 issues"也应触发此 skill。
---

# GitHub Issue WebUI Skill

通过本地 Gradio WebUI 可视化审核和批量处理 GitHub Issues，
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
    「请执行：gh auth login」
  → 用户配置完成后重新执行 STEP 1

IF OK → 继续 STEP 2
```

---

## STEP 2 — 查询 Issues 并准备数据

```bash
# 获取指定仓库的开放 issues
REPO="${REPO:-blackif/claw_hjm}"
ISSUES_JSON=$(gh issue list --repo "$REPO" --state open \
  --json number,title,body,createdAt,updatedAt,author,labels,comments \
  --limit 100)

# 添加 owner 和 repo 字段
ISSUES_WITH_REPO=$(echo "$ISSUES_JSON" | jq --arg repo "$REPO" '
  .[] | . + {
    owner: ($repo | split("/")[0]),
    repo: $repo
  }
' | jq -s '.')
```

```
IF 没有任何 issues
  → 输出：「当前仓库没有开放的 issues。」
  → 结束本次执行

IF 有可用 issues → 继续 STEP 3
```

---

## STEP 3 — 启动 WebUI

```bash
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_PATH="${SKILL_DIR}/script/launch-github-webui.sh"

# 检查启动脚本
if [ ! -f "$SCRIPT_PATH" ]; then
  echo "❌ 启动脚本不存在：$SCRIPT_PATH"
  exit 1
fi

# 启动 WebUI
"$SCRIPT_PATH" "$REPO" "Issues Review"
```

向用户发送访问链接：

```
WebUI 已启动，请在浏览器中打开：
http://<你的服务器公网 IP>:7860

注意：请确保防火墙已开放 TCP 7860 端口。
如使用 SSH 隧道，请执行：ssh -L 7860:localhost:7860 ubuntu@<服务器公网 IP>
然后访问：http://localhost:7860

等待您在表单中确认提交后自动执行...
```

---

## STEP 4 — 用户操作流程（WebUI 界面）

### 4.1 界面结构

| 区域 | 内容 |
|------|------|
| **Header** | `项目名称  N Issues` |
| **Body - 每行** | Checkbox + Issue 编号 + 标题 + 💬评论按钮 + Require 下拉框 |
| **Footer** | 📖 Require 说明按钮 + ✅ 确认提交按钮 |

### 4.2 Require 选项说明

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
------请注意这是 AI 做出的评论内容
```

### 4.3 提交流程

1. **勾选 Issues** - 用户勾选需要处理的 issue
2. **选择 Require** - 为每个勾选的 issue 选择操作类型
3. **点击确认提交** - 弹出二次确认对话框
4. **再次确认** - 用户点击"✅ 确认提交"
5. **异步执行** - 立即显示成功消息，后台执行 AI 任务
6. **完成** - 用户前往 GitHub 确认结果

**确认对话框内容：**
```
请确认提交内容：
- issue#XX：标题（require 名称）
- issue#YY：标题（require 名称）
...

[✅ 确认提交] [取消]
```

---

## STEP 5 — 执行 AI Task

WebUI 提交后，根据每个 issue 的 require 依次执行：

### 5.1 AI 调用方式

使用 OpenAI 兼容 API 格式调用 Bailian/Qwen：

```python
import json
from urllib.request import urlopen, Request

def call_ai(prompt: str) -> str:
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    
    data = json.dumps({
        "model": "qwen3.5-plus",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.7
    }).encode('utf-8')
    
    req = Request(
        "https://coding.dashscope.aliyuncs.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    
    with urlopen(req, timeout=90) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result["choices"][0]["message"]["content"]
```

### 5.2 各 Require 的 Prompt 模板

**确认：**
```
你是一个 GitHub issue 助手。
请仔细阅读以下 issue 的完整内容（标题、描述、所有 comment），
然后给出一个确认回答。你只能追加 comment，不能修改任何文件。

Issue #<N>：<title>
仓库：<owner/repo>
内容：<body + comments>

请用简洁专业的语言回答这个 issue。
```

**修改：**
```
你是一个代码修改助手。
请仔细阅读以下 issue 的内容，找到需要修改的文件，
执行修改后追加 comment：「已经完成修改，请确认」。

Issue #<N>：<title>
仓库：<owner/repo>
内容：<body + comments>

请分析需要修改什么文件，然后执行修改并推送。
```

**方案：**
```
你是一个技术方案规划师。
请基于以下 issue 内容，给出一个完整的解决方案（不执行修改，只输出方案）。

Issue #<N>：<title>
仓库：<owner/repo>
内容：<body + comments>

请输出完整方案，包括：问题分析、解决思路、具体步骤、潜在风险。
```

**分析：**
```
你是一个技术分析师。
请对以下 issue 进行深度分析，输出分析报告。

Issue #<N>：<title>
仓库：<owner/repo>
内容：<body + comments>

请输出：根本原因分析、影响范围、优先级评估、相关 issue 关联。
```

### 5.3 推送 Comment

```bash
# 所有 require 类型都通过此命令追加 comment
gh issue comment $ISSUE_NUMBER \
  --repo "$OWNER/$REPO" \
  --body "$AI_RESPONSE

------请注意这是 AI 做出的评论内容"

# 关闭类：
gh issue close $ISSUE_NUMBER --repo "$OWNER/$REPO"

# 移交类：
gh issue edit $ISSUE_NUMBER --repo "$OWNER/$REPO" --add-label "needs-human"

# 暂挂类：
gh issue edit $ISSUE_NUMBER --repo "$OWNER/$REPO" --add-label "on-hold"
```

---

## STEP 6 — 输出执行结果

WebUI 提交后自动关闭，向用户输出简洁结果：

```
✅ 提交完成！请前往 GitHub 确认结果。

https://github.com/<owner>/<repo>/issues
```

**注意：结果不描述具体操作内容，用户自行去 GitHub 确认。**

---

## 附录：文件结构

```
skills/github-issue-webui/
├── .gradio/              # Gradio 配置
├── SKILL.md              # 本文件
└── script/               # 执行脚本
    ├── app.py            # WebUI 主程序
    ├── ai_caller.py      # AI 调用模块
    └── launch-github-webui.sh  # 启动脚本
```

### 启动脚本参数

```bash
./script/launch-github-webui.sh [REPO] [PROJECT_NAME]

# 示例
./script/launch-github-webui.sh blackif/claw_hjm "Issues Review"
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CONFIG_FILE` | 配置文件路径 | `/home/ubuntu/.openclaw/workspace/config.json` |
| `DASHSCOPE_API_KEY` | AI API Key | 从配置文件读取 |

### 配置文件格式

```json
{
  "webui": {
    "public_host": "3.107.252.75",
    "port": 7860,
    "theme": "light"
  },
  "api": {
    "dashscope_key": "sk-xxxxx",
    "model": "qwen3.5-plus"
  }
}
```

---

## 技术要求

- Python 3.8+
- gradio >= 4.0
- gh CLI（已认证）
- 通过环境变量接收数据：`ISSUES_JSON`、`PROJECT_NAME`
- 提交完成后写入 `/tmp/giu_submit_result.json`
- 启动后主动打印访问地址

## 样式要求

- 整体风格参考 GitHub Issues 页面
- Require 说明使用侧边栏面板展示
- 确认弹窗使用 Gradio 原生 Modal
- 成功消息使用 `gr.Info()` 异步显示
