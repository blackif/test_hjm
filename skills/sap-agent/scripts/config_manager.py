#!/usr/bin/env python3
"""
config_manager.py
Handles reading, writing, and encrypting the SAP Agent configuration file.
Uses Fernet symmetric encryption for sensitive fields (SMTP password, SAProuter password).
"""

import os
import json
import base64
import hashlib
import subprocess
from datetime import datetime, timezone

CONFIG_DIR   = os.path.expanduser("~/.sap-agent")
CONFIG_FILE  = os.path.join(CONFIG_DIR, "config.json")
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")
KEY_FILE     = os.path.join(CONFIG_DIR, ".key")
SCRIPTS_DIR  = os.path.join(CONFIG_DIR, "scripts")


# ─────────────────────────────────────────────
# Key management
# ─────────────────────────────────────────────

def _get_or_create_key() -> bytes:
    """Load or generate a Fernet key stored in ~/.sap-agent/.key"""
    os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)

    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read().strip()

    # Generate new key using cryptography library
    try:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
    except ImportError:
        # Fallback: derive key from machine-specific info + os.urandom
        import secrets
        raw = secrets.token_bytes(32)
        key = base64.urlsafe_b64encode(raw)

    # Save with restricted permissions
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    os.chmod(KEY_FILE, 0o600)
    return key


def encrypt(plaintext: str) -> str:
    """Encrypt a string, return base64 ciphertext."""
    if not plaintext:
        return ""
    try:
        from cryptography.fernet import Fernet
        key = _get_or_create_key()
        f = Fernet(key)
        return f.encrypt(plaintext.encode()).decode()
    except ImportError:
        # Fallback: XOR obfuscation (not secure, but better than plaintext)
        key = _get_or_create_key()[:32]
        raw = plaintext.encode()
        result = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
        return "xor:" + base64.b64encode(result).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a previously encrypted string."""
    if not ciphertext:
        return ""
    try:
        from cryptography.fernet import Fernet
        key = _get_or_create_key()

        if ciphertext.startswith("xor:"):
            key_bytes = key[:32]
            raw = base64.b64decode(ciphertext[4:])
            return bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(raw)).decode()

        f = Fernet(key)
        return f.decrypt(ciphertext.encode()).decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")


# ─────────────────────────────────────────────
# Config read / write
# ─────────────────────────────────────────────

def load_config() -> dict:
    """Load config.json, return dict. Returns {} if not found."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(email_cfg: dict, sap_cfg: dict) -> None:
    """
    Build and save config.json.

    email_cfg keys:
        smtp_host, smtp_port (int), smtp_use_tls (bool), smtp_use_ssl (bool),
        smtp_user, smtp_password (plaintext), notify_email

    sap_cfg keys:
        mode, ashost, sysnr, client, sysid, group, lang,
        saprouter_host, saprouter_port, saprouter_password (plaintext, optional)
    """
    os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)

    config = {
        "version": "1.1",
        "initialized": True,
        "initialized_at": datetime.now(timezone.utc).isoformat(),
        "email": {
            "smtp_host":          email_cfg["smtp_host"],
            "smtp_port":          int(email_cfg["smtp_port"]),
            "smtp_use_tls":       bool(email_cfg.get("smtp_use_tls", True)),
            "smtp_use_ssl":       bool(email_cfg.get("smtp_use_ssl", False)),
            "smtp_user":          email_cfg["smtp_user"],
            "smtp_password_enc":  encrypt(email_cfg["smtp_password"]),
            "notify_email":       email_cfg["notify_email"],
            "verified":           True,
            "verified_at":        datetime.now(timezone.utc).isoformat(),
        },
        "sap": {
            "mode":                    sap_cfg.get("mode", "direct"),
            "ashost":                  sap_cfg.get("ashost", ""),
            "sysnr":                   str(sap_cfg.get("sysnr", "00")),
            "client":                  str(sap_cfg.get("client", "100")),
            "sysid":                   sap_cfg.get("sysid", ""),
            "group":                   sap_cfg.get("group", "PUBLIC"),
            "lang":                    sap_cfg.get("lang", "ZH"),
            "saprouter_host":          sap_cfg.get("saprouter_host", ""),
            "saprouter_port":          sap_cfg.get("saprouter_port", "3299"),
            "saprouter_password_enc":  encrypt(sap_cfg.get("saprouter_password", "")),
            "mshost":                  sap_cfg.get("mshost", ""),
            "msserv":                  sap_cfg.get("msserv", ""),
        },
        "security": {
            "auto_disconnect_cron": "0 0 * * *",
            "cron_installed": False,
        }
    }

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    os.chmod(CONFIG_FILE, 0o600)

    # Initialize empty session
    _init_session()


def _init_session():
    """Create a fresh session.json."""
    session = {
        "connected": False,
        "connected_at": None,
        "sap_user": None,
        "force_disconnect": False,
        "force_disconnect_reason": None,
        "last_activity": None,
    }
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)
    os.chmod(SESSION_FILE, 0o600)


def load_session() -> dict:
    if not os.path.exists(SESSION_FILE):
        return {"connected": False, "force_disconnect": False}
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_session(session: dict):
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)


# ─────────────────────────────────────────────
# Cron installation
# ─────────────────────────────────────────────

def install_cron() -> bool:
    """
    Add a daily midnight cron job to auto-disconnect SAP.
    Returns True on success.
    """
    script_path = os.path.join(SCRIPTS_DIR, "auto_disconnect.py")
    python_exec = _find_python()
    cron_line   = f"0 0 * * * {python_exec} {script_path}  # sap-agent-auto-disconnect"

    try:
        # Read current crontab
        result = subprocess.run(["crontab", "-l"],
                                capture_output=True, text=True)
        current = result.stdout if result.returncode == 0 else ""

        # Avoid duplicate
        if "sap-agent-auto-disconnect" in current:
            return True

        new_crontab = current.rstrip("\n") + "\n" + cron_line + "\n"

        proc = subprocess.run(["crontab", "-"], input=new_crontab,
                               capture_output=True, text=True)
        success = (proc.returncode == 0)

        if success:
            cfg = load_config()
            cfg.setdefault("security", {})["cron_installed"] = True
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)

        return success

    except FileNotFoundError:
        # crontab not available (Windows or restricted env)
        return False


def _find_python() -> str:
    for candidate in ["python3", "python"]:
        try:
            result = subprocess.run([candidate, "--version"],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                return candidate
        except FileNotFoundError:
            continue
    return "python3"
