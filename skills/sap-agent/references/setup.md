# SAP Agent 完整安装与配置指南

**适用对象：** 第一次使用 SAP Agent 的用户

**最后更新：** 2026-03-19

---

## 目录

1. [前置条件](#前置条件)
2. [步骤 1：安装 SAP NW RFC SDK](#步骤-1 安装-sap-nw-rfc-sdk)
3. [步骤 2：创建配置文件](#步骤-2 创建配置文件)
4. [步骤 3：安装 HTTP 服务依赖](#步骤-3 安装-http-服务依赖)
5. [步骤 4：启动 HTTP 服务](#步骤-4 启动-http-服务)
6. [步骤 5：测试连接](#步骤-5 测试连接)
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
- [ ] 集团代码 (CLIENT)
- [ ] SAP 用户名
- [ ] SAP 密码
- [ ] 管理员邮箱

### Agent 需求

- [ ] 配置收发邮件功能
- [ ] 准备 SMTP 服务器信息

---

## 步骤 1：安装 SAP NW RFC SDK

参照 [sdk/README.md](sdk/README.md) 文件执行安装。

---

## 步骤 2：创建配置文件

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
  "email": {
    "adress": "your-email@example.com",
    "smtp_port": 587,
    "smtp_use_tls": true,
    "smtp_use_ssl": false,
    "smtp_user": "",
    "smtp_password_enc": "",
    "verified": false
  },
  "sap": {
    "mode": "saprouter",
    "ashost": "/H/your-saprouter/S/3299/H/your-server",
    "sysnr": "YOUR SYSNR",
    "client": "your client",
    "sysid": "your sysid",
    "lang": "your lang",
    "saprouter_host": "your-saprouter",
    "saprouter_port": "3299"
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
| `manager-email` | 管理员邮箱地址 | `admin@company.com` |
| `email.adress` | Agent 发件邮箱 | `agent@company.com` |
| `sap.mode` | 连接方式 | `saprouter` / `direct` / `msserver` |
| `sap.ashost` | SAProuter 连接字符串 | `/H/vs064.HAND-CHINA.COM/S/3299/H/192.168.11.34` |
| `sap.sysnr` | 系统编号（2 位） | `10` |
| `sap.client` | 集团代码 | `800` |
| `sap.sysid` | 系统 ID | `ED1` |
| `sap.lang` | 登录语言 | `ZH` / `EN` |

### 2.4 SAProuter 连接字符串格式

```
/H/<路由器主机>/S/<路由器端口>/H/<目标服务器>
```

**示例：**
```
/H/vs064.HAND-CHINA.COM/S/3299/H/192.168.11.34
```

**带路由密码：**
```
/H/router/S/3299/P/password/H/server
```

**多跳 SAProuter：**
```
/H/outer-router/S/3299/H/inner-router/S/3299/H/sap-host
```

---

## 步骤 3：安装 HTTP 服务依赖

```bash
pip3 install --break-system-packages fastapi uvicorn
```

**验证安装：**
```bash
python3 -c "import fastapi; print('FastAPI:', fastapi.__version__)"
```

---

## 步骤 4：启动 HTTP 服务

### 4.1 设置环境变量

```bash
export SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk
export LD_LIBRARY_PATH=/usr/local/sap/nwrfcsdk/lib
```

### 4.2 启动服务

```bash
cd /home/ubuntu/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/public/sap-agent/scripts
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
User=ubuntu
Environment="SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk"
Environment="LD_LIBRARY_PATH=/usr/local/sap/nwrfcsdk/lib"
WorkingDirectory=/home/ubuntu/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/public/sap-agent/scripts
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

---

## 步骤 5：测试连接

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

**文档版本：** 3.0
**更新时间：** 2026-03-19
