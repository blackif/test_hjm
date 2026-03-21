# GitHub Issues Auto Comment - Script 说明

## 📁 文件说明

| 文件 | 作用 |
|------|------|
| `ai_caller.py` | AI 调用模块 - 调用 Bailian/Qwen 生成 AI 回答 |
| `app.py` | 主程序入口（定时作业执行） |
| `launch-github-webui.sh` | WebUI 启动脚本（可选，用于调试） |

---

## 🤖 Require 选项说明

| 选项 | AI 行为 |
|------|--------|
| **确认** | 仅追加 comment 回答，**不得修改任何文件** |
| **修改** | 根据上下文修改相关文件，完成后追加 comment：`已经完成修改，请确认` |
| **方案** | 不修改文件，仅在 comment 中给出完整解决方案 |
| **分析** | 对 issue 内容进行深度分析，在 comment 中输出分析报告 |
| **关闭** | 追加关闭说明 comment 后关闭 issue |
| **移交** | 追加 comment 说明需要人工跟进的原因，添加 `needs-human` label |
| **暂挂** | 追加 comment：「此 issue 暂时挂起，待后续跟进」，添加 `on-hold` label |

**所有 AI comment 末尾必须附加：**
```
------请注意这是 AI 做出的评论内容
```

---

## 🔧 AI Caller 说明

**`ai_caller.py` 的作用：**

1. **调用 AI 生成回答** - 使用 OpenAI 兼容格式调用 Bailian/Qwen API
2. **获取配置** - 从 `~/.openclaw/openclaw.json` 读取 API Key 和模型配置
3. **返回 AI 回答** - 将生成的文本返回给调用方

**不是**仅仅检查 AI 是否可以调用，而是**实际调用 AI 并获取回答**。

---

## 📝 使用示例

```python
from ai_caller import call_ai_api

prompt = "你是一个 GitHub issue 助手。请回答以下 issue...\n\nIssue #47: ..."
response = call_ai_api(prompt)
print(response)  # AI 生成的回答
```

---

## 🔑 配置要求

**环境变量或配置文件：**

| 配置项 | 说明 | 来源 |
|--------|------|------|
| `DASHSCOPE_API_KEY` | AI API Key | 环境变量 |
| `~/.openclaw/openclaw.json` | OpenClaw 配置（含 API Key） | 配置文件 |

**API 端点：**
- `https://coding.dashscope.aliyuncs.com/v1/chat/completions`

**模型：**
- `qwen3.5-plus`

---

## 📦 依赖

- Python 3.8+
- `gh` CLI（已认证）
- 网络连接（访问 GitHub API 和 DashScope API）
