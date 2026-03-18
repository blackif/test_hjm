#!/usr/bin/env python3
"""
sap_session.py
Manages the SAP RFC connection lifecycle:
  - connect(): build RFC params (direct / SAProuter / msserver) and connect
  - check_session(): verify session is still valid
  - disconnect(): graceful teardown
  - safe_call(): wrapper around conn.call() with error handling
"""

import os
import json
import re
from datetime import datetime, timezone

CONFIG_DIR   = os.path.expanduser("~/.sap-agent")
CONFIG_FILE  = os.path.join(CONFIG_DIR, "config.json")
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")

# ─── Module-level connection handle ───────────────
_conn = None
_conn_from_pool = None  # 从连接池获取的连接


# ─────────────────────────────────────────────────
# 连接池集成
# ─────────────────────────────────────────────────

def get_connection_from_pool(user: str = "", password: str = ""):
    """
    从连接池获取连接（性能优化）
    
    Args:
        user: SAP 用户名
        password: SAP 密码
    
    Returns:
        RFC 连接对象，失败返回 None
    """
    try:
        from connection_pool import get_connection as pool_get
        return pool_get(user=user, password=password)
    except Exception as e:
        print(f"连接池获取失败：{e}")
        return None


def release_connection_to_pool(conn):
    """
    释放连接回连接池
    
    Args:
        conn: RFC 连接对象
    """
    try:
        from connection_pool import release_connection as pool_release
        pool_release(conn)
    except Exception as e:
        print(f"连接池释放失败：{e}")


# ─────────────────────────────────────────────────
# Session helpers
# ─────────────────────────────────────────────────

def _load_session() -> dict:
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"connected": False, "force_disconnect": False}


def _save_session(data: dict):
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.chmod(SESSION_FILE, 0o600)


# ─────────────────────────────────────────────────
# Build RFC connection parameters
# ─────────────────────────────────────────────────

def _build_conn_params(config: dict, sap_user: str, sap_password: str) -> dict:
    """
    Build pyrfc.Connection kwargs from config + runtime credentials.
    Handles: direct | saprouter | msserver
    """
    from config_manager import decrypt

    sap_cfg = config["sap"]
    mode    = sap_cfg.get("mode", "direct")
    sysnr   = sap_cfg.get("sysnr", "00").zfill(2)
    client  = sap_cfg.get("client", "100")
    lang    = sap_cfg.get("lang", "ZH")

    base = {
        "client": client,
        "user":   sap_user,
        "passwd": sap_password,
        "lang":   lang,
    }

    if mode == "direct":
        base["ashost"] = sap_cfg["ashost"]
        base["sysnr"]  = sysnr

    elif mode == "saprouter":
        router      = sap_cfg.get("saprouter_host", "")
        router_port = sap_cfg.get("saprouter_port", "3299")
        router_pwd  = decrypt(sap_cfg.get("saprouter_password_enc", ""))
        target      = sap_cfg["ashost"]

        pwd_seg = f"/P/{router_pwd}" if router_pwd else ""
        route   = f"/H/{router}/S/{router_port}{pwd_seg}/H/{target}/S/sapdp{sysnr}"

        base["ashost"] = route
        base["sysnr"]  = sysnr

    elif mode == "msserver":
        router      = sap_cfg.get("saprouter_host", "")
        router_port = sap_cfg.get("saprouter_port", "3299")
        ms_host     = sap_cfg.get("mshost", sap_cfg.get("ashost", ""))
        ms_serv     = sap_cfg.get("msserv", "3600")

        if router:
            base["mshost"] = f"/H/{router}/S/{router_port}/H/{ms_host}"
        else:
            base["mshost"] = ms_host

        base["msserv"] = ms_serv
        base["sysid"]  = sap_cfg.get("sysid", "")
        base["group"]  = sap_cfg.get("group", "PUBLIC")

    else:
        raise ValueError(f"Unknown SAP connection mode: {mode}")

    return base


# ─────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────

def connect(config: dict, sap_user: str, sap_password: str) -> dict:
    """
    Establish RFC connection.
    Returns:
        {"success": True,  "sysid": ..., "client": ..., "user": ..., "connected_at": ...}
        {"success": False, "error": "<human-readable Chinese message>", "error_type": ...}
    """
    global _conn
    try:
        import pyrfc
    except ImportError:
        return {
            "success": False,
            "error": "pyrfc 未安装。请先安装 SAP NW RFC SDK 和 pyrfc。",
            "error_type": "import_error"
        }

    try:
        params = _build_conn_params(config, sap_user, sap_password)
        _conn  = pyrfc.Connection(**params)

        # Ping to confirm
        _conn.call("RFC_PING")

        now = datetime.now(timezone.utc).isoformat()
        _save_session({
            "connected":             True,
            "connected_at":          now,
            "sap_user":              sap_user,
            "sap_sysid":             config["sap"].get("sysid", ""),
            "sap_client":            config["sap"].get("client", "100"),
            "force_disconnect":      False,
            "force_disconnect_reason": None,
            "last_activity":         now,
        })

        return {
            "success":      True,
            "sysid":        config["sap"].get("sysid", ""),
            "client":       config["sap"].get("client", "100"),
            "user":         sap_user,
            "connected_at": now,
        }

    except pyrfc.LogonError as e:
        return {"success": False,
                "error": f"登录失败：用户名或密码错误（{e}）",
                "error_type": "logon_error"}

    except pyrfc.CommunicationError as e:
        msg = str(e)
        if "NI_ROUT_PERM_DENIED" in msg or "NICONN_REFUSED" in msg:
            hint = "SAProuter 拒绝了连接请求，请确认路由权限表 (routeperm) 是否包含本机 IP。"
        elif "WSAEHOSTUNREACH" in msg or "WSAETIMEDOUT" in msg or "Connection timed out" in msg:
            hint = "无法到达 SAP 服务器，请检查网络/防火墙。"
        else:
            hint = msg
        return {"success": False,
                "error": f"连接失败：{hint}",
                "error_type": "communication_error"}

    except pyrfc.ABAPRuntimeError as e:
        return {"success": False,
                "error": f"ABAP 运行时错误：{e.message}",
                "error_type": "abap_error"}

    except Exception as e:
        return {"success": False,
                "error": f"未知错误：{e}",
                "error_type": "unknown"}


def check_session() -> str:
    """
    Returns: "ok" | "force_disconnect" | "disconnected"
    Also updates last_activity timestamp if connected.
    """
    global _conn
    session = _load_session()

    if session.get("force_disconnect"):
        _conn = None
        return "force_disconnect"

    if not session.get("connected") or _conn is None:
        return "disconnected"

    # Try a quick RFC ping to confirm connection is still alive
    try:
        _conn.call("RFC_PING")
        now = datetime.now(timezone.utc).isoformat()
        session["last_activity"] = now
        _save_session(session)
        return "ok"
    except Exception:
        _conn = None
        session["connected"] = False
        _save_session(session)
        return "disconnected"


def disconnect(reason: str = "user_request"):
    """Gracefully close the RFC connection."""
    global _conn
    session = _load_session()

    try:
        if _conn is not None:
            _conn.close()
    except Exception:
        pass
    finally:
        _conn = None

    # Calculate duration
    duration_str = ""
    if session.get("connected_at"):
        try:
            start = datetime.fromisoformat(session["connected_at"])
            now   = datetime.now(timezone.utc)
            diff  = now - start
            h, m  = divmod(int(diff.total_seconds()), 3600)
            m, s  = divmod(m, 60)
            duration_str = f"{h}小时 {m}分钟" if h > 0 else f"{m}分钟 {s}秒"
        except Exception:
            pass

    _save_session({
        "connected":               False,
        "connected_at":            None,
        "sap_user":                None,
        "force_disconnect":        False,
        "force_disconnect_reason": None,
        "last_activity":           datetime.now(timezone.utc).isoformat(),
    })

    return {
        "disconnected": True,
        "reason":       reason,
        "duration":     duration_str,
        "sysid":        session.get("sap_sysid", ""),
        "user":         session.get("sap_user", ""),
    }


# ─────────────────────────────────────────────────
# Safe SAP call wrapper
# ─────────────────────────────────────────────────

def safe_call(func_name: str, **kwargs) -> dict:
    """
    Execute an RFC function call with full error handling.
    Also checks BAPI RETURN table for E/A messages.
    """
    global _conn
    if _conn is None:
        return {"success": False, "error": "未连接到 SAP，请先登录。", "error_type": "not_connected"}

    state = check_session()
    if state != "ok":
        return {"success": False, "error": f"SAP 会话已断开（{state}），请重新登录。", "error_type": state}

    try:
        result = _conn.call(func_name, **kwargs)

        # Auto-check BAPI RETURN table
        return_msgs = result.get("RETURN", [])
        errors = [m for m in return_msgs if m.get("TYPE") in ("E", "A")]
        warnings = [m for m in return_msgs if m.get("TYPE") == "W"]

        if errors:
            import pyrfc
            _conn.call("BAPI_TRANSACTION_ROLLBACK")
            return {
                "success": False,
                "error": errors[0].get("MESSAGE", "BAPI 执行失败"),
                "error_type": "bapi_error",
                "all_errors": errors,
            }

        return {
            "success":  True,
            "data":     result,
            "warnings": warnings,
        }

    except Exception as e:
        import pyrfc
        if isinstance(e, pyrfc.ABAPRuntimeError):
            return {"success": False, "error": f"ABAP 错误：{e.message}", "error_type": "abap"}
        elif isinstance(e, pyrfc.CommunicationError):
            _conn = None
            return {"success": False, "error": "RFC 通信中断，请检查网络后重新登录。", "error_type": "comm_lost"}
        return {"success": False, "error": str(e), "error_type": "unknown"}


# ─────────────────────────────────────────────────
# Disconnect keyword detection
# ─────────────────────────────────────────────────

DISCONNECT_KEYWORDS = [
    r"退出\s*sap", r"退出系统", r"断开\s*sap", r"断开连接", r"登出\s*sap",
    r"登出系统", r"下线", r"断连", r"关闭\s*sap", r"关闭连接", r"注销\s*sap",
    r"exit\s*sap", r"disconnect\s*sap", r"logout\s*sap", r"quit\s*sap",
    r"close\s*sap", r"log\s*off\s*sap", r"sign\s*out\s*sap",
]

_DISCONNECT_RE = re.compile(
    "|".join(DISCONNECT_KEYWORDS), re.IGNORECASE
)


def is_disconnect_intent(user_message: str) -> bool:
    """Return True if the message contains a disconnect/logout intent."""
    return bool(_DISCONNECT_RE.search(user_message))
