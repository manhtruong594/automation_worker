# Tài Liệu Tham Chiếu Project Overview

Sử dụng tài liệu này khi cần tìm hoặc diễn giải các file project overview để tạo đầu việc trên WorkAI.

## Vị Trí Dự Kiến

Tìm nội dung project overview trong workspace hiện tại trước khi hỏi người dùng, ưu tiên tìm theo id project:

- `project_overviews/<project-name>_<project-id>.md`

Dùng cách khớp không phân biệt hoa thường, đồng thời chấp nhận khác biệt về khoảng trắng, dấu gạch ngang, dấu gạch dưới và dấu tiếng Việt khi so sánh tên dự án.

## Dữ liệu project và ID

85 — G - MOB.ERA — key GTLU
81 — G - QUANLY-DIEUHANH-GAME — key QLDH
30 — G - SKYDEFENSE — key SKYD
110 — G - ViecCaNhan — key GVCN
59 — G - ViecChungNgoaiDuAn — key VCNDA
115 — G - WarSurvival — key GFW
39 — G - ZOMBIEHUNTER — key ZBH

## Quy Tắc Khớp Dự Án

Nếu chỉ có một overview khớp dự án được yêu cầu, hãy đọc file đó và tiếp tục.

Nếu có nhiều overview cùng khớp, hãy hỏi người dùng muốn dùng file nào.

Nếu không có overview nào khớp, hãy yêu cầu người dùng cung cấp hoặc tạo đúng `project_overview` trước khi tạo đầu việc WorkAI, trừ khi người dùng cho phép rõ ràng việc tiếp tục mà không có overview.

## Cách Dùng Trong Các Trường Đầu Việc

Dùng overview để mở rộng các tên đầu việc ngắn thành phần tóm tắt dài hơn 50 ký tự. Ưu tiên mẫu sau:

`<Hành động> <tính năng/phân hệ> cho <bối cảnh dự án hoặc kết quả mong muốn>`

Giữ phần mô tả và tiêu chí nghiệm thu ngắn gọn. Hãy để nút gợi ý bằng AI của WorkAI tạo bản nháp khi có thể, sau đó rút gọn hoặc chỉnh lại kết quả.
