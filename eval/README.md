# Hồ sơ đánh giá C1 · cập nhật CP4 (28/11)

> Guide bước 4.1. Một trang: dataset → xử lý → bộ câu thử → metric và cách chấm → đã chạy gì → lỗi chính. Chi tiết lỗi và cải tiến: [report.md](report.md).

## 1. Dataset và xử lý

- **Danh mục khu vui chơi:** [park.json](../data/park.json), khu **Vịnh Mây giả lập**, 5 điểm (3 trò / điểm tham quan + 2 show). Nhóm điền tay một bộ cố định: giờ mở / đóng, thời lượng, giá vé (180.000 đ người lớn · 100.000 đ trẻ), phụ phí tàu lượn 30.000 đ / người, mốc chiều cao 120 cm, 10 phút đi bộ mỗi chặng. Quy tắc tính giờ và tiền: [DATA_CARD](../data/DATA_CARD.md).
- **Data thật để dựng tình huống:** 15 review VinWonders Nha Trang trên Traveloka, xem 27/11/2026 ([data-mining.md](../evidence/data-mining.md)), đã bỏ tên. Chỉ lấy *tình huống* (trễ giờ, trò bảo trì, canh giờ show…); giờ, giá, mã trò chuyển sang bộ mô phỏng. Không mang giá hay lịch trong review vào danh mục.
- **Không có:** dữ liệu thời gian xếp hàng, tồn vé hay GPS.

## 2. Bộ câu thử

[benchmark.csv](benchmark.csv): **26 câu** — 10 `thuong` · 13 `kho` · 3 `tu_choi`. **9/26 từ data thật** (`data_that`, mỗi câu ghi mã review), còn lại `tu_viet` có ghi lý do.

| Nhóm | Câu | Nguồn |
|---|---|---|
| CP2 | C01–C12 | 5 câu từ review, còn lại tự viết (lịch đầy đủ, trễ show / giờ đóng, thiếu thông tin, thiếu tiền, từ chối lịch vi phạm) |
| Sau CP2 | C13–C21 | cặp sát biên tự viết (đến cổng 10:50 / 10:51 trước show 11:00, chiều cao 119 / 120 cm, thiếu 1 đồng phụ phí, điểm bắt buộc đã đóng, ưu tiên điểm, đóng hết điểm) |
| 27/11 | C22 | trẻ đi không có người lớn (từ chối bằng code) |
| 27/11 | C23–C26 | chuyển thể từ review R07, R03, R10, R14 |

Mỗi câu có `pass_criterion` đọc output là biết đạt hay không. Không sửa `expected` hay xoá câu trượt sau CP2.

## 3. Metric và cách chấm

[metric_spec.yaml](metric_spec.yaml), chốt ở CP2, không đổi:

| Metric | Đo gì | Chuẩn |
|---|---|---|
| `task_pass` | câu đáp ứng toàn bộ `pass_criterion` / tổng | **≥22/26** (5/6, `spec.md` §7) |
| `route_validity` | lịch dùng mã đúng, không trùng, đủ đi bộ, đúng giờ mở / show, đệm, chiều cao, ngân sách, điểm bắt buộc, điểm đóng | 100% lịch xuất hợp lệ |
| `factual_numbers` | giờ từng điểm và tổng tiền khớp tính lại từ `park.json` | 100% |
| `refusal` | mọi câu `tu_choi` chặn đúng hành động bị dụ | 100% |

**Chấm:** người chấm tay (1 đạt / 0 trượt) chỉ theo chữ của `pass_criterion` + quy tắc DATA_CARD. Hai người chấm độc lập rồi đối chiếu; câu lệch thì đọc lại tiêu chí và thống nhất. Lượt 1 và lượt 2 dùng **cùng cách chấm**. Một bộ kiểm tự động độc lập (tính lại giờ và tiền từ `park.json`) dùng để soát, **không thay** người chấm. Ở CP2, Phương Nam và Bình An chấm thử 5 đầu ra model giả, đồng thuận 5/5.

## 4. Đã chạy gì

| Run ID | Model | Cấu hình | Kết quả (người chấm) | Ghi chú |
|---|---|---|---|---|
| `run-fake` (CP2) | fake | model giả, bộ câu lúc đó | không tính | kiểm khung, chấm thử 5 đầu ra |
| `run-1@20261127-202533` | gemini-3.1-flash-lite | code trước cải tiến (`ffa1586`), 26 câu | **25/26 (96%)** · thuong 10/10 · kho 12/13 · tu_choi 3/3 | Đạt chuẩn; trượt C21 |
| `run-2@20261127-202738` | gemini-3.1-flash-lite | gửi model bản tóm tắt lịch có phút đi bộ, giờ xong, số show (`671f0f9`), 26 câu | **25/26 (96%)** · thuong 10/10 · kho 12/13 · tu_choi 3/3 | Đạt chuẩn; trượt C21; token vào +39% |

- Cả hai lượt: 26/26 câu chạy, 0 lỗi kỹ thuật; kiểm tự động 12/12 lịch hợp lệ và khớp số.
- Chấm tay: Bình An + Tuấn Khanh (thay Phương Nam), đồng thuận 26/26 mỗi lượt — [phiếu lượt 1](phieu-cham-run-1.md) · [phiếu lượt 2](phieu-cham-run-2.md). Số lấy từ `python run.py score eval/run-N.csv`.
- Kết quả từng câu: `eval/run-1.csv`, `eval/run-2.csv` · trace: `traces/run-1.jsonl`, `traces/run-2.jsonl`.

## 5. Lỗi chính

- **C21 (trượt cả hai lượt):** nhóm không có trẻ, mọi điểm đóng → lý do nhắc “chiều cao của bé”. Lỗi câu giải thích trong `explain_no_route`, không làm sai lịch; chưa sửa.
- **Hiểu sở thích (ngoài benchmark):** thử thêm 8 câu sở thích ([explore-preferences.md](explore-preferences.md)) → lượt 1 sai 2/8 (“ít đi bộ, bé nhanh mệt”, “chỉ muốn xem show” nhận lịch nhiều điểm) → lượt 2 sai 0/8. Benchmark không có câu đo phần này nên điểm không đổi.
- **Giới hạn của bộ đo:** ràng buộc cứng do Python kiểm trước khi gọi model, nên benchmark chủ yếu đo **tính hợp lệ**, chưa đo **mức khớp sở thích**. Việc tiếp: thêm câu có tiêu chí kiểm được (vd “ít đi bộ → lịch ít điểm nhất trong các lịch hợp lệ”).
