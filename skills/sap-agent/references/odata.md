# SAP OData / REST API (S/4HANA Fallback)

Use this when:
- SAP NW RFC SDK cannot be installed
- Target system is **S/4HANA Cloud** (no direct RFC access)
- Need to integrate via standard APIs

---

## Authentication

### S/4HANA On-Prem (Basic Auth)
```python
import requests
from requests.auth import HTTPBasicAuth

SAP_HOST = "https://your-sap-host:44300"
AUTH = HTTPBasicAuth("user", "password")

# CSRF token (required for POST/PUT/DELETE)
def get_csrf_token(service_url):
    resp = requests.get(service_url, auth=AUTH,
        headers={"X-CSRF-Token": "Fetch"})
    return resp.headers.get("X-CSRF-Token"), resp.cookies

token, cookies = get_csrf_token(f"{SAP_HOST}/sap/opu/odata/sap/MM_PUR_PO_MAINTAIN_SRV/")
```

### S/4HANA Cloud (OAuth 2.0)
```python
def get_oauth_token(client_id, client_secret, token_url):
    resp = requests.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    })
    return resp.json()["access_token"]
```

---

## Common OData Services

| Module | Service | Path |
|--------|---------|------|
| MM - PO | MM_PUR_PO_MAINTAIN_SRV | /sap/opu/odata/sap/... |
| MM - Material | API_MATERIAL_DOCUMENT_SRV | /sap/opu/odata/sap/... |
| FI - Journals | API_JOURNALENTRYITEMBASIC | /sap/opu/odata/sap/... |
| SD - Sales Order | API_SALES_ORDER_SRV | /sap/opu/odata/sap/... |
| HR - Employee | HCM_EMPLOYEE_API_SRV | /sap/opu/odata/sap/... |

---

## Read (GET)

```python
def odata_get(service_path, entity, filters=None, select=None, top=100):
    url = f"{SAP_HOST}{service_path}/{entity}"
    params = {"$format": "json", "$top": top}
    if filters: params["$filter"] = filters
    if select: params["$select"] = ",".join(select)
    
    resp = requests.get(url, auth=AUTH, params=params)
    resp.raise_for_status()
    return resp.json()["d"]["results"]

# Example: Get purchase orders
pos = odata_get(
    "/sap/opu/odata/sap/MM_PUR_PO_MAINTAIN_SRV",
    "PurchaseOrder",
    filters="CompanyCode eq '1000'",
    select=["PurchaseOrder", "Supplier", "DocumentDate"]
)
```

## Create (POST)

```python
def odata_post(service_path, entity, payload):
    url = f"{SAP_HOST}{service_path}/{entity}"
    token, cookies = get_csrf_token(f"{SAP_HOST}{service_path}/")
    
    resp = requests.post(url, auth=AUTH, cookies=cookies,
        headers={"X-CSRF-Token": token, "Content-Type": "application/json"},
        json=payload
    )
    resp.raise_for_status()
    return resp.json()["d"]
```

---

## SAP Business Accelerator Hub

Browse all available APIs: https://api.sap.com

Search for your business process to find the right OData service name.
