# WorkAI API Response Shapes

Tóm tắt từ `api-responses-latest.json`, captured at `2026-08-20T14:21:19.9640563+07:00`.

## Timeline Week

Endpoint:

```http
GET /time-allocations?start_date=2026-08-17&end_date=2026-08-23
```

Response thành công:

```json
{
  "success": true,
  "data": {
    "allocations": {
      "2026-08-17": [],
      "2026-08-18": [],
      "2026-08-19": [],
      "2026-08-20": [
        {
          "id": 88872,
          "user_id": 168,
          "issue_id": 266767,
          "allocation_date": "2026-08-20",
          "planned_hours": 0.1,
          "effective_hours": null,
          "sort_order": 0,
          "notes": null,
          "issue": {
            "id": 266767,
            "jira_issue_key": "GFW-516",
            "summary": "Thay effect mới nâng cấp cho đám đông, cho phép đổi màu effect theo loại nâng cấp",
            "status": "In Progress",
            "priority": "Medium",
            "issue_type": "Story",
            "project": {
              "id": 115,
              "name": "G - WarSurvival",
              "jira_project_key": "GFW"
            }
          }
        }
      ]
    },
    "daily_summary": [
      {
        "date": "2026-08-20",
        "day_of_week": 4,
        "is_weekend": false,
        "is_saturday": false,
        "is_holiday": false,
        "is_day_off": false,
        "is_half_day_off": false,
        "half_day_period": null,
        "total_allocated_hours": 0.1,
        "effective_allocated_hours": 0.1,
        "effective_ratio": 1,
        "actual_work_hours": 8,
        "standard_hours": 8,
        "ot_hours": 0,
        "ot_level": null,
        "idle_hours": 7.9,
        "over_hours": 0,
        "allocation_count": 1,
        "status": "normal",
        "utilization_status": "under",
        "has_actual_data": false,
        "check_in_time": "08:00",
        "check_out_time": null
      }
    ],
    "week_summary": {
      "total_allocated": 0.1,
      "total_effective_allocated": 0.1,
      "total_actual": 50.3,
      "total_standard": 48,
      "total_ot": 2.14,
      "ot_level": "normal",
      "total_idle": 50.2,
      "total_over": 0,
      "utilization_pct": 0.2
    }
  },
  "meta": {
    "user_id": 168,
    "is_viewing_as": false,
    "can_edit": true,
    "locked_periods": []
  }
}
```

Capacity nên lấy từ `idle_hours` khi có. Weekend trong mẫu có:

```json
{
  "status": "weekend",
  "utilization_status": "weekend",
  "actual_work_hours": 0,
  "standard_hours": 0,
  "idle_hours": 0
}
```

## Find Issue By Key

Endpoint:

```http
GET /time-allocations/available-issues?week_start_date=2026-08-17&search=GTLU-2716&page=1
```

Không có kết quả:

```json
{
  "success": true,
  "data": [],
  "meta": {
    "current_page": 1,
    "per_page": 20,
    "total": 0,
    "last_page": 1,
    "from": null,
    "to": null
  }
}
```

## Read Issue By ID

Endpoint:

```http
GET /issues/2716
```

Các field quan trọng trong response:

```json
{
  "success": true,
  "data": {
    "id": 2716,
    "project_id": 22,
    "jira_issue_key": "GPXF-3079",
    "summary": "Test reward các vị trí trong và ngoài trận Android Adjust",
    "description": null,
    "issue_type": "Story",
    "status": "Done",
    "priority": "Must-Have",
    "estimated_hours": null,
    "acceptance_criteria": null,
    "issue_key": "GPXF-3079",
    "project": {
      "id": 22,
      "jira_project_key": "GPXF",
      "name": "G - PIXELFLOWPUZZLE",
      "description": "# PROJECT OVERVIEW: Flow Color Pixel Puzzle..."
    }
  }
}
```

`estimated_hours` có thể null ở issue cũ. Khi retry task mới, ưu tiên state local nếu server không trả `estimated_hours`.

## Side Effect Endpoints Đã Xác Nhận

```http
POST /issues
PUT /issues/<issue_id>
POST /issues/<issue_id>/transition
POST /time-allocations
PUT /time-allocations/<allocation_id>
```

Quy tắc đã xác nhận:

- `POST /issues/<issue_id>/transition` yêu cầu `transition_id`; `wf_to_do_in_progress` chỉ khả dụng khi issue chưa `In Progress`. Không coi transition là bằng chứng allocation.
- `POST /time-allocations` yêu cầu `issue_id`, `allocation_date`, `planned_hours`; issue phải được gán cho user hiện tại. Vì vậy, `assignee_id` tùy chọn phải bằng `meta.user_id`; nếu bỏ trống thì resolve thành `meta.user_id` trước khi tạo side effect.
- Một issue chỉ có một allocation trên một ngày. Nếu đã tồn tại, API trả `422` với message `Issue này đã được phân bổ cho ngày này.`
- `PUT /time-allocations/<allocation_id>` nhận `planned_hours` để sửa allocation đã xác định.
- `POST /issues/quick-create/suggest-description` yêu cầu `project_key`.
- `POST /issues/quick-create/suggest-description` dùng client timeout 30 giây. Response thành công trả `data.suggested_description` và `data.suggested_acceptance_criteria`; map hai field này sang `description` và `acceptance_criteria`. Chỉ fallback khi timeout, `AI_GENERATION_FAILED`, hoặc dữ liệu vẫn thiếu sau mapping.
- `PUT /issues/<issue_id>` lưu `assignee_id`, `description` và `acceptance_criteria`.
