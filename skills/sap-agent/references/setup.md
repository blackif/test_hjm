# SAP Agent 完整安装与配置指南

---

## 目录

1. [前置条件](#前置条件)
2. [安装 SAP NW RFC SDK](#安装 SAP NW RFC SDK)
3. [创建配置文件](#创建配置文件)
4. [安装 HTTP 服务依赖](#安装 HTTP 服务依赖)
5. [启动 HTTP 服务](#启动 HTTP 服务)
6. [测试连接](#测试连接)
7. [高级配置](#高级配置)
8. [常见问题](#常见问题)

---

## 前置条件

### 系统要求

- [ ] Python 3.8+ 已安装
- [ ] Linux (Ubuntu/Debian) 或 Windows
- [ ] 网络可访问 SAP 服务器或 SAProuter

### 必需文件

- [ ] SAP NW RFC SDK 7.50
  - 位置：`sdk/nwrfc750P_18-80009783.zip` (技能文件夹内)

### SAP 系统信息

准备以下信息：
- [ ] SAP 系统类型（ECC / S/4HANA）
- [ ] 连接方式（直连 / SAProuter / 消息服务器）
- [ ] 服务器地址
- [ ] 系统编号 (SYSNR)
- [ ] SAP 用户名
- [ ] SAP 密码
- [ ] 管理员邮箱

注意：集团代码 (CLIENT) 和语言 (LANG) 在 SAP 登录时提供，不需要在此准备。

### Agent 需求

- [ ] 配置收发邮件功能
- [ ] 准备 SMTP 服务器信息

---

## 安装 SAP NW RFC SDK

参照 `sdk/README.md` 文件执行安装。

---

## 创建配置文件

### 2.1 创建配置目录

```bash
mkdir -p ~/.sap-agent
```

### 2.2 创建主配置文件

```bash
cat > ~/.sap-agent/config.json << 'EOF'
{
  "version": "1.1",
  "initialized": true,
  "initialized_at": "2026-03-19T00:00:00Z",
  "manager-email": "your-email@example.com",
  "sap-1": {
    "directions": "对此 SAP 服务器的说明或备注",
    "mode": "saprouter",
    "ashost": "/H/<router-host>/S/<port>/H/<target-server>",
    "sysnr": "<2-digit-system-number>",
    "sysid": "<system-id>",
    "saprouter_host": "<router-host>",
    "saprouter_port": "<port>"
  },
  "sdk": {
    "home": "/usr/local/sap/nwrfcsdk",
    "version": "7.50",
    "installed": true
  }
}
EOF

# 设置权限
chmod 600 ~/.sap-agent/config.json
```

### 2.3 配置参数说明

| 参数 | 说明 | 示例值 |
|------|------|--------|
| `version` | 配置文件版本号，用于兼容性检查 | `"1.1"` |
| `initialized` | 初始化状态标识 | `true` / `false` |
| `initialized_at` | 初始化时间戳（ISO 8601 格式） | `"2026-03-19T00:00:00Z"` |
| `manager-email` | 管理员邮箱地址，用于接收通知 | `"admin@company.com"` |
| `sap-1` | SAP 服务器配置对象（可配置多个，如 `sap-1`、`sap-2` 等，用于区分不同环境或服务器） | 见下方 SAP 配置属性 |
| `sap-1.directions` | 对此 SAP 服务器的说明或备注，用于记录服务器用途、环境说明等信息 | `"生产环境 - 财务系统"` / `"测试环境 - MM 模块"` / `"DEV 开发系统"` |
| `sap-1.mode` | SAP 连接方式 | `saprouter`（通过 SAProuter 连接）/ `direct`（直连 SAP 服务器）/ `msserver`（通过消息服务器连接） |
| `sap-1.ashost` | SAP 目标主机地址或 SAProuter 路由字符串 | 直连模式：`"192.168.1.100"`；SAProuter 模式：`"/H/<路由器主机>/S/<路由器端口>/H/<目标服务器>"`，如 `"/H/router.company.com/S/3299/H/192.168.1.100"`；多跳路由：`"/H/outer-router/S/3299/H/inner-router/S/3299/H/sap-host"`；带路由密码：`"/H/router/S/3299/P/password/H/server"` |
| `sap-1.sysnr` | SAP 系统编号（2 位数字） | `"10"` / `"01"` / `"42"` |
| `sap-1.sysid` | SAP 系统标识符（SID） | `"ED1"` / `"PRD"` / `"DEV"` |
| `sap-1.saprouter_host` | SAProuter 服务器主机名（仅 saprouter 模式） | `"router.company.com"` |
| `sap-1.saprouter_port` | SAProuter 服务端口（通常 3299） | `"3299"` |
| `sdk.home` | SAP NW RFC SDK 安装路径 | `"/usr/local/sap/nwrfcsdk"` |
| `sdk.version` | SDK 版本号 | `"7.50"` |
| `sdk.installed` | SDK 安装状态标识 | `true` / `false` |

**多服务器配置示例：**

```json
{
  "version": "1.1",
  "initialized": true,
  "manager-email": "admin@company.com",
  "sap-1": {
    "directions": "生产环境 - 财务系统",
    "mode": "saprouter",
    "ashost": "/H/router-prod/S/3299/H/192.168.1.100",
    "sysnr": "10",
    "sysid": "PRD"
  },
  "sap-2": {
    "directions": "测试环境 - MM 模块",
    "mode": "saprouter",
    "ashost": "/H/router-test/S/3299/H/192.168.1.101",
    "sysnr": "20",
    "sysid": "TST"
  },
  "sdk": {
    "home": "/usr/local/sap/nwrfcsdk",
    "version": "7.50",
    "installed": true
  }
}
```

---

## 安装 HTTP 服务依赖

```bash
pip3 install --break-system-packages fastapi uvicorn
```

**验证安装：**
```bash
python3 -c "import fastapi; print('FastAPI:', fastapi.__version__)"
```

---

## 启动 HTTP 服务

### 4.1 设置环境变量

```bash
export SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk
export LD_LIBRARY_PATH=/usr/local/sap/nwrfcsdk/lib
```

### 4.2 启动服务

```bash
cd <sap-agent 技能目录>/scripts
python3 sap_service.py --host 127.0.0.1 --port 8765
```

**预期输出：**
```
启动 SAP Agent 服务...
  地址：http://127.0.0.1:8765
  健康检查：http://127.0.0.1:8765/health

INFO:     Started server process [...]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765
```

### 4.3 后台运行（可选）

```bash
nohup python3 sap_service.py --host 127.0.0.1 --port 8765 > /tmp/sap_service.log 2>&1 &
```

### 4.4 配置 systemd 服务（推荐）

```bash
sudo tee /etc/systemd/system/sap-agent.service > /dev/null << 'EOF'
[Unit]
Description=SAP Agent HTTP Service
After=network.target

[Service]
Type=simple
User=<当前用户名>
Environment="SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk"
Environment="LD_LIBRARY_PATH=/usr/local/sap/nwrfcsdk/lib"
WorkingDirectory=<sap-agent 技能目录>/scripts
ExecStart=/usr/bin/python3 sap_service.py --host 127.0.0.1 --port 8765
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable sap-agent
sudo systemctl start sap-agent
sudo systemctl status sap-agent
```

**路径说明：**
- `<当前用户名>`：替换为实际用户名（如 `ubuntu`）
- `<sap-agent 技能目录>`：替换为 sap-agent skill 的实际路径（如 `/home/ubuntu/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/public/sap-agent`）

---

## 测试连接

### 5.1 健康检查

```bash
curl http://127.0.0.1:8765/health | python3 -m json.tool
```

**预期输出：**
```json
{
  "status": "healthy",
  "sessions_active": 0,
  "pool_stats": {
    "max_connections": 5,
    "idle_connections": 0
  }
}
```

### 5.2 建立连接

```bash
curl -X POST http://127.0.0.1:8765/connect \
  -H "Content-Type: application/json" \
  -d '{"user": "your_user", "password": "your_password", "use_pool": true}' | python3 -m json.tool
```

**预期输出：**
```json
{
  "session_id": "xxx-xxx-xxx",
  "connected": true,
  "use_pool": true,
  "pool_stats": {...}
}
```

### 5.3 测试查询

```bash
# 保存 session_id
SESSION_ID="xxx-xxx-xxx"

# 查询表
curl -X POST http://127.0.0.1:8765/read_table \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION_ID" \
  -d '{
    "table_name": "T001",
    "fields": ["BUKRS", "BUTXT", "WAERS"],
    "rowcount": 5
  }' | python3 -m json.tool
```

### 5.4 断开连接

```bash
# 释放回连接池（推荐）
curl -X POST http://127.0.0.1:8765/disconnect \
  -H "X-Session-ID: $SESSION_ID" \
  -d '{"close": false}' | python3 -m json.tool
```

---

## 高级配置

### 性能配置

创建 `~/.sap-agent/performance.json`：

```json
{
  "connection_pool": {
    "max_connections": 5,
    "idle_timeout": 300
  },
  "service": {
    "host": "127.0.0.1",
    "port": 8765,
    "session_timeout": 3600
  },
  "batch": {
    "max_rows_per_call": 1000
  }
}
```

### 连接池使用

```bash
# 使用连接池（默认）
curl -X POST http://127.0.0.1:8765/connect \
  -d '{"user": "user", "password": "pass", "use_pool": true}'

# 释放回池（保持连接）
curl -X POST http://127.0.0.1:8765/disconnect \
  -d '{"close": false}'

# 真正关闭
curl -X POST http://127.0.0.1:8765/disconnect \
  -d '{"close": true}'
```

### 性能对比

| 操作 | 无连接池 | 有连接池 | 提升 |
|------|----------|----------|------|
| 首次连接 | 1.3 秒 | 1.3 秒 | - |
| 后续连接 | 1.3 秒 | 0.37 秒 | 72% |
| 连续 10 次查询 | 13 秒 | 4 秒 | 69% |

---

## 常见问题

### Q1: pyrfc 导入失败

**错误：**
```
ImportError: libsapnwrfc.so: cannot open shared object file
```

**解决：**
```bash
export SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk
export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib
```

### Q2: 连接超时

**错误：**
```
RFC_CLOSED timeout
```

**解决：**
1. 检查 SAProuter 是否允许你的 IP 访问
2. 联系 Basis 团队将你的 IP 加入白名单
3. 确认防火墙端口 3299 已开放

### Q3: 认证失败

**错误：**
```
LogonError: 用户名或密码错误
```

**解决：**
1. 检查用户名和密码是否正确
2. 确认账户未锁定
3. 确认集团代码正确

### Q4: HTTP 服务无法启动

**错误：**
```
Address already in use
```

**解决：**
```bash
# 查找占用端口的进程
lsof -i :8765

# 停止进程
kill -9 <PID>

# 或者使用其他端口
python3 sap_service.py --port 8766
```

### Q5: SAProuter 错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `NI_ROUT_PERM_DENIED` | IP 不在白名单 | 联系 Basis 添加 IP |
| `NICONN_REFUSED` | 端口错误或路由器宕机 | 确认端口 |
| `RFC_ERROR_COMMUNICATION` | 路由字符串语法错误 | 检查 `/H/` `/S/` 格式 |

---

## 附录

### 配置文件权限

```bash
chmod 600 ~/.sap-agent/config.json      # 仅所有者可读写
chmod 644 ~/.sap-agent/performance.json # 所有人可读
chmod 600 ~/.sap-agent/session.json     # 仅所有者可读写
```

### 停止服务

```bash
# 停止 HTTP 服务
pkill -9 -f sap_service.py

# 关闭连接池
python3 -c "from connection_pool import close_pool; close_pool()"

# 更新会话状态
python3 -c "
import json
from pathlib import Path
session = {'connected': False, 'force_disconnect': True}
with open(Path.home()/'/.sap-agent/session.json', 'w') as f:
    json.dump(session, f)
"
```

---

**文档版本：** 3.1
