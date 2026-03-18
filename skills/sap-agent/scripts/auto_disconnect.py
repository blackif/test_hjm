#!/usr/bin/env python3
"""
auto_disconnect.py
Installed as a daily cron job: 0 0 * * *
Sets force_disconnect=True in session.json so the next SAP operation
triggers re-authentication.

Does NOT need pyrfc — operates purely on the session file.
"""

import os
import json
import logging
from datetime import datetime, timezone

CONFIG_DIR   = os.path.expanduser("~/.sap-agent")
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")
LOG_FILE     = os.path.join(CONFIG_DIR, "auto_disconnect.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def main():
    if not os.path.exists(SESSION_FILE):
        logging.info("Session file not found — nothing to disconnect.")
        return

    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            session = json.load(f)
    except Exception as e:
        logging.error(f"Failed to read session file: {e}")
        return

    if not session.get("connected"):
        logging.info("SAP was already disconnected — no action needed.")
        return

    # Mark force_disconnect
    session["force_disconnect"]        = True
    session["force_disconnect_reason"] = "scheduled_midnight"
    session["connected"]               = False
    session["last_activity"]           = datetime.now(timezone.utc).isoformat()

    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2)
        os.chmod(SESSION_FILE, 0o600)

        user   = session.get("sap_user", "unknown")
        sysid  = session.get("sap_sysid", "unknown")
        since  = session.get("connected_at", "unknown")
        logging.info(
            f"Auto-disconnected SAP session: user={user}, sysid={sysid}, "
            f"connected_since={since}"
        )

    except Exception as e:
        logging.error(f"Failed to write session file: {e}")


if __name__ == "__main__":
    main()
