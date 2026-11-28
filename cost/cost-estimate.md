# Chi phí khi dùng thật

> Điền ở guide bước 4.2, nộp ở CP4 14:30 Thứ Bảy 28/11. Ôn lại: ngày 13, ngày 1, ngày 14 · lab ngày 13, lab ngày 14. Chấm ở rubric R6.
> Số **không điền tay**: điền `cost/personas.yaml` → `python run.py simulate` → chép bảng trong `cost/simulate-N-summary.md` vào đây.
> Lúc build dùng gói miễn phí vẫn tính theo **giá gói trả phí** — đây là chi phí cho lúc đưa vào dùng thật.

## 1. Đầu vào

- **Persona** (`cost/personas.yaml`): 3 kiểu theo checklist C1 — lập lịch một lần (50%, 2 lượt/phiên), chỉnh trước chuyến (30%, 4 lượt), xếp lại giữa buổi (20%, 3 lượt, câu thường và khó). Mỗi người 1 phiên/tháng. Kiểu persona lấy từ phỏng vấn P1–P3 (P1, P3 chuẩn bị trước; P2 xếp lại giữa buổi khi lỡ show); tỉ trọng 50/30/20 và số lượt hỏi *(tự ước tính)*, khảo sát chưa có kết quả.
- **Số người dùng thật** 3 kịch bản (gia đình dùng trợ lý mỗi tháng ở một khu): thấp 1.265 · cơ sở 6.325 · cao 12.650 = 1% · 5% · 10% *(tỉ lệ dùng tự ước tính)* của ≈126.500 nhóm-lượt gia đình / tháng ở `spec.md` §2 (chuỗi VinWonders 9,11 triệu lượt năm 2025 ÷ 3 người/nhóm × 50% gia đình có trẻ *(tự ước tính)* ÷ 12).
- **Giá** 2 mức model, từ `further-reading/model-prices.csv` của repo đề (BTC tra https://ai.google.dev/gemini-api/docs/pricing ngày 25/11/2026): gemini-3.1-flash-lite vào $0,25 · ra $1,50 / 1M token · gemini-3.8-flash (giá từ 01/01/2027) vào $1,50 · ra $7,50 / 1M token.
- **Tỉ lệ đạt** dùng để tính: **25/26 (96%)** — lượt `run-2@20261127-202738`, chấm tay bởi Bình An và Tuấn Khanh ([phiếu](../eval/phieu-cham-run-2.md)), trượt C21.
- Đo token trên model gemini-3.1-flash-lite, tính giá gemini-3.1-flash-lite và gemini-3.8-flash.

## 2. Kết quả mô phỏng

Lượt mô phỏng: `cost/simulate-2.csv` · run ID `simulate-2@20261128-120240` · 50 phiên · 0 phiên lỗi · `--rate-from eval/run-2.csv --wait 4` · code commit `00e236d` (cùng code lượt 2). Trace: `traces/simulate-2.jsonl`. Bản tóm tắt: [simulate-2-summary.md](simulate-2-summary.md). Lượt cũ `simulate-1` (số người dùng tự ước tính, chưa có tỉ lệ đạt) giữ nguyên để đối chiếu.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| lap_lich_mot_lan | 24 | 2 | 540 | 9 | 1.1 | 5.7 |
| chinh_truoc_chuyen | 14 | 4 | 857 | 15 | 2.1 | 10.6 |
| xep_lai_giua_buoi | 12 | 3 | 748 | 15 | 1.9 | 7.7 |

| Model (giá) | Chi phí / phiên | Chi phí / task thành công | Chi phí / câu hỏi đạt | / tháng — thấp (1.265 người) | / tháng — cơ sở (6.325 người) | / tháng — cao (12.650 người) | / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| gemini-3.1-flash-lite (vào 0.25 · ra 1.5 $/1M) | $0.00019 | $0.00020 | $0.000070 | $0.2367 | $1.18 | $2.37 | $0.00019 |
| gemini-3.8-flash (vào 1.5 · ra 7.5 $/1M) | $0.0011 | $0.0012 | $0.00041 | $1.40 | $6.99 | $13.97 | $0.0011 |

Chi phí / task thành công = chi phí / phiên ÷ tỉ lệ đạt 25/26 — **không coi như đạt 100%**. Token đo trên gemini-3.1-flash-lite; dòng gemini-3.8-flash là đo trên gemini-3.1-flash-lite, tính giá gemini-3.8-flash (bộ tách token khác thì số thật có thể lệch).

**Giới hạn của mô phỏng này:** đầu vào lấy từ benchmark (dòng tên=giá trị), nên chưa tính bước rút điều kiện từ câu chat mà web demo dùng. Đo thử trên web ngày 27/11: một tin chat đủ điều kiện gọi model 2 lần, 1.821 token vào / 103 ra, so với 994 / 6 khi gửi cùng điều kiện dạng tên=giá trị. Vì vậy chi phí thật của bản chatbox **khoảng gấp 2–3 lần** bảng trên *(ước tính từ một lần đo, cần mô phỏng lại với câu chat)*.

## 3. So với impact

- Impact / người / tháng (`spec.md` §2): khoảng **17 phút / gia đình / tháng** (0,33 lần đi / tháng × (45 phút chuẩn bị + 5 phút xếp lại), trung vị 3 phỏng vấn — chưa phải tỉ lệ chung). Đây là phút gia đình đang bỏ ra, không phải phút bản chạy thử chắc chắn tiết kiệm được.
- Chi phí / người / tháng (cơ sở, gemini-3.1-flash-lite): **$0,00019** (bản tên=giá trị); khoảng $0,0005 nếu tính bước chat *(ước tính gấp 2–3 lần)*. Model đắt hơn (gemini-3.8-flash): $0,0011.
- **Kết luận một dòng — đáng làm không:** đáng làm về chi phí — kịch bản cao (12.650 gia đình) với model đắt hơn và nhân 3 cho bước chat vẫn khoảng $42/tháng, trong khi mỗi gia đình bỏ ra ~17 phút/tháng; rủi ro chính không phải chi phí mà là impact mới có từ 3 phỏng vấn và tỉ lệ dùng tự ước tính.

## 4. *(Muốn sâu hơn, không bắt buộc)*

- Cần gạt lớn nhất là độ dài prompt chọn lịch: lượt 2 tăng token vào 39% so với lượt 1 vì bản tóm tắt dài hơn; khung 09:00–12:00 có 34 lịch ứng viên (khoảng 3.600 token vào mỗi lần chọn), cả ngày 09:00–17:30 có 73 lịch. Rút gọn bản tóm tắt hoặc chỉ gửi 20 lịch tốt nhất theo luật sẽ giảm mạnh.
- Chi phí ngoài model: hosting Streamlit Community Cloud gói miễn phí cho demo; dùng thật cần máy chủ riêng (chưa ước tính).
