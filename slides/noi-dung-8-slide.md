# Nội dung 8 slide · C1 · Sao Cũng Được

> Bản nháp theo [outline.md](outline.md). Mỗi trang có số hoặc nguồn. **[CẦN NHÓM]** = chỗ phải điền bằng kết quả thật (lời người dùng, video, kết quả chấm). Không điền số khi chưa có nguồn. Xuất PDF thành `demo-slides.pdf` ở gốc repo.

## 1 · Người dùng và pain
- Phụ huynh tự lên kế hoạch đưa trẻ dưới 12 tuổi đi một khu vui chơi trong một buổi, có giờ vào và giờ phải về.
- Việc khó: tự ghép giờ show, giờ đóng trò, 10 phút đi bộ mỗi chặng, chiều cao của bé và ngân sách.
- Phỏng vấn 3 phụ huynh ngoài nhóm (27/11): **2/3** gặp lỗi giờ / điều kiện (P1 con thiếu 2 cm, P2 lỡ show xiếc vì giờ hỏi miệng sai + trò bảo trì) → đạt ngưỡng chốt trước; **3/3** có trò định chơi mà không chơi được; 2/3 vì xếp hàng.
- Trích P2: “Tôi hỏi chú bảo vệ thì bảo tầm 2h có suất xiếc, ai ngờ tới nơi show chạy từ 1h30 và xong mất rồi.”
- Khảo sát kiểm lại (group cư dân, 20 phản hồi, **10 qua sàng lọc**, chưa đủ ≥20): lỗi giờ / điều kiện chỉ **2/10** → dưới ngưỡng 1/4; lý do đổi kế hoạch lớn nhất là **xếp hàng 3/5**. Trích S14: “Tàu lượn siêu tốc nhưng quá đông nên bỏ”.
- Review: 2/15 (Traveloka, VinWonders Nha Trang) khuyên canh giờ, vd R15 “Making sure you take photos of the show timetables”.
- *Điều nhóm học được:* pain có thật nhưng **hàng chờ lớn hơn lỗi giờ**. Nguồn: `evidence/summary.md`.

## 2 · Vì sao chọn bài này
- Công thức impact: số gia đình × số lần đi / tháng × (phút chuẩn bị + phút xếp lại) / lần (`spec.md` §2).
- Ba thừa số: ≈126.500 nhóm-lượt gia đình / tháng (VinWonders 9,11 triệu lượt 2025 ÷ 3 người/nhóm × 50% có trẻ *(tự ước tính)*) · 0,33 lần / tháng (P1–P3) · 45 + 5 phút (P1–P3) → **≈17 phút / gia đình / tháng, ≈105.000 giờ / tháng**.
- Giới hạn: khảo sát cho phút chuẩn bị thấp hơn (8/10 ≤15 phút) → số trên có thể cao.
- Chọn A — xếp lịch thoả điều kiện (chiều cao, trò đóng, giờ show + đệm, giờ về, ngân sách): ràng buộc cứng, code kiểm được.
- Loại B — báo thời gian chờ, né hàng đông: bằng chứng mạnh nhất (3/5 khảo sát, 2/3 phỏng vấn) nhưng cần dữ liệu hàng chờ real-time không có; app chính thức (P3) đã làm. Loại C — chỉ nhắc giờ show: hẹp (1/3), gộp vào A.

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
- Số: `simulate-2@20261128-120240` (50 phiên, 0 lỗi), tỉ lệ đạt lượt 2 = **25/26 (96%)**: **$0,00019 / phiên · $0,00020 / task thành công**. Mỗi tháng: thấp 1.265 gia đình $0,24 · cơ sở 6.325 $1,18 · cao 12.650 $2,37 (gemini-3.8-flash: $13,97).
- So với impact: ~17 phút / gia đình / tháng (§2) so với $0,00019 / gia đình / tháng → chi phí model không phải điểm nghẽn, kể cả nhân 3 cho bước chat.
- Số người dùng = 1% · 5% · 10% của ≈126.500 nhóm-lượt gia đình / tháng (VinWonders 2025, §2); tỉ lệ dùng và persona *(tự ước tính)*, chờ khảo sát.

## 7 · Kết luận
- **Quyết định: ITERATE** — giữ lõi kiểm ràng buộc, đổi trọng tâm sang hàng chờ.
- Giữ: bản chạy thử đạt **25/26** ở cả hai lượt (trang 5); chi phí **$0,00019 / gia đình / tháng**, so với ~17 phút / gia đình / tháng (trang 6) → chi phí không phải điểm nghẽn.
- Đổi: pain lỗi giờ / điều kiện có ở phỏng vấn (2/3) nhưng khảo sát chỉ **2/10** (dưới ngưỡng 1/4); pain lớn nhất là **xếp hàng** (3/5 khảo sát, 2/3 phỏng vấn) — bản chạy thử chưa có dữ liệu này (trang 1).
- Chưa Go vì: impact mới từ 3 phỏng vấn, khảo sát chưa đủ ≥20 phụ huynh, benchmark chưa đo khớp sở thích.

## 8 · Nếu có thêm 1 tuần
- Thêm câu benchmark đo mức khớp sở thích nhịp độ (lỗi lượt 1 chưa có trong bộ).
- Rút gọn bản tóm tắt gửi model để giảm token (lượt 2 tăng 39%).
- Thêm câu có nguồn từ phỏng vấn (`nguoi_dung`); hỏi phụ huynh có cần lọc trong nhà/ngoài trời không.
- **[CẦN NHÓM]** phản hồi người dùng thử ở `validation/log.md`.
