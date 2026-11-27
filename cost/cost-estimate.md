# Chi phí khi dùng thật

> Điền ở guide bước 4.2, nộp ở CP4 14:30 Thứ Bảy 28/11. Ôn lại: ngày 13, ngày 1, ngày 14 · lab ngày 13, lab ngày 14. Chấm ở rubric R6.
> Số **không điền tay**: điền `cost/personas.yaml` → `python run.py simulate` → chép bảng trong `cost/simulate-N-summary.md` vào đây.
> Lúc build dùng gói miễn phí vẫn tính theo **giá gói trả phí** — đây là chi phí cho lúc đưa vào dùng thật.

## 1. Đầu vào

- **Persona** (`cost/personas.yaml`): 3 kiểu theo checklist C1 — lập lịch một lần (50%, 2 lượt/phiên), chỉnh trước chuyến (30%, 4 lượt), xếp lại giữa buổi (20%, 3 lượt, câu thường và khó). Mỗi người 1 phiên/tháng. Nguồn: *(tự ước tính)*, chờ khảo sát câu 9, 11 và phỏng vấn P1–P3 của Phương Nam.
- **Số người dùng thật** 3 kịch bản (gia đình dùng trợ lý mỗi tháng ở một khu): thấp 500 · cơ sở 2.000 · cao 5.000. Nguồn: *(tự ước tính)*; chưa có số khách công khai đã kiểm cho một khu.
- **Giá** 2 mức model, từ `further-reading/model-prices.csv` của repo đề (BTC tra https://ai.google.dev/gemini-api/docs/pricing ngày 25/11/2026): gemini-3.1-flash-lite vào $0,25 · ra $1,50 / 1M token · gemini-3.8-flash (giá từ 01/01/2027) vào $1,50 · ra $7,50 / 1M token.
- **Tỉ lệ đạt** dùng để tính: **chờ chấm** — lượt `run-2@20261127-202738` chưa có nhãn của người chấm.
- Đo token trên model gemini-3.1-flash-lite, tính giá gemini-3.1-flash-lite và gemini-3.8-flash.

## 2. Kết quả mô phỏng

Lượt mô phỏng: `cost/simulate-1.csv` · run ID `simulate-1@20261127-191410` · 50 phiên · seed 42 · 0 phiên lỗi · code commit `671f0f9` (lượt 2). Trace: `traces/simulate-1.jsonl`.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên |
|---|---:|---:|---:|---:|---:|
| lap_lich_mot_lan | 23 | 2 | 469 | 8 | 1.0 |
| chinh_truoc_chuyen | 17 | 4 | 1269 | 18 | 2.2 |
| xep_lai_giua_buoi | 10 | 3 | 641 | 14 | 1.6 |

| Model | Chi phí / phiên | Chi phí / task thành công | / tháng — thấp | / tháng — cơ sở | / tháng — cao | / người / tháng (cơ sở) |
|---|---|---|---|---|---|---|
| gemini-3.1-flash-lite | $0.00021 | chờ tỉ lệ đạt | $0.10 | $0.41 | $1.02 | $0.00020 |
| gemini-3.8-flash | $0.0013 | chờ tỉ lệ đạt | $0.60 | $2.41 | $6.03 | $0.0012 |

Chi phí / task thành công = chi phí trung bình mỗi phiên ÷ tỉ lệ đạt — **không coi như đạt 100%**. Sau khi Nam và An chấm `run-2.csv` và chạy `python3 run.py score eval/run-2.csv`, chạy lại `python3 run.py simulate --rate-from eval/run-2.csv --wait 4` rồi chép bảng mới vào đây.

**Giới hạn của mô phỏng này:** đầu vào lấy từ benchmark (dòng tên=giá trị), nên chưa tính bước rút điều kiện từ câu chat mà web demo dùng. Đo thử trên web ngày 27/11: một tin chat đủ điều kiện gọi model 2 lần, 1.821 token vào / 103 ra, so với 994 / 6 khi gửi cùng điều kiện dạng tên=giá trị. Vì vậy chi phí thật của bản chatbox **khoảng gấp 2–3 lần** bảng trên *(ước tính từ một lần đo, cần mô phỏng lại với câu chat)*.

## 3. So với impact

- Impact / người / tháng (`spec.md` §2): **chờ số** — cần số lần phải xếp lịch/tháng và phút mất/lần từ khảo sát, phỏng vấn.
- Chi phí / người / tháng (cơ sở, model gemini-3.1-flash-lite): $0,0002 (bản tên=giá trị); khoảng $0,0005 nếu tính bước chat *(ước tính)*.
- **Kết luận một dòng — đáng làm không:** chi phí model không phải điểm nghẽn: kể cả model đắt hơn (gemini-3.8-flash) và nhân 3 cho bước chat, kịch bản cao vẫn dưới $20/tháng. Quyết định đáng làm hay không phụ thuộc vào impact (số phút gia đình thật sự mất), đang chờ bằng chứng.

## 4. *(Muốn sâu hơn, không bắt buộc)*

- Cần gạt lớn nhất là độ dài prompt chọn lịch: lượt 2 tăng token vào 39% so với lượt 1 vì bản tóm tắt dài hơn; khung 09:00–12:00 có 34 lịch ứng viên (khoảng 3.600 token vào mỗi lần chọn), cả ngày 09:00–17:30 có 73 lịch. Rút gọn bản tóm tắt hoặc chỉ gửi 20 lịch tốt nhất theo luật sẽ giảm mạnh.
- Chi phí ngoài model: hosting Streamlit Community Cloud gói miễn phí cho demo; dùng thật cần máy chủ riêng (chưa ước tính).
