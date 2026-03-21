#!/usr/bin/env python3
"""
AI Caller - 使用 OpenClaw 相同的方式调用 Bailian/Qwen
OpenAI 兼容 API 格式
"""

import os
import sys
import json
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


def get_openclaw_config():
    """获取 OpenClaw 配置"""
    config_paths = [
        Path.home() / ".openclaw" / "openclaw.json",
    ]
    for config_path in config_paths:
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text())
                providers = config.get("models", {}).get("providers", {})
                bailian = providers.get("bailian", {})
                if bailian:
                    return {
                        "base_url": bailian.get("baseUrl", "https://coding.dashscope.aliyuncs.com/v1"),
                        "api_key": bailian.get("apiKey", ""),
                        "model": "qwen3.5-plus"
                    }
            except Exception:
                pass
    return None


def call_bailian_openai_compat(prompt: str) -> str:
    """使用 OpenAI 兼容格式调用 Bailian"""
    config = get_openclaw_config()
    
    if not config or not config.get("api_key"):
        # 尝试从环境变量获取
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if api_key:
            config = {
                "base_url": "https://coding.dashscope.aliyuncs.com/v1",
                "api_key": api_key,
                "model": "qwen3.5-plus"
            }
        else:
            return "⚠️ 未配置 API Key（OpenClaw 配置或环境变量 DASHSCOPE_API_KEY）"
    
    base_url = config["base_url"].rstrip("/")
    api_key = config["api_key"]
    model = config.get("model", "qwen3.5-plus")
    
    try:
        # OpenAI 兼容格式
        data = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.7
        }).encode('utf-8')
        
        req = Request(
            f"{base_url}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        
        with urlopen(req, timeout=90) as response:
            result = json.loads(response.read().decode('utf-8'))
            choices = result.get("choices", [])
            if choices:
                text = choices[0].get("message", {}).get("content", "")
                return text.strip() if text else "❌ AI 回答为空"
            return "❌ AI 回答格式异常"
    
    except HTTPError as e:
        error_body = e.read().decode('utf-8')[:300] if hasattr(e, 'fp') and e.fp else ""
        return f"❌ API 调用失败 ({e.code}): {error_body}"
    except URLError as e:
        return f"❌ 网络错误：{str(e.reason)[:200]}"
    except TimeoutError:
        return "⏱️ AI 调用超时"
    except Exception as e:
        return f"❌ AI 调用异常：{str(e)[:200]}"


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    
    if not prompt:
        print("用法：python ai_caller.py <prompt>")
        sys.exit(1)
    
    response = call_bailian_openai_compat(prompt)
    print(response)
