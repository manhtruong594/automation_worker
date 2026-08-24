---
name: workai-auto-onboarding-api
description: Tạo và xếp lịch một hoặc nhiều đầu việc WorkAI qua API với preflight toàn batch, nội dung/tiêu chí nghiệm thu, checkpoint và retry không tạo trùng. Dùng khi input có dự án, đầu việc, ngày bắt đầu, thời lượng dự kiến và cần tạo issue WorkAI hoặc tiếp tục một lần chạy dở.
---

# WorkAI Auto Onboarding API

## Mục Tiêu

Tạo issue, gán người thực hiện, chuyển trạng thái, phân bổ đủ giờ và lưu description/acceptance criteria. Ưu tiên:

1. Không tạo side effect trước khi toàn bộ input qua preflight.
2. Không tạo trùng khi retry hoặc khi response bị timeout.
3. State local chỉ là checkpoint; server là nguồn xác nhận issue và allocation.
4. Không ghi đè assignee hoặc allocation không chắc thuộc lần chạy hiện tại.

Đọc `references/workai-api.md` trước khi gọi API. Khi cần diễn giải response, đọc thêm `references/api-response-shapes.md`. Không suy đoán endpoint hoặc field ngoài tài liệu này.

## Xác Thực

Dùng một trong hai biến môi trường:

```text
WORKAI_TOKEN
WORKAI_SESSION_TOKEN
```

Gửi tương ứng:

```http
Authorization: Bearer <WORKAI_TOKEN>
Cookie: sessionToken=<WORKAI_SESSION_TOKEN>
```

## Input Và Chuẩn Hóa

Nhận một object hoặc bảng nhiều dòng. Trường bắt buộc:

```yaml
project_name: ""
task_name: ""
start_date: ""
estimated_duration: ""
```

Trường tùy chọn: `optional_context`, `issue_type`, `assignee_id`; `issue_type` mặc định `Story`.

`assignee_id` phải là số nguyên dương nếu được cung cấp. Nếu bỏ trống, resolve thành `meta.user_id` lấy từ request kiểm tra auth. API phân bổ giờ hiện chỉ hỗ trợ user hiện tại, nên toàn batch phải dừng ở preflight với `ASSIGNEE_NOT_CURRENT_USER` nếu `assignee_id != meta.user_id`.

Chuẩn hóa tiêu đề:

| Tiêu đề input | Trường chuẩn |
|---|---|
| Dự án | `project_name` |
| Đầu việc, Tên đầu việc | `task_name` |
| Ngày bắt đầu | `start_date` |
| Thời lượng, Thời lượng dự kiến | `estimated_duration` |
| Bối cảnh, Ghi chú | `optional_context` |
| Loại đầu việc | `issue_type` |
| ID người thực hiện | `assignee_id` |

Quy tắc:

- Giữ nguyên thứ tự và từng dòng, kể cả các dòng có nội dung giống nhau.
- Nhận ngày `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `hôm nay`, `ngày mai`. Chuẩn hóa thành `YYYY-MM-DD` theo `Asia/Bangkok`.
- Nhận duration như `12h`, `4 tiếng`, `1.5 ngày`. Mặc định `1 ngày = 8 giờ`; ghi quy đổi này trong báo cáo nếu input dùng đơn vị ngày.
- `estimated_hours` phải là số dương.
- Khớp project không phân biệt hoa thường, dấu tiếng Việt, khoảng trắng, `-` và `_`.
- Summary phải có ít nhất 51 ký tự. Nếu `task_name` ngắn, sinh theo mẫu `<Hành động> <tính năng/phân hệ> cho <bối cảnh hoặc kết quả>` từ overview/context; không thêm diễn đạt chung chung chỉ để đủ độ dài.

Danh sách project chuẩn:

| project_id | project_name | project_key |
|---:|---|---|
| 85 | G - MOB.ERA | GTLU |
| 81 | G - QUANLY-DIEUHANH-GAME | QLDH |
| 30 | G - SKYDEFENSE | SKYD |
| 110 | G - ViecCaNhan | GVCN |
| 59 | G - ViecChungNgoaiDuAn | VCNDA |
| 115 | G - WarSurvival | GFW |
| 39 | G - ZOMBIEHUNTER | ZBH |

Nếu không khớp, báo `PROJECT_NOT_FOUND`. Nếu nhiều project khớp, hỏi người dùng chọn.

## Định Danh Ổn Định

Tạo canonical identity từ `project_id`, `task_name` đã trim, `start_date`, `estimated_hours` và số thứ tự dòng. Băm SHA-256 canonical JSON có key theo thứ tự cố định:

- `item_id = workai-item-<12 ký tự hex đầu>`
- `client_request_id = workai-onboarding-<start_date>-<12 ký tự hex đầu>`

Không đưa `summary`, `optional_context`, `assignee_id` hoặc nội dung sinh tự động vào identity: chỉnh câu chữ hoặc người thực hiện khi retry không được tạo ID issue mới. Tạo `batch_id` từ SHA-256 của toàn bộ input đã chuẩn hóa theo thứ tự dòng. Không dùng timestamp. Số thứ tự giúp hai dòng cố ý trùng nhau vẫn là hai item khác nhau.

## Quy Trình

### A. Preflight Toàn Batch — Không Side Effect

Hoàn tất mọi bước sau trước `POST`/`PUT` đầu tiên:

1. Parse, chuẩn hóa và validate toàn bộ dòng.
2. Resolve project và summary.
3. Tìm overview theo thứ tự:
   - `project_overviews/<project-name>_<project-id>.md`
   - file Markdown có tên chứa `project_overview` hoặc `overview`
4. Nếu nhiều overview khớp, hỏi chọn. Nếu không có, chỉ tiếp tục khi người dùng cho phép rõ ràng và ghi vào báo cáo.
5. Tạo ID ổn định; đọc hoặc khởi tạo state trong `.agents/skills/workai-auto-onboarding-api/.runs/`.
6. Kiểm tra auth bằng request chỉ đọc; resolve `assignee_id` rỗng thành `meta.user_id`, rồi xác nhận mọi `assignee_id == meta.user_id`. Nếu khác, trả `ASSIGNEE_NOT_CURRENT_USER` và chưa tạo gì trong batch.
7. Với từng tuần cần dùng, gọi `GET /time-allocations` một lần rồi dùng cache để lập kế hoạch capacity. Tuần là thứ Hai đến Chủ nhật. Khi nhiều item dùng cùng ngày, trừ cả reservation tạm của item trước khỏi capacity của item sau.

Nếu bất kỳ dòng nào có input/overview chưa rõ, hỏi lại một lần cho tất cả dòng lỗi và chưa tạo gì trong batch.

Cache overview theo `project_id` và timeline theo `week_start`. Sau mỗi allocation thành công, cập nhật cache rồi đọc lại timeline để chống dữ liệu cũ.

Ngày hợp lệ khi:

- `meta.can_edit == true`;
- không thuộc `meta.locked_periods`;
- `daily_summary.status != weekend` và `is_day_off == false`;
- `actual_work_hours > 0` hoặc `standard_hours > 0`.

Tính capacity:

```text
available_hours = max(0, idle_hours)
```

Nếu `idle_hours` thiếu hoặc không hợp lệ:

```text
capacity = actual_work_hours nếu > 0, ngược lại standard_hours
available_hours = max(0, capacity - total_allocated_hours)
```

Không dùng capacity âm và không ghi đè block có sẵn.

### B. Reconcile Trước Khi Ghi

Với từng item theo thứ tự input:

1. Nếu state có `issue_id`, gọi `GET /issues/<issue_id>` để xác minh.
2. Đọc timeline từ `start_date`, lọc allocation theo `issue_id`, rồi đồng bộ `allocation_id`, ngày, giờ vào state.
3. Đọc issue detail để đồng bộ assignee, status, description và acceptance criteria.
4. Tính `remaining_hours = estimated_hours - tổng planned_hours trên server`.
5. Nếu issue trong state không còn tồn tại, đặt lỗi `ISSUE_NOT_FOUND`; không tự tạo issue thay thế khi chưa báo người dùng.

Không xem state local hoặc response transition là bằng chứng allocation đã tồn tại.

### C. Thực Thi Từng Item

Ghi state atomically ngay sau mỗi side effect thành công: ghi file tạm cùng thư mục, flush, rồi rename thay thế.

1. **Tạo issue** — Nếu chưa có issue được server xác nhận, `POST /issues` với `client_request_id` ổn định. Lưu ngay `issue_id` và `issue_key`/`jira_issue_key`.
2. **Gán người thực hiện** — Dùng `assignee_id` đã resolve ở preflight. Nếu issue chưa có assignee, `PUT /issues/<issue_id>` với `assignee_id`. Nếu issue đã gán đúng ID, không gọi lại. Nếu đã gán người khác, dừng item và yêu cầu xác nhận; không tự đổi.
3. **Chuyển trạng thái** — Nếu issue chưa `In Progress` và transition phù hợp, gọi `POST /issues/<issue_id>/transition` với `transition_id=wf_to_do_in_progress`. Không gọi lại nếu đã `In Progress`.
4. **Tạo allocation** — Từ `start_date`, theo ngày tăng dần:

   ```text
   hours_to_add = min(remaining_hours, available_hours)
   ```

   Trước mỗi `POST /time-allocations`, kiểm tra server theo `issue_id + allocation_date`:
   - đã đúng giờ: ghi state, không POST;
   - thuộc chính run nhưng sai giờ: `PUT /time-allocations/<allocation_id>`;
   - không chắc ownership: không sửa; thử ngày hợp lệ tiếp theo.

   Ngay trước mutation, đọc lại ngày/tuần và tính lại capacity để xử lý thay đổi đồng thời trên server. Dùng `client_request_id` ổn định theo item, ngày và giờ. Sau mỗi POST/PUT, lưu checkpoint rồi đọc lại timeline. Nếu hết tuần mà còn giờ, đọc tuần tiếp theo.
5. **Sinh nội dung** — Đọc issue, rồi gọi `POST /issues/quick-create/suggest-description` với `project_key` và overview. Nếu timeout hoặc `AI_GENERATION_FAILED`, tự sinh fallback: description 1–3 câu và 3–5 acceptance criteria kiểm chứng được; ghi fallback vào báo cáo.
6. **Lưu nội dung** — `PUT /issues/<issue_id>` với description và acceptance criteria. Đọc lại issue; chỉ đặt `content_applied=true` khi description không rỗng và `acceptance_criteria_items` có dữ liệu.
7. **Hoàn tất** — Chỉ đặt `completed` khi issue tồn tại, assignee trên server bằng `assignee_id` đã resolve, tổng allocation server bằng `estimated_hours`, và nội dung đã được xác minh.

Xử lý tuần tự. Lỗi runtime ở một item không chặn item hợp lệ tiếp theo, trừ lỗi auth/quyền hoặc lỗi chứng minh mọi request tiếp theo sẽ thất bại.

Không dùng endpoint batch khi tài liệu tham chiếu chưa xác nhận; gọi API riêng cho từng item.

## Retry Sau Timeout Hoặc Lỗi Mơ Hồ

Không retry mutation ngay:

- Sau timeout tạo issue: gọi lại `POST /issues` chỉ với cùng `client_request_id`; không sinh ID mới.
- Sau timeout tạo/sửa allocation: đọc timeline và kiểm tra `issue_id + allocation_date` trước.
- Sau timeout PUT issue: đọc issue detail trước.
- Với `IDEMPOTENCY_CONFLICT`: reconcile server/state, không retry mù.
- Với `INTERNAL_ERROR`: dừng side effect cho item, lưu bước cuối đã xác minh và báo cáo.

## State

Một file cho mỗi batch: `.runs/<batch_id>.json`. Input đơn vẫn dùng schema batch với một item.

```json
{
  "schema_version": 1,
  "batch_id": "workai-batch-...",
  "source_row_count": 1,
  "items": [
    {
      "row_number": 1,
      "item_id": "workai-item-...",
      "status": "pending",
      "last_verified_step": "preflight",
      "client_request_id": "workai-onboarding-...",
      "project_id": 85,
      "project_name": "G - MOB.ERA",
      "project_key": "GTLU",
      "summary": "...",
      "start_date": "2026-08-21",
      "estimated_hours": 12,
      "issue_id": null,
      "issue_key": null,
      "assignee_id": 168,
      "blocks": [],
      "content_applied": false,
      "fallback_used": false,
      "error": null
    }
  ]
}
```

`status`: `pending`, `issue_created`, `partially_scheduled`, `completed`, `failed`.

Mỗi phần tử `blocks` gồm `date`, `hours`, `client_request_id`, `allocation_id` và `verified_at`; chỉ cập nhật từ response server đã xác minh.

Không lưu token, cookie hoặc toàn bộ response chứa dữ liệu không cần thiết. Không xóa state thành công; state là bằng chứng retry/audit.

## Xử Lý Lỗi

| Code/tình huống | Hành động |
|---|---|
| `UNAUTHENTICATED` | Dừng batch; yêu cầu credential mới. |
| `FORBIDDEN` | Dừng batch; báo quyền còn thiếu. |
| `VALIDATION_ERROR` | Sửa payload nếu xác định chắc field lỗi; nếu không, dừng item. |
| `PROJECT_NOT_FOUND` | Không tạo gì; hỏi lại project. |
| `ASSIGNEE_NOT_CURRENT_USER` | Không tạo gì; dùng `meta.user_id` hoặc bỏ trống `assignee_id`. |
| `ISSUE_NOT_FOUND` khi retry | Báo state cũ không hợp lệ; không tự tạo lại. |
| `AI_GENERATION_FAILED`/timeout | Dùng fallback; tiếp tục và báo rõ. |
| `TIMELINE_NOT_FOUND` | Dừng item; giữ issue/state đã tạo. |
| `NON_WORKING_DAY` | Bỏ qua ngày; thử ngày tiếp theo. |
| `INSUFFICIENT_DAY_CAPACITY` | Thử ngày tiếp theo. |
| `IDEMPOTENCY_CONFLICT` | Reconcile server/state. |
| `INTERNAL_ERROR` | Dừng side effect item; báo bước cuối đã xác minh. |

## Báo Cáo

Input đơn: dự án, issue key, summary cuối, `assignee_id`, ngày bắt đầu, tổng giờ, phân bổ theo ngày, fallback/cảnh báo và file state.

Input bảng:

| Dòng | Dự án | Issue key | Summary | Assignee ID | Tổng giờ | Phân bổ | Trạng thái/Lỗi |
|---:|---|---|---|---:|---:|---|---|

Ghi tổng `completed`, `failed`, `partially_scheduled` và đường dẫn file state. Khi lỗi, nêu bước chặn, issue đã tạo hay chưa, block đã thêm, checkpoint cuối và hành động tiếp theo. Không báo thành công chung nếu còn item chưa hoàn tất.

## Tham Chiếu

- `references/workai-api.md`
- `references/api-response-shapes.md`
