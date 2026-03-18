#!/usr/bin/env python3
"""
init_check.py
Entry point called at the start of every SAP Agent session.
Outputs one of: first_run | needs_login | connected | force_disconnect
"""

import os
import json
import sys

CONFIG_DIR  = os.path.expanduser("~/.sap-agent")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


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
