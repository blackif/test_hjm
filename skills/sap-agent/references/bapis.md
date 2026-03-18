# SAP BAPI Reference by Business Process

## FI (Financial Accounting)

| Business Action | BAPI / FM | Key Params |
|----------------|-----------|------------|
| Post journal entry | `BAPI_ACC_DOCUMENT_POST` | DOCUMENTHEADER, ACCOUNTGL, CURRENCYAMOUNT |
| Display FI doc | `BAPI_DOCUMENT_GETDETAIL2` | AWTYP, AWKEY |
| Clear open items | `BAPI_ACC_DOCUMENT_POST` (clearing type) | |
| Get GL balance | `BAPI_GL_GETGLACCPERIODVALUES` | COMPANYCODE, GLACCOUNT |
| Vendor invoice | `BAPI_INCOMINGINVOICE_CREATE` | HEADERDATA, ITEMDATA |
| Customer payment | `BAPI_ACC_DOCUMENT_POST` | ACCOUNTRECEIVABLE |

## MM (Materials Management)

| Business Action | BAPI / FM | Key Params |
|----------------|-----------|------------|
| Create PO | `BAPI_PO_CREATE1` | POHEADER, POITEM, POSCHEDULE |
| Change PO | `BAPI_PO_CHANGE` | PURCHASEORDER, POHEADER, POITEM |
| Get PO detail | `BAPI_PO_GETDETAIL1` | PURCHASEORDER |
| Goods receipt | `BAPI_GOODSMVT_CREATE` | GOODSMVT_HEADER, GOODSMVT_ITEM |
| Material stock | `BAPI_MATERIAL_STOCK_REQ_LIST` | MATERIAL, PLANT |
| Create material | `BAPI_MATERIAL_SAVEDATA` | HEADDATA, various views |
| Change material | `BAPI_MATERIAL_SAVEDATA` | same |
| Create vendor | `BAPI_VENDOR_CREATEFROMDATA` | COMPANYDATA, PERSONALDATA |

## SD (Sales & Distribution)

| Business Action | BAPI / FM | Key Params |
|----------------|-----------|------------|
| Create sales order | `BAPI_SALESORDER_CREATEFROMDAT2` | ORDER_HEADER_IN, ORDER_ITEMS_IN |
| Change sales order | `BAPI_SALESORDER_CHANGE` | SALESDOCUMENT, ORDER_HEADER_IN |
| Create delivery | `BAPI_OUTB_DELIVERY_CREATE_STO` | |
| Post goods issue | `BAPI_OUTB_DELIVERY_POST_GOO` | DELIVERY |
| Create invoice | `RV_INVOICE_CREATE` | VBSK_I, VBSS_I |
| Get customer | `BAPI_CUSTOMER_GETDETAIL2` | CUSTOMERNO |

## PP (Production Planning)

| Business Action | BAPI / FM | Key Params |
|----------------|-----------|------------|
| Create prod order | `BAPI_PRODORD_CREATE` | ORDERDATA |
| Release prod order | `BAPI_PRODORD_RELEASE` | NUMBER |
| Confirm order op | `BAPI_PRODORDCONF_CREATE_TT` | TIMETICKETS |
| Get order detail | `BAPI_PRODORD_GET_DETAIL` | NUMBER |

## HR (Human Resources)

| Business Action | BAPI / FM | Key Params |
|----------------|-----------|------------|
| Get employee data | `BAPI_EMPLOYEE_GETDATA` | EMPLOYEE_ID |
| Create employee | `BAPI_EMPLOYEE_CREATEFROMDATA` | |
| Get org assignment | `BAPI_EMPINTERNALWAGECOMP_GET` | |
| Read infotype | `HR_READ_INFOTYPE` | PERNR, INFTY, BEGDA, ENDDA |

## Workflow / Common

| Business Action | BAPI / FM | Key Params |
|----------------|-----------|------------|
| Commit transaction | `BAPI_TRANSACTION_COMMIT` | WAIT="X" |
| Rollback | `BAPI_TRANSACTION_ROLLBACK` | |
| Execute workitem | `BAPI_WORKITEM_EXECUTE` | WORKITEMID |
| Read user data | `SUSR_USER_AUTH_FOR_OBJ_GET` | BNAME |
| Schedule job | `JOB_OPEN`, `JOB_SUBMIT`, `JOB_CLOSE` | |

---

## BAPI Call Pattern (Always use this)

```python
# 1. Call BAPI
result = conn.call("BAPI_PO_CREATE1",
    POHEADER={"COMP_CODE": "1000", "DOC_TYPE": "NB", ...},
    POITEM=[{"PO_ITEM": "00010", "MATERIAL": "MAT001", ...}],
    POSCHEDULE=[{"PO_ITEM": "00010", "QUANTITY": 10.0, ...}]
)

# 2. ALWAYS check RETURN table
return_table = result.get("RETURN", [])
for msg in return_table:
    msg_type = msg.get("TYPE", "")
    msg_text = msg.get("MESSAGE", "")
    if msg_type in ("E", "A"):  # Error or Abort
        raise Exception(f"SAP Error: {msg_text}")
    elif msg_type == "W":  # Warning
        print(f"Warning: {msg_text}")

# 3. Commit only if success
conn.call("BAPI_TRANSACTION_COMMIT", WAIT="X")

# 4. Get created document number
po_number = result.get("EXPPURCHASEORDER", "")
print(f"PO created: {po_number}")
```
