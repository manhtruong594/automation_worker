# Nhập việc tự động WorkAI

Project dùng Codex để tạo issue, gán người thực hiện, chuyển sang `In Progress` và xếp đủ số giờ lên Timeline WorkAI qua API.

## Chuẩn bị

Thiết lập đúng một biến môi trường. Chỉ nhập giá trị token, không thêm `Bearer ` hoặc `sessionToken=`:

```powershell
# Chỉ áp dụng cho cửa sổ PowerShell hiện tại
$env:WORKAI_TOKEN = '<token>'
# hoặc
$env:WORKAI_SESSION_TOKEN = '<session-token>'
```

Lưu lâu dài cho tài khoản Windows:

```powershell
$tokenMoi = Read-Host 'Dán token mới'
[Environment]::SetEnvironmentVariable('WORKAI_TOKEN', $tokenMoi, 'User')
Remove-Variable tokenMoi
```

Đổi `WORKAI_TOKEN` thành `WORKAI_SESSION_TOKEN` nếu dùng session token. Sau đó mở lại Codex/PowerShell. Kiểm tra mà không hiển thị token:

```powershell
if ($env:WORKAI_TOKEN) { "WORKAI_TOKEN đã nạp, độ dài: $($env:WORKAI_TOKEN.Length)" }
elseif ($env:WORKAI_SESSION_TOKEN) { "WORKAI_SESSION_TOKEN đã nạp, độ dài: $($env:WORKAI_SESSION_TOKEN.Length)" }
else { 'Chưa có token trong phiên hiện tại' }
```

Không lưu hoặc gửi token trong Git, file cấu hình hay chat.

Mỗi dự án cần có file `project_overview*.md` trong workspace để Codex tạo summary và nội dung đúng ngữ cảnh.

## Cách dùng

Gửi cho Codex một đầu việc hoặc bảng nhiều đầu việc với bốn trường bắt buộc và các trường tùy chọn:

```yaml
project_name: G - MOB.ERA
task_name: Hoàn thiện cơ chế nâng cấp lính trong trận
start_date: 25/08/2026
estimated_duration: 12h
optional_context: Ưu tiên luồng nâng cấp bằng quảng cáo
issue_type: Story
assignee_id: 168
```

| Trường tùy chọn | Ý nghĩa | Mặc định/ràng buộc |
|---|---|---|
| `optional_context` | Bối cảnh hoặc ghi chú bổ sung | Để trống nếu không có |
| `issue_type` | Loại đầu việc WorkAI | `Story` |
| `assignee_id` | ID người thực hiện | Số nguyên dương; để trống để dùng `meta.user_id`. Hiện phải bằng user đang xác thực để phân bổ giờ. |

Có thể dùng ngày `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `hôm nay`, `ngày mai`; thời lượng dạng `4h`, `4 tiếng`, `1.5 ngày`. Một ngày được tính là 8 giờ.

Ví dụ yêu cầu:

```text
Tạo và xếp lịch các đầu việc WorkAI sau:
- G - MOB.ERA | Hoàn thiện cơ chế nâng cấp lính trong trận | 25/08/2026 | 12h
```

Codex sẽ kiểm tra toàn bộ input trước khi ghi dữ liệu, tự chia thời lượng sang các ngày làm việc còn capacity và báo lại issue key cùng phân bổ theo ngày.

## Cập nhật 26/08/2026

Thêm skill [`workai-complete-issues-api`](.agents/skills/workai-complete-issues-api/SKILL.md) để hoàn thành một hoặc nhiều issue WorkAI cùng lúc từ bảng có cột `issue_id`:

| issue_id | Tên việc |
|---:|---|
| 2716 | Hoàn thiện đăng nhập |
| 2717 | Kiểm thử đăng nhập |

Ví dụ yêu cầu:

```text
Hoàn thành các issue WorkAI trong bảng trên.
```

Skill kiểm tra toàn bộ ID trước khi cập nhật, chỉ xử lý một lần với ID trùng, bỏ qua issue đã hoàn thành và xác minh lại trạng thái sau mỗi request. Mỗi issue chưa hoàn thành được gọi qua `POST /api/issues/<issue_id>/transition` với payload:

```json
{"transition_id":"wf_in_progress_done"}
```

Kết quả được báo theo từng dòng với các trạng thái `completed`, `already_completed`, `duplicate`, `failed` hoặc `not_attempted`. Skill dùng cùng biến môi trường `WORKAI_TOKEN` hoặc `WORKAI_SESSION_TOKEN` đã hướng dẫn ở phần Chuẩn bị.

## Retry và kiểm tra

Checkpoint được lưu tại `.agents/skills/workai-auto-onboarding-api/.runs/`. Khi lần chạy bị timeout hoặc dở dang, yêu cầu Codex tiếp tục từ checkpoint; không xóa file state hoặc tạo lại thủ công để tránh trùng issue.

Quy trình chi tiết: [`Quy_Trinh_Tu_Dong_Nhap_Viec.md`](Quy_Trinh_Tu_Dong_Nhap_Viec.md).
