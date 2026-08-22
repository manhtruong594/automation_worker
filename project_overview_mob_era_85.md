# 1. GAME OVERVIEW

## 1.1 Game Concept

Game là một casual auto-battle runner với cơ chế điều khiển trung tâm dựa trên Wheel (bàn xoay tự động). Người chơi không điều khiển đơn vị trực tiếp mà điều phối nhịp spawn lính thông qua thao tác vuốt trái/phải, kết hợp buff trong trận và nâng cấp vĩnh viễn ngoài trận để vượt qua các chướng ngại vật

## 1.2 Genre

Casual / Hyper-casual

Auto-battle

Runner

## 1.3 Platform

Mobile (iOS / Android)

## 1.4 Target Audience

Người chơi casual

Độ tuổi: 12+

Ưa thích game đơn giản, nhanh, có cảm giác tiến bộ rõ rệt

Có thể chơi offline hoặc online

# 2. CORE FANTASY & PLAYER EXPERIENCE

## 2.1 Core Fantasy

Trở thành người điều phối đội quân, liên tục gia tăng sức mạnh để phá vỡ mọi chướng ngại vật và tiến hóa qua các thời đại.

## 2.2 Player Experience Goals

Điều khiển 1 thao tác (vuốt trái phải để di chuyển), dễ học

Nhịp chơi nhanh, liên tục

Thua không gây ức chế

Cảm giác sức mạnh tăng trưởng rõ rệt qua mỗi lần chơi

# 3. CORE GAME LOOP

## 3.1 In-Level Loop

Wheel tự động tiến về phía trước và quay để triển khai nhân vật

→ Player vuốt trái/phải điều chỉnh slot

→ Spawn lính

→ Auto-combat với chướng ngại vật

→ Nhận buff tạm thời

→ Tiếp cận chướng ngại vật cuối

→ Win / Lose

## 3.2 Meta Loop

Win / Lose

→ Nhận Cash

→ Nâng cấp vĩnh viễn

→ Thử lại Age hiện tại hoặc mở Age mới

→ Lặp lại

# 4. GAMEPLAY MECHANICS

## 4.1 Wheel Mechanic

Wheel luôn:

Tự động quay theo chiều kim đồng hồ

Tự động di chuyển về phía trước

Player chỉ vuốt trái/phải để điều chỉnh lệch ngang

Mục tiêu: điều phối slot đi qua Spawn Point

## 4.2 Slot & Spawn System

Hiển thị tối đa: 8 slot

Logic: slot không giới hạn, có thể chồng

Khi slot đi qua Spawn Point → spawn 1 lính

Spawn tức thời, không delay

## 4.3 Ally Unit Behavior

Auto-move về phía trước

Auto-attack chướng ngại trong tầm

Không điều khiển trực tiếp

## 4.4 Obstacle System

Chướng ngại vật có HP

HP tăng theo level và Age

Cụm chướng ngại cuối là DPS Check

## 4.4 Obstacle System

Chướng ngại vật có HP

HP tăng theo level và Age

Cụm chướng ngại cuối là DPS Check

## 4.5 Phase Play

Một trận đấu có tối thiểu 2 Phase và tối đa là 3 Phase.

Phase 1 - Phase 2: Phase tăng sức mạnh cho người chơi. 

Cụm chướng ngại cuối là DPS Check

# 5. BUFF SYSTEM (IN-RUN)

## 5.1 Nguyên tắc

Buff chỉ tồn tại trong màn chơi

Kích hoạt ngay khi đi qua

Có thể cộng dồn

## 5.2 Buff tiêu biểu

Tăng Level của lính

Tăng Fire Rate

Tăng Range

Tăng số lượng lính spawn

# 6. WIN / LOSE CONDITION

Không có thắng hay thua, chỉ có hoàn thành.

Chạm được vào cửa cuối cùng: Lên Age kế tiếp

Không chạm được vào cửa cuối cùng: Tiếp tục chơi lại Age hiện tại

Hoàn thành màn chơi nhận Cash

# 7. PROGRESSION SYSTEM

## 7.1 Age System

Game chia thành nhiều Age (Thời đại)

Mỗi Age có độ khó cao hơn

Thắng Age hiện tại để mở khóa Age tiếp theo

## 7.2 Timeline System

Timeline là tiến trình dài hạn gồm nhiều Age

Hoàn thành Timeline mở nội dung mới

## 7.3 Meta Upgrade

Dùng Cash để nâng cấp:

Level của lính

Số slot khởi đầu

Progress của buff thêm lính Ingame.

Tăng income

Những nâng cấp này khi qua Age mới sẽ reset lại từ đầu.

# 8. UI / UX OVERVIEW

UI tối giản, tập trung vào Wheel và đường chạy

Feedback rõ ràng khi:

Spawn lính

Nhận buff

Phá hủy chướng ngại

# 9. ART & AUDIO DIRECTION (OVERVIEW)

## 9.1 Art Style

Stylized, rõ ràng, dễ đọc

Thay đổi theo Age / Timeline

## 9.2 Audio

Âm spawn ngắn, rõ

Âm phá chướng ngại tạo cảm giác thỏa mãn

# 10. TECH & DESIGN CONSTRAINTS

One-hand control

Performance ổn định trên mobile

Session ngắn (30–90s / run)

# 11. BALANCE & TUNING POINTS

Tốc độ quay Wheel

Spawn rate

HP curve của obstacle

Cost curve của upgrade
