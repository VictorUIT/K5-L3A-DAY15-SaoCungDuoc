# Dàn slide → lấy số từ file nào

> Làm ở guide bước 5.1. Luật: **không có bằng chứng thì không có slide** — mỗi trang ≥1 con số / trích dẫn có nguồn / kết quả đo.
> Xuất PDF thành `demo-slides.pdf` ở thư mục gốc repo, nộp tại CP4 14:30 Thứ Bảy 28/11. Nộp PDF, không nộp link.

| # | Trang | Có gì | Số lấy từ | Xong |
|---|---|---|---|---|
| 1 | Người dùng & pain | Ai · việc gì · chỗ đau + số và trích dẫn | `evidence/summary.md` | ☐ |
| 2 | Vì sao chọn bài này | Bảng impact rút gọn + hướng bị loại | `spec.md` §2 | ☐ |
| 3 | Giải pháp | Lát cắt một câu · sơ đồ · AI tự làm đến đâu, vì sao | `spec.md` §4 | ☐ |
| 4 | Demo live | 1 trường hợp thường + 1 trường hợp khó (lấy từ bộ câu thử); mạng hỏng → video dự phòng | `eval/benchmark.csv` | ☐ |
| 5 | **Đánh giá thế nào** | Dataset · bộ câu thử · metric · lượt 1 → lượt 2 so với chuẩn "đạt" (kèm run ID) · lỗi chính | `eval/README.md`, `eval/report.md` | ☐ |
| 6 | **Chi phí khi dùng thật** | Chi phí / task thành công · 3 kịch bản · so với impact | `cost/cost-estimate.md` | ☐ |
| 7 | Kết luận | Go / iterate / stop — dẫn số ở trang 1, 5, 6 | — | ☐ |
| 8 | Nếu có thêm 1 tuần | 2–3 việc, trỏ về lỗi còn lại / phản hồi người dùng | `eval/report.md` mục 4 · `validation/log.md` | ☐ |

**Trước khi lên:** tải repo về một máy khác (hoặc thư mục mới), chạy theo mục "Chạy trong 3 phút" của `README.md` · `.env` có trên máy demo, đã gọi thử 1 câu trong vòng 1 giờ trước giờ demo · video dự phòng mở được bằng cửa sổ ẩn danh · biết bản chạy thử sẽ làm gì với **1 câu thử lạ** của giám khảo.

Ai nói trang nào (mỗi người ≥1 phần):

| Trang | Người nói | Lý do |
|---|---|---|
| 1 · Người dùng & pain | Đỗ Phương Nam | phụ trách bằng chứng pain (phỏng vấn, khảo sát, review — evidence/) |
| 2 · Vì sao chọn bài này | Trần Quốc Tuấn Khanh | đội trưởng, phụ trách canvas, spec và tổng thể slide |
| 3 · Giải pháp | Trần Quốc Tuấn Khanh | nắm thiết kế giải pháp, lát cắt và giới hạn AI trong spec.md |
| 4 · Demo live | Nguyễn Văn Ngọc Sơn | phụ trách bản chạy thử (codebase/) và vận hành trực tiếp |
| 5 · Đánh giá thế nào | Nguyễn Bình An | phụ trách data card, bộ câu thử, metric, báo cáo đánh giá (data/, eval/) |
| 6 · Chi phí khi dùng thật | Nguyễn Văn Ngọc Sơn | phụ trách mô phỏng chi phí (cost/) |
| 7 · Kết luận | Trần Quốc Tuấn Khanh | đội trưởng, chốt quyết định từ pain, eval và chi phí |
| 8 · Nếu có thêm 1 tuần | Nguyễn Bình An | nắm các lỗi, hạn chế còn tồn đọng từ eval/ và validation/ |
