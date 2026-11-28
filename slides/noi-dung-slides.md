# Nội dung slide · C1 · Sao Cũng Được

> Theo [outline.md](outline.md) và khung 8 trang ở guide 5.1 (rubric R7). Mỗi trang có số hoặc nguồn. Bản trình chiếu: `demo-slides.pdf` ở gốc repo, dựng từ [demo-slides.html](demo-slides.html) — sửa chữ ở đây thì sửa cả file HTML rồi xuất lại PDF. Người nói: bảng cuối [outline.md](outline.md).


## 1 · Người dùng và pain *(Đỗ Phương Nam)*
- Phụ huynh tự lên kế hoạch đưa trẻ dưới 12 tuổi đi một khu vui chơi trong một buổi, có giờ vào và giờ phải về.
- Việc khó: tự ghép giờ show, giờ đóng trò, 10 phút đi bộ mỗi chặng, chiều cao của bé và ngân sách.
- Phỏng vấn 3 phụ huynh ngoài nhóm (27/11): **2/3** gặp lỗi giờ / điều kiện (P1 con thiếu 2 cm, P2 lỡ show xiếc vì giờ hỏi miệng sai + trò bảo trì) → đạt ngưỡng chốt trước; **3/3** có trò định chơi mà không chơi được.
- Khảo sát kiểm lại (group cư dân, 20 phản hồi, **10 qua sàng lọc**, chưa đủ ≥20): lỗi giờ / điều kiện chỉ **2/10** → dưới ngưỡng 1/4; lý do đổi kế hoạch lớn nhất là **xếp hàng 3/5**.
- Trích dẫn:
  - P2: “Tôi hỏi chú bảo vệ thì bảo tầm 2h có suất xiếc, ai ngờ tới nơi show chạy từ 1h30 và xong mất rồi.”
  - Khảo sát S14: “Tàu lượn siêu tốc nhưng quá đông nên bỏ”
  - Review R15 (Traveloka, VinWonders Nha Trang, 2/15 review khuyên canh giờ): “Making sure you take photos of the show timetables”
- *Điều nhóm học được:* pain có thật nhưng **hàng chờ lớn hơn lỗi giờ**.
- Nguồn: `evidence/summary.md`, `evidence/survey/results.csv`.

## 2 · Vì sao chọn bài này *(Trần Quốc Tuấn Khanh)*
- Công thức impact: số gia đình × số lần đi / tháng × (phút chuẩn bị + phút xếp lại) / lần (`spec.md` §2).

| Thừa số | Số · nguồn |
|---|---|
| Nhóm-lượt gia đình có trẻ / tháng | ≈126.500 — VinWonders 9,11 triệu lượt 2025 ÷ 3 người/nhóm × 50% *(tự ước tính)* |
| Số lần đi / tháng | 0,33 — P1–P3 |
| Phút chuẩn bị + xếp lại | 45 + 5 — P1–P3 (khảo sát: 8/10 chuẩn bị ≤15 phút → số này có thể cao) |

- Kết quả: **≈17 phút / gia đình / tháng, ≈105.000 giờ / tháng**.

| Hướng | Bằng chứng | Quyết định |
|---|---|---|
| A. Xếp lịch thoả điều kiện (chiều cao, trò đóng, giờ show + đệm, giờ về, ngân sách) | 2/3 phỏng vấn · 2/10 khảo sát | **Chọn** — ràng buộc cứng, code kiểm được |
| B. Báo thời gian chờ, né hàng đông | 2/3 phỏng vấn · 3/5 khảo sát | Loại — cần dữ liệu hàng chờ real-time, không có; app chính thức (P3) đã làm |
| C. Chỉ nhắc giờ show | 1/3 phỏng vấn | Gộp vào A |


## 3 · Giải pháp *(Trần Quốc Tuấn Khanh)*
- Lát cắt: một phụ huynh nhập khung giờ, nhóm khách, ngân sách và hoạt động bắt buộc → trợ lý chọn một lịch khả thi và trả giờ cùng tổng tiền cho cả nhà.
- Luồng (`spec.md` §4): rút điều kiện (Python kiểm từng trường) → `feasible_routes` (Python liệt kê và kiểm mọi lịch 1–3 điểm) → `call_model` gemini-3.1-flash-lite chỉ chọn `{"index": n}` → trả lời, giờ và tiền lấy từ Python.
- AI không tự quyết ràng buộc cứng: giờ, giá, chiều cao, đi bộ kiểm bằng code **trước** khi gọi model.
- Vô nghiệm: nêu ràng buộc đang chặn kèm số và gợi ý đã kiểm lại là ra lịch. Trẻ đi không có người lớn: chặn bằng code. JSON hỏng hoặc chỉ số ngoài danh sách: báo chưa chọn được.

## 4 · Demo live *(Nguyễn Văn Ngọc Sơn)*
- Web: `streamlit run streamlit_app.py` trên máy có `.env`. Khu Vịnh Mây (dữ liệu mô phỏng, 5 điểm); nhãn “Dữ liệu mô phỏng” luôn hiện.
- Ca thường (C01): 2 người lớn, 1 bé 110 cm, 09:00–12:00, 500.000 đ, phải có Show chim → Vườn hoa, Nhà tranh, Show chim 11:00–11:20, tổng 460.000 đ.
- Ca khó (C14): đến cổng 10:51, show 11:00 → không có lịch, “đến sớm nhất 11:01”, gợi ý “đến cổng lúc 10:50 hoặc sớm hơn”. Sửa giờ ngay trên web rồi tạo lại.
- Video dự phòng 26 giây (gọi model thật): https://drive.google.com/file/d/163YYxVCp81kX1ixeHPpIcfg5yK9pNAlm/view?usp=sharing


## 5 · Đánh giá thế nào *(Nguyễn Bình An)*
- Dataset: khu Vịnh Mây mô phỏng (5 điểm). Bộ câu thử 26 câu (10 thường, 13 khó, 3 từ chối), 9/26 từ data thật. 4 metric, chuẩn đạt khoá ở CP2 (`spec.md` §7).

| Lượt · run ID | Tổng | Thường | Khó | Từ chối |
|---|---:|---:|---:|---:|
| 1 · `run-1@20261127-202533` | **25/26** | 10/10 | 12/13 | 3/3 |
| 2 · `run-2@20261127-202738` | **25/26** | 10/10 | 12/13 | 3/3 |

- Đạt chuẩn ≥22/26. Hai người chấm tay (Bình An, Tuấn Khanh), cùng cách chấm, đồng thuận 26/26 mỗi lượt. Câu trượt duy nhất ở cả hai lượt: C21. Nguồn: `eval/phieu-cham-run-1.md`, `eval/phieu-cham-run-2.md`, `python run.py score`.
- **Vì sao điểm benchmark cao mà AI vẫn sai:**
  - Ràng buộc cứng do **Python kiểm**; AI chỉ chọn 1 lịch trong danh sách đã hợp lệ. Benchmark chủ yếu đo phần này nên điểm cao là do thiết kế.
  - Lỗi thật của AI nằm ở **hiểu sở thích**, ngoài benchmark: “ít đi bộ, bé nhanh mệt” nhận lịch đi bộ nhiều nhất → **2/8 → 0/8** sau lượt 2 (gửi model phút đi bộ, giờ xong, số show). Nguồn: `eval/report.md`, `eval/explore-preferences.md`.
  - C21: không có trẻ nhưng lý do nhắc “chiều cao của bé” (lỗi câu giải thích, chưa sửa).
  - Giới hạn: bộ câu thử đo **hợp lệ**, chưa đo **khớp sở thích**.
- *Câu nói khi demo:* "25/26 vì ràng buộc cứng do code kiểm, không phải AI; câu trượt là lỗi câu giải thích. Lỗi thật của AI là hiểu sở thích — nhóm tìm được 2/8 câu sai ngoài bộ thử và sửa ở lượt 2. Bộ câu thử chưa đo được phần này, đó là việc tiếp theo."

## 6 · Chi phí khi dùng thật *(Nguyễn Văn Ngọc Sơn)*
- `simulate-2@20261128-120240` (50 phiên, 0 lỗi), tỉ lệ đạt lượt 2 = **25/26**: **$0,00019 / phiên · $0,00020 / task thành công**.

| Model | / task thành công | Thấp 1.265 gia đình | Cơ sở 6.325 | Cao 12.650 |
|---|---:|---:|---:|---:|
| gemini-3.1-flash-lite | $0.00020 | $0.24 / tháng | **$1.18 / tháng** | $2.37 / tháng |
| gemini-3.8-flash | $0.0012 | $1.40 / tháng | $6.99 / tháng | $13.97 / tháng |

- So với impact: ~17 phút / gia đình / tháng so với $0,00019 / gia đình / tháng → chi phí model không phải điểm nghẽn, kể cả nhân 3 cho bước chat (kịch bản cao, model đắt ≈ $42 / tháng).
- Số gia đình = 1% · 5% · 10% của ≈126.500 nhóm-lượt gia đình / tháng (§2); tỉ lệ dùng và persona *(tự ước tính)*. Đo token trên gemini-3.1-flash-lite, tính giá cả hai model (bảng giá BTC xem 25/11/2026). Nguồn: `cost/cost-estimate.md`.


## 7 · Kết luận *(Trần Quốc Tuấn Khanh)*
- **Quyết định: ITERATE** — giữ lõi kiểm ràng buộc, đổi trọng tâm sang hàng chờ.
- Số dẫn: **25/26** cả hai lượt (trang 5) · **$0,00019 / gia đình / tháng** so với ~17 phút (trang 6) · **2/10** khảo sát gặp lỗi giờ / điều kiện (trang 1) · **3/5** đổi kế hoạch vì xếp hàng (trang 1).
- Giữ: bản chạy thử đúng và rẻ — ràng buộc cứng do code kiểm, chi phí không đáng kể.
- Đổi: pain lớn nhất là **xếp hàng** (3/5 khảo sát, 2/3 phỏng vấn) — bản chạy thử chưa có dữ liệu này.
- Chưa Go vì: impact mới từ 3 phỏng vấn, khảo sát chưa đủ ≥20 phụ huynh, benchmark chưa đo khớp sở thích.

## 8 · Nếu có thêm 1 tuần *(Nguyễn Bình An)*
- Khảo sát lại đúng người dùng: lọc “đi cùng trẻ dưới 12”, cài rẽ nhánh câu 1, đủ ≥20 phụ huynh; đo riêng pain hàng chờ.
- Thêm câu benchmark đo khớp sở thích, vd “ít đi bộ → lịch ít điểm nhất trong các lịch hợp lệ”.
- Rút gọn bản tóm tắt gửi model để giảm token (lượt 2 tăng 39%).
- Sửa C21 trong câu giải thích vô nghiệm.
- Dữ liệu thật: snapshot VinWonders Nha Trang (nhánh `binhan`) — planner từ chối xếp lịch khi thiếu dữ liệu an toàn, giá, giờ.
- Người dùng thử (`validation/log.md`, 3 phụ huynh ngoài nhóm, bản `main`, 10:00 28/11): **hơi tiếc 2 · không sao 1 · rất tiếc 0**. Lỗi cao nhất: tưởng gợi ý đã tự xếp lại cả buổi và giữ chỗ / vé → thêm nhãn “chỉ là gợi ý, chưa giữ chỗ hay mua vé”; cảnh báo chiều cao rõ hơn; hiện phút đi bộ; hệ thống bỏ qua ý hàng chờ → báo “chưa có dữ liệu hàng chờ”.
