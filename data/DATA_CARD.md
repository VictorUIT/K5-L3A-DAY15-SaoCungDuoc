# Dữ liệu C1 tại CP2

| Nguồn và đơn vị | Quy mô, xử lý và mục đích |
|---|---|
| [park.json](park.json), phiên bản CP2, khu Vịnh Mây giả lập | 5 điểm: 3 trò/điểm tham quan và 2 show. Nhóm điền tay một bộ cố định, không dùng trình sinh ngẫu nhiên; seed không áp dụng. Tên, khung giờ, thời lượng, giá, giới hạn chiều cao, quãng đi và trạng thái đóng đều là giả lập phục vụ kiểm thử. |
| [Review Traveloka](../evidence/data-mining.md), ngày xem 27/11/2026 | 15 đoạn review đọc được từ trang VinWonders Nha Trang; lưu diễn giải đã bỏ tên và một trích đoạn ngắn. Dùng tìm tín hiệu ban đầu và chuyển tình huống thực thành câu thử. Không mang giá hay lịch lịch sử trong review sang danh mục. |
| Use case nhóm, hai phần “Lên lịch trình chi tiết” và “Mua khu vui chơi” | Kịch bản thiết kế để chọn phạm vi và cách hỏi thiếu thông tin. Các đầu vào do nhóm dựng được đánh dấu tu_viet. |
| [Benchmark](../eval/benchmark.csv), phiên bản CP2 | 12 câu do nhóm biên soạn. 5 câu ghi nguồn review cụ thể cho tình huống gốc; toàn bộ giờ, giá và mã trò trong các câu đó được chuyển sang bộ mô phỏng. |

**Cách tính độc lập.** Đồng Việt Nam, giờ địa phương trong cùng một ngày. Vé mẫu 180.000 đ/người lớn, 100.000 đ/trẻ, một lần cho cả buổi. Phụ phí tàu lượn 30.000 đ/người, trẻ tham gia phải cao ít nhất 120 cm. Gia đình đi cùng nhau. Khung đầu vào tính từ cổng đến lúc kết thúc điểm cuối. Mỗi chặng, kể cả cổng đến điểm đầu, mất 10 phút. Giờ bắt đầu = giờ muộn hơn giữa lúc đến và lúc mở. Show bắt đầu đúng lịch, có mặt trước ít nhất số phút đệm khách chọn (mặc định 0). Trò phải kết thúc trước hoặc đúng giờ đóng và giờ khách kết thúc. Không có dữ liệu thời gian xếp hàng, ra cổng hay tồn vé trực tiếp.

**Thử lại.** Dùng cùng file JSON, cùng đầu vào thì bộ kiểm cho cùng tập lịch. Để cập nhật sự kiện đóng, truyền mã vào trường đóng của yêu cầu. Bản CP2 giới hạn 1–3 điểm khác nhau. Khách có thể gửi yêu cầu mới với khung giờ còn lại và điều kiện đã đổi.
