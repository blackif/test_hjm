# MM Module Workflows

## Create Purchase Order (BAPI_PO_CREATE1)

### Required Fields Checklist
- [ ] Company Code (BUKRS)
- [ ] Purchasing Org (EKORG)  
- [ ] Purchasing Group (EKGRP)
- [ ] Vendor (LIFNR)
- [ ] Material Number (MATNR)
- [ ] Quantity (MENGE)
- [ ] Plant (WERKS)
- [ ] Storage Location (LGORT) — optional
- [ ] Delivery Date (EINDT)

### Code
```python
def create_purchase_order(conn, header, items):
    """
    header: dict with COMP_CODE, PURCH_ORG, PUR_GROUP, VENDOR
    items: list of dicts with MATERIAL, QUANTITY, PLANT, NET_PRICE, CURRENCY
    """
    po_header = {
        "COMP_CODE":  header["company_code"],
        "PURCH_ORG":  header["purch_org"],
        "PUR_GROUP":  header["pur_group"],
        "VENDOR":     header["vendor"],
        "DOC_TYPE":   header.get("doc_type", "NB"),
        "CURRENCY":   header.get("currency", "CNY"),
    }
    
    po_items = []
    po_schedule = []
    
    for i, item in enumerate(items, 1):
        item_no = str(i * 10).zfill(5)
        po_items.append({
            "PO_ITEM":   item_no,
            "MATERIAL":  item["material"],
            "PLANT":     item["plant"],
            "STGE_LOC":  item.get("storage_loc", ""),
            "QUANTITY":  item["quantity"],
            "NET_PRICE": item.get("net_price", 0),
            "CURRENCY":  item.get("currency", "CNY"),
            "UNIT":      item.get("unit", "PC"),
        })
        po_schedule.append({
            "PO_ITEM":   item_no,
            "SCHED_LINE": "0001",
            "DEL_DATCAT_EXT": "D",
            "DELIVERY_DATE": item.get("delivery_date", ""),
            "QUANTITY":  item["quantity"],
        })
    
    result = conn.call("BAPI_PO_CREATE1",
        POHEADER=po_header,
        POITEM=po_items,
        POSCHEDULE=po_schedule
    )
    
    # Check errors
    errors = [m for m in result.get("RETURN", []) if m["TYPE"] in ("E","A")]
    if errors:
        conn.call("BAPI_TRANSACTION_ROLLBACK")
        raise Exception(f"PO creation failed: {errors[0]['MESSAGE']}")
    
    conn.call("BAPI_TRANSACTION_COMMIT", WAIT="X")
    return result.get("EXPPURCHASEORDER")
```

---

## Goods Receipt (BAPI_GOODSMVT_CREATE)

```python
def post_goods_receipt(conn, po_number, items):
    """
    Movement type 101: GR against PO
    items: list of {po_item, material, plant, quantity, storage_loc}
    """
    header = {
        "PSTNG_DATE": datetime.now().strftime("%Y%m%d"),
        "DOC_DATE":   datetime.now().strftime("%Y%m%d"),
        "PR_UNAME":   "AGENT",
        "REF_DOC_NO": po_number,
    }
    
    gm_items = []
    for item in items:
        gm_items.append({
            "MATERIAL":   item["material"],
            "PLANT":      item["plant"],
            "STGE_LOC":   item.get("storage_loc", "0001"),
            "MOVE_TYPE":  "101",
            "ENTRY_QNT":  item["quantity"],
            "ENTRY_UOM":  item.get("unit", "PC"),
            "PO_NUMBER":  po_number,
            "PO_ITEM":    item["po_item"],
        })
    
    result = conn.call("BAPI_GOODSMVT_CREATE",
        GOODSMVT_HEADER=header,
        GOODSMVT_ITEM=gm_items,
        GOODSMVT_CODE={"GM_CODE": "01"}
    )
    
    errors = [m for m in result.get("RETURN", []) if m["TYPE"] in ("E","A")]
    if errors:
        conn.call("BAPI_TRANSACTION_ROLLBACK")
        raise Exception(errors[0]["MESSAGE"])
    
    conn.call("BAPI_TRANSACTION_COMMIT", WAIT="X")
    return result.get("MATERIALDOCUMENT"), result.get("MATDOCUMENTYEAR")
```

---

## Query Stock (Read Table)

```python
def get_material_stock(conn, material, plant=None):
    where = f"MATNR EQ '{material.zfill(18)}'"
    if plant:
        where += f" AND WERKS EQ '{plant}'"
    
    rows = read_sap_table(conn, "MARD",
        fields=["MATNR","WERKS","LGORT","LABST","EINME","SPEME"],
        where=where
    )
    return rows
    # LABST = unrestricted stock
    # EINME = stock in transfer
    # SPEME = blocked stock
```
