# Complete API Documentation for `/claims/search` Endpoint

## Overview
The `/claims/search` endpoint is a powerful search and filtering API for medical claims data. It supports complex filtering, keyword search, pagination, and custom sorting with special handling for priority claims.

---

## Endpoint Details

**Method:** `POST`  
**URL:** `/claims/search`  
**Authentication:** Required (Bearer Token)

---

## Authentication

**Header Required:**
```
Authorization: Bearer <firebase_id_token>
```

The endpoint uses Firebase authentication and automatically extracts the user's company from the token for multi-tenancy support.

---

## Request Schema

### Body Parameters

```json
{
  "tabIndex": 0,
  "currentPage": 1,
  "perPage": 50,
  "keyword": "",
  "selectedTags": [],
  "startDate": null,
  "endDate": null,
  "extra": {},
  "code": "",
  "remark": "",
  "procedure": "",
  "pos": "",
  "sort": ""
}
```

### Parameter Details

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `tabIndex` | integer | No | `0` | - | Tab context for filtering claims (0-6) |
| `currentPage` | integer | No | `1` | >= 1 | Current page number for pagination |
| `perPage` | integer | No | `50` | 1-1000 | Number of results per page |
| `keyword` | string | No | `""` | - | Search keyword for ClaimNo, PayerName, PatientName, or PrimaryDX |
| `selectedTags` | array[string] | No | `[]` | - | Category tags for filtering (see Tag Logic below) |
| `startDate` | string | No | `null` | ISO date | Service date range start (inclusive) |
| `endDate` | string | No | `null` | ISO date | Service date range end (inclusive) |
| `extra` | object | No | `{}` | - | Additional filters (see Extra Filters below) |
| `code` | string | No | `""` | - | Adjustment code filter (format: GroupReason, e.g., "CONULL") |
| `remark` | string | No | `""` | - | Filter by remark code |
| `procedure` | string | No | `""` | - | Filter by procedure code |
| `pos` | string | No | `""` | - | Filter by Place of Service |
| `sort` | string | No | `""` | - | Sort column (prefix with `-` for descending) |

---

## Response Schema

### Success Response (200 OK)

```json
{
  "message": "Success",
  "data": [
    {
      "ActionDate": "Wed, 15 Jan 2025 12:30:00 GMT",
      "ActionTaken": "Appeal Filed",
      "AllowedAmt": "250.00",
      "Amount": "500.00",
      "Category": "C",
      "ClaimNo": "3012374106",
      "LoadDate": "Mon, 01 Jan 2025 08:00:00 GMT",
      "PayerID": "12345",
      "PayerName": "Blue Cross Blue Shield",
      "PayerSeq": "P",
      "PlaceOfService": "11",
      "PrimaryCode": "CO45",
      "PrimaryDX": "Z00.00",
      "PrimaryGroup": "CO",
      "PrimaryProcedure": "99213",
      "ProvNPI": "1234567890",
      "ProvTaxID": "12-3456789",
      "Remark": "N115",
      "ServiceDate": "Tue, 10 Dec 2024 00:00:00 GMT"
    }
  ],
  "page": 1,
  "maxPage": -1
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Status message |
| `data` | array | Array of claim objects |
| `page` | integer | Current page number |
| `maxPage` | integer | Maximum page number (-1 indicates not calculated) |

### Claim Object Fields

| Field | Type | Format | Description |
|-------|------|--------|-------------|
| `ActionDate` | string/null | GMT datetime | Date action was taken on claim |
| `ActionTaken` | string/null | - | Description of action taken |
| `AllowedAmt` | string/null | "0.00" | Amount allowed by payer |
| `Amount` | string/null | "0.00" | Total claim amount |
| `Category` | string/null | - | Claim category/status |
| `ClaimNo` | string/null | - | Unique claim number |
| `LoadDate` | string/null | GMT datetime | Date claim was loaded |
| `PayerID` | string/null | - | Payer identifier |
| `PayerName` | string/null | - | Name of insurance payer |
| `PayerSeq` | string/null | - | Payer sequence (P=Primary, S=Secondary, etc.) |
| `PlaceOfService` | string/null | - | Location where service was provided |
| `PrimaryCode` | string/null | - | Primary adjustment/denial code |
| `PrimaryDX` | string/null | - | Primary diagnosis code |
| `PrimaryGroup` | string/null | - | Primary adjustment group |
| `PrimaryProcedure` | string/null | - | Primary procedure code |
| `ProvNPI` | string/null | - | Provider National Provider Identifier |
| `ProvTaxID` | string/null | - | Provider Tax ID |
| `Remark` | string/null | - | Remark code |
| `ServiceDate` | string/null | GMT datetime | Date service was provided |

---

## Filtering Logic

### 1. Keyword Search
When `keyword` is provided, searches across:
- Claim Number (`ClaimNo`)
- Payer Name (`PayerName`)
- Patient Name (`PatientName`)
- Primary Diagnosis (`PrimaryDX`)

Uses case-insensitive partial matching (LIKE %keyword%).

### 2. Tag/Category Logic

Tags are context-sensitive based on `tabIndex`:

| tabIndex | Description | Allowed Tags |
|----------|-------------|--------------|
| 0 | All Claims | All except DELINQUENT, Contractual Adj, Patient Resp, Documentation |
| 1 | Contractual | Contractual Adj only |
| 2 | Patient Responsibility | Patient Resp only |
| 3 | Delinquent | DELINQUENT only |
| 5, 6 | Special tabs | All tags |

**Special behavior:**
- If `DELINQUENT` tag is selected: filters claims where `Category IS NULL`
- If no valid tags: defaults to `Category = 'A'` (or NULL if DELINQUENT)
- Multiple tags create an OR condition

### 3. Automation Filter

Based on `tabIndex`:
- **tabIndex = 0**: Automation in ['0', '1'] (manual and automated)
- **tabIndex = 5 with "All" in extra**: No automation filter
- **tabIndex = 5**: Automation != '0' (only automated)
- **tabIndex = 6**: No automation filter
- **Other tabs**: Automation = '0' (manual only)

### 4. Date Range
- `startDate`: Filters `ServiceDate >= startDate`
- `endDate`: Filters `ServiceDate <= endDate`
- Ignores values equal to "string"

### 5. Place of Service
- `pos`: Exact match on `PlaceOfService`

### 6. Subquery Filters

**Remark Code (`remark`):**
Joins with `CustomPaidServiceRemark` table to find claims with specific remark codes.

**Procedure Code (`procedure`):**
Joins with `Procedures` table to find claims with specific procedure codes.

**Adjustment Code (`code`):**
Format: `GroupReason` (e.g., "CO45", "CONULL")
- First 2 characters = Adjustment Group
- Remaining characters = Adjustment Reason
- "NULL" as reason searches for any code in that group
- Joins with `CustomServiceCodeForTable`

---

## Extra Filters Object

The `extra` object supports the following keys:

| Key | Type | Description |
|-----|------|-------------|
| `Recovery` | any | If present, filters claims with Recovery = '1' |
| `PayerResponsibility` | string | Filters by payer sequence (P, S, T, etc.) |
| `InsuranceType` | string | Filters by insurance type |
| `PayerName` | string | Searches payer name (supports '*' delimiter for multiple names) |
| `PayerNameAll` | string | Partial match on payer name |
| `Only` | any | If present, only shows claims with denial actions |
| `Title` | string | Filters by specific denial action title |
| `All` | any | Used with tabIndex=5 to show all automation types |

**Example:**
```json
{
  "extra": {
    "Recovery": "1",
    "PayerResponsibility": "P",
    "InsuranceType": "Commercial",
    "PayerName": "Blue Cross*Aetna",
    "Title": "Appeal"
  }
}
```

---

## Sorting

### Sort Parameter Format
- Column name for ascending: `"ClaimNo"`
- Prefix with `-` for descending: `"-ClaimNo"`
- Default: `-ClaimNo` (descending by claim number)

### Allowed Sort Columns
- `ClaimNo`
- `ServiceDate`
- `Amount`
- `DeniedAmt`
- `PayerName`
- `Category`
- `PrimaryCode`
- `Automation`
- `PlaceOfService`
- `LoadDate`
- `AllowedAmt`
- `ActionDate`

### Priority Claims
The following claims are always sorted first (regardless of sort order):
```
3012374106, 3012144775, 3011958455, 3012844576, 3012373360,
3012104978, 3012036672, 3012007212, 3012006190, 3013333059,
3012186160, 3012670620, 3012684286, 3012301429, 3013310585,
3012820822, 3012525510, 3013182507, 3013146008, 3013269653,
3013192283, 3013255723, 3013054155, 3013040103, 3011978959,
3012091235, 3012202580, 3012342716, 3013408527
```

---

## Pagination

- Uses offset-based pagination
- Offset calculated as: `(currentPage - 1) * perPage`
- Maximum items per page: 1000
- Response does not calculate total pages (maxPage = -1)

---

## Example Requests

### Example 1: Basic Search
```bash
curl -X POST "https://api.example.com/claims/search" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "currentPage": 1,
    "perPage": 50
  }'
```

### Example 2: Keyword Search with Date Range
```bash
curl -X POST "https://api.example.com/claims/search" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "Blue Cross",
    "startDate": "2024-01-01",
    "endDate": "2024-12-31",
    "currentPage": 1,
    "perPage": 100
  }'
```

### Example 3: Advanced Filtering
```bash
curl -X POST "https://api.example.com/claims/search" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "tabIndex": 0,
    "selectedTags": ["C", "D"],
    "pos": "11",
    "code": "CO45",
    "procedure": "99213",
    "extra": {
      "Recovery": "1",
      "PayerResponsibility": "P"
    },
    "sort": "-ServiceDate",
    "currentPage": 1,
    "perPage": 50
  }'
```

### Example 4: Search with Multiple Payers
```bash
curl -X POST "https://api.example.com/claims/search" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "extra": {
      "PayerName": "Blue Cross*Aetna*Cigna"
    },
    "currentPage": 1,
    "perPage": 25
  }'
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Unauthorized or invalid company"
}
```

**Cause:** Invalid or missing authentication token, or user has no associated company.

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "currentPage"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

**Cause:** Invalid request body (validation errors).

---

## Performance Notes

1. **Pagination**: Results are limited to prevent large data transfers. Use pagination for all queries.

2. **Subqueries**: Using `code`, `remark`, or `procedure` filters triggers additional subqueries which may impact performance.

3. **Keyword Search**: Searches across multiple fields using LIKE operator - may be slow on large datasets without proper indexing.

4. **Date Ranges**: Always specify date ranges when possible to improve query performance.

---

## Business Logic Summary

This endpoint implements complex business logic for medical claims management:
- **Multi-tenancy**: Automatically filters by user's company
- **Context-aware filtering**: Different tab contexts apply different rules
- **Priority handling**: Certain claims always appear first
- **Flexible searching**: Supports keyword, tag, date, and multiple custom filters
- **Denial management**: Can filter by denial actions and their titles
- **Recovery tracking**: Can filter claims marked for recovery
- **Payer responsibility**: Supports primary, secondary, tertiary payer filtering

---

## Technical Implementation Details

### Database Tables Used
- `CustomAll` - Main claims table
- `CustomPaidServiceRemark` - Remark codes
- `Procedures` - Procedure codes
- `CustomServiceCodeForTable` - Adjustment codes
- `DenialActions` - Denial action tracking

### Dependencies
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM and query builder
- **Pydantic** - Request/response validation
- **Firebase Authentication** - User authentication and authorization

### Multi-Tenancy
The endpoint automatically filters all queries by the user's company, which is extracted from the Firebase authentication token. This ensures data isolation between different organizations using the system.

---

## Changelog

### Version 2.0.0
- Initial documented version
- Support for complex filtering logic
- Priority claims handling
- Multi-tenancy support
- Firebase authentication integration
