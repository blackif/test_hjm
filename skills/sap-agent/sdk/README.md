# SAP NW RFC SDK

此文件夹包含 SAP NetWeaver RFC SDK 安装包。

---

## 文件说明

| 文件 | 大小 | 说明 |
|------|------|------|
| `nwrfc750P_18-80009783.zip` | 23MB | SAP NW RFC SDK 7.50 安装包 |

---

## 版本信息

- **版本：** 7.50 Patch 18
- **发布日期：** 2024
- **平台：** Linux x86_64 / ARM64
- **来源：** SAP ONE Support Launchpad

---

## 使用方法

### 方式 1：自动安装（推荐）

```bash
cd ../scripts
bash setup_sdk.sh
```

### 方式 2：手动安装

```bash
# 1. 解压
unzip nwrfc750P_18-80009783.zip -d /tmp/

# 2. 复制到系统目录
sudo mkdir -p /usr/local/sap
sudo cp -r /tmp/nwrfcsdk /usr/local/sap/

# 3. 设置环境变量
export SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk
export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib

# 4. 添加到 ~/.bashrc
echo 'export SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib:$LD_LIBRARY_PATH' >> ~/.bashrc

# 5. 安装 pyrfc
pip3 install --break-system-packages pyrfc
```

---

## 验证安装

```bash
python3 -c "import pyrfc; print('pyrfc version:', pyrfc.__version__)"
```

**预期输出：**
```
pyrfc version: 3.4
```

---

## 相关文件

- [../references/setup.md](../references/setup.md) - 完整安装指南
- [../scripts/setup_sdk.sh](../scripts/setup_sdk.sh) - 自动安装脚本

---

**更新时间：** 2026-03-19
