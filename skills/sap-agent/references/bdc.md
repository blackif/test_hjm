# BDC / Batch Input Guide

BDC (Batch Data Communication) simulates SAP GUI screen-by-screen entry.
Use when a business process has **no BAPI** or the BAPI is too restrictive.

All BDC calls use `run_bdc()` from the SAP session module.

---

## How BDC Works

```
Agent builds dynpro_data list
         │
         ▼
ABAP4_CALL_TRANSACTION
         │
         ▼
SAP processes screens sequentially:
  [Screen header] → [Field values] → [Screen header] → [Field values] ...
         │
         ▼
Returns BDCMSGCOLL (message collection) with results
```

Each entry in `dynpro_data` is either:
- **Screen header**: `{"PROGRAM": "...", "DYNPRO": "NNNN", "DYNBEGIN": "X"}`
- **Field value**: `{"FNAM": "field_name", "FVAL": "value"}`

Special field names:
| Field | Meaning |
|---|---|
| `BDC_OKCODE` | Function code (like pressing a button or Enter) |
| `BDC_CURSOR` | Field that receives cursor focus |

Common `BDC_OKCODE` values:
| Code | Action |
|---|---|
| `/00` or `` (empty) | Press Enter |
| `=SICH` or `=BU` | Save (Buchen) |
| `=BACK` | Back (F3) |
| `=EXIT` | Exit (F15) |
| `=CANC` | Cancel |
| `=P+` | Page Down |

---

## How to Find Screen/Field Names

**Method 1: SAP GUI Recording**
1. In SAP GUI → System → Utilities → **Recording** (SHDB)
2. Create new recording, enter T-code, perform the steps manually
3. Save → view the generated BDC program — it lists every PROGRAM, DYNPRO, and FNAM

**Method 2: Technical info overlay**
- In SAP GUI, go to the screen
- Menu: System → **Technical Information** (or Shift+F1 on a field)
- Shows: Program name, Screen number, Field name (Data element → Structure-Field)

**Method 3: SE51 (Screen Painter)**
- Open transaction SE51
- Enter program + screen number
- View the field list with their technical names

---

## Common BDC Transactions

### FB01 — Post General Journal Entry

```python
# Post a simple G/L debit/credit pair
dynpro_data = [
    # Screen 1: Document header
    {"PROGRAM": "SAPMF05A", "DYNPRO": "0100", "DYNBEGIN": "X"},
    {"FNAM": "BDC_CURSOR",   "FVAL": "RF05A-NEWBS"},
    {"FNAM": "BKPF-BLDAT",   "FVAL": "01.01.2024"},  # Document date (DD.MM.YYYY)
    {"FNAM": "BKPF-BLART",   "FVAL": "SA"},           # Document type
    {"FNAM": "BKPF-BUKRS",   "FVAL": "1000"},          # Company code
    {"FNAM": "BKPF-BUDAT",   "FVAL": "01.01.2024"},   # Posting date
    {"FNAM": "BKPF-MONAT",   "FVAL": "01"},            # Period
    {"FNAM": "BKPF-WAERS",   "FVAL": "CNY"},           # Currency
    {"FNAM": "RF05A-NEWBS",  "FVAL": "40"},            # Posting key (40=debit GL)
    {"FNAM": "RF05A-NEWKO",  "FVAL": "0000113100"},    # Account number
    {"FNAM": "BDC_OKCODE",   "FVAL": "/00"},           # Enter

    # Screen 2: First line item (debit)
    {"PROGRAM": "SAPMF05A", "DYNPRO": "0300", "DYNBEGIN": "X"},
    {"FNAM": "BDC_CURSOR",   "FVAL": "BSEG-WRBTR"},
    {"FNAM": "BSEG-WRBTR",   "FVAL": "1000.00"},       # Amount
    {"FNAM": "BSEG-SGTXT",   "FVAL": "Agent BDC post"},# Item text
    {"FNAM": "RF05A-NEWBS",  "FVAL": "50"},            # Next posting key (50=credit GL)
    {"FNAM": "RF05A-NEWKO",  "FVAL": "0000400000"},    # Credit account
    {"FNAM": "BDC_OKCODE",   "FVAL": "/00"},           # Enter

    # Screen 3: Second line item (credit)
    {"PROGRAM": "SAPMF05A", "DYNPRO": "0300", "DYNBEGIN": "X"},
    {"FNAM": "BDC_CURSOR",   "FVAL": "BSEG-WRBTR"},
    {"FNAM": "BSEG-WRBTR",   "FVAL": "1000.00"},
    {"FNAM": "BSEG-SGTXT",   "FVAL": "Agent BDC post"},
    {"FNAM": "BDC_OKCODE",   "FVAL": "=BU"},           # Save
]

result = run_bdc("FB01", dynpro_data, mode="N")
```

---

### ME21N — Create Purchase Order (screen-based)

Use this when `BAPI_PO_CREATE1` is not available or authorized.

```python
dynpro_data = [
    # Initial screen
    {"PROGRAM": "SAPMM06E",  "DYNPRO": "0100", "DYNBEGIN": "X"},
    {"FNAM": "BDC_CURSOR",   "FVAL": "EKKO-LIFNR"},
    {"FNAM": "EKKO-LIFNR",   "FVAL": "0001000123"},   # Vendor
    {"FNAM": "EKKO-EKORG",   "FVAL": "1000"},          # Purchase org
    {"FNAM": "EKKO-EKGRP",   "FVAL": "001"},           # Purchase group
    {"FNAM": "EKKO-BUKRS",   "FVAL": "1000"},          # Company code
    {"FNAM": "BDC_OKCODE",   "FVAL": "/00"},

    # Item screen
    {"PROGRAM": "SAPMM06E",  "DYNPRO": "0120", "DYNBEGIN": "X"},
    {"FNAM": "EKPO-MATNR(01)","FVAL": "MATERIAL001"},  # Material
    {"FNAM": "EKPO-MENGE(01)","FVAL": "10"},           # Quantity
    {"FNAM": "EKPO-WERKS(01)","FVAL": "1000"},         # Plant
    {"FNAM": "EKPO-EINDT(01)","FVAL": "31.12.2024"},   # Delivery date
    {"FNAM": "BDC_OKCODE",   "FVAL": "=SICH"},         # Save
]
```

---

### XD01 — Create Customer Master

```python
dynpro_data = [
    # Account group selection
    {"PROGRAM": "SAPMF02D",  "DYNPRO": "0100", "DYNBEGIN": "X"},
    {"FNAM": "RF02D-KTOKD",  "FVAL": "DEBI"},          # Account group
    {"FNAM": "RF02D-BUKRS",  "FVAL": "1000"},
    {"FNAM": "RF02D-VKORG",  "FVAL": "1000"},          # Sales org
    {"FNAM": "RF02D-VTWEG",  "FVAL": "10"},            # Distribution channel
    {"FNAM": "RF02D-SPART",  "FVAL": "00"},            # Division
    {"FNAM": "BDC_OKCODE",   "FVAL": "/00"},

    # General data
    {"PROGRAM": "SAPMF02D",  "DYNPRO": "0110", "DYNBEGIN": "X"},
    {"FNAM": "KNA1-NAME1",   "FVAL": "Test Customer Co"},
    {"FNAM": "KNA1-SORTL",   "FVAL": "TESTCUST"},
    {"FNAM": "KNA1-LAND1",   "FVAL": "CN"},
    {"FNAM": "KNA1-ORT01",   "FVAL": "Shanghai"},
    {"FNAM": "BDC_OKCODE",   "FVAL": "/00"},

    # Save
    {"PROGRAM": "SAPMF02D",  "DYNPRO": "0120", "DYNBEGIN": "X"},
    {"FNAM": "BDC_OKCODE",   "FVAL": "=SICH"},
]
```

---

## Reading BDC Results

```python
result = run_bdc("FB01", dynpro_data, mode="N")

if not result["success"]:
    print(f"BDC failed: {result['error']}")
else:
    # Parse BDCMSGCOLL for detailed messages
    messages = result["data"].get("MESSTAB", [])  # or BDCMSGCOLL depending on FM
    for msg in messages:
        msg_type = msg.get("MSGTYP", "")    # S=success, E=error, W=warning
        msg_text = msg.get("MSGV1", "")
        if msg_type == "E":
            print(f"Error: {msg_text}")
        elif msg_type == "S":
            print(f"OK: {msg_text}")          # Often contains created document number
```

---

## BDC Mode Reference

| Mode | Behavior | Use when |
|---|---|---|
| `N` | No dialog, background | Production / automation |
| `A` | Show all screens | Testing / debugging |
| `E` | Show only error screens | Semi-automatic with error handling |

Always use `N` in production. Switch to `A` or `E` only during development to verify screen flow.

---

## Tips & Gotchas

- **Date format**: SAP expects `DD.MM.YYYY` in BDC, NOT `YYYYMMDD` (that's for BAPIs)
- **Leading zeros**: Accounts and materials need full padded format (`0001000123`, not `1000123`)
- **Mandatory F4 checks**: Some fields validate against allowed values on screen — the BDC value must match exactly what F4 would return
- **Table controls**: For repeating line items, use index notation: `FNAM: "FIELDNAME(01)"`, `"FIELDNAME(02)"`, etc.
- **OKCODE timing**: Always place `BDC_OKCODE` as the **last** entry on a screen block, after all field values
- **Long texts**: Fields with F1 long text editors require additional screen navigation — avoid if possible
