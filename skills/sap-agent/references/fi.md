# FI (Financial Accounting) Module Workflows

All calls use `safe_call()` and `call_bapi()` from the SAP session module.

---

## Key FI Tables

| Table | Description | Primary Keys |
|---|---|---|
| BKPF | Accounting document header | MANDT, BUKRS, BELNR, GJAHR |
| BSEG | Accounting document line items | +BUZEI |
| BSAK | Cleared vendor items (archive view) | BUKRS, LIFNR, AUGDT |
| BSIK | Open vendor items | BUKRS, LIFNR |
| BSAD | Cleared customer items | BUKRS, KUNNR |
| BSID | Open customer items | BUKRS, KUNNR |
| BSIS | Open G/L items | BUKRS, HKONT |
| BSAS | Cleared G/L items | BUKRS, HKONT |
| LFA1 | Vendor master (general) | LIFNR |
| LFB1 | Vendor master (company code) | LIFNR, BUKRS |
| KNA1 | Customer master (general) | KUNNR |
| KNB1 | Customer master (company code) | KUNNR, BUKRS |
| SKA1 | G/L account master (chart of accounts) | KTOPL, SAKNR |
| SKB1 | G/L account master (company code) | BUKRS, SAKNR |
| T001 | Company codes | BUKRS |
| TCURR | Exchange rates | KURST, FCURR, TCURR, GDATU |

---

## 1. Post G/L Journal Entry (BAPI_ACC_DOCUMENT_POST)

### Required fields checklist
- [ ] Company code (BUKRS)
- [ ] Document date (BLDAT)
- [ ] Posting date (BUDAT)
- [ ] Document type (BLART) — e.g. SA=G/L, KR=vendor invoice, DR=customer invoice
- [ ] Currency (WAERS)
- [ ] At least 2 line items, debits = credits

```python
def post_gl_document(company_code: str, doc_date: str, post_date: str,
                     currency: str, items: list, header_text: str = "") -> dict:
    """
    items: list of dicts with keys:
        gl_account (str), debit_credit ('S'=debit/'H'=credit),
        amount (float), cost_center (str, optional), text (str, optional)
    doc_date / post_date: 'YYYYMMDD'
    """
    doc_header = {
        "COMP_CODE":   company_code,
        "DOC_DATE":    doc_date,
        "PSTNG_DATE":  post_date,
        "DOC_TYPE":    "SA",
        "CURRENCY":    currency,
        "HEADER_TXT":  header_text,
    }

    account_gl   = []
    currency_amt = []

    for i, item in enumerate(items, 1):
        account_gl.append({
            "ITEMNO_ACC":  str(i * 10).zfill(10),
            "GL_ACCOUNT":  item["gl_account"].zfill(10),
            "ITEM_TEXT":   item.get("text", ""),
            "COSTCENTER":  item.get("cost_center", ""),
        })
        currency_amt.append({
            "ITEMNO_ACC":  str(i * 10).zfill(10),
            "CURRENCY":    currency,
            "AMT_DOCCUR":  item["amount"] if item["debit_credit"] == "S" else -item["amount"],
        })

    result = safe_call("BAPI_ACC_DOCUMENT_POST",
        DOCUMENTHEADER=doc_header,
        ACCOUNTGL=account_gl,
        CURRENCYAMOUNT=currency_amt,
    )

    if not result["success"]:
        return result

    safe_call("BAPI_TRANSACTION_COMMIT", WAIT="X")

    # Get created document number from RETURN messages
    messages = result["data"].get("RETURN", [])
    doc_number = ""
    for msg in messages:
        if msg.get("TYPE") == "S" and msg.get("NUMBER") == "017":
            # Message 017: Document XXXXXXXXXX posted in company code XXXX
            doc_number = msg.get("MESSAGE_V2", "")
            break

    return {"success": True, "doc_number": doc_number, "messages": messages}
```

---

## 2. Post Vendor Invoice (BAPI_INCOMINGINVOICE_CREATE)

```python
def post_vendor_invoice(company_code: str, vendor: str, invoice_date: str,
                        post_date: str, amount: float, currency: str,
                        po_number: str = "", tax_code: str = "") -> dict:
    """
    po_number: reference PO if this is a PO-based invoice
    tax_code:  SAP tax condition code (e.g. 'J1' for 6% VAT)
    """
    header = {
        "INVOICE_IND":  "X",          # X=invoice, space=credit memo
        "DOC_TYPE":     "RE",
        "COMP_CODE":    company_code,
        "PSTNG_DATE":   post_date,
        "INVOICE_DATE": invoice_date,
        "VENDOR_NO":     vendor.zfill(10),
        "CURRENCY":     currency,
        "GROSS_AMOUNT": str(amount),
        "PMNTTRMS":     "",
    }

    item_data = []
    if po_number:
        item_data.append({
            "INVOICE_DOC_ITEM": "000001",
            "PO_NUMBER":        po_number,
            "PO_ITEM":          "00010",
            "TAX_CODE":         tax_code,
            "ITEM_AMOUNT":      str(amount),
            "QUANTITY":         "1",
        })

    result = safe_call("BAPI_INCOMINGINVOICE_CREATE",
        HEADERDATA=header,
        ITEMDATA=item_data if item_data else [],
    )

    if not result["success"]:
        return result

    safe_call("BAPI_TRANSACTION_COMMIT", WAIT="X")

    inv_doc = result["data"].get("INVOICEDOCNUMBER", "")
    return {"success": True, "invoice_doc": inv_doc}
```

---

## 3. Display FI Document (BAPI_DOCUMENT_GETDETAIL2)

```python
def get_fi_document(company_code: str, doc_number: str, fiscal_year: str) -> dict:
    result = safe_call("BAPI_DOCUMENT_GETDETAIL2",
        COMPANYCODE=company_code,
        DOCUMENTNUMBER=doc_number.zfill(10),
        FISCALYEAR=fiscal_year,
    )
    if not result["success"]:
        return result

    data = result["data"]
    return {
        "success":  True,
        "header":   data.get("DOCUMENTHEADER", {}),
        "items":    data.get("LINEITEMS", []),
        "currency": data.get("CURRENCYLIST", []),
    }
```

---

## 4. Get Open Items (vendor / customer)

```python
def get_open_items(account_type: str, account: str, company_code: str) -> list:
    """
    account_type: 'K'=vendor, 'D'=customer, 'S'=G/L
    """
    table_map = {"K": "BSIK", "D": "BSID", "S": "BSIS"}
    key_map   = {"K": "LIFNR", "D": "KUNNR", "S": "HKONT"}

    table = table_map[account_type]
    key   = key_map[account_type]

    from references.operations import read_sap_table
    rows = read_sap_table(
        table,
        fields=["BELNR", "GJAHR", "BUDAT", "BLDAT", "BLART", "WRBTR", "WAERS", "SGTXT"],
        where=f"BUKRS EQ '{company_code}' AND {key} EQ '{account.zfill(10)}'",
        max_rows=200
    )
    return rows
```

---

## 5. Get G/L Account Balance

```python
def get_gl_balance(company_code: str, gl_account: str,
                   fiscal_year: str, period_from: int = 1, period_to: int = 12) -> dict:
    result = safe_call("BAPI_GL_GETGLACCPERIODVALUES",
        COMPANYCODE=company_code,
        GLACCOUNT=gl_account.zfill(10),
        FISCALYEAR=fiscal_year,
        PERIODRANGE={"PERIOD_FROM": str(period_from).zfill(3),
                     "PERIOD_TO":   str(period_to).zfill(3)},
    )
    return result
```

---

## 6. Clear Open Items (BAPI_ACC_DOCUMENT_POST with clearing)

```python
def clear_vendor_items(company_code: str, vendor: str,
                       items_to_clear: list, clearing_date: str) -> dict:
    """
    items_to_clear: list of {"doc_number": "...", "fiscal_year": "...", "item_no": "001"}
    """
    header = {
        "COMP_CODE":   company_code,
        "DOC_DATE":    clearing_date,
        "PSTNG_DATE":  clearing_date,
        "DOC_TYPE":    "KZ",          # Payment clearing
    }

    accounts_payable = [{
        "ITEMNO_ACC":    "0000000010",
        "VENDOR_NO":     vendor.zfill(10),
        "PMNT_BLOCK":    "",
    }]

    open_item_list = []
    for item in items_to_clear:
        open_item_list.append({
            "ITEMNO_ACC":    "0000000010",
            "COMP_CODE":     company_code,
            "FISC_YEAR":     item["fiscal_year"],
            "FI_DOC_NUM":    item["doc_number"].zfill(10),
            "ONE_TIME_ACCT": "",
        })

    result = safe_call("BAPI_ACC_DOCUMENT_POST",
        DOCUMENTHEADER=header,
        ACCOUNTPAYABLE=accounts_payable,
        PAYMENTCARDS=[],
        CRITERIA=open_item_list,
    )

    if not result["success"]:
        return result

    safe_call("BAPI_TRANSACTION_COMMIT", WAIT="X")
    return {"success": True}
```

---

## Common FI Document Types

| Type | Description |
|---|---|
| SA | G/L account document |
| KR | Vendor invoice |
| KZ | Vendor payment |
| KG | Vendor credit memo |
| RE | Invoice receipt (MM-FI) |
| DR | Customer invoice |
| DZ | Customer payment |
| DG | Customer credit memo |
| AA | Asset posting |
| AB | Accounting document |

## Common Posting Keys

| Key | Description | Account type |
|---|---|---|
| 40 | Debit G/L | G/L |
| 50 | Credit G/L | G/L |
| 31 | Vendor invoice | Vendor |
| 25 | Vendor outgoing payment | Vendor |
| 01 | Customer invoice | Customer |
| 15 | Customer incoming payment | Customer |
