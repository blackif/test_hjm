---
name: sap-agent
description: >
  用于连接和操作 SAP 系统的技能。支持查询表、调用 BAPI、执行事务、过账凭证、管理主数据等
  SAP ERP/S4HANA 工作流。触发词包括："SAP"、"BAPI"、"RFC"、"ABAP"、"SAP 事务"、
  "MM/FI/SD/HR"、"IDoc"、"帮我操作 SAP"、"查 SAP 数据"、"过 SAP 凭证"、"连接 SAP"、
  "退出 SAP"、"断开 SAP"。始终使用此技能处理 SAP 操作，不要凭记忆处理。
compatibility:
  python: ">=3.8"
  required_libs: ["pyrfc", "requests", "cryptography"]
  system: "SAP NW RFC SDK required (see references/setup.md)"
---

# SAP Agent Skill

管理 SAP 的完整生命周期：初始化、连接、操作和断开。

---

## 入口：状态机

每次激活此技能时，**首先**运行此决策树：

```
scripts/init_check.py   →   返回："first_run" | "needs_login" | "connected" | "force_disconnect"
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

| 返回状态 | 操作 |
|---|---|
| `first_run` | → 运行首次运行向导 |
| `needs_login` | → 运行 SAP 登录 |
| `connected` | → 继续执行操作 |
| `force_disconnect` | → 告知用户连接已自动关闭，→ 运行 SAP 登录 |

---

## 配置文件

**位置**: `~/.sap-agent/config.json`
**会话状态**: `~/.sap-agent/session.json`（仅运行时，不备份）

```
~/.sap-agent/
├── config.json          ← 持久化：邮箱 + SAP 参数（密码加密）
├── session.json         ← 临时：连接状态 + force_disconnect 标志
├── scripts/
│   ├── init_check.py
│   ├── config_manager.py
│   ├── email_verify.py
│   ├── sap_session.py
│   └── auto_disconnect.py
└── .otp_tmp             ← 临时：当前 OTP + 过期时间（验证后删除）
```

**config.json 结构**:
```json
{
  "version": "1.1",
  "initialized": true,
  "initialized_at": "2024-01-01T00:00:00Z",
  "manager-email": "admin@company.com",
  "sap-1": {
    "directions": "生产环境 - 财务系统",
    "mode": "saprouter",
    "ashost": "/H/router/S/3299/H/sap-host",
    "sysnr": "00",
    "client": "800",
    "sysid": "ED1",
    "lang": "ZH"
  },
  "sdk": {
    "home": "/usr/local/sap/nwrfcsdk",
    "version": "7.50",
    "installed": true
  }
}
```

**session.json 结构**:
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

## 首次运行向导

当 `config.json` 不存在时触发。**按顺序**引导用户完成所有步骤。

### 步骤 1 — 检查并收集 SMTP 设置

告知用户：
> "这是首次使用 SAP Agent。首先需要配置邮件服务，用于后续发送验证码和通知。"

通过对话收集：
```
SMTP 服务器地址 (例：smtp.office365.com):
SMTP 端口 (常用：587=TLS, 465=SSL, 25):
加密方式：TLS / SSL / 无
发件邮箱地址：
发件邮箱密码：
```

使用 `scripts/email_verify.py` 在继续前测试 SMTP：
```python
from scripts.email_verify import test_smtp_connection
ok, msg = test_smtp_connection(smtp_config)
# 如果 ok 为假 → 告知用户错误，请求重新输入
```

### 步骤 2 — 收集接收邮箱并发送验证码

```
您的邮箱地址 (用于接收验证码):
```

然后调用：
```python
from scripts.email_verify import send_otp
otp_id = send_otp(smtp_config, recipient_email)
# 返回 otp_id；实际 6 位验证码保存到 ~/.sap-agent/.otp_tmp
```

告知用户：
> "验证码已发送至 [email]，请在 10 分钟内输入 6 位数字验证码："

### 步骤 3 — 验证验证码

```python
from scripts.email_verify import verify_otp
result = verify_otp(user_input_code)
# 返回："ok" | "expired" | "wrong"
```

| 结果 | 操作 |
|---|---|
| `ok` | 继续步骤 4 |
| `wrong` | 告知用户验证码错误，允许最多 3 次重试，然后提供重发选项 |
| `expired` | 告知用户验证码已过期（>10 分钟），提供重发选项 |

### 步骤 4 — 收集 SAP 系统参数

询问：
```
SAP 系统类型：ECC / S/4HANA On-Prem / S/4HANA Cloud
连接方式：直连 (direct) / SAProuter / 消息服务器 (msserver)
SAP 应用服务器 IP 或主机名:
系统编号 (sysnr, 例：00):
集团代码 (client, 例：100):
系统 ID (SID, 例：PRD):
语言 (ZH / EN):
```

如果 mode = `saprouter`，还需询问：
```
SAProuter 主机名/IP:
SAProuter 端口 (默认 3299):
SAProuter 路由密码 (没有则留空):
```

如果 mode = `msserver`，还需询问：
```
消息服务器主机名:
消息服务器端口 (msserv, 例：3600):
登录组 (group, 例：PUBLIC):
```

### 步骤 5 — 保存配置并安装定时任务

```python
from scripts.config_manager import save_config, install_cron
save_config(email_config, sap_config)
install_cron()   # 安装：0 0 * * * python3 ~/.sap-agent/scripts/auto_disconnect.py
```

告知用户：
> "✅ 配置已保存。已设置每日凌晨 00:00 自动断开 SAP 连接。"
> "现在请提供您的 SAP 用户名和密码以连接系统。"

→ 继续到 SAP 登录

---

## SAP 登录

加载配置，仅向用户询问**用户名和密码**（绝不保存）：

> "请输入您的 SAP 用户名和密码（仅用于本次连接，不会保存）："

```python
from scripts.sap_session import connect
result = connect(config, sap_user, sap_password)
```

**成功时** → 告知用户：
> "✅ 已成功连接到 SAP 系统 [SID] / 集团 [CLIENT]
>  系统：[sysid] | 用户：[user] | 连接时间：[datetime]
>  请告诉我您要做什么。"

**失败时** → 告知用户具体错误：
```python
# pyrfc 异常映射 → 见 scripts/sap_session.py
"登录失败：用户名或密码错误"          # LogonError
"连接失败：无法到达 SAP 服务器"        # CommunicationError  
"连接失败：SAProuter 拒绝请求"         # NI_ROUT_PERM_DENIED
"连接失败：RFC 授权不足"               # ABAPRuntimeError AUTH_FAILURE
```

提供最多 3 次重试，然后建议联系 SAP Basis 团队。

---

## 执行操作

每次操作前，调用：
```python
from scripts.sap_session import check_session
state = check_session()   # "ok" | "force_disconnect" | "disconnected"
```

如果为 `force_disconnect` 或 `disconnected` → 告知用户并转到 SAP 登录。

### 断开连接关键词检测

**在处理任何用户消息之前**，扫描断开连接意图：

关键词（不区分大小写）：
```python
DISCONNECT_KEYWORDS = [
    "退出 sap", "退出系统", "断开 sap", "断开连接", "登出 sap", "登出系统",
    "下线", "断连", "关闭 sap", "关闭连接",
    "exit sap", "disconnect sap", "logout sap", "quit sap",
    "close sap", "log off sap", "sign out sap"
]
```

如果匹配：
```python
from scripts.sap_session import disconnect
disconnect()
```

告知用户：
> "✅ 已断开与 SAP 系统 [SID] 的连接。
>  本次连接时长：[duration]
>  如需重新连接，请告诉我。"

**不要**在断开连接后的同一条消息中执行任何 SAP 操作。

### 操作路由

根据用户意图路由到正确的脚本：

| 用户意图 | 操作 | 参考 |
|---|---|---|
| 查数据 / 查表 | `read_sap_table()` | 见下方核心 SAP 操作 |
| 创建/修改业务单据 | `call_bapi()` 并确认 | 见下方核心 SAP 操作 |
| 没有 BAPI 的事务 | `run_bdc()` | 见下方核心 SAP 操作 |
| 查库存/物料 | MM 工作流 | 见下方核心 SAP 操作 |
| 过账/凭证 | FI 工作流 | 见下方核心 SAP 操作 |

> ⚠️ **黄金规则**: 任何创建/修改/过账/删除操作必须在提交（`BAPI_TRANSACTION_COMMIT`）前显示摘要并请求用户明确确认。

---

## 自动断开（定时任务）

`scripts/auto_disconnect.py` 安装为定时任务：`0 0 * * *`

它设置 `session.json → force_disconnect: true, reason: "scheduled_midnight"`。
下次代理操作时，`check_session()` 检测到此标志并阻止 SAP 调用，直到用户重新认证。

手动检查定时任务：
```bash
crontab -l | grep sap-agent
```

手动移除：
```bash
crontab -l | grep -v sap-agent | crontab -
```

---

## 核心 SAP 操作

→ 表查询：使用 `read_sap_table()` 函数，支持字段选择、条件过滤、分页
→ BAPI 调用：使用 `call_bapi()` 函数，支持参数传递、返回消息处理、事务提交
→ BDC 批量输入：使用 `run_bdc()` 函数，用于无 BAPI 的事务自动化
→ MM 模块：库存查询、物料主数据、采购订单、收货过账
→ FI 模块：会计凭证过账、科目余额查询、付款处理

详细工作流参考 `references/setup.md`。

---

## 性能优化（HTTP 服务模式）

对于大型查询和频繁操作，使用带连接池的 HTTP 服务模式以获得更好性能。

### 启动 HTTP 服务

```bash
# 安装依赖
pip3 install --break-system-packages fastapi uvicorn

# 启动服务
python3 scripts/sap_service.py --host 127.0.0.1 --port 8765
```

### API 端点

| 端点 | 方法 | 说明 |
|----------|--------|-------------|
| `/health` | GET | 健康检查 |
| `/stats` | GET | 服务统计 |
| `/connect` | POST | 建立 SAP 连接 |
| `/disconnect` | POST | 关闭连接 |
| `/call` | POST | 调用 RFC 函数 |
| `/read_table` | POST | 查询 SAP 表（优化版） |
| `/batch` | POST | 批量操作 |
| `/shutdown` | POST | 关闭服务 |

### 示例：连接并查询

```bash
# 1. 连接
SESSION=$(curl -s -X POST http://127.0.0.1:8765/connect \
  -H "Content-Type: application/json" \
  -d '{"user": "10437", "password": "your_password"}' | jq -r '.session_id')

# 2. 查询表
curl -s -X POST http://127.0.0.1:8765/read_table \
  -H "X-Session-ID: $SESSION" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "T001",
    "fields": ["BUKRS", "BUTXT", "WAERS"],
    "rowcount": 100
  }'

# 3. 断开
curl -s -X POST http://127.0.0.1:8765/disconnect \
  -H "X-Session-ID: $SESSION"
```

### Python 客户端示例

```python
import requests

# 连接
resp = requests.post('http://127.0.0.1:8765/connect', json={
    'user': '10437',
    'password': 'your_password'
})
session_id = resp.json()['session_id']

# 使用会话查询
headers = {'X-Session-ID': session_id}
resp = requests.post('http://127.0.0.1:8765/read_table',
    headers=headers,
    json={
        'table_name': 'T001',
        'fields': ['BUKRS', 'BUTXT'],
        'rowcount': 100
    }
)
data = resp.json()

# 断开
requests.post('http://127.0.0.1:8765/disconnect', headers=headers)
```

### 性能对比

| 操作 | 直接 RFC | HTTP 服务 | 提升 |
|-----------|-----------|--------------|-------------|
| 单次查询 | 0.5-2 秒 | 0.1-0.5 秒 | 4 倍 |
| 100 行批量 | 50-200 秒 | 5-10 秒 | 10-20 倍 |
| 连接复用 | ❌ | ✅ | 不适用 |

### 配置

编辑 `~/.sap-agent/performance.json`：

```json
{
  "connection_pool": {
    "max_connections": 5,
    "idle_timeout": 300
  },
  "batch": {
    "max_rows_per_call": 1000
  }
}
```

---

## 文件参考

### 脚本

| 文件 | 用途 |
|------|---------|
| `scripts/init_check.py` | 会话状态检查 |
| `scripts/sap_session.py` | 连接管理（+ 连接池集成） |
| `scripts/config_manager.py` | 配置加密/解密 |
| `scripts/email_verify.py` | 邮箱验证 |
| `scripts/auto_disconnect.py` | 定时断开 |
| `scripts/setup_sdk.sh` | SDK 安装 |
| `scripts/connection_pool.py` | **新增** 连接池 |
| `scripts/sap_service.py` | **新增** HTTP 服务 |
| `scripts/batch_operations.py` | **新增** 批量操作 |

### 配置文件

| 文件 | 用途 |
|------|---------|
| `~/.sap-agent/config.json` | 主配置 |
| `~/.sap-agent/session.json` | 会话状态 |
| `~/.sap-agent/performance.json` | **新增** 性能设置 |

### 参考文档

| 文件 | 内容 |
|------|---------|
| `references/setup.md` | 完整安装与配置指南 |
