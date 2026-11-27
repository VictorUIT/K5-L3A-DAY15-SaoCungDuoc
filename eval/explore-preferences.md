# Thử sở thích ngoài benchmark · trước và sau cải tiến lượt 2

Ngày 27/11/2026, model thật `gemini-3.1-flash-lite`, mỗi dòng gọi một lần qua `answer(text)`. Đây **không** thuộc 24 câu benchmark; dùng để tìm lỗi quyết định của AI mà bộ câu thử chưa bắt được. Cùng điều kiện cho mọi dòng:

`giờ=09:00-12:00; lớn=2; trẻ=1; cao=125; đồng=600000; ưu tiên=<sở thích>`

Trước: commit dc69f88 (model nhận JSON lịch thô). Sau: commit 671f0f9 (model nhận bản tóm tắt có số điểm, phút đi bộ, giờ xong, tổng tiền, số show). Đánh giá ở cột cuối do Sơn ghi theo nghĩa thông thường của sở thích; người chấm có thể xem lại.

| Sở thích | Trước | Sau | Token vào trước → sau | Đánh giá |
|---|---|---|---|---|
| ít đi bộ, bé nhanh mệt | Vườn hoa 09:10–09:35 → Nhà tranh 09:45–10:15 → Show chim 11:00–11:20 · 460.000 đ | Vườn hoa 09:10–09:35 · 460.000 đ | 3514 → 3600 | Trước sai (3 điểm, 30 phút đi bộ) → sau đúng (1 điểm) |
| muốn về sớm | Vườn hoa 09:10–09:35 · 460.000 đ | Vườn hoa 09:10–09:35 · 460.000 đ | 3510 → 3596 | Đúng cả hai |
| chỉ muốn xem show | Nhà tranh 09:10–09:40 → Show chim 11:00–11:20 → Vườn hoa 11:30–11:55 · 460.000 đ | Show chim 11:00–11:20 · 460.000 đ | 3511 → 3597 | Trước sai (thêm 2 điểm không phải show) → sau đúng (chỉ Show chim) |
| không thích show, thích trò chơi | Vườn hoa 09:10–09:35 → Nhà tranh 09:45–10:15 → Tàu lượn 10:25–10:45 · 550.000 đ | Vườn hoa 09:10–09:35 → Nhà tranh 09:45–10:15 → Tàu lượn 10:25–10:45 · 550.000 đ | 3513 → 3599 | Đúng cả hai |
| tiết kiệm nhất có thể | Vườn hoa 09:10–09:35 → Show chim 11:00–11:20 → Nhà tranh 11:30–12:00 · 460.000 đ | Vườn hoa 09:10–09:35 → Nhà tranh 09:45–10:15 → Show chim 11:00–11:20 · 460.000 đ | 3512 → 3598 | Đúng cả hai (460.000 đ là mức thấp nhất) |
| bé thích động vật | Nhà tranh 09:10–09:40 → Vườn hoa 09:50–10:15 → Show chim 11:00–11:20 · 460.000 đ | Vườn hoa 09:10–09:35 → Nhà tranh 09:45–10:15 → Show chim 11:00–11:20 · 460.000 đ | 3510 → 3596 | Đúng cả hai (có Show chim) |
| cảm giác mạnh | Vườn hoa 09:10–09:35 → Nhà tranh 09:45–10:15 → Tàu lượn 10:25–10:45 · 550.000 đ | Vườn hoa 09:10–09:35 → Nhà tranh 09:45–10:15 → Tàu lượn 10:25–10:45 · 550.000 đ | 3510 → 3596 | Đúng cả hai (có Tàu lượn) |
| chỗ mát, trong nhà | Vườn hoa 09:10–09:35 → Nhà tranh 09:45–10:15 → Show chim 11:00–11:20 · 460.000 đ | Vườn hoa 09:10–09:35 → Nhà tranh 09:45–10:15 → Show chim 11:00–11:20 · 460.000 đ | 3512 → 3598 | Mơ hồ: dữ liệu không có thuộc tính trong nhà/ngoài trời |

Kết quả nhóm lỗi "sở thích về nhịp độ bị lấn bởi lịch nhiều điểm": 2/8 sai trước → 0/8 sai sau. Token vào mỗi lượt tăng khoảng 2,5% trên bộ này.
