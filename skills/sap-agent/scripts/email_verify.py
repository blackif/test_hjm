#!/usr/bin/env python3
"""
email_verify.py
Handles SMTP connectivity test, 6-digit OTP generation/sending, and verification.
OTP is stored temporarily in ~/.sap-agent/.otp_tmp (deleted after successful verify).
"""

import os
import json
import random
import smtplib
import hashlib
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CONFIG_DIR = os.path.expanduser("~/.sap-agent")
OTP_FILE   = os.path.join(CONFIG_DIR, ".otp_tmp")

OTP_EXPIRY_SECONDS = 600   # 10 minutes
OTP_MAX_RETRIES    = 3


# ─────────────────────────────────────────────
# SMTP connection test
# ─────────────────────────────────────────────

def test_smtp_connection(smtp_cfg: dict) -> tuple[bool, str]:
    """
    Test SMTP connectivity without sending any email.
    Returns (success: bool, message: str)

    smtp_cfg keys: smtp_host, smtp_port, smtp_use_tls, smtp_use_ssl,
                   smtp_user, smtp_password
    """
    try:
        host     = smtp_cfg["smtp_host"]
        port     = int(smtp_cfg["smtp_port"])
        use_ssl  = smtp_cfg.get("smtp_use_ssl", False)
        use_tls  = smtp_cfg.get("smtp_use_tls", True)
        user     = smtp_cfg["smtp_user"]
        password = smtp_cfg["smtp_password"]

        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            if use_tls:
                server.starttls()

        server.login(user, password)
        server.quit()
        return True, "SMTP 连接测试成功"

    except smtplib.SMTPAuthenticationError:
        return False, "SMTP 认证失败：用户名或密码错误"
    except smtplib.SMTPConnectError as e:
        return False, f"无法连接到 SMTP 服务器：{e}"
    except smtplib.SMTPException as e:
        return False, f"SMTP 错误：{e}"
    except Exception as e:
        return False, f"连接失败：{e}"


# ─────────────────────────────────────────────
# OTP generated and sending
# ─────────────────────────────────────────────

def _generate_otp() -> str:
    """Generate a cryptographically random 6-digit code."""
    return str(random.SystemRandom().randint(100000, 999999))


def _save_otp(code: str):
    """Save OTP hash + expiry to temp file."""
    os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)

    code_hash = hashlib.sha256(code.encode()).hexdigest()
    expires_at = time.time() + OTP_EXPIRY_SECONDS

    payload = {
        "code_hash": code_hash,
        "expires_at": expires_at,
        "attempts": 0,
    }
    with open(OTP_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    os.chmod(OTP_FILE, 0o600)


def _build_email_html(code: str) -> str:
    return f"""
<html><body>
<div style="font-family: Arial, sans-serif; max-width: 480px; margin: 40px auto;
            padding: 32px; border: 1px solid #e0e0e0; border-radius: 8px;">
  <h2 style="color: #1a237e; margin-top: 0;">SAP Agent 邮箱验证</h2>
  <p>您的验证码为：</p>
  <div style="font-size: 40px; font-weight: bold; letter-spacing: 12px;
              color: #1a237e; padding: 16px 0; text-align: center;">
    {code}
  </div>
  <p style="color: #666; font-size: 13px;">
    此验证码将在 <strong>10 分钟</strong>后过期。<br>
    如非本人操作，请忽略此邮件。
  </p>
</div>
</body></html>
"""


def send_otp(smtp_cfg: dict, recipient_email: str) -> tuple[bool, str]:
    """
    Generate a 6-digit OTP and send it to recipient_email.
    Also decrypts smtp_password if needed (pass plaintext or encrypted).
    Returns (success: bool, message: str)
    """
    code = _generate_otp()
    _save_otp(code)

    # Decrypt password if it was stored encrypted
    smtp_password = smtp_cfg.get("smtp_password", "")
    if not smtp_password and smtp_cfg.get("smtp_password_enc"):
        from config_manager import decrypt
        smtp_password = decrypt(smtp_cfg["smtp_password_enc"])

    subject = "【SAP Agent】邮箱验证码"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = smtp_cfg["smtp_user"]
    msg["To"]      = recipient_email

    msg.attach(MIMEText(f"您的 SAP Agent 验证码是：{code}，有效期 10 分钟。", "plain", "utf-8"))
    msg.attach(MIMEText(_build_email_html(code), "html", "utf-8"))

    try:
        host     = smtp_cfg["smtp_host"]
        port     = int(smtp_cfg["smtp_port"])
        use_ssl  = smtp_cfg.get("smtp_use_ssl", False)
        use_tls  = smtp_cfg.get("smtp_use_tls", True)
        user     = smtp_cfg["smtp_user"]

        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=15)
        else:
            server = smtplib.SMTP(host, port, timeout=15)
            if use_tls:
                server.starttls()

        server.login(user, smtp_password)
        server.sendmail(user, recipient_email, msg.as_string())
        server.quit()

        return True, f"验证码已发送至 {recipient_email}"

    except Exception as e:
        # Clean up OTP file on send failure
        if os.path.exists(OTP_FILE):
            os.remove(OTP_FILE)
        return False, f"发送失败：{e}"


# ─────────────────────────────────────────────
# OTP verification
# ─────────────────────────────────────────────

def verify_otp(user_input: str) -> str:
    """
    Verify user-supplied OTP against saved hash.
    Returns: "ok" | "expired" | "wrong" | "max_retries" | "no_otp"
    """
    if not os.path.exists(OTP_FILE):
        return "no_otp"

    with open(OTP_FILE, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Check expiry
    if time.time() > payload["expires_at"]:
        os.remove(OTP_FILE)
        return "expired"

    # Check retry count
    if payload["attempts"] >= OTP_MAX_RETRIES:
        os.remove(OTP_FILE)
        return "max_retries"

    # Increment attempt counter
    payload["attempts"] += 1
    with open(OTP_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    # Verify hash (constant-time comparison via hashlib)
    input_hash = hashlib.sha256(user_input.strip().encode()).hexdigest()
    if input_hash == payload["code_hash"]:
        os.remove(OTP_FILE)
        return "ok"

    remaining = OTP_MAX_RETRIES - payload["attempts"]
    if remaining <= 0:
        os.remove(OTP_FILE)
        return "max_retries"

    return "wrong"
