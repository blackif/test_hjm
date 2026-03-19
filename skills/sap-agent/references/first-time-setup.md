# SAP Agent 首次安装指南

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
7. [常见问题](#常见问题)

---

## 前置条件

- [ ] Python 3.8+ 已安装
- [ ] SAP NW RFC SDK 7.50 已提供（位于 `sdk/nwrfc750P_18-80009783.zip`）
- [ ] 有 SAP 系统访问权限（用户名、密码）
- [ ] 网络可访问 SAP 服务器或 SAProuter

---

## 步骤 1：安装 SAP NW RFC SDK

### 1.1 运行安装脚本

```bash
cd /home/ubuntu/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/public/sap-agent/scripts
bash setup_sdk.sh
```

### 1.2 重新加载环境变量

```bash
source ~/.bashrc
```

### 1.3 验证安装

```bash
python3 -c "import pyrfc; print('pyrfc version:', pyrfc.__version__)"
```

**预期输出：**
```
pyrfc version: 3.4
```

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
  "email": {
    "smtp_host": "smtp.office365.com",
    "smtp_port": 587,
    "smtp_use_tls": true,
    "smtp_use_ssl": false,
    "smtp_user": "",
    "smtp_password_enc": "",
    "notify_email": "",
    "verified": false
  },
  "sap": {
    "mode": "saprouter",
    "ashost": "/H/your-saprouter/S/3299/H/your-server",
    "sysnr": "00",
    "client": "800",
    "sysid": "ED1",
    "lang": "ZH",
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
```

### 2.3 设置权限

```bash
chmod 600 ~/.sap-agent/config.json
```

### 2.4 修改配置参数

| 参数 | 说明 | 示例值 |
|------|------|--------|
| `sap.ashost` | SAProuter 连接字符串 | `/H/vs064.HAND-CHINA.COM/S/3299/H/192.168.11.34` |
| `sap.sysnr` | 系统编号（2 位） | `10` |
| `sap.client` | 集团代码 | `800` |
| `sap.sysid` | 系统 ID | `ED1` |
| `sap.lang` | 登录语言 | `ZH` |

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
  统计信息：http://127.0.0.1:8765/stats

INFO:     Started server process [...]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765
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
  "use_pool": true
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

## 常见问题

### Q1: pyrfc 导入失败

**错误：**
```
ImportError: libsapnwrfc.so: cannot open shared object file
```

**解决：**
```bash
export SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk
export LD_LIBRARY_PATH=/usr/local/sap/nwrfcsdk/lib
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

---

## 附录：配置文件说明

### config.json 完整结构

```json
{
  "version": "1.1",
  "initialized": true,
  "email": {
    "smtp_host": "smtp.office365.com",
    "smtp_port": 587,
    "smtp_use_tls": true,
    "smtp_user": "your@email.com",
    "smtp_password_enc": "<encrypted>",
    "notify_email": "notify@email.com",
    "verified": false
  },
  "sap": {
    "mode": "saprouter",
    "ashost": "/H/router/S/3299/H/server",
    "sysnr": "00",
    "client": "800",
    "sysid": "ED1",
    "lang": "ZH",
    "saprouter_host": "router",
    "saprouter_port": "3299"
  },
  "sdk": {
    "home": "/usr/local/sap/nwrfcsdk",
    "version": "7.50",
    "installed": true
  }
}
```

### performance.json 结构

```json
{
  "connection_pool": {
    "max_connections": 5,
    "idle_timeout": 300
  },
  "service": {
    "host": "127.0.0.1",
    "port": 8765
  }
}
```

---

## 下一步

完成首次安装后，可以：

1. 使用 HTTP API 进行 SAP 操作
2. 使用 Python 脚本直接调用
3. 配置定时任务自动断开连接
4. 集成到其他应用

---

**相关文档：**
- [setup.md](setup.md) - SDK 安装详细指南
- [operations.md](operations.md) - SAP 操作指南
- [SKILL.md](../SKILL.md) - 技能说明
