# Nội dung 8 slide · C1 · Sao Cũng Được

> Bản nháp theo [outline.md](outline.md). Mỗi trang có số hoặc nguồn. **[CẦN NHÓM]** = chỗ phải điền bằng kết quả thật (lời người dùng, video, kết quả chấm). Không điền số khi chưa có nguồn. Xuất PDF thành `demo-slides.pdf` ở gốc repo.

## 1 · Người dùng và pain
- Phụ huynh tự lên kế hoạch đưa trẻ dưới 12 tuổi đi một khu vui chơi trong một buổi, có giờ vào và giờ phải về.
- Việc khó: tự ghép giờ show, giờ đóng trò, 10 phút đi bộ mỗi chặng, chiều cao của bé và ngân sách.
- Số: 2/15 review công khai (Traveloka, VinWonders Nha Trang, xem 27/11/2026) chủ động kể hoặc khuyên canh giờ; trích R15 “Making sure you take photos of the show timetables”. Nguồn: `evidence/data-mining.md`.
- **[CẦN NHÓM]** kết quả khảo sát (x/N phụ huynh gặp lỡ show, trò đóng hoặc thiếu chiều cao, theo câu 7) và ≥1 trích dẫn phỏng vấn P1–P3.

## 2 · Vì sao chọn bài này
- Công thức impact: số gia đình × số lần phải xếp lịch/tháng × phút mất/lần (`spec.md` §2).
- **[CẦN NHÓM]** điền ba thừa số từ khảo sát câu 6, 9, 11 và phỏng vấn; ghi hướng bị loại (chọn trò khi đóng, xử lý vào muộn) và lý do.

## 3 · Giải pháp
- Lát cắt: một phụ huynh nhập khung giờ, nhóm khách, ngân sách và hoạt động bắt buộc → trợ lý chọn một lịch khả thi và trả giờ cùng tổng tiền cho cả nhà.
- Sơ đồ: `spec.md` §4. Python kiểm giờ, giá, chiều cao, đi bộ **trước**; model `gemini-3.1-flash-lite` chỉ chọn chỉ số một lịch đã kiểm; giờ và tiền hiển thị lấy từ Python.
- Vô nghiệm: nêu ràng buộc đang chặn kèm số và gợi ý đã kiểm lại là ra lịch. Trẻ đi không có người lớn: chặn bằng code.

## 4 · Demo live
- Web: `streamlit run streamlit_app.py` (hoặc URL Streamlit Cloud **[CẦN NHÓM sau khi deploy]**). Nhãn “Dữ liệu mô phỏng” luôn hiện.
- Ca thường (C01): 2 người lớn, 1 bé 110 cm, 09:00–12:00, 500.000 đ, phải có Show chim → Vườn hoa, Nhà tranh, Show chim 11:00–11:20, tổng 460.000 đ.
- Ca khó (C14): đến cổng 10:51, show 11:00 → không có lịch, “đến sớm nhất 11:01”, gợi ý “đến cổng lúc 10:50 hoặc sớm hơn”. Sửa giờ ngay trên web rồi tạo lại.
- **[CẦN NHÓM]** video dự phòng 30 giây (Khanh).

## 5 · Đánh giá thế nào
- Dataset: khu Vịnh Mây mô phỏng (5 điểm). Bộ câu thử 26 câu (10 thường, 13 khó, 3 từ chối), 9/26 từ data thật. 4 metric, chuẩn đạt khoá ở CP2 (`spec.md` §7).
- Lượt 1 `run-1@20261127-202533` → lượt 2 `run-2@20261127-202738`, cùng 26 câu, cùng model, 0 lỗi kỹ thuật. Kiểm tự động: 12/12 lịch hợp lệ và khớp số ở cả hai lượt.
- **[CẦN NHÓM]** điểm người chấm x/26 mỗi lượt và so với chuẩn ≥5/6 (22/26) (`python3 run.py score`).
- Lỗi chính và cải tiến: “ít đi bộ”, “chỉ muốn xem show” bị chọn lịch nhiều điểm (2/8 → 0/8 sau khi gửi model bản tóm tắt có phút đi bộ, giờ xong, số show). Nguồn: `eval/report.md`, `eval/explore-preferences.md`.

## 6 · Chi phí khi dùng thật
- Đo token trên `gemini-3.1-flash-lite`, tính giá gemini-3.1-flash-lite và gemini-3.8-flash (giá từ 01/01/2027), nguồn bảng giá BTC xem 25/11/2026.
- Số: lấy từ `cost/cost-estimate.md` (mô phỏng 50 phiên, seed 42). Chi phí / task thành công cần tỉ lệ đạt lượt 2 **[CẦN NHÓM chấm xong]**.
- Số người dùng và persona đang là *(tự ước tính)* **[CẦN NHÓM thay bằng số khảo sát]**.

## 7 · Kết luận
- **[CẦN NHÓM]** Go / iterate / stop, dẫn số trang 1 (pain), 5 (điểm đạt), 6 (chi phí so với impact).

## 8 · Nếu có thêm 1 tuần
- Thêm câu benchmark đo mức khớp sở thích nhịp độ (lỗi lượt 1 chưa có trong bộ).
- Rút gọn bản tóm tắt gửi model để giảm token (lượt 2 tăng 39%).
- Thêm câu có nguồn từ phỏng vấn (`nguoi_dung`); hỏi phụ huynh có cần lọc trong nhà/ngoài trời không.
- **[CẦN NHÓM]** phản hồi người dùng thử ở `validation/log.md`.
