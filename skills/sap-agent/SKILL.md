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
scripts/init_check.py   →   返回："first_run" | "open_http" | "sap_login" | "connected" | "closed_sap" | "closed_http"
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
| `open_http` | → 检查/启动 HTTP 服务（如启用性能优化） |
| `sap_login` | → SAP 登录（用户名密码验证） |
| `connected` | → 继续执行操作 |
| `closed_sap` | → SAP 已退出（空闲超时或手动断开），→ 运行 SAP 登录 |
| `closed_http` | → HTTP 服务已关闭（可选，服务未运行时） |

**状态流转：**
```
first_run → open_http → sap_login → connected → closed_sap → sap_login (循环)
                              ↓
                         closed_http (可选)
```

详见 `references/setup.md`。

---

## 首次运行向导

当 `config.json` 不存在时触发。**按顺序**引导用户完成所有步骤。

### 步骤 1 — 检查邮箱配置

先检查 `config.json` 中是否已配置 SMTP 和发件邮箱：

```python
from scripts.config_manager import load_config
config = load_config()
if config.get("email"):
    # 已配置，跳过此步骤
    proceed_to_step_2()
else:
    # 未配置，收集邮箱
    collect_email()
```

如未配置，通过对话收集：
```
SMTP 服务器地址 (例：smtp.office365.com):
SMTP 端口 (常用：587=TLS, 465=SSL, 25):
加密方式：TLS / SSL / 无
发件邮箱地址：
发件邮箱密码：
```

使用 `scripts/email_verify.py` 测试 SMTP 连接：
```python
from scripts.email_verify import test_smtp_connection
ok, msg = test_smtp_connection(smtp_config)
# 如果 ok 为假 → 告知用户错误，请求重新输入
```

### 步骤 2 — 收集管理员邮箱

收集管理员邮箱地址，用于接收 SAP Agent 的通知邮件：

```
管理员邮箱地址（用于接收通知）:
```

### 步骤 3 — 收集 SAP 系统参数

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

### 步骤 4 — 保存配置并启动 HTTP 服务

```python
from scripts.config_manager import save_config
save_config(email_config, sap_config)
```

**启动 HTTP 服务（推荐）：**

告知用户：
> "✅ 配置已保存。现在启动 HTTP 服务以启用连接池优化（可避免每次登录等待 50s）。"

```bash
# 安装依赖（如未安装）
pip3 install --break-system-packages fastapi uvicorn

# 启动服务
export SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk
export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib
python3 scripts/sap_service.py --host 127.0.0.1 --port 8765
```

**配置空闲超时自动断开：**

在 `~/.sap-agent/performance.json` 中设置：
```json
{
  "security": {
    "idle_timeout_minutes": 60
  }
}
```

告知用户：
> "✅ HTTP 服务已启动。已设置 60 分钟无操作自动断开连接。"
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
state = check_session()   # "connected" | "closed_sap" | "disconnected"
```

如果为 `closed_sap` 或 `disconnected` → 告知用户并转到 SAP 登录。

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

| 用户意图 | 操作 |
|---|---|
| 查数据 / 查表 | `read_sap_table()` |
| 创建/修改业务单据 | `call_bapi()` 并确认 |
| 没有 BAPI 的事务 | `run_bdc()` |
| 查库存/物料 | MM 工作流 |
| 过账/凭证 | FI 工作流 |

> ⚠️ **黄金规则**: 任何创建/修改/过账/删除操作必须在提交（`BAPI_TRANSACTION_COMMIT`）前显示摘要并请求用户明确确认。

---

## 自动断开（空闲超时）

**空闲超时机制：**

1. 在 `session.json` 中记录 `last_activity` 时间戳
2. 每次 SAP 操作前检查空闲时间
3. 超过设定时间（默认 60 分钟）无操作自动设置 `closed_sap` 状态

**配置超时时间：**

编辑 `~/.sap-agent/performance.json`：
```json
{
  "security": {
    "idle_timeout_minutes": 60
  }
}
```

**手动断开：**

使用断开连接关键词（见上方列表）或运行：
```python
from scripts.sap_session import disconnect
disconnect()
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

**详细说明请查看 `references/setup.md`**

简要说明：
- HTTP 服务提供连接池功能，避免每次查询都重新登录
- 登录后连接保持在池中，后续查询直接使用，速度提升 4-20 倍
- 建议在首次运行向导的步骤 4 中启动服务

---

## 文件参考

### 脚本

| 文件 | 用途 |
|------|---------|
| `scripts/init_check.py` | 会话状态检查（含 HTTP 服务健康检查） |
| `scripts/sap_session.py` | 连接管理（+ 连接池集成） |
| `scripts/config_manager.py` | 配置加密/解密 |
| `scripts/email_verify.py` | SMTP 连接测试 |
| `scripts/auto_disconnect.py` | 空闲超时检查 |
| `scripts/setup_sdk.sh` | SDK 安装 |
| `scripts/connection_pool.py` | 连接池管理 |
| `scripts/sap_service.py` | HTTP 服务 |
| `scripts/batch_operations.py` | 批量操作 |

### 配置文件

| 文件 | 用途 |
|------|---------|
| `~/.sap-agent/config.json` | 主配置 |
| `~/.sap-agent/session.json` | 会话状态（含 last_activity） |
| `~/.sap-agent/performance.json` | 性能和安全设置（含 idle_timeout_minutes） |

### 参考文档

| 文件 | 内容 |
|------|---------|
| `references/setup.md` | 完整安装与配置指南（含 HTTP 服务详细说明） |
