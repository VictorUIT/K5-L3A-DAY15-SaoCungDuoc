# Người dùng thử *(bonus)*

> Điền ở guide bước 4.3 — 2–3 người ngoài nhóm, ~10 phút / người, theo 5 nhịp: làm quen · bối cảnh · giao việc · quan sát · hỏi sau. Ôn lại: ngày 5, ngày 13. Chấm ở rubric Bonus.
> Không ghi tên: ghi vai. Hành vi quan sát được nặng hơn lời nói; toàn lời khen = phiên chưa đạt, giao việc khó hơn.
> Người dùng thử **không thay được** bằng chứng pain ở `evidence/`.

**Phiên thử:** Trần Quốc Tuấn Khanh (đội trưởng) đứng phiên · 10:00 28/11/2026 · bản `main` (web chatbox, khu Vịnh Mây mô phỏng) · 3 phụ huynh ngoài nhóm.

| Người thử (vai) | Việc giao (theo kết quả, không theo nút) | Quan sát (làm gì đầu tiên, chỗ do dự, chỗ hiểu sai) | Trích nguyên văn | Mức nghiêm trọng (cao / vừa / thấp) |
|---|---|---|---|---|
| Phụ huynh có con 6 tuổi (ngoài nhóm) | Tìm phương án xử lý khi lỡ show biểu diễn lúc 13h45 và có bé nhỏ đi cùng | Mở màn hình chính, nhập yêu cầu theo kiểu hội thoại tự nhiên; hệ thống báo khu chỉ có show 11:00 và 15:00 (không có suất 13h45); do dự ~8 giây ở bước xem giờ show tiếp theo vì tưởng hệ thống tự đổi luôn lịch cả buổi; hiểu nhầm rằng phần gợi ý thay thế đã tự giữ chỗ/vé | "Mình tưởng nó tự xếp lại hết lịch chiều cho mình luôn chứ, hóa ra chỉ gợi ý phương án để mình chọn lại." | Cao |
| Phụ huynh có con 8 tuổi và 4 tuổi (ngoài nhóm) | Kiểm tra điều kiện vào trò chơi cho bé lớn và tìm phương án thay thế khi hàng chờ quá đông | Nhập đồng thời tuổi/chiều cao 2 bé và tên khu vui chơi; màn hình hiện danh sách lịch (bản `main` chỉ có khu Vịnh Mây, không có bộ lọc trò riêng); thao tác nhanh, nhưng hơi ngập ngừng khi đọc mốc cảnh báo giới hạn chiều cao vì chữ nhỏ; hiểu đúng là cần đối chiếu lại thước đo trực tiếp tại cổng; khi nhập ý hàng chờ quá đông, hệ thống vẫn trả một lịch, **không nhắc gì đến hàng chờ** | "Cảnh báo chiều cao có hiện ra nhưng nhìn lướt qua dễ bị sót nếu đang vội dỗ con." | Vừa |
| Phụ huynh có con 5 tuổi (ngoài nhóm) | Xem các hoạt động còn mở trong khung chiều khi trời nắng và bé bắt đầu mệt | Nhập khung giờ buổi chiều và trạng thái "bé mệt, cần chỗ nghỉ/trò nhẹ"; hệ thống trả lịch **Nhà tranh, Show nhạc** (dữ liệu không có thuộc tính trong nhà / trò nhẹ — model chọn trong các lịch hợp lệ); làm quen rất nhanh với kết quả; do dự ngắn khi so sánh thời gian di chuyển giữa hai khu vì chưa rõ quãng đường đi bộ thực tế | "Đang dắt con đi nắng mà nhìn ra được mấy chỗ nhẹ nhàng gần nhau ngay thì đỡ phải nghĩ nhiều." | Thấp |

Câu hỏi sau: *"Nếu mai không được dùng nữa, bạn thấy: rất tiếc / hơi tiếc / không sao?"* → rất tiếc 0 / **hơi tiếc 2** / không sao 1 (không ghi theo từng người)

## Tổng hợp

- Chủ đề lặp nhiều nhất: người dùng **chưa rõ hệ thống làm đến đâu và dựa trên số nào** — tưởng tự xếp lại cả buổi và tự giữ chỗ / vé (người 1), dễ sót cảnh báo chiều cao (người 2), chưa rõ quãng đi bộ thực tế giữa hai khu (người 3). 3/3 người nhập bằng câu tự nhiên và dùng được ngay. Không ai chọn "rất tiếc" (hơi tiếc 2 · không sao 1) → giá trị hiện tại chưa đủ mạnh, khớp kết luận ITERATE.
- Sửa gì (ghi `spec.md` §10): (1) ghi rõ trên kết quả "chỉ là gợi ý, chưa giữ chỗ hay mua vé" — mức **cao**; (2) cảnh báo chiều cao hiện to, đặt ngay cạnh tên trò; (3) hiện số phút đi bộ mỗi chặng trong lịch; (4) khi người dùng nhắc hàng chờ, nói rõ "chưa có dữ liệu hàng chờ" thay vì im lặng trả lịch.
- Giữ gì và vì sao: ô chat nhập câu tự nhiên (3/3 làm được ngay, không cần hướng dẫn); gợi ý các điểm gần nhau khi bé mệt (người 3: "đỡ phải nghĩ nhiều").
- Để dành sau: phương án thay thế khi hàng chờ đông (người 2 hỏi, hệ thống bỏ qua) — cần dữ liệu hàng chờ, bản chạy thử chưa có, cùng hướng với khảo sát (xếp hàng 3/5); thuộc tính trong nhà / trò nhẹ cho sở thích "bé mệt" (người 3); tự xếp lại cả buổi chiều sau khi lỡ show (người 1).
