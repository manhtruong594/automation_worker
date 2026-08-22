---
name: workai-auto-onboarding-api
description: Tự động tạo một hoặc nhiều đầu việc nhập việc WorkAI bằng API từ input đơn hoặc bảng nhiều dòng và xếp lịch timeline. Sử dụng khi người dùng cung cấp dự án, đầu việc, ngày bắt đầu, thời lượng dự kiến và muốn tạo issue WorkAI, sinh mô tả/tiêu chí nghiệm thu, phân bổ giờ theo capacity, retry không tạo trùng.
---

# WorkAI Auto Onboarding API

## Auth

Gửi request với 1 trong 2 cách:

```http
Authorization: Bearer <WORKAI_TOKEN>
```

Hoac:

```http
Cookie: sessionToken=4662|gcDTZ63I1PVZHqZhSIABRdJk2sr2Xe3TurePdCUTc6776120
```

Nếu token/cookie hết hạn:

```json
{
  "error": {
    "code": "UNAUTHENTICATED",
    "message": "Chrome session expired or missing WorkAI auth token."
  }
}
```

## Dữ Liệu Đầu Vào

Chấp nhận input đơn hoặc bảng nhiều dòng.

### Input đơn

Các trường tối thiểu:

```yaml
project_name: ""
task_name: ""
start_date: ""
estimated_duration: ""
optional_context: ""
```

### Input bảng nhiều dòng

Mỗi dòng là một đầu việc độc lập. Chấp nhận bảng Markdown hoặc dữ liệu dạng hàng/cột tương đương. Các cột bắt buộc:

| project_name | task_name | start_date | estimated_duration |
|---|---|---|---|
| G - MOB.ERA | Làm màn hình đăng nhập | 21/08/2026 | 12h |
| G - SKYDEFENSE | Sửa luồng nhận thưởng | 22/08/2026 | 1.5 ngày |

Cột tùy chọn: `optional_context`, `issue_type`. `issue_type` mặc định là `Story` cho từng dòng.

Chấp nhận tiêu đề tiếng Việt tương ứng và chuẩn hóa về tên trường chuẩn:

| Tiêu đề input | Trường chuẩn |
|---|---|
| Dự án | `project_name` |
| Đầu việc, Tên đầu việc | `task_name` |
| Ngày bắt đầu | `start_date` |
| Thời lượng, Thời lượng dự kiến | `estimated_duration` |
| Bối cảnh, Ghi chú | `optional_context` |
| Loại đầu việc | `issue_type` |

Không gộp các dòng giống nhau. Mỗi dòng phải có định danh ổn định dựa trên `project_id`, `task_name`, `start_date`, `estimated_hours` và số thứ tự xuất hiện để hai dòng cố ý trùng nội dung vẫn tạo thành hai đầu việc riêng.

Chấp nhận `start_date` dạng `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `hôm nay`, `ngày mai`.

Chấp nhận duration như `12h`, `4 tiếng`, `1.5 ngày`. Quy đổi sang `estimated_hours` dạng số giờ decimal.

Trước mọi API có side effect, parse và kiểm tra toàn bộ các dòng. Gắn lỗi với số dòng và tên đầu việc. Nếu không parse chắc chắn được ngày, dự án hoặc thời lượng của bất kỳ dòng nào, hỏi lại một lần cho các dòng lỗi và chưa tạo đầu việc nào trong batch.

## Xử Lý Batch

Với bảng nhiều dòng:

1. Giữ nguyên thứ tự dòng từ input.
2. Chuẩn hóa và kiểm tra toàn bộ batch trước khi tạo issue.
3. Tạo một `batch_id` ổn định từ nội dung bảng đã chuẩn hóa; không dùng timestamp làm thành phần duy nhất.
4. Xử lý tuần tự từng dòng theo toàn bộ quy trình bên dưới: xác định project, đọc overview, tạo issue, phân bổ timeline, sinh description và acceptance criteria.
5. Lưu state ngay sau mỗi side effect. Mỗi dòng có state và `client_request_id` riêng.
6. Lỗi runtime ở một dòng không hoàn tác các dòng đã thành công và không ngăn xử lý các dòng hợp lệ còn lại, trừ `UNAUTHENTICATED`, `FORBIDDEN` hoặc lỗi cho thấy mọi request tiếp theo chắc chắn thất bại.
7. Khi chạy lại cùng batch, đọc state và chỉ tiếp tục phần còn thiếu của từng dòng. Không tạo lại issue hoặc timeline block đã tồn tại.

Không dùng endpoint batch nếu endpoint đó không được tài liệu tham chiếu xác nhận. Mặc định gọi API riêng cho từng dòng.

## Quy Trình Bắt Buộc

### 1. Xác Định Project

Tra project theo danh sách chuẩn:

| project_id | project_name | issue key |
|---:|---|---|
| 85 | G - MOB.ERA | GTLU |
| 81 | G - QUANLY-DIEUHANH-GAME | QLDH |
| 30 | G - SKYDEFENSE | SKYD |
| 110 | G - ViecCaNhan | GVCN |
| 59 | G - ViecChungNgoaiDuAn | VCNDA |
| 115 | G - WarSurvival | GFW |
| 39 | G - ZOMBIEHUNTER | ZBH |

Khớp tên không phân biệt hoa thường, dấu tiếng Việt, khoảng trắng, gạch ngang và gạch dưới.

Nếu nhiều project cùng khớp, hỏi người dùng chọn. Nếu không có project khớp, dừng và báo `PROJECT_NOT_FOUND`.

### 2. Đọc Project Overview

Luôn đọc overview trước khi tạo issue.

Tìm trong workspace theo thứ tự:

1. `project_overviews/<project-name>_<project-id>.md`
2. File Markdown có tên chứa `project_overview` hoặc `overview`

Nếu chỉ có một overview khớp, đọc file đó và tiếp tục.

Nếu nhiều overview cùng khớp, hỏi người dùng chọn file.

Nếu không có overview, chỉ tiếp tục khi người dùng cho phép rõ ràng. Khi tiếp tục không có overview, ghi rõ trong báo cáo.

### 3. Chuẩn Hóa Summary

`issue_type` mặc định là `Story`.

`summary` phải dài hơn 50 ký tự. Nếu `task_name` ngắn hơn, tự sinh summary dựa trên `task_name`, `project_overview`, `optional_context`.

Mẫu ưu tiên:

```text
<Hành động> <tính năng/phân hệ> cho <bối cảnh dự án hoặc kết quả mong muốn>
```

Giữ summary cụ thể. Không nhồi mô tả dài vào summary.

### 4. Tạo Issue

Gọi:

```http
POST https://workai-be.horus.io.vn/api/issues
Content-Type: application/json
```

Payload:

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

Yêu cầu:

- Dùng `client_request_id` ổn định theo task để retry không tạo trùng.
- Lưu lại `issue_id`, `issue_key` hoặc `jira_issue_key`.
- Không tạo issue mới nếu run state đã có issue còn tồn tại.

### 5. Đọc Timeline Theo Tuần

Tính tuần chứa `start_date`, rồi gọi:

```http
GET https://workai-be.horus.io.vn/api/time-allocations?start_date=<week_start>&end_date=<week_end>
```

Dữ liệu cần dùng:

- `data.allocations[date][]`
- `data.daily_summary[]`
- `meta.can_edit`
- `meta.locked_periods`

Chỉ xếp lịch khi:

- `meta.can_edit == true`
- Ngày không nằm trong `locked_periods`
- `daily_summary.status` không phải `weekend`
- `is_day_off == false`
- `actual_work_hours > 0` hoặc `standard_hours > 0`
- Còn capacity: ưu tiên `idle_hours`; nếu thiếu, dùng `standard_hours - total_allocated_hours` khi hợp lệ.

Không ghi đè block có sẵn.

### 6. Phân Bổ Giờ

Phân bổ từ `start_date` theo ngày tăng dần.

Với mỗi ngày:

```text
available_hours = max(0, capacity - total_allocated_hours)
hours_to_add = min(remaining_hours, available_hours)
```

Nếu ngày hiện tại hết capacity mà `remaining_hours > 0`, đọc tuần tiếp theo và tiếp tục.

Tổng block đã tạo phải bằng `estimated_hours`, trừ khi hết ngày hợp lệ hoặc API trả lỗi chặn.

### 7. Gán Người Thực Hiện Và Chuyển Trạng Thái

Lấy user hiện tại từ `meta.user_id` của timeline. Đọc issue bằng `GET /issues/<issue_id>`:

- Nếu `assignee_id` rỗng, gán cho user hiện tại:

```http
PUT https://workai-be.horus.io.vn/api/issues/<issue_id>
Content-Type: application/json
```

```json
{
  "assignee_id": 168
}
```

- Nếu issue đã gán cho user khác, không tự đổi assignee; dừng dòng đó và yêu cầu xác nhận.
- Lưu `assignee_id` vào state ngay sau khi gán thành công.

Nếu cần chuyển issue từ `To Do` sang `In Progress`, gọi:

```http
POST https://workai-be.horus.io.vn/api/issues/<issue_id>/transition
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

`transition_id` là bắt buộc. Endpoint transition chỉ dùng để đổi trạng thái; không coi response transition là bằng chứng timeline block đã được tạo. Nếu issue đã `In Progress`, không gọi lại transition này.

### 8. Thêm Timeline Block

Tạo allocation thực bằng:

```http
POST https://workai-be.horus.io.vn/api/time-allocations
Content-Type: application/json
```

```json
{
  "client_request_id": "workai-onboarding-2026-08-21-mob-era-login-ui-2026-08-21-8h",
  "issue_id": 2716,
  "allocation_date": "2026-08-21",
  "planned_hours": 8
}
```

Yêu cầu:

- Issue phải được gán cho `meta.user_id` trước khi tạo allocation.
- WorkAI chỉ cho một allocation trên mỗi cặp `issue_id + allocation_date`. Trước khi `POST`, đọc `data.allocations[date][]` và kiểm tra cặp này.
- Nếu allocation của issue đã tồn tại đúng số giờ, ghi nhận vào state và không tạo lại.
- Nếu allocation của chính run này đã tồn tại nhưng sai số giờ, sửa bằng `PUT /time-allocations/<allocation_id>` với `planned_hours` đúng. Nếu không chắc ownership, không ghi đè; bỏ qua ngày và thử ngày hợp lệ tiếp theo.
- `client_request_id` phải ổn định, nhưng không dựa riêng vào nó để chống trùng; luôn đối chiếu allocation server.
- Sau mỗi `POST` hoặc `PUT`, lưu `allocation_id`, ngày và giờ vào state, rồi đọc lại timeline để xác minh.
- Nếu API lỗi sau khi issue đã tạo, báo rõ issue đã tồn tại để tránh tạo trùng.

### 9. Sinh Và Lưu Description, Acceptance Criteria

Gọi api mở issue vừa tạo trước
```http
GET https://workai-be.horus.io.vn/api/issues/<issue_id>
```

Sau đó sinh description và acceptance criteria bằng api:
```http
POST https://workai-be.horus.io.vn/api/issues/quick-create/suggest-description
```

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

`project_key` là bắt buộc và lấy từ danh sách project chuẩn (`GTLU`, `GFW`, `SKYD`...).

Nếu API timeout hoặc trả `AI_GENERATION_FAILED`, được tự sinh nội dung thay thế ngắn gọn:

- Description: 1-3 câu, nêu phạm vi chính và kết quả mong muốn.
- Acceptance criteria: 3-5 tiêu chí kiểm chứng được.

Báo rõ `AI_GENERATION_FAILED` hoặc timeout trong kết quả cuối nếu dùng fallback.

Sau khi có nội dung từ WorkAI AI hoặc fallback, lưu vào issue:

```http
PUT https://workai-be.horus.io.vn/api/issues/<issue_id>
Content-Type: application/json
```

```json
{
  "description": "Bối cảnh, phạm vi và kết quả mong muốn...",
  "acceptance_criteria": [
    {
      "text": "Tiêu chí kiểm chứng được",
      "weight": 1,
      "evidence_types": ["link", "image"],
      "evidence_hint": "Bằng chứng cần đính kèm"
    }
  ]
}
```

Đọc lại `GET /issues/<issue_id>` và chỉ ghi `content_applied=true` khi `description` không rỗng và `acceptance_criteria_items` có dữ liệu.

## Retry Và State

Lưu state trong thư mục `.runs/` của skill:

```text
.agents/skills/workai-auto-onboarding-api/.runs/
```

Với input bảng, lưu một file batch chứa trạng thái từng dòng. State tối thiểu:

```json
{
  "batch_id": "workai-batch-...",
  "source_row_count": 2,
  "items": [
    {
      "row_number": 1,
      "item_id": "workai-item-...",
      "status": "pending",
      "client_request_id": "workai-onboarding-...",
      "project_id": 85,
      "project_name": "G - MOB.ERA",
      "summary": "",
      "estimated_hours": 12,
      "issue_id": null,
      "issue_key": null,
      "assignee_id": null,
      "blocks": [],
      "content_applied": false,
      "error": null
    }
  ]
}
```

`status` là một trong: `pending`, `issue_created`, `partially_scheduled`, `completed`, `failed`. Ghi file state theo cách atomic để tránh mất trạng thái batch khi tiến trình bị ngắt.

State tối thiểu:

```json
{
  "client_request_id": "",
  "project_id": 0,
  "project_name": "",
  "summary": "",
  "estimated_hours": 0,
  "issue_id": null,
  "issue_key": null,
  "assignee_id": null,
  "blocks": [
    {
      "date": "2026-08-21",
      "hours": 8,
      "client_request_id": "",
      "allocation_id": null
    }
  ],
  "content_applied": false
}
```

Khi chạy lại:

1. Đọc state local.
2. Nếu đã có `issue_id` hoặc `issue_key`, xác minh issue còn tồn tại.
3. Đọc timeline theo từng tuần từ `start_date`; lọc allocation theo `issue_id`. Không dùng block local hoặc response transition làm nguồn xác nhận duy nhất.
4. Đồng bộ state từ allocation server, gồm `allocation_id`, `allocation_date` và `planned_hours`.
5. Tính `remaining_hours = estimated_hours - tổng planned_hours trên server`.
6. Chỉ thêm phần còn thiếu và không `POST` lần hai cho cùng `issue_id + allocation_date`.
7. Đọc issue detail để xác minh assignee, description và acceptance criteria.
8. Không tạo issue mới nếu issue cũ còn tồn tại.


## Mã Lỗi Cần Xử Lý

- `UNAUTHENTICATED`: yêu cầu đăng nhập/lấy token mới.
- `FORBIDDEN`: không có quyền tạo issue hoặc sửa timeline.
- `VALIDATION_ERROR`: sửa payload, đặc biệt `summary`, `project_id`, `estimated_hours`.
- `PROJECT_NOT_FOUND`: dừng, hỏi lại project.
- `ISSUE_NOT_FOUND`: nếu retry, báo state cũ không còn hợp lệ trước khi tạo lại.
- `AI_GENERATION_FAILED`: dùng fallback nội dung ngắn, báo trong kết quả.
- `TIMELINE_NOT_FOUND`: dừng, báo không đọc được timeline tuần.
- `NON_WORKING_DAY`: bỏ qua ngày đó, thử ngày tiếp theo.
- `INSUFFICIENT_DAY_CAPACITY`: thử ngày tiếp theo.
- `IDEMPOTENCY_CONFLICT`: đọc state server/local, không retry mù.
- `INTERNAL_ERROR`: không tạo thêm side effect; báo bước cuối đã hoàn tất.

## Báo Cáo Hoàn Tất

Báo cáo input đơn ngắn:

- Dự án.
- Issue key.
- Summary cuối cùng.
- Ngày bắt đầu.
- Tổng giờ dự kiến.
- Phân bổ theo ngày.
- Fallback đã dùng, nếu có.

Với input bảng, báo cáo một dòng cho mỗi đầu việc:

| Dòng | Dự án | Issue key | Summary | Tổng giờ | Phân bổ | Trạng thái/Lỗi |
|---:|---|---|---|---:|---|---|

Sau bảng, ghi tổng số dòng `completed`, `failed`, `partially_scheduled` và đường dẫn file state batch. Không chỉ báo thành công chung nếu có dòng thất bại.

Nếu thất bại, báo:

- Bước đang chặn.
- Issue đã tạo hay chưa.
- Block timeline đã thêm.
- File state local.
- Hành động cần làm tiếp.

## Tham Chiếu

- `references/workai-api.md`
- `references/api-response-shapes.md`
