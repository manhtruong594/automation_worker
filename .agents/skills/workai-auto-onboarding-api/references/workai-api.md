# WorkAI API Reference

## Base URL

```text
https://workai-be.horus.io.vn/api
```

## Auth

Không hardcode token.

```http
Authorization: Bearer <WORKAI_TOKEN>
```

hoặc:

```http
Cookie: sessionToken=<WORKAI_SESSION_TOKEN>
```

## Generate Description And Acceptance Criteria

```http
POST /issues/quick-create/suggest-description
Content-Type: application/json
```

Request:

```json
{
  "project_id": 85,
  "project_key": "GTLU",
  "project_name": "G - MOB.ERA",
  "issue_type": "Story",
  "summary": "Xay dung man hinh dang nhap cho quy trinh nguoi choi Mob Era",
  "estimated_hours": 12,
  "project_overview": "Noi dung project_overview da doc tu workspace...",
  "optional_context": "Can ho tro email/password va thong bao loi ngan gon."
}
```

`project_key` là bắt buộc.

Failure mẫu:

```json
{
  "error": {
    "code": "AI_GENERATION_FAILED",
    "message": "WorkAI AI generation unavailable."
  }
}
```

Trong dữ liệu thử gần nhất, request endpoint này timeout sau 75 giây. Skill phải có fallback tự sinh description và acceptance criteria.

## Create Issue

```http
POST /issues
Content-Type: application/json
```

Request:

```json
{
  "client_request_id": "workai-onboarding-2026-08-21-mob-era-login-ui",
  "project_id": 85,
  "project_name": "G - MOB.ERA",
  "issue_type": "Story",
  "summary": "Xay dung man hinh dang nhap cho quy trinh nguoi choi Mob Era",
  "estimated_hours": 12,
  "description": "",
  "acceptance_criteria": [],
  "optional_context": ""
}
```

`client_request_id` bắt buộc ổn định để retry không tạo trùng.

## Read Timeline Week

```http
GET /time-allocations?start_date=<week_start>&end_date=<week_end>
```

Response chính:

```json
{
  "success": true,
  "data": {
    "allocations": {
      "2026-08-20": []
    },
    "daily_summary": [],
    "week_summary": {}
  },
  "meta": {
    "user_id": 168,
    "is_viewing_as": false,
    "can_edit": true,
    "locked_periods": []
  }
}
```

## Find Issue By Key

```http
GET /time-allocations/available-issues?week_start_date=<week_start>&search=<issue_key>&page=1
```

Dùng khi retry hoặc cần xác minh issue có thể được thêm vào timeline.

## Read Issue By ID

```http
GET /issues/<issue_id>
```

Response có thể chứa:

- `data.id`
- `data.project_id`
- `data.jira_issue_key`
- `data.issue_key`
- `data.summary`
- `data.issue_type`
- `data.status`
- `data.estimated_hours`
- `data.project.id`
- `data.project.name`
- `data.project.jira_project_key`

## Add Timeline Block

```http
POST /time-allocations
Content-Type: application/json
```

Request:

```json
{
  "client_request_id": "workai-onboarding-2026-08-21-mob-era-login-ui-2026-08-21-8h",
  "issue_id": 2716,
  "allocation_date": "2026-08-21",
  "planned_hours": 8
}
```

Issue phải có `assignee_id == meta.user_id`. Mỗi cặp `issue_id + allocation_date` chỉ có một allocation.

Sửa allocation đã xác định thuộc run hiện tại:

```http
PUT /time-allocations/<allocation_id>
Content-Type: application/json
```

```json
{
  "planned_hours": 2
}
```

## Assign Issue

```http
PUT /issues/<issue_id>
Content-Type: application/json
```

```json
{
  "assignee_id": 168
}
```

Lấy `168` từ `meta.user_id`. Không tự đổi issue đang được gán cho user khác.

## Transition Issue Status

```http
POST /issues/<issue_id>/transition
Content-Type: application/json
```

```json
{
  "client_request_id": "workai-onboarding-2026-08-21-mob-era-login-ui-transition-in-progress",
  "project_id": 85,
  "issue_key": "GTLU-2716",
  "transition_id": "wf_to_do_in_progress",
  "date": "2026-08-21",
  "hours": 8
}
```

Endpoint này đổi trạng thái. Không dùng response của nó để kết luận timeline allocation đã tồn tại.

## Save Generated Content

```http
PUT /issues/<issue_id>
Content-Type: application/json
```

```json
{
  "description": "...",
  "acceptance_criteria": [
    {
      "text": "Tiêu chí kiểm chứng được",
      "weight": 1,
      "evidence_types": ["link"],
      "evidence_hint": "Bằng chứng cần cung cấp"
    }
  ]
}
```

Xác minh bằng `GET /issues/<issue_id>`: `description` không rỗng và `acceptance_criteria_items` có dữ liệu.

## Error Shape

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

Các code cần xử lý:

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
