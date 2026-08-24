# Nhập việc tự động WorkAI

Project dùng Codex để tạo issue, gán người thực hiện, chuyển sang `In Progress` và xếp đủ số giờ lên Timeline WorkAI qua API.

## Chuẩn bị

Thiết lập một trong hai biến môi trường:

```powershell
$env:WORKAI_TOKEN = "<token>"
# hoặc
$env:WORKAI_SESSION_TOKEN = "<session-token>"
```

Mỗi dự án cần có file `project_overview*.md` trong workspace để Codex tạo summary và nội dung đúng ngữ cảnh.

## Cách dùng

Gửi cho Codex một đầu việc hoặc bảng nhiều đầu việc với bốn trường bắt buộc:

```yaml
project_name: G - MOB.ERA
task_name: Hoàn thiện cơ chế nâng cấp lính trong trận
start_date: 25/08/2026
estimated_duration: 12h
optional_context: Ưu tiên luồng nâng cấp bằng quảng cáo
```

Có thể dùng ngày `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `hôm nay`, `ngày mai`; thời lượng dạng `4h`, `4 tiếng`, `1.5 ngày`. Một ngày được tính là 8 giờ.

Ví dụ yêu cầu:

```text
Tạo và xếp lịch các đầu việc WorkAI sau:
- G - MOB.ERA | Hoàn thiện cơ chế nâng cấp lính trong trận | 25/08/2026 | 12h
```

Codex sẽ kiểm tra toàn bộ input trước khi ghi dữ liệu, tự chia thời lượng sang các ngày làm việc còn capacity và báo lại issue key cùng phân bổ theo ngày.

## Retry và kiểm tra

Checkpoint được lưu tại `.agents/skills/workai-auto-onboarding-api/.runs/`. Khi lần chạy bị timeout hoặc dở dang, yêu cầu Codex tiếp tục từ checkpoint; không xóa file state hoặc tạo lại thủ công để tránh trùng issue.

Quy trình chi tiết: [`Quy_Trinh_Tu_Dong_Nhap_Viec.md`](Quy_Trinh_Tu_Dong_Nhap_Viec.md).
