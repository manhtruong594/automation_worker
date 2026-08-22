---
name: workai-timeline-schedule
description: Tạo và xếp lịch đầu việc trên https://workai.horus.io.vn/timeline-schedule cho quy trình nhập việc WorkAI. Sử dụng khi người dùng cung cấp tên dự án, tên đầu việc, ngày bắt đầu và thời gian dự kiến, rồi muốn Codex đọc đúng project_overview, tạo issue WorkAI, sinh mô tả/tiêu chí nghiệm thu ngắn gọn, thêm vào timeline và tự chia sang ngày tiếp theo khi vượt capacity.
---

# Lịch Timeline WorkAI

## Dữ Liệu Đầu Vào

Input tối thiểu:

```yaml
project_name: ""
task_name: ""
start_date: ""
estimated_duration: ""
optional_context: ""
```

Chấp nhận `start_date` dạng `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `hôm nay`, `ngày mai`. Chấp nhận duration như `12h`, `4 tiếng`, `1.5 ngày`.

Nếu ngày hoặc thời lượng vẫn mơ hồ sau khi parse, hỏi lại trước khi tạo issue.

## Luồng chạy nhập việc tự động

### Project Overview

Luôn đọc overview trước khi tạo issue. Tìm trong workspace theo thứ tự:

- Ưu tiên tìm theo id project: `project_overviews/<project-name>_<project-id>.md`
- File Markdown có tên chứa `project_overview` hoặc `overview`.

Nếu nhiều overview cùng khớp, hỏi người dùng chọn file. Nếu không có overview, chỉ tiếp tục khi người dùng cho phép rõ.


### Tạo Issue

Tạo issue trong đúng `workai_name`.

Quy tắc:

- Type mặc định: `Story`.
- Summary lấy từ script, phải dài hơn 50 ký tự (nếu ngắn hơn hãy tự động sinh Summary dựa vào project_overview đã đọc ở trên).
- Estimate lấy từ `issue.estimated_hours`.
- Description và acceptance criteria sẽ tự genarate bằng tính năng đã có trên work.ai

Sau khi tạo, ghi lại issue key, ví dụ `GTLU-2716`.

### Xếp Timeline

Với mỗi đầu việc được tạo ra:

1. Chuyển đến đúng tuần chứa `date`.
2. Thêm issue key vào ngày đó.
3. Nhập đúng `hours`.
4. Không ghi đè block có sẵn.
5. Xác minh tổng phân bổ bằng `estimated_hours`.
6. Nếu đã phân đổ đủ số giờ trong ngày mà thời gian estimated_hours vẫn còn thì phân bổ sang ngày tiếp theo.

### Báo Cáo Hoàn Tất

Báo cáo ngắn:

- Dự án.
- Issue key.
- Summary cuối cùng.
- Ngày bắt đầu.
- Tổng giờ dự kiến.
- Phân bổ theo ngày.

Nếu thất bại, báo đúng trạng thái đang chặn, bước cuối đã hoàn tất và dữ liệu đã tạo trên WorkAI để tránh tạo trùng.
