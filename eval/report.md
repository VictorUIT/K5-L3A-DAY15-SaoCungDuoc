# Báo cáo đánh giá — lượt 1 → một cải tiến → lượt 2

> Điền ở guide bước 4.1. Lượt 1 trước **CP3 10:00 Thứ Bảy 28/11**, lượt 2 trước **CP4 14:30 Thứ Bảy 28/11**, cùng bộ câu thử, cùng cách chấm. Chấm ở rubric R5.
> Số lấy từ `python run.py score eval/run-1.csv` (và `run-2.csv`) sau khi điền cột `pass`. **Kết quả thấp ghi thật vẫn đủ điểm.**
> Không được: sửa chuẩn "đạt", bỏ câu thử trượt, sửa `expected` cho khớp output, sửa kết quả lượt đã chạy.

**Cập nhật 28/11:** cả hai lượt đã chấm tay bởi Bình An và Tuấn Khanh (chấm thay Phương Nam), cùng cách chấm, đồng thuận **26/26 ở mỗi lượt**. C21 chấm 0 ở cả hai lượt (cùng đầu ra). Lượt 1 ban đầu ghi 26/26 do đội trưởng chốt C21 = 1 (số đã nộp ở CP3, kèm ghi chú "tính chặt là 25/26"); khi chấm lượt 2 nhóm thống nhất chấm chặt C21 cho cả hai lượt. Chi tiết: [phiếu lượt 1](phieu-cham-run-1.md) · [phiếu lượt 2](phieu-cham-run-2.md).

**Trạng thái 27/11 tối:** cả hai lượt đã chạy bằng model thật, **chưa có nhãn của người chấm**. Các ô "chờ chấm" điền sau khi Phương Nam và Bình An chấm tay theo [phiếu lượt 1](phieu-cham-run-1.md) và ghi kết quả thống nhất vào cột `pass`, rồi chạy `python3 run.py score`. Phần "kiểm tự động" bên dưới là bộ kiểm độc lập của Sơn (tính lại giờ và tiền từ `park.json`), **không thay cho chấm của người**.

## 1. Kết quả

| Lượt | Run ID | Đạt / tổng | % | thuong | kho | tu_choi | So với chuẩn "đạt" |
|---|---|---|---|---|---|---|---|
| 1 | `run-1@20261127-202533` | 25/26 | 96% | 10/10 | 12/13 | 3/3 | Đạt (≥22/26; trượt C21) |
| 2 | `run-2@20261127-202738` | 25/26 | 96% | 10/10 | 12/13 | 3/3 | Đạt (≥22/26; trượt C21) |

Cả hai lượt: model `gemini-3.1-flash-lite`, 26/26 câu chạy, 0 lỗi kỹ thuật. Lượt 1 chạy bằng code trước cải tiến (commit `ffa1586`), lượt 2 bằng code sau cải tiến, cùng bộ 26 câu. 12/26 câu gọi model; 12 câu Python báo không có lịch trước bước gọi model; 2 câu hỏi lại (C08 thiếu chiều cao, C22 thiếu người lớn).

| Chỉ số (kiểm tự động, người chấm đã xác nhận) | Lượt 1 | Lượt 2 |
|---|---|---|
| Lịch xuất hợp lệ (route_validity) | 12/12 | 12/12 |
| Giờ và tổng tiền khớp tính độc lập (factual_numbers) | 12/12 | 12/12 |
| Câu "không có lịch" mà thật sự không có lịch | 12/12 | 12/12 |
| Token vào / ra cả bộ | 3.674 / 108 | 5.091 / 91 |

Kết quả từng câu: `eval/run-1.csv`, `eval/run-2.csv`. Trace: `traces/run-1.jsonl`, `traces/run-2.jsonl`. Một câu đổi đầu ra giữa hai lượt: C02 (ưu tiên Nhà tranh: Vườn hoa + Nhà tranh → chỉ Nhà tranh), vẫn hợp lệ theo kiểm tự động. Hai lượt chạy trước đó trên bộ 24 câu (chưa chấm) đã được thay bằng hai lượt này sau khi gộp bộ 26 câu của Bình An; bản cũ còn trong commit `ffa1586` và `671f0f9`.

## 2. Lỗi lượt 1 — gom thành nhóm có tên

Kiểm tự động không thấy câu benchmark nào vi phạm giờ, tiền hay ràng buộc. Vì vậy lỗi dưới đây lấy từ **thử thêm ngoài benchmark** bằng cùng model ([explore-preferences.md](explore-preferences.md)) và từ đọc lại đầu ra lượt 1. Người chấm xác nhận: câu benchmark duy nhất trượt ở cả hai lượt là C21.

| Nhóm lỗi | Số câu | Câu |
|---|---|---|
| Sở thích về nhịp độ bị lấn bởi lịch nhiều điểm | 2/8 câu thử sở thích | "ít đi bộ, bé nhanh mệt", "chỉ muốn xem show" |
| Lý do vô nghiệm nói sai đối tượng | 1/26 | C21 |
| Benchmark không phân biệt lịch "khớp sở thích" với lịch "hợp lệ" | cả bộ | C02, C19, C20 chỉ kiểm có điểm được nhắc tên |

**≥3 lỗi cụ thể:**

| Câu | Input | Output | Vì sao sai |
|---|---|---|---|
| Thử ngoài bộ | `giờ=09:00-12:00; lớn=2; trẻ=1; cao=125; đồng=600000; ưu tiên=ít đi bộ, bé nhanh mệt` | Vườn hoa 09:10–09:35 → Nhà tranh 09:45–10:15 → Show chim 11:00–11:20 · 460.000 đ | Chọn lịch nhiều điểm nhất (30 phút đi bộ) trong khi có lịch 1 điểm (10 phút). Gia đình có trẻ dễ mệt nhận đúng lịch họ muốn tránh. |
| Thử ngoài bộ | cùng điều kiện, `ưu tiên=chỉ muốn xem show` | Nhà tranh → Show chim → Vườn hoa · 460.000 đ | Thêm hai điểm không phải show; có lịch chỉ gồm Show chim. |
| C21 | `giờ=09:00-12:00; lớn=2; trẻ=0; đồng=500000; đóng=vuon,nha,tau,chim,nhac` | "Mọi điểm trong danh mục đều đang đóng hoặc chưa hợp chiều cao của bé." | Nhóm không có trẻ nhưng câu trả lời nhắc "chiều cao của bé". Lý do không nêu rõ mọi điểm đang đóng → hai người chấm thống nhất **trượt** ở cả hai lượt. |

Nguyên nhân chung của nhóm lỗi đầu: model nhận danh sách lịch dạng JSON thô, không thấy số phút đi bộ, giờ xong hay lịch nào có show; prompt còn nghiêng về "nhiều điểm hơn".

## 3. Một lần cải tiến

- Nhắm vào nhóm lỗi: **sở thích về nhịp độ bị lấn bởi lịch nhiều điểm** — vì sao là nhóm **đau nhất với người dùng**: người dùng là phụ huynh có trẻ nhỏ; "bé nhanh mệt" mà nhận lịch đi bộ nhiều nhất là đúng cái pain nhóm muốn giải (ghép lịch hợp với cả nhà). Lỗi C21 chỉ sai chữ, không đổi quyết định.
- Đã sửa gì (commit `671f0f9`): `describe()` trong `codebase/agent.py` gửi mỗi lịch thành một dòng có số điểm, phút đi bộ, giờ xong, tổng tiền, số show do Python tính; prompt hệ thống nêu cách hiểu các loại sở thích chung (tên điểm, ít đi bộ, về sớm, chỉ show, không show, tiết kiệm). Không thêm câu nào của benchmark vào prompt. Python vẫn kiểm mọi lịch trước bước chọn.
- Kết quả: nhóm lỗi đó **2/8 → 0/8** câu sai trên bộ thử sở thích ([explore-preferences.md](explore-preferences.md)) · benchmark tổng: **25/26 → 25/26**, không đổi (benchmark chưa có câu đo khớp sở thích nên cải tiến không hiện trong điểm benchmark).
- Câu nào **tốt lên / tệ đi** sau khi sửa: không câu nào đổi đạt ↔ trượt (người chấm). Chỉ C02 đổi đầu ra (Vườn hoa + Nhà tranh → chỉ Nhà tranh, khách ưu tiên Nhà tranh), cả hai lượt đều đạt; C21 trượt ở cả hai lượt (lỗi `explain_no_route`, chưa sửa). Chi phí tệ đi: token vào cả bộ tăng 39% (3.674 → 5.091) vì bản tóm tắt dài hơn ở lịch ngắn.

## 4. Còn lại

- Lỗi chưa sửa + nguy hiểm thế nào: C21 nhắc "chiều cao của bé" khi không có trẻ (gây khó hiểu, không gây sai lịch). Sở thích không có trong dữ liệu (vd "trong nhà", "chỗ mát") không kiểm được vì `park.json` không có thuộc tính này. Benchmark chưa có câu đo mức khớp sở thích, nên cải tiến lượt 2 chưa thể hiện trong điểm benchmark. 
- Nếu có thêm 1 tuần: thêm câu benchmark về sở thích nhịp độ với tiêu chí kiểm được (vd "ít đi bộ → lịch có ít điểm nhất trong các lịch hợp lệ"); rút gọn bản tóm tắt để giảm token; thêm thuộc tính trong nhà/ngoài trời vào dữ liệu sau khi hỏi phụ huynh có cần không; dùng phỏng vấn của Phương Nam để thêm câu có nguồn `nguoi_dung`.
