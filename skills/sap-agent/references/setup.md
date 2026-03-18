# SAP NW RFC SDK Setup Guide

## What You Need
1. **SAP NW RFC SDK** — provided by user in workspace
   - Location: `~/.openclaw/workspace/sap-sdk/nwrfcsdk`
   - Version: SAP NW RFC SDK 7.50

2. **pyrfc** — Python wrapper for the SDK

---

## Linux (Ubuntu/Debian) — Automated Setup

```bash
# Run the setup script from sap-agent skill
cd ~/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/public/sap-agent/scripts
bash setup_sdk.sh

# After setup, reload shell environment
source ~/.bashrc

# Test installation
python3 -c "import pyrfc; print('pyrfc version:', pyrfc.__version__)"
```

---

## Linux (Ubuntu/Debian) — Manual Setup

```bash
# 1. SDK is already extracted to workspace
SDK_SOURCE=$HOME/.openclaw/workspace/sap-sdk/nwrfcsdk
SDK_TARGET=/usr/local/sap/nwrfcsdk

# 2. Copy SDK to system location
sudo mkdir -p /usr/local/sap
sudo cp -r $SDK_SOURCE $SDK_TARGET

# 3. Set environment
export SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk
export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib:$LD_LIBRARY_PATH

# Add to ~/.bashrc for persistence
echo 'export SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib:$LD_LIBRARY_PATH' >> ~/.bashrc

# 4. Install pyrfc
pip install pyrfc

# 5. Test
python3 -c "import pyrfc; print('pyrfc OK')"
```

## Windows

```powershell
# 1. Extract to C:\nwrfcsdk
# 2. Add to System PATH: C:\nwrfcsdk\lib
# 3. Install pyrfc
pip install pyrfc
```

## macOS (Apple Silicon note)

```bash
# NW RFC SDK has no ARM64 build — use x86_64 via Rosetta
# Or use Docker (recommended for M1/M2/M3)
docker run --platform linux/amd64 -it python:3.11 bash
# then follow Linux steps inside container
```

## Docker (Recommended for CI/Agent)

```dockerfile
FROM python:3.11-slim
COPY nwrfc750*.zip /tmp/
RUN apt-get update && apt-get install -y unzip libstdc++6 \
    && mkdir /usr/local/sap \
    && unzip /tmp/nwrfc750*.zip -d /usr/local/sap/nwrfcsdk

ENV SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk
ENV LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib

RUN pip install pyrfc pandas
```

---

## SAProuter Connection

If your SAP system requires SAProuter, use route strings instead of a direct `ashost`.

### Route string format
```
/H/<router_host>/S/<port>/[P/<password>/]H/<sap_host>/S/sapdp<sysnr>
```
- `/H/` = hostname
- `/S/` = service/port (default `3299` or `sapdp99`)
- `/P/` = route password (omit if none)

### Single-hop SAProuter
```python
conn = pyrfc.Connection(
    ashost="/H/saprouter.company.com/S/3299/H/sap-erp.internal/S/sapdp00",
    sysnr="00", client="100", user="...", passwd="..."
)
```

### SAProuter with route password
```python
conn = pyrfc.Connection(
    ashost="/H/saprouter.company.com/S/3299/P/routerpwd/H/sap-erp.internal/S/sapdp00",
    sysnr="00", client="100", user="...", passwd="..."
)
```

### Multi-hop (chained SAProuters)
```python
conn = pyrfc.Connection(
    ashost="/H/outer-router.com/S/3299/H/inner-router.local/S/3299/H/sap-host/S/sapdp00",
    sysnr="00", client="100", user="...", passwd="..."
)
```

### Via Message Server (load balancing) + SAProuter
```python
conn = pyrfc.Connection(
    mshost="/H/saprouter.company.com/S/3299/H/sap-msg-server.internal",
    msserv="3601", sysid="PRD", group="PUBLIC",
    client="100", user="...", passwd="..."
)
```

### SNC encryption (enterprise)
```python
conn = pyrfc.Connection(
    ashost="/H/saprouter.company.com/S/3299/H/sap-host/S/sapdp00",
    sysnr="00", client="100",
    snc_on="1",
    snc_partnername="p:CN=PRD, OU=SAP, O=Company, C=CN",
    snc_lib="/usr/lib/libsapcrypto.so",
    snc_qop="9"
)
```

### Common SAProuter errors

| Error | Cause | Fix |
|---|---|---|
| `NI_ROUT_PERM_DENIED` | Agent IP not in `routeperm` | Ask SAP Basis to whitelist your IP |
| `NICONN_REFUSED` | Wrong port or router down | Confirm port with Basis |
| `RFC_ERROR_COMMUNICATION` | Route string syntax error | Double-check `/H/` `/S/` segments |
| Connection timeout | Firewall blocking port 3299 | Open firewall for agent machine → SAProuter |

---

## Verify Connection

```python
import pyrfc

conn = pyrfc.Connection(
    ashost="your-sap-host",
    sysnr="00",
    client="100",
    user="your-user",
    passwd="your-password"
)

# Test ping
result = conn.call("RFC_PING")
print("SAP connection OK!")
conn.close()
```

---

## Alternative: No SDK (S/4HANA Cloud only)

If you can't install the SDK, use pure HTTP OData:
→ see `references/odata.md`
