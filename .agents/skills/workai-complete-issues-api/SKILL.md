---
name: workai-complete-issues-api
description: Hoàn thành một hoặc nhiều issue WorkAI qua transition API từ input dạng bảng, với preflight toàn batch và báo cáo kết quả từng dòng. Dùng khi người dùng yêu cầu chuyển các issue WorkAI sang Done/Hoàn thành; không dùng để tạo, sửa nội dung hoặc phân bổ giờ cho issue.
---

# WorkAI Complete Issues API

Chuyển các issue được chỉ định sang trạng thái hoàn thành bằng:

```http
POST https://workai-be.horus.io.vn/api/issues/<issue_id>/transition
Content-Type: application/json
```

```json
{"transition_id":"wf_in_progress_done"}
```

Không thêm field vào payload. Không gọi endpoint khác để sửa issue.

## Xác thực

Dùng một trong hai biến môi trường; không yêu cầu người dùng dán credential vào bảng và không ghi credential ra output:

```text
WORKAI_TOKEN
WORKAI_SESSION_TOKEN
```

`WORKAI_TOKEN` được gửi bằng `Authorization: Bearer ...`. Nếu không có token, dùng `Cookie: sessionToken=...`.

## Input bảng

Nhận bảng Markdown hoặc bảng được người dùng dán từ spreadsheet. Cột bắt buộc là `issue_id`; chấp nhận tiêu đề `Issue ID`, `ID issue`, `Mã issue`. Các cột khác chỉ dùng để đối chiếu trong báo cáo.

Ví dụ:

| issue_id | Tên việc |
|---:|---|
| 2716 | Hoàn thiện đăng nhập |
| 2717 | Kiểm thử đăng nhập |

Trước khi gọi API:

1. Parse toàn bộ bảng, giữ số dòng nguồn.
2. Yêu cầu mỗi `issue_id` là số nguyên dương. Nếu có dòng thiếu hoặc sai định dạng, báo tất cả dòng lỗi và không mutation issue nào.
3. Nhận diện ID trùng. Chỉ chuyển trạng thái một lần cho mỗi ID và đánh dấu các dòng trùng trong báo cáo.
4. Không suy diễn ID từ tên việc, issue key hoặc URL không chứa ID số rõ ràng.

## Thực thi

Dùng helper để preflight và thực thi toàn batch trong một lệnh:

```powershell
python scripts/complete_issues.py --issue-id 2716 --issue-id 2717
```

Resolve `scripts/complete_issues.py` tương đối với thư mục chứa `SKILL.md`, không tương đối với current working directory.

Helper thực hiện các invariant sau:

- `GET /issues/<issue_id>` cho toàn bộ ID duy nhất trước mutation đầu tiên. Nếu bất kỳ preflight nào thất bại, dừng cả batch.
- Bỏ qua issue đã ở trạng thái Done/Completed/Hoàn thành.
- Gọi transition tuần tự cho từng issue còn lại với đúng payload đã chỉ định.
- Đọc lại issue sau mỗi transition để xác minh trạng thái trên server.
- Sau timeout/lỗi mơ hồ, đọc lại issue; nếu chưa xác minh Done thì không retry mutation tự động.
- Nếu gặp `401` hoặc `403` trong khi mutation, dừng các issue còn lại.

Nếu môi trường không có Python, thực hiện cùng quy trình bằng HTTP client sẵn có; vẫn phải giữ preflight toàn batch, payload chính xác và không retry mutation mù.

## Kết quả

Chuyển JSON từ helper thành bảng ngắn, giữ ánh xạ về dòng input:

| Dòng | Issue ID | Trạng thái | Chi tiết |
|---:|---:|---|---|

Trạng thái báo cáo:

- `completed`: transition đã được server xác minh.
- `already_completed`: issue đã hoàn thành trước khi gọi transition.
- `duplicate`: ID trùng, không gọi lần hai; tham chiếu dòng đầu.
- `failed`: request thất bại hoặc trạng thái sau transition chưa được xác minh.
- `not_attempted`: dừng do lỗi auth/quyền ở issue trước.

Không báo thành công chung nếu còn `failed` hoặc `not_attempted`. Với lỗi, giữ HTTP status, error `code`/`message` nếu API trả về và nêu rõ transition có thể đã được gửi nhưng chưa xác minh hay chưa.
