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
- Video dự phòng 26 giây (gọi model thật): https://drive.google.com/file/d/163YYxVCp81kX1ixeHPpIcfg5yK9pNAlm/view?usp=sharing

## 5 · Đánh giá thế nào
- Dataset: khu Vịnh Mây mô phỏng (5 điểm). Bộ câu thử 26 câu (10 thường, 13 khó, 3 từ chối), 9/26 từ data thật. 4 metric, chuẩn đạt khoá ở CP2 (`spec.md` §7).
- Lượt 1 `run-1@20261127-202533` → lượt 2 `run-2@20261127-202738`, cùng 26 câu, cùng model, 0 lỗi kỹ thuật. Kiểm tự động: 12/12 lịch hợp lệ và khớp số ở cả hai lượt.
- **Lượt 1: 25/26 (96%) → Lượt 2: 25/26 (96%)** — mỗi lượt thuong 10/10 · kho 12/13 · tu_choi 3/3, đạt chuẩn ≥22/26. Câu trượt duy nhất ở cả hai lượt: C21. Hai người chấm tay (Bình An, Tuấn Khanh), cùng cách chấm, đồng thuận 26/26 mỗi lượt. Nguồn: `eval/phieu-cham-run-1.md`, `eval/phieu-cham-run-2.md`, `python run.py score`.
- **Vì sao điểm benchmark cao mà AI vẫn sai:**
  - Ràng buộc cứng (giờ, đi bộ, chiều cao, tiền, điểm đóng) do **Python kiểm**; AI chỉ chọn 1 lịch trong danh sách đã hợp lệ. Benchmark chủ yếu đo phần này nên điểm cao là do thiết kế.
  - Lỗi thật của AI nằm ở **hiểu sở thích**, ngoài benchmark: thử thêm 8 câu sở thích → 2/8 sai (khách dặn "ít đi bộ, bé nhanh mệt" mà nhận lịch đi bộ nhiều nhất).
  - C21 trượt cả hai lượt: không có trẻ nhưng lý do nhắc "chiều cao của bé" (lỗi câu giải thích trong code, chưa sửa).
  - Giới hạn tự nhận: bộ câu thử đo **hợp lệ**, chưa đo **khớp sở thích**. Việc tiếp: thêm câu có tiêu chí kiểm được (vd "ít đi bộ → lịch ít điểm nhất trong các lịch hợp lệ").
- *Câu nói khi demo:* "25/26 vì ràng buộc cứng do code kiểm, không phải AI; câu trượt là lỗi câu giải thích. Lỗi thật của AI là hiểu sở thích — nhóm tìm được 2/8 câu sai ngoài bộ thử và sửa ở lượt 2. Bộ câu thử chưa đo được phần này, đó là việc tiếp theo."
- Lỗi chính và cải tiến: “ít đi bộ”, “chỉ muốn xem show” bị chọn lịch nhiều điểm (2/8 → 0/8 sau khi gửi model bản tóm tắt có phút đi bộ, giờ xong, số show). Nguồn: `eval/report.md`, `eval/explore-preferences.md`.

## 6 · Chi phí khi dùng thật
- Đo token trên `gemini-3.1-flash-lite`, tính giá gemini-3.1-flash-lite và gemini-3.8-flash (giá từ 01/01/2027), nguồn bảng giá BTC xem 25/11/2026.
- Số: lấy từ `cost/cost-estimate.md` (mô phỏng 50 phiên, seed 42). Chi phí / task thành công dùng tỉ lệ đạt lượt 2 = **25/26 (96%)**.
- Số người dùng và persona đang là *(tự ước tính)* **[CẦN NHÓM thay bằng số khảo sát]**.

## 7 · Kết luận
- **[CẦN NHÓM]** Go / iterate / stop, dẫn số trang 1 (pain), 5 (điểm đạt), 6 (chi phí so với impact).

## 8 · Nếu có thêm 1 tuần
- Thêm câu benchmark đo mức khớp sở thích nhịp độ (lỗi lượt 1 chưa có trong bộ).
- Rút gọn bản tóm tắt gửi model để giảm token (lượt 2 tăng 39%).
- Thêm câu có nguồn từ phỏng vấn (`nguoi_dung`); hỏi phụ huynh có cần lọc trong nhà/ngoài trời không.
- **[CẦN NHÓM]** phản hồi người dùng thử ở `validation/log.md`.
