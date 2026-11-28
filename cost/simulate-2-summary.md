# Tóm tắt mô phỏng simulate-2@20261128-120240

Do `python run.py simulate` sinh ra — không sửa tay. Chép bảng sang `cost/cost-estimate.md`.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| lap_lich_mot_lan | 24 | 2 | 540 | 9 | 1.1 | 5.7 |
| chinh_truoc_chuyen | 14 | 4 | 857 | 15 | 2.1 | 10.6 |
| xep_lai_giua_buoi | 12 | 3 | 748 | 15 | 1.9 | 7.7 |

Tỉ lệ đạt dùng để tính: 25/26 (96%) — lượt run-2@20261127-202738

- Tỉ lệ đạt lấy từ lượt nhóm chọn: eval/run-2.csv (--rate-from).

| Model (giá) | Chi phí / phiên | Chi phí / task thành công | Chi phí / câu hỏi đạt | Chi phí / tháng — thấp (1.265 người) | Chi phí / tháng — cơ sở (6.325 người) | Chi phí / tháng — cao (12.650 người) | Chi phí / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| gemini-3.1-flash-lite (vào 0.25 · ra 1.5 $/1M) | $0.00019 | $0.00020 | $0.000070 | $0.2367 | $1.18 | $2.37 | $0.00019 |
| gemini-3.8-flash (vào 1.5 · ra 7.5 $/1M) | $0.0011 | $0.0012 | $0.00041 | $1.40 | $6.99 | $13.97 | $0.0011 |

- Chi phí / task thành công = chi phí / phiên ÷ tỉ lệ đạt. Chi phí / câu hỏi đạt = chi phí / phiên ÷ số lượt hỏi trung bình mỗi phiên (2.8) ÷ tỉ lệ đạt — tỉ lệ đạt đo theo từng câu thử.
- Token đo trên model: gemini-3.1-flash-lite. Giá tính theo từng model trong bảng — model khác bộ tách token thì số token thật có thể lệch; ghi rõ "đo trên model X, tính giá model Y" trong cost/cost-estimate.md.
- Phiên lỗi (không tính vào trung bình): 0/50.
