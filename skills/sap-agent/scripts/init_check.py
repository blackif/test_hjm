#!/usr/bin/env python3
"""
init_check.py
Entry point called at the start of every SAP Agent session.
Outputs one of: first_run | needs_login | connected | force_disconnect

Extended: Also checks HTTP service health if enabled
"""

import os
import json
import sys
import urllib.request
import urllib.error

CONFIG_DIR   = os.path.expanduser("~/.sap-agent")
CONFIG_FILE  = os.path.join(CONFIG_DIR, "config.json")
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")
PERF_FILE    = os.path.join(CONFIG_DIR, "performance.json")


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def check_service_health() -> dict:
    """
    检查 HTTP 服务健康状态
    
    Returns:
        服务状态字典
    """
    perf = load_json(PERF_FILE)
    service_cfg = perf.get("service", {})
    host = service_cfg.get("host", "127.0.0.1")
    port = service_cfg.get("port", 8765)
    
    try:
        url = f"http://{host}:{port}/health"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return {
                "service_running": True,
                "service_url": url,
                "service_data": data
            }
    except Exception:
        return {
            "service_running": False,
            "service_url": f"http://{host}:{port}"
        }


def main():
    # 1. No config → first run
    if not os.path.exists(CONFIG_FILE):
        print("first_run")
        return

    config = load_json(CONFIG_FILE)

    # 2. Config exists but not fully initialized
    if not config.get("initialized"):
        print("first_run")
        return

    # 3. Check session state
    session = load_json(SESSION_FILE)

    # force_disconnect set by cron or manual trigger
    if session.get("force_disconnect"):
        print("force_disconnect")
        return

    # already connected in this session
    if session.get("connected"):
        print("connected")
        return

    # config is good, session is clean → needs login
    print("needs_login")


if __name__ == "__main__":
    main()
