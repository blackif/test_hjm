# Common SAP Tables by Module

## FI Tables
| Table | Description | Key Fields |
|-------|-------------|------------|
| BKPF | Accounting Document Header | MANDT,BUKRS,BELNR,GJAHR |
| BSEG | Accounting Document Segment | +BUZEI,KOART,HKONT |
| SKA1 | G/L Account Master (Chart of Accounts) | KTOPL,SAKNR |
| SKB1 | G/L Account Master (Company Code) | BUKRS,SAKNR |
| BSAK | Cleared vendor items | BUKRS,LIFNR |
| BSIK | Open vendor items | BUKRS,LIFNR |
| BSAD | Cleared customer items | BUKRS,KUNNR |
| BSID | Open customer items | BUKRS,KUNNR |
| LFB1 | Vendor Master Company Code | LIFNR,BUKRS |
| LFA1 | Vendor Master General | LIFNR |
| KNB1 | Customer Master Company Code | KUNNR,BUKRS |
| KNA1 | Customer Master General | KUNNR |

## MM Tables
| Table | Description | Key Fields |
|-------|-------------|------------|
| MARA | Material Master General Data | MANDT,MATNR |
| MARC | Material Master Plant Data | MATNR,WERKS |
| MARD | Storage Location Data | MATNR,WERKS,LGORT |
| MAKT | Material Descriptions | MATNR,SPRAS |
| EKKO | Purchase Order Header | MANDT,EBELN |
| EKPO | Purchase Order Item | EBELN,EBELP |
| EKET | Delivery Schedule | EBELN,EBELP,ETENR |
| MSEG | Material Document Segment | MBLNR,MJAHR,ZEILE |
| MKPF | Material Document Header | MBLNR,MJAHR |
| EBAN | Purchase Requisition | BANFN,BNFPO |

## SD Tables
| Table | Description | Key Fields |
|-------|-------------|------------|
| VBAK | Sales Document Header | VBELN |
| VBAP | Sales Document Item | VBELN,POSNR |
| VBEP | Sales Document Schedule Line | VBELN,POSNR,ETENR |
| LIKP | Delivery Header | VBELN |
| LIPS | Delivery Item | VBELN,POSNR |
| VBRK | Billing Document Header | VBELN |
| VBRP | Billing Document Item | VBELN,POSNR |
| KNA1 | Customer Master | KUNNR |

## PP Tables
| Table | Description | Key Fields |
|-------|-------------|------------|
| AUFK | Order Master Data | AUFNR |
| AFPO | Order Item | AUFNR,POSNR |
| RESB | Reservation/Requirements | RSNUM,RSPOS |
| PLKO | Task List Header | PLNTY,PLNNR |
| PLPO | Task List Operation | PLNTY,PLNNR,PLNKN |

## HR Tables
| Table | Description | Key Fields |
|-------|-------------|------------|
| PA0000 | Actions (Infotype 0000) | PERNR,BEGDA,ENDDA |
| PA0001 | Org Assignment (Infotype 0001) | PERNR,BEGDA |
| PA0002 | Personal Data (Infotype 0002) | PERNR,BEGDA |
| PA0008 | Basic Pay (Infotype 0008) | PERNR,BEGDA |
| HRP1000 | Org Object (Infotype 1000) | OTYPE,OBJID |

## System/Basis Tables
| Table | Description | Key Fields |
|-------|-------------|------------|
| T001 | Company Codes | BUKRS |
| T001W | Plants | WERKS |
| T880 | Client Table | MANDT |
| TVARVC | Table of Variant Variables | NAME,TYPE |
| USR02 | User Password Data | BNAME |
| AGR_USERS | Role Assignments | BNAME,AGR_NAME |

---

## RFC_READ_TABLE Usage Notes

```python
# ⚠️ RFC_READ_TABLE has a 512-char row width limit
# For wide tables, select specific fields only

result = conn.call("RFC_READ_TABLE",
    QUERY_TABLE="EKKO",
    DELIMITER="|",
    ROWCOUNT=200,
    FIELDS=[
        {"FIELDNAME": "EBELN"},
        {"FIELDNAME": "LIFNR"},
        {"FIELDNAME": "BEDAT"},
        {"FIELDNAME": "NETWR"},
    ],
    OPTIONS=[
        {"TEXT": "BUKRS EQ '1000'"},
        {"TEXT": "AND BEDAT GE '20240101'"}
    ]
)
```

**Alternative for wide tables**: Use custom ABAP FM or `/BODS/RFC_READ_TABLE2` if available.
