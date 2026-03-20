#!/usr/bin/env python3
"""
GitHub Issue WebUI — Gradio-based review interface
Started by github-issue-webui skill. Do NOT run manually without ISSUES_JSON env var.
"""

import os
import json
import argparse
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import gradio as gr

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
SUBMIT_RESULT_PATH = "/tmp/giu_submit_result.json"
REQUIRE_OPTIONS = ["", "确认", "修改", "方案", "分析", "关闭", "移交", "暂挂"]
AI_COMMENT_FOOTER = "\n\n------请注意这是 AI 做出的评论内容"

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
    """Fetch full comment thread for a given issue."""
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_number),
             "--repo", f"{owner}/{repo}",
             "--json", "body,comments"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return f"⚠️ 无法加载评论：{result.stderr.strip()}"
        data = json.loads(result.stdout)
        body = data.get("body", "")
        comments = data.get("comments", [])
        lines = ["**Issue 内容：**\n", body, "\n\n---\n"]
        for c in comments:
            author = c.get("author", {}).get("login", "unknown")
            created = c.get("createdAt", "")[:16].replace("T", " ")
            body_text = c.get("body", "")
            lines.append(f"**{author}** · {created}\n\n{body_text}\n\n---\n")
        return "".join(lines) if lines else "暂无评论"
    except Exception as e:
        return f"⚠️ 加载失败：{e}"

# ─────────────────────────────────────────────
# AI Task execution
# ─────────────────────────────────────────────

PROMPT_TEMPLATES = {
    "确认": (
        "你是一个 GitHub issue 助手。\n"
        "请仔细阅读以下 issue 的完整内容，给出确认回答。\n"
        "你只能追加 comment，不能修改任何文件。\n\n"
        "Issue #{number}：{title}\n"
        "仓库：{repo}\n"
        "内容：\n{body}\n\n"
        "请用简洁专业的语言回答这个 issue。"
    ),
    "修改": (
        "你是一个代码修改助手。\n"
        "请仔细阅读以下 issue 的内容，找到需要修改的文件并执行修改，"
        "完成后追加 comment：「已经完成修改，请确认」。\n\n"
        "Issue #{number}：{title}\n"
        "仓库：{repo}\n"
        "内容：\n{body}\n\n"
        "请分析需要修改什么，然后执行修改并推送到 GitHub。"
    ),
    "方案": (
        "你是一个技术方案规划师。\n"
        "请基于以下 issue 内容给出完整解决方案（不执行修改，只输出方案）。\n\n"
        "Issue #{number}：{title}\n"
        "仓库：{repo}\n"
        "内容：\n{body}\n\n"
        "请输出完整方案，包括：问题分析、解决思路、具体步骤、潜在风险。"
    ),
    "分析": (
        "你是一个技术分析师。\n"
        "请对以下 issue 进行深度分析，输出分析报告。\n\n"
        "Issue #{number}：{title}\n"
        "仓库：{repo}\n"
        "内容：\n{body}\n\n"
        "请输出：根本原因分析、影响范围、优先级评估、相关关联。"
    ),
    "关闭": (
        "你是一个 GitHub issue 助手。\n"
        "请为以下 issue 撰写一条关闭说明 comment，然后关闭此 issue。\n\n"
        "Issue #{number}：{title}\n"
        "仓库：{repo}\n"
        "内容：\n{body}"
    ),
    "移交": (
        "你是一个 GitHub issue 助手。\n"
        "请为以下 issue 撰写一条移交说明 comment，说明需要人工跟进的原因。\n\n"
        "Issue #{number}：{title}\n"
        "仓库：{repo}\n"
        "内容：\n{body}"
    ),
    "暂挂": (
        "你是一个 GitHub issue 助手。\n"
        "请为以下 issue 撰写一条暂挂说明 comment。\n\n"
        "Issue #{number}：{title}\n"
        "仓库：{repo}\n"
        "内容：\n{body}"
    ),
}

def push_comment(owner: str, repo: str, issue_number: int, body: str) -> bool:
    full_body = body + AI_COMMENT_FOOTER
    result = subprocess.run(
        ["gh", "issue", "comment", str(issue_number),
         "--repo", f"{owner}/{repo}",
         "--body", full_body],
        capture_output=True, text=True, timeout=30
    )
    return result.returncode == 0

def execute_task(issue: dict, require: str) -> dict:
    number = issue.get("number")
    title = issue.get("title", "")
    repo = issue.get("repo", "")
    owner = issue.get("owner", "")
    body_text = issue.get("body", "") + "\n\n" + "\n---\n".join(
        c.get("body", "") for c in issue.get("comments", [])
    )

    template = PROMPT_TEMPLATES.get(require, PROMPT_TEMPLATES["确认"])
    prompt = template.format(
        number=number, title=title, repo=repo, body=body_text[:3000]
    )

    try:
        ai_result = subprocess.run(
            ["gh", "api", "/"],
            capture_output=True, text=True, timeout=60
        )
        ai_response = f"[AI 回答占位符 — 实际由 skill 执行层处理]\n\nPrompt 已生成，将在提交后由 AI 处理。"
    except Exception as e:
        ai_response = f"⚠️ AI 调用失败：{e}"

    if require not in ("修改",):
        push_comment(owner, repo, number, ai_response)

    if require == "关闭":
        subprocess.run(
            ["gh", "issue", "close", str(number), "--repo", f"{owner}/{repo}"],
            capture_output=True, timeout=15
        )
    elif require == "移交":
        subprocess.run(
            ["gh", "issue", "edit", str(number), "--repo", f"{owner}/{repo}",
             "--add-label", "needs-human"],
            capture_output=True, timeout=15
        )
    elif require == "暂挂":
        subprocess.run(
            ["gh", "issue", "edit", str(number), "--repo", f"{owner}/{repo}",
             "--add-label", "on-hold"],
            capture_output=True, timeout=15
        )

    return {"number": number, "require": require, "success": True}

# ─────────────────────────────────────────────
# Build Gradio UI
# ─────────────────────────────────────────────

def build_app(issues: list, project_name: str):
    now_str = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    checkboxes = []
    require_dropdowns = []

    custom_css = """
    .issue-row { 
        border-bottom: 1px solid #000000; 
        padding: 12px 0;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .issue-checkbox-group {
        display: flex;
        align-items: center;
        gap: 4px;
        min-width: 120px;
    }
    .issue-checkbox-group label {
        border: none !important;
    }
    .issue-checkbox-group input[type="checkbox"] {
        border: none !important;
        box-shadow: none !important;
    }
    .issue-checkbox-label {
        font-weight: bold;
        color: #000000;
        white-space: nowrap;
    }
    .issue-title-box {
        flex: 0 0 280px;
        display: flex;
        align-items: center;
    }
    .issue-title {
        color: #000000;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .issue-label {
        background: #f6f8fa;
        border: 1px solid #000000;
        border-radius: 12px;
        padding: 2px 8px;
        font-size: 12px;
        margin-left: 8px;
    }
    .comment-btn {
        min-width: 140px;
        border: none !important;
        background: #f97316 !important;
        color: #ffffff !important;
    }
    .comment-btn:hover {
        background: #ea580c !important;
    }
    .require-dropdown {
        min-width: 120px;
        border: none !important;
        box-shadow: none !important;
    }
    .require-dropdown .wrap {
        border: none !important;
    }
    .comment-panel {
        background: #FFFFFF;
        border: 1px solid #000000;
        border-radius: 6px;
        padding: 12px;
        max-height: 400px;
        overflow-y: auto;
    }
    .gh-header {
        background: #FFFFFF;
        color: #000000;
        padding: 12px 20px;
        border-radius: 6px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 15px;
        border-bottom: 2px solid #000000;
        margin-bottom: 20px;
    }
    .confirm-preview {
        background: #FFFFFF;
        border: 1px solid #000000;
        border-radius: 6px;
        padding: 12px;
        font-size: 13px;
    }
    """

    with gr.Blocks(css=custom_css, title="GitHub Issue WebUI") as app:
        gr.HTML(f"""
        <div class="gh-header">
            <strong>project:</strong> {project_name}
            &nbsp;&nbsp;
            <span style="font-size:12px; opacity:0.8">{now_str}</span>
        </div>
        """)

        if not issues:
            gr.Markdown("⚠️ **没有找到需要处理的 issues。**")
            return app

        error_msg = gr.Markdown("", visible=False)
        confirm_preview = gr.Markdown("", visible=False)
        submit_state = gr.State({})

        # Modal for comments (side panel simulation)
        with gr.Group(visible=False) as comment_modal:
            gr.Markdown("### 💬 Comments")
            modal_comment_content = gr.Markdown("")
            modal_close = gr.Button("关闭", size="sm")

        # Modal for confirmation
        with gr.Group(visible=False) as confirm_modal:
            gr.Markdown("### 请确认是否提交")
            modal_confirm_text = gr.Markdown("")
            with gr.Row():
                modal_ok = gr.Button("确认", variant="primary", size="sm")
                modal_cancel = gr.Button("取消", size="sm")

        result_msg = gr.Markdown("", visible=False)

        # Issue rows
        MAX_TITLE_LEN = 15  # 最大汉字长度

        for issue in issues:
            number = issue.get("number", "?")
            title = issue.get("title", "")
            labels = issue.get("labels", [])
            if labels and isinstance(labels, list) and len(labels) > 0:
                label_data = labels[0]
                label_str = label_data.get("name", "") if isinstance(label_data, dict) else str(label_data)
            else:
                label_str = ""
            repo = issue.get("repo", "")
            owner = issue.get("owner", "")

            # 截断 title：超过 15 个汉字则截断并加...
            if len(title) > MAX_TITLE_LEN:
                display_title = title[:MAX_TITLE_LEN] + "..."
            else:
                display_title = title

            with gr.Row(elem_classes=["issue-row"]):
                # Column 1: Checkbox with label "Issues#XX"
                cb = gr.Checkbox(label=f"Issues#{number}", value=False, elem_classes=["issue-checkbox-group"])
                
                # Column 2: Title with fixed width (15 汉字 + ... 约 280px)
                with gr.Column(elem_classes=["issue-title-box"]):
                    gr.HTML(f"""
                    <span class="issue-title">{display_title}</span>
                    """)
                
                # Column 3: Label badge
                if label_str:
                    gr.HTML(f'<span class="issue-label">{label_str}</span>')
                
                # Column 4: View Comments button (moved forward)
                comment_btn = gr.Button("💬 查看 comments", size="sm", variant="secondary", elem_classes=["comment-btn"])
                
                # Column 5: Require dropdown
                req = gr.Dropdown(
                    choices=REQUIRE_OPTIONS,
                    value="",
                    label="",
                    interactive=True,
                    elem_classes=["require-dropdown"]
                )

                # Comment modal state
                comment_visible = gr.State(False)

                def show_comments(iss_owner, iss_repo, iss_number, visible):
                    content = get_full_comments(iss_owner, iss_repo, iss_number)
                    return gr.update(value=content, visible=True), True

                def hide_comments(visible):
                    return gr.update(visible=False), False

                comment_btn.click(
                    fn=show_comments,
                    inputs=[gr.State(owner), gr.State(repo), gr.State(number), comment_visible],
                    outputs=[modal_comment_content, comment_visible]
                ).then(
                    fn=lambda v: gr.update(visible=True),
                    outputs=[comment_modal]
                )

                modal_close.click(
                    fn=hide_comments,
                    inputs=[comment_visible],
                    outputs=[comment_modal, comment_visible]
                )

            checkboxes.append(cb)
            require_dropdowns.append(req)

        # Footer
        with gr.Row():
            confirm_btn = gr.Button("✅ 确认提交", variant="primary", scale=2)
            cancel_btn = gr.Button("取消", scale=1)

        def handle_confirm(*args):
            n = len(issues)
            cbs = list(args[:n])
            reqs = list(args[n:])

            errors = []
            selected = []
            for i, (checked, req) in enumerate(zip(cbs, reqs)):
                if checked:
                    if not req:
                        errors.append(f"issue#{issues[i]['number']} 请选择 require")
                    else:
                        selected.append((issues[i], req))

            if not selected and not errors:
                return (
                    gr.update(value="⚠️ 请至少勾选一个 issue", visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    {}
                )

            if errors:
                return (
                    gr.update(value="⚠️ " + " ".join(errors), visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    {}
                )

            lines = ["**请确认是否提交：**\n\n"]
            for iss, req in selected:
                lines.append(f"- **Issues#{iss['number']}**: {iss['title'][:50]}（{req}）\n")
            preview_text = "".join(lines)

            return (
                gr.update(visible=False),
                gr.update(value=preview_text, visible=True),
                gr.update(visible=True),
                gr.update(value=preview_text),
                gr.update(visible=False),
                {"selected": [{"issue": iss, "require": req} for iss, req in selected]}
            )

        def execute_all(state):
            selected = state.get("selected", [])
            results = []
            for item in selected:
                r = execute_task(item["issue"], item["require"])
                results.append(r)

            with open(SUBMIT_RESULT_PATH, "w") as f:
                json.dump({"results": results, "submitted_at": datetime.now().isoformat()}, f)

            def shutdown():
                time.sleep(2)
                os._exit(0)
            threading.Thread(target=shutdown, daemon=True).start()

            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(value="✅ 提交完成！页面即将关闭，请前往 GitHub 确认结果。", visible=True)
            )

        def handle_cancel():
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False)
            )

        all_inputs = checkboxes + require_dropdowns

        confirm_btn.click(
            fn=handle_confirm,
            inputs=all_inputs,
            outputs=[error_msg, confirm_preview, confirm_modal, modal_confirm_text, comment_modal, submit_state]
        )

        modal_ok.click(
            fn=execute_all,
            inputs=[submit_state],
            outputs=[confirm_preview, confirm_modal, comment_modal, result_msg]
        )

        modal_cancel.click(
            fn=handle_cancel,
            outputs=[confirm_preview, confirm_modal, comment_modal, result_msg]
        )

        cancel_btn.click(
            fn=handle_cancel,
            outputs=[confirm_preview, confirm_modal, comment_modal, result_msg]
        )

    return app


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Issue WebUI")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    issues = load_issues()
    project_name = get_project_name()

    Path(SUBMIT_RESULT_PATH).unlink(missing_ok=True)

    app = build_app(issues, project_name)

    import socket
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"\n✅ WebUI 已启动：http://{local_ip}:{args.port}\n")

    app.launch(
        server_name=args.host,
        server_port=args.port,
        share=False,
        quiet=False,
        prevent_thread_lock=False
    )
