# Core SAP Operation Patterns

All operations use the `sap_session.safe_call()` wrapper which handles:
- Session validity check before every call
- BAPI RETURN table error detection
- Automatic rollback on E/A type messages
- RFC error classification with Chinese messages

Import pattern for all operations:
```python
from scripts.sap_session import safe_call
```

---

## 1. Read SAP Table (RFC_READ_TABLE)

Use for: querying transparent tables (MARA, BKPF, EKKO, KNA1, etc.)

```python
def read_sap_table(table: str, fields: list = [], where: str = "", max_rows: int = 100) -> list[dict]:
    """
    Returns a list of dicts, one per row.
    fields: list of field names to select (empty = all, but risks 512-char row limit)
    where:  WHERE clause string, e.g. "BUKRS EQ '1000' AND GJAHR EQ '2024'"
    """
    result = safe_call("RFC_READ_TABLE",
        QUERY_TABLE=table,
        DELIMITER="|",
        ROWCOUNT=max_rows,
        FIELDS=[{"FIELDNAME": f} for f in fields],
        OPTIONS=[{"TEXT": where}] if where else []
    )
    if not result["success"]:
        raise Exception(result["error"])

    data    = result["data"]
    headers = [f["FIELDNAME"] for f in data["FIELDS"]]
    rows    = []
    for row in data["DATA"]:
        values = row["WA"].split("|")
        rows.append(dict(zip(headers, [v.strip() for v in values])))
    return rows
```

> ⚠️ `RFC_READ_TABLE` has a **512-character row width limit**.
> Always specify `fields` to select only needed columns.
> For wide tables, use a custom ABAP FM or `/BODS/RFC_READ_TABLE2` if available.

### Multi-condition WHERE
```python
# Multiple conditions must each be ≤72 chars per OPTIONS row
options = [
    {"TEXT": "BUKRS EQ '1000'"},
    {"TEXT": " AND GJAHR EQ '2024'"},
    {"TEXT": " AND BELNR GE '0100000000'"},
]
result = safe_call("RFC_READ_TABLE",
    QUERY_TABLE="BKPF",
    DELIMITER="|",
    ROWCOUNT=500,
    FIELDS=[{"FIELDNAME": "BELNR"}, {"FIELDNAME": "BUDAT"}, {"FIELDNAME": "BLART"}],
    OPTIONS=options
)
```

---

## 2. Call BAPI / Function Module

Use for: business operations — create PO, post FI document, change material, etc.

```python
def call_bapi(bapi_name: str, params: dict, commit: bool = True) -> dict:
    """
    Calls a BAPI and commits if successful.
    Always confirm with user before calling with commit=True.
    """
    result = safe_call(bapi_name, **params)

    if not result["success"]:
        # safe_call already rolled back if BAPI returned E/A
        return result

    if commit:
        safe_call("BAPI_TRANSACTION_COMMIT", WAIT="X")

    return result
```

### BAPI call pattern with confirmation
```python
# 1. Build params
params = {
    "POHEADER": {"COMP_CODE": "1000", "VENDOR": "0001000123", ...},
    "POITEM":   [...],
    "POSCHEDULE": [...],
}

# 2. Show summary to user and ask for confirmation
# "即将创建采购订单：供应商 0001000123，3 行物料，总金额 ¥12,500。确认创建？"

# 3. Only call after user confirms
result = call_bapi("BAPI_PO_CREATE1", params, commit=True)

# 4. Return created document number
if result["success"]:
    po_number = result["data"].get("EXPPURCHASEORDER")
    print(f"✅ 采购订单已创建：{po_number}")
```

---

## 3. BDC / Batch Input (Transaction Simulation)

Use for: transactions that have no BAPI equivalent.
→ See `references/bdc.md` for screen field mapping patterns and common transactions.

```python
def run_bdc(tcode: str, dynpro_data: list, mode: str = "N") -> dict:
    """
    Simulate SAP GUI transaction entry.
    mode: N=no display, A=show all screens, E=show errors only
    dynpro_data: alternating screen headers and field entries
    """
    result = safe_call("ABAP4_CALL_TRANSACTION",
        TCODE=tcode,
        MODE=mode,
        UPDATE="S",        # S=synchronous
        USING=dynpro_data
    )
    return result
```

### BDC data structure
```python
dynpro_data = [
    # Screen header
    {"PROGRAM": "SAPMF05A", "DYNPRO": "0100", "DYNBEGIN": "X"},
    # Field values on that screen
    {"FNAM": "BDC_CURSOR",  "FVAL": "RF05A-NEWBS"},
    {"FNAM": "RF05A-NEWBS", "FVAL": "40"},         # posting key
    {"FNAM": "RF05A-NEWKO", "FVAL": "0000113100"}, # account
    # Next screen
    {"PROGRAM": "SAPMF05A", "DYNPRO": "0300", "DYNBEGIN": "X"},
    {"FNAM": "BSEG-WRBTR",  "FVAL": "1000.00"},    # amount
    {"FNAM": "BSEG-SGTXT",  "FVAL": "Agent post"}, # text
]
```

---

## 4. Send IDoc

Use for: EDI integration, triggering processes in remote systems.

```python
def send_idoc(idoc_type: str, control_data: dict, data_records: list) -> dict:
    """
    Send an inbound IDoc to SAP.
    control_data: EDIDC40 structure fields (RCVPOR, RCVPRT, RCVPRN, SNDPRT, SNDPRN, IDOCTYP, etc.)
    data_records: list of EDIDD40 structures (SEGNAM + SDATA)
    """
    result = safe_call("IDOC_INBOUND_ASYNCHRONOUS",
        IDOC_CONTROL_REC_40=[control_data],
        IDOC_DATA_REC_40=data_records
    )
    return result
```

### Minimal IDoc example (MATMAS outbound trigger)
```python
control = {
    "TABNAM":  "EDI_DC40",
    "MANDT":   "100",
    "DOCNUM":  "0000000000000001",
    "DIRECT":  "1",              # 1=inbound
    "IDOCTYP": "MATMAS05",
    "RCVPRT":  "LS",
    "RCVPRN":  "TARGETLOGICAL",
    "SNDPRT":  "LS",
    "SNDPRN":  "SOURCELOGICAL",
}
```

---

## 5. Run ABAP Report

Use for: executing reports with selection screen parameters.

```python
def run_report(report_name: str, variant: str = "") -> dict:
    """
    Execute an ABAP report (background-style via RFC).
    variant: saved selection variant name (optional)
    """
    params = {"RFCDEST": "NONE", "RFCPROG": report_name}
    if variant:
        params["RFCPARAM"] = f"VARIANT={variant}"

    return safe_call("RFC_START_PROGRAM", **params)
```

---

## 6. F4 Value Help (Domain lookup)

Use to replace SAP GUI F4 key — get valid values for a field.

```python
def get_f4_values(fm_name: str, params: dict) -> list:
    """
    Many fields have dedicated F4 FMs (e.g. F4IF_FIELD_VALUE_REQUEST).
    For simple domains, read the check table directly.
    """
    # Example: get valid company codes
    rows = read_sap_table("T001",
        fields=["BUKRS", "BUTXT"],
        where="",
        max_rows=200
    )
    return rows  # [{"BUKRS": "1000", "BUTXT": "Company Name"}, ...]
```

Common check tables for F4:

| Field | Check table | Key | Description field |
|---|---|---|---|
| Company code (BUKRS) | T001 | BUKRS | BUTXT |
| Plant (WERKS) | T001W | WERKS | NAME1 |
| Storage location (LGORT) | T001L | WERKS+LGORT | LGOBE |
| Purchase org (EKORG) | T024E | EKORG | EKOTX |
| GL account (HKONT) | SKA1 | SAKNR | TXT50 |
| Cost center (KOSTL) | CSKS | KOSTL | KTEXT |
| Currency (WAERS) | TCURC | WAERS | LTEXT (in TCURT) |
| Movement type (BWART) | T156 | BWART | BTEXT (in T156T) |

---

## 7. Connection Pool (production use)

For agents that make many rapid calls, use a connection pool to avoid repeated logon overhead.

```python
from contextlib import contextmanager
import pyrfc
import threading

class SAPConnectionPool:
    def __init__(self, conn_params: dict, pool_size: int = 3):
        self._params  = conn_params
        self._lock    = threading.Lock()
        self._pool    = [pyrfc.Connection(**conn_params) for _ in range(pool_size)]
        self._available = list(self._pool)

    @contextmanager
    def get(self):
        with self._lock:
            if not self._available:
                # All connections busy — create a temporary one
                conn = pyrfc.Connection(**conn_params)
                temp = True
            else:
                conn = self._available.pop()
                temp = False
        try:
            yield conn
        finally:
            if temp:
                try:
                    conn.close()
                except Exception:
                    pass
            else:
                with self._lock:
                    self._available.append(conn)

    def close_all(self):
        with self._lock:
            for conn in self._pool:
                try:
                    conn.close()
                except Exception:
                    pass
            self._pool.clear()
            self._available.clear()

# Usage
pool = SAPConnectionPool(conn_params, pool_size=3)
with pool.get() as conn:
    result = conn.call("RFC_READ_TABLE", QUERY_TABLE="MARA", ...)
```

---

## Error handling reference

| Exception | Meaning | Agent response |
|---|---|---|
| `pyrfc.LogonError` | Wrong user/password | "登录失败：用户名或密码错误" |
| `pyrfc.CommunicationError` | Network/SAProuter issue | "连接失败：检查网络或 SAProuter" |
| `pyrfc.ABAPRuntimeError` | ABAP dump or auth issue | Show `e.message` content |
| `pyrfc.ExternalRuntimeError` | RFC layer error | Show error details |
| RETURN TYPE=E | BAPI business error | Show MESSAGE field content |
| RETURN TYPE=W | BAPI warning | Show to user but allow continue |
