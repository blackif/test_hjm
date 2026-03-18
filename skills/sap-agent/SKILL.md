---
name: sap-agent
description: >
  Use this skill whenever the user wants to connect to SAP, operate SAP like SAP GUI,
  call BAPIs or function modules, read SAP tables, post documents, manage master data,
  execute transactions, or automate any SAP ERP/S4HANA workflow. Also triggers for
  first-time setup, SAP connection management, disconnect, logout. Trigger phrases include:
  "SAP", "BAPI", "RFC", "ABAP", "SAP transaction", "MM/FI/SD/HR", "IDoc",
  "帮我操作 SAP", "查 SAP 数据", "过 SAP 凭证", "连接 SAP", "退出 SAP", "断开 SAP".
  Always use this skill — never handle SAP operations or lifecycle from memory alone.
compatibility:
  python: ">=3.8"
  required_libs: ["pyrfc", "requests", "cryptography"]
  system: "SAP NW RFC SDK required (see references/setup.md)"
---

# SAP Agent Skill

Manages the full lifecycle of SAP connectivity: initialization, email verification,
connection, operation, and graceful disconnect — including scheduled auto-disconnect.

---

## Entry Point: State Machine

Every time this skill activates, run this decision tree **first** before doing anything else:

```
scripts/init_check.py   →   returns: "first_run" | "needs_login" | "connected" | "force_disconnect"
```

```python
# scripts/init_check.py
import subprocess, sys
result = subprocess.run(
    ["python3", "~/.sap-agent/scripts/init_check.py"],
    capture_output=True, text=True
)
state = result.stdout.strip()
```

| State returned | Action |
|---|---|
| `first_run` | → Run First Run Wizard |
| `needs_login` | → Run SAP Login |
| `connected` | → Proceed to Execute Operation |
| `force_disconnect` | → Inform user connection was auto-closed, → Run SAP Login |

---

## Config File

**Location**: `~/.sap-agent/config.json`
**Session state**: `~/.sap-agent/session.json` (runtime only, not backed up)

```
~/.sap-agent/
├── config.json          ← persistent: email + SAP params (password encrypted)
├── session.json         ← transient: connection state + force_disconnect flag
├── scripts/
│   ├── init_check.py
│   ├── config_manager.py
│   ├── email_verify.py
│   ├── sap_session.py
│   └── auto_disconnect.py
└── .otp_tmp             ← temp: current OTP + expiry (deleted after verify)
```

**config.json schema**:
```json
{
  "version": "1.1",
  "initialized": true,
  "initialized_at": "2024-01-01T00:00:00Z",
  "email": {
    "smtp_host": "smtp.office365.com",
    "smtp_port": 587,
    "smtp_use_tls": true,
    "smtp_use_ssl": false,
    "smtp_user": "sap-agent@company.com",
    "smtp_password_enc": "<fernet_encrypted_base64>",
    "notify_email": "user@company.com",
    "verified": true,
    "verified_at": "2024-01-01T00:00:00Z"
  },
  "sap": {
    "mode": "direct | saprouter | msserver",
    "ashost": "sap-host.company.com",
    "sysnr": "00",
    "client": "100",
    "sysid": "PRD",
    "group": "PUBLIC",
    "lang": "ZH",
    "saprouter_host": "",
    "saprouter_port": "3299",
    "saprouter_password_enc": ""
  },
  "sdk": {
    "home": "/usr/local/sap/nwrfcsdk",
    "version": "7.50",
    "installed": true
  },
  "security": {
    "auto_disconnect_cron": "0 0 * * *",
    "cron_installed": true
  }
}
```

**session.json schema**:
```json
{
  "connected": false,
  "connected_at": null,
  "sap_user": null,
  "force_disconnect": false,
  "force_disconnect_reason": null,
  "last_activity": null
}
```

---

## First Run Wizard

Trigger when `config.json` does not exist. Guide user through all steps **in sequence**.

### Step 1 — Check & collect SMTP settings

Tell user:
> "这是首次使用 SAP Agent。首先需要配置邮件服务，用于后续发送验证码和通知。"

Collect via conversation:
```
SMTP 服务器地址 (例：smtp.office365.com):
SMTP 端口 (常用：587=TLS, 465=SSL, 25):
加密方式：TLS / SSL / 无
发件邮箱地址:
发件邮箱密码:
```

Use `scripts/email_verify.py` to test SMTP before proceeding:
```python
from scripts.email_verify import test_smtp_connection
ok, msg = test_smtp_connection(smtp_config)
# If not ok → tell user the error, ask to re-enter
```

### Step 2 — Collect recipient email & send OTP

```
您的邮箱地址 (用于接收验证码):
```

Then call:
```python
from scripts.email_verify import send_otp
otp_id = send_otp(smtp_config, recipient_email)
# Returns an otp_id; actual 6-digit code is saved to ~/.sap-agent/.otp_tmp
```

Tell user:
> "验证码已发送至 [email]，请在 10 分钟内输入 6 位数字验证码："

### Step 3 — Verify OTP

```python
from scripts.email_verify import verify_otp
result = verify_otp(user_input_code)
# Returns: "ok" | "expired" | "wrong"
```

| Result | Action |
|---|---|
| `ok` | Proceed to Step 4 |
| `wrong` | Tell user code incorrect, allow up to 3 retries then offer resend |
| `expired` | Tell user code expired (>10 min), offer to resend |

### Step 4 — Collect SAP system parameters

Ask:
```
SAP 系统类型：ECC / S/4HANA On-Prem / S/4HANA Cloud
连接方式：直连 (direct) / SAProuter / 消息服务器 (msserver)
SAP 应用服务器 IP 或主机名:
系统编号 (sysnr, 例：00):
集团代码 (client, 例：100):
系统 ID (SID, 例：PRD):
语言 (ZH / EN):
```

If mode = `saprouter`, also ask:
```
SAProuter 主机名/IP:
SAProuter 端口 (默认 3299):
SAProuter 路由密码 (没有则留空):
```

If mode = `msserver`, also ask:
```
消息服务器主机名:
消息服务器端口 (msserv, 例：3600):
登录组 (group, 例：PUBLIC):
```

### Step 5 — Save config & install cron

```python
from scripts.config_manager import save_config, install_cron
save_config(email_config, sap_config)
install_cron()   # installs: 0 0 * * * python3 ~/.sap-agent/scripts/auto_disconnect.py
```

Tell user:
> "✅ 配置已保存。已设置每日凌晨 00:00 自动断开 SAP 连接。"
> "现在请提供您的 SAP 用户名和密码以连接系统。"

→ Continue to SAP Login

---

## SAP Login

Load config, ask user for **username and password only** (never saved):

> "请输入您的 SAP 用户名和密码（仅用于本次连接，不会保存）："

```python
from scripts.sap_session import connect
result = connect(config, sap_user, sap_password)
```

**On success** → tell user:
> "✅ 已成功连接到 SAP 系统 [SID] / 集团 [CLIENT]
>  系统：[sysid] | 用户：[user] | 连接时间：[datetime]
>  请告诉我您要做什么。"

**On failure** → tell user specific error:
```python
# pyrfc exception mapping → see scripts/sap_session.py
"登录失败：用户名或密码错误"          # LogonError
"连接失败：无法到达 SAP 服务器"        # CommunicationError  
"连接失败：SAProuter 拒绝请求"         # NI_ROUT_PERM_DENIED
"连接失败：RFC 授权不足"               # ABAPRuntimeError AUTH_FAILURE
```

Offer retry up to 3 times, then suggest checking with SAP Basis.

---

## Execute Operation

Before every operation, call:
```python
from scripts.sap_session import check_session
state = check_session()   # "ok" | "force_disconnect" | "disconnected"
```

If `force_disconnect` or `disconnected` → inform user and go to SAP Login.

### Disconnect keyword detection

**Before processing ANY user message**, scan for disconnect intent:

Keywords (case-insensitive):
```python
DISCONNECT_KEYWORDS = [
    "退出 sap", "退出系统", "断开 sap", "断开连接", "登出 sap", "登出系统",
    "下线", "断连", "关闭 sap", "关闭连接",
    "exit sap", "disconnect sap", "logout sap", "quit sap",
    "close sap", "log off sap", "sign out sap"
]
```

If matched:
```python
from scripts.sap_session import disconnect
disconnect()
```

Tell user:
> "✅ 已断开与 SAP 系统 [SID] 的连接。
>  本次连接时长：[duration]
>  如需重新连接，请告诉我。"

Do **not** execute any SAP operation after disconnect in the same message.

### Operation routing

Route to the right script based on user intent:

| User intent | Operation | Reference |
|---|---|---|
| 查数据 / 查表 | `read_sap_table()` | `references/tables.md` |
| 创建/修改业务单据 | `call_bapi()` with confirm | `references/bapis.md` |
| 没有 BAPI 的事务 | `run_bdc()` | `references/bdc.md` |
| 查库存/物料 | MM workflow | `references/mm.md` |
| 过账/凭证 | FI workflow | `references/fi.md` |
| IDoc 发送 | `send_idoc()` | `references/odata.md` |

> ⚠️ **Golden Rule**: Any CREATE / CHANGE / POST / DELETE operation must show a summary and ask for explicit user confirmation before committing (`BAPI_TRANSACTION_COMMIT`).

---

## Auto-Disconnect (Cron)

`scripts/auto_disconnect.py` is installed as a cron job: `0 0 * * *`

It sets `session.json → force_disconnect: true, reason: "scheduled_midnight"`.
On next agent operation, `check_session()` detects this and blocks SAP calls
until user re-authenticates.

To manually check cron:
```bash
crontab -l | grep sap-agent
```

To manually remove:
```bash
crontab -l | grep -v sap-agent | crontab -
```

---

## Core SAP Operations

→ See original operation code patterns in `references/operations.md`
→ Module-specific: `references/mm.md`, `references/fi.md`
→ SAProuter connection params: `references/setup.md`
→ BAPI reference: `references/bapis.md`
→ Table reference: `references/tables.md`
