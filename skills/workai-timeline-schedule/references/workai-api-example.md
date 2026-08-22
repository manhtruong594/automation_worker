# WorkAI API Mau Cho Timeline Schedule

Tai lieu nay la contract mau de backend WorkAI co the trien khai endpoint noi bo cho tool `workai-timeline-schedule`.

## Nguyen Tac

- Tool doc cookie/token tu Chrome session hien co va goi API bang header `Authorization` hoac cookie session.
- API phai idempotent theo `client_request_id` de retry khong tao trung issue/block.
- Moi response loi phai tra `code`, `message`, va trang thai da tao neu co.
- Gio tinh bang hour dang decimal, vi du `1.5`.
- Ngay dung ISO `YYYY-MM-DD`.

## Auth

Tool gui request voi mot trong hai cach:

```http
Authorization: Bearer <WORKAI_TOKEN>
```

Hoac:

```http
Cookie: sessionToken=4662|gcDTZ63I1PVZHqZhSIABRdJk2sr2Xe3TurePdCUTc6776120
```

Neu token/cookie het han:

```json
{
  "error": {
    "code": "UNAUTHENTICATED",
    "message": "Chrome session expired or missing WorkAI auth token."
  }
}
```

## 1. Tao Issue

```http
POST https://workai-be.horus.io.vn/api/issues
Content-Type: application/json
```

Request:

```json
{
  "client_request_id": "workai-timeline-2026-08-20-mob-era-login-ui",
  "project_id": 85,
  "project_name": "G - MOB.ERA",
  "issue_type": "Story",
  "summary": "Xay dung man hinh dang nhap cho quy trinh nguoi choi Mob Era",
  "estimated_hours": 12,
  "description": "",
  "acceptance_criteria": [],
  "optional_context": "Can ho tro email/password va thong bao loi ngan gon."
}
```

## 2. Generate Description Va Acceptance Criteria Bang AI WorkAI

```http
POST https://workai-be.horus.io.vn/api/issues/quick-create/suggest-description
Content-Type: application/json
```

Request:

```json
{
  "project_id": 85,
  "project_name": "G - MOB.ERA",
  "issue_type": "Story",
  "summary": "Xay dung man hinh dang nhap cho quy trinh nguoi choi Mob Era",
  "estimated_hours": 12,
  "project_overview": "Noi dung project_overview da doc tu workspace...",
  "optional_context": "Can ho tro email/password va thong bao loi ngan gon."
}
```

Neu AI khong sinh duoc:

```json
{
  "error": {
    "code": "AI_GENERATION_FAILED",
    "message": "WorkAI AI generation unavailable."
  }
}
```

Khi gap loi nay, tool duoc phep tu sinh noi dung ngan thay the va bao ro trong report.

## 3. Doc Timeline Theo Tuan

```http
GET https://workai-be.horus.io.vn/api/time-allocations?start_date=<start_date>&end_date=<end_date>
```

Tool chi duoc xep vao ngay co `total_hours > 0` va `used_hours < total_hours`.

## 4. Them Block Timeline

```http
POST https://workai-be.horus.io.vn/api/issues/<issue_id>/transition
```

Request:

```json
{
  "client_request_id": "workai-timeline-2026-08-20-mob-era-login-ui-2026-08-17-8h",
  "project_id": 85,
  "issue_key": "GTLU-2716",
  "date": "2026-08-17",
  "hours": 8
}
```

## 5. Tim Issue Theo Key

Dung khi retry hoac can xac minh issue da ton tai.

```http
GET https://workai-be.horus.io.vn/api/time-allocations/available-issues?week_start_date<start_date>&search=<issue_key>&page=1
```

## 6. Doc Timeline Blocks Theo Issue

Dung khi chay lai de chi them phan gio con thieu.

```http
GET https://workai-be.horus.io.vn/api/issues/<issue_id>
```

## Retry Behavior Bat Buoc

Tool luu state tai:

```text
skills/workai-timeline-schedule/.runs/
```

Khi chay lai:

1. Doc run state local.
2. Neu da co `issue_key`, goi `GET /issues/{key}` de xac minh.
3. Goi `GET /timeline/blocks?issue_key=...`.
4. Tinh `remaining_hours = estimated_hours - total_allocated_hours`.
5. Chi them block cho `remaining_hours`.
6. Khong tao issue moi neu issue cu con ton tai.

## Error Response Chung

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "summary must be longer than 50 characters.",
    "details": {
      "field": "summary"
    }
  }
}
```

Code nen ho tro:

- `UNAUTHENTICATED`
- `FORBIDDEN`
- `VALIDATION_ERROR`
- `PROJECT_NOT_FOUND`
- `ISSUE_NOT_FOUND`
- `AI_GENERATION_FAILED`
- `TIMELINE_NOT_FOUND`
- `NON_WORKING_DAY`
- `INSUFFICIENT_DAY_CAPACITY`
- `IDEMPOTENCY_CONFLICT`
- `INTERNAL_ERROR`
