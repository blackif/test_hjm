#!/usr/bin/env python3
"""
GitHub Issue WebUI — Gradio-based review interface (simplified)
"""

import os
import json
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import gradio as gr

# 尝试导入 requests 用于 AI 调用
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
SUBMIT_RESULT_PATH = "/tmp/giu_submit_result.json"
REQUIRE_OPTIONS    = ["", "确认", "修改", "方案", "分析", "关闭", "移交", "暂挂"]
AI_COMMENT_FOOTER  = "\n\n------请注意这是 AI 做出的评论内容"

REQUIRE_DOCS = """
## 📖 Require 选项说明

### ✅ 确认
仅追加 comment 回答，**严禁修改任何文件**。

### ✏️ 修改
根据 issue 内容修改相关文件，完成后追加 comment：「已经完成修改，请确认」。

### 💡 方案
给出完整解决方案（问题分析 / 解决思路 / 具体步骤 / 潜在风险），**不执行修改**。

### 🔍 分析
输出深度分析报告（根本原因 / 影响范围 / 优先级 / 相关关联）。

### 🔒 关闭
撰写关闭说明 comment 后关闭该 issue。**操作不可逆，请谨慎。**

### 🤝 移交
撰写移交说明 comment，并自动添加 `needs-human` 标签。

### ⏸️ 暂挂
追加暂挂说明 comment，并自动添加 `on-hold` 标签。

---
> 所有 AI 评论末尾均附加：
> `------请注意这是 AI 做出的评论内容`
"""

# ─────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────

def load_issues():
    raw = os.environ.get("ISSUES_JSON", "[]")
    try:
        issues = json.loads(raw)
    except json.JSONDecodeError:
        issues = []
    issues.sort(key=lambda x: x.get("number", 0))
    return issues

def get_project_name():
    return os.environ.get("PROJECT_NAME", "Unknown Project")

# ─────────────────────────────────────────────
# GitHub helpers
# ─────────────────────────────────────────────

def get_full_comments(owner: str, repo: str, issue_number: int) -> str:
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_number),
             "--repo", f"{owner}/{repo}",
             "--json", "body,comments"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return f"⚠️ 无法加载评论：{result.stderr.strip()}"
        data     = json.loads(result.stdout)
        body     = data.get("body", "")
        comments = data.get("comments", [])
        lines    = [f"**Issue 内容：**\n\n{body}\n\n---\n"]
        for c in comments:
            author    = c.get("author", {}).get("login", "unknown")
            created   = c.get("createdAt", "")[:16].replace("T", " ")
            body_text = c.get("body", "")
            lines.append(f"**{author}** · {created}\n\n{body_text}\n\n---\n")
        return "".join(lines)
    except Exception as e:
        return f"⚠️ 加载失败：{e}"

# ─────────────────────────────────────────────
# AI Task execution
# ─────────────────────────────────────────────

PROMPT_TEMPLATES = {
    "确认": "你是一个 GitHub issue 助手。请仔细阅读以下 issue，给出确认回答。只能追加 comment，不能修改任何文件。\n\nIssue #{number}：{title}\n仓库：{repo}\n内容：\n{body}",
    "修改": "你是一个代码修改助手。请阅读以下 issue，找到需要修改的文件并执行修改，完成后追加 comment：「已经完成修改，请确认」。\n\nIssue #{number}：{title}\n仓库：{repo}\n内容：\n{body}",
    "方案": "你是一个技术方案规划师。请基于以下 issue 给出完整解决方案（不执行修改）。包括：问题分析、解决思路、具体步骤、潜在风险。\n\nIssue #{number}：{title}\n仓库：{repo}\n内容：\n{body}",
    "分析": "你是一个技术分析师。请对以下 issue 进行深度分析：根本原因、影响范围、优先级评估、相关关联。\n\nIssue #{number}：{title}\n仓库：{repo}\n内容：\n{body}",
    "关闭": "你是一个 GitHub issue 助手。请为以下 issue 撰写关闭说明 comment，然后关闭此 issue。\n\nIssue #{number}：{title}\n仓库：{repo}\n内容：\n{body}",
    "移交": "你是一个 GitHub issue 助手。请为以下 issue 撰写移交说明 comment，说明需要人工跟进的原因。\n\nIssue #{number}：{title}\n仓库：{repo}\n内容：\n{body}",
    "暂挂": "你是一个 GitHub issue 助手。请为以下 issue 撰写暂挂说明 comment。\n\nIssue #{number}：{title}\n仓库：{repo}\n内容：\n{body}",
}

def push_comment(owner, repo, issue_number, body) -> tuple:
    """追加评论到 GitHub Issue，返回 (success, error_msg)"""
    try:
        result = subprocess.run(
            ["gh", "issue", "comment", str(issue_number),
             "--repo", f"{owner}/{repo}",
             "--body", body + AI_COMMENT_FOOTER],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return (True, "")
        else:
            return (False, result.stderr[:300])
    except Exception as e:
        return (False, str(e)[:200])

def call_ai_api(prompt: str) -> str:
    """
    调用 AI 生成回答 - 使用 ai_caller.py 脚本
    """
    script_path = Path(__file__).parent / "ai_caller.py"
    
    if not script_path.exists():
        return "⚠️ AI 调用脚本不存在：ai_caller.py"
    
    try:
        # 截断 prompt 避免过长
        prompt = prompt[:3000]
        
        result = subprocess.run(
            ["python3", str(script_path), prompt],
            capture_output=True, text=True, timeout=120
        )
        
        if result.returncode == 0 and result.stdout.strip():
            output = result.stdout.strip()
            if output.startswith("⚠️") or output.startswith("❌"):
                return output
            return output
        else:
            error = result.stderr[:300] or result.stdout[:300]
            return f"❌ AI 调用失败：{error}"
    
    except subprocess.TimeoutExpired:
        return "⏱️ AI 调用超时（>120 秒），请稍后重试"
    except Exception as e:
        return f"❌ AI 调用异常：{str(e)[:200]}"


def execute_task(issue: dict, require: str) -> dict:
    import sys
    number    = issue.get("number")
    title     = issue.get("title", "")
    repo      = issue.get("repo", "")
    owner     = issue.get("owner", "")
    body_text = issue.get("body", "") + "\n\n" + "\n---\n".join(
        c.get("body", "") for c in issue.get("comments", []))
    
    prompt = PROMPT_TEMPLATES.get(require, PROMPT_TEMPLATES["确认"]).format(
        number=number, title=title, repo=repo, body=body_text[:3000])
    
    success = True
    error_msg = ""
    ai_response = ""
    comment_success = True

    try:
        # 调用 AI 生成回答
        ai_response = call_ai_api(prompt)
        
        # 追加评论（除了"修改"操作）
        if require != "修改":
            comment_success, comment_error = push_comment(owner, repo, number, ai_response)
            if not comment_success:
                error_msg = f"评论失败：{comment_error}"
                success = False
        
        # 执行特殊操作
        if require == "关闭":
            result = subprocess.run(
                ["gh", "issue", "close", str(number), "--repo", f"{owner}/{repo}"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                success = False
                error_msg += f"; 关闭失败：{result.stderr[:200]}"
        elif require == "移交":
            result = subprocess.run(
                ["gh", "issue", "edit", str(number), "--repo", f"{owner}/{repo}",
                 "--add-label", "needs-human"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                success = False
                error_msg += f"; 移交失败：{result.stderr[:200]}"
        elif require == "暂挂":
            result = subprocess.run(
                ["gh", "issue", "edit", str(number), "--repo", f"{owner}/{repo}",
                 "--add-label", "on-hold"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                success = False
                error_msg += f"; 暂挂失败：{result.stderr[:200]}"
    except Exception as e:
        success = False
        error_msg = str(e)

    # 输出日志
    print(f"[EXEC] Issue #{number} [{require}]: success={success}, ai_response_len={len(ai_response)}", file=sys.stderr)
    
    return {"number": number, "require": require, "success": success, "error": error_msg, "ai_response": ai_response[:300]}

# ─────────────────────────────────────────────
# Minimal side-panel CSS (only for the fixed overlay — no styling of content)
# ─────────────────────────────────────────────
PANEL_CSS = """
.giu-panel {
    position: fixed;
    right: 0;
    top: 0;
    width: 460px;
    height: 100%;
    background: white;
    border-left: 1px solid #e5e7eb;
    z-index: 999;
    overflow-y: auto;
    padding: 20px;
    box-shadow: -4px 0 16px rgba(0,0,0,0.1);
}
"""

# ─────────────────────────────────────────────
# Build UI
# ─────────────────────────────────────────────

def build_app(issues: list, project_name: str):

    with gr.Blocks(title="GitHub Issue WebUI") as app:

        # Hidden state to store selected issues
        submit_state = gr.State({})

        # ── Header info ──
        gr.Markdown(f"## {project_name} `{len(issues)} Issues`")
        gr.Markdown("---")

        # ── Side panel: Comments ──
        with gr.Column(visible=False, elem_classes=["giu-panel"]) as panel_comments:
            gr.Markdown("### 💬 Comments")
            panel_comments_content = gr.Markdown("")
            close_comments = gr.Button("✕ 关闭")

        # ── Side panel: Require 说明 ──
        with gr.Column(visible=False, elem_classes=["giu-panel"]) as panel_require:
            gr.Markdown(REQUIRE_DOCS)
            close_require = gr.Button("✕ 关闭")

        # ── Side panel: Confirm ──
        with gr.Column(visible=False, elem_classes=["giu-panel"]) as panel_confirm:
            gr.Markdown("### 📋 请确认是否提交")
            confirm_content = gr.Markdown("")
            with gr.Row():
                btn_ok     = gr.Button("✅ 确认提交", variant="primary")
                btn_cancel = gr.Button("取消")

        result_msg = gr.Markdown(visible=False)

        close_comments.click(fn=lambda: gr.update(visible=False), outputs=panel_comments)
        close_require.click(fn=lambda: gr.update(visible=False),  outputs=panel_require)

        # ── Issue rows ──
        checkboxes        = []
        dropdowns         = []

        for issue in issues:
            number = issue.get("number", "?")
            title  = issue.get("title", "")
            owner  = issue.get("owner", "")
            repo   = issue.get("repo", "")

            with gr.Row():
                cb  = gr.Checkbox(label=f"Issue#{number}：{title}", scale=5, container=False) 
                btn = gr.Button("💬", scale=0, min_width=40)                
                req = gr.Dropdown(choices=REQUIRE_OPTIONS, value="",
                                  container=False, scale=1, min_width=100)

            checkboxes.append(cb)
            dropdowns.append(req)

            # Bind comment button click - use closure to capture owner/repo/number
            def make_comment_handler(o, r, n):
                def handler():
                    return (gr.update(visible=True), get_full_comments(o, r, n))
                return handler
            
            btn.click(fn=make_comment_handler(owner, repo, number), outputs=[panel_comments, panel_comments_content])

        gr.Markdown("---")

        # ── Footer ──
        with gr.Row():
            btn_require = gr.Button("📖 Require 说明", scale=1)
            btn_confirm = gr.Button("✅ 确认提交", variant="primary", scale=1)

        btn_require.click(fn=lambda: gr.update(visible=True), outputs=panel_require)

        # ── Confirm handler ──
        def handle_confirm(*args):
            n    = len(issues)
            cbs  = args[:n]
            reqs = args[n:]

            if not any(cbs):
               gr.Warning("请至少勾选一个 issue", duration=6)
               return [gr.update(), gr.update(visible=False), {}] + [gr.update() for _ in range(n)]

            errors = [f"issue#{issues[i]['number']} 请选择 require"
                      for i, (c, r) in enumerate(zip(cbs, reqs)) if c and not r]
            if errors:
                gr.Warning(" ".join(errors), duration=6)
                return [gr.update(), gr.update(visible=False), {}] + [gr.update() for _ in range(n)]
            
            selected = [(issues[i], r) for i, (c, r) in enumerate(zip(cbs, reqs)) if c]
            preview  = "**请确认提交内容：**\n\n" + "\n".join(
                f"- issue#{iss['number']}：{iss['title'][:50]}**（{req}）**"
                for iss, req in selected)
            state = {"selected": [{"issue": iss, "require": req} for iss, req in selected]}

            return [gr.update(value=preview), gr.update(visible=True), state] + [gr.update(interactive=False) for _ in range(n)]

        btn_confirm.click(
            fn=handle_confirm,
            inputs=checkboxes + dropdowns,
            outputs=[confirm_content, panel_confirm, submit_state] + checkboxes
        )

        # ── Cancel ──
        def handle_cancel():
            return [gr.update(visible=False)] + [gr.update(interactive=True) for _ in range(len(checkboxes))]
        
        btn_cancel.click(fn=handle_cancel, outputs=[panel_confirm] + checkboxes)

        # ── Execute ──
        def execute_all(state):
            selected = state.get("selected", [])
            results  = [execute_task(item["issue"], item["require"]) for item in selected]
            Path(SUBMIT_RESULT_PATH).write_text(
                json.dumps({"results": results, "submitted_at": datetime.now().isoformat()}))
            threading.Thread(target=lambda: (time.sleep(2), os._exit(0)), daemon=True).start()
            gr.Warning("✅ 提交完成！页面即将关闭，请前往 GitHub 确认结果。", duration=6)
            return gr.update(visible=False)

        btn_ok.click(fn=execute_all, inputs=submit_state, outputs=panel_confirm)

    return app


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    args = parser.parse_args()

    issues       = load_issues()
    project_name = get_project_name()
    Path(SUBMIT_RESULT_PATH).unlink(missing_ok=True)

    app = build_app(issues, project_name)
    
    # Load public host from config file
    public_host = "localhost"
    display_port = args.port
    if args.config and Path(args.config).exists():
        try:
            config = json.loads(Path(args.config).read_text())
            public_host = config.get("webui", {}).get("public_host", "localhost")
            display_port = config.get("webui", {}).get("port", args.port)
        except Exception:
            pass
    
    print(f"\n✅ WebUI 已启动：http://{public_host}:{display_port}?__theme=light\n")

    app.launch(server_name=args.host, server_port=args.port,
               share=False, quiet=True, css=PANEL_CSS)
