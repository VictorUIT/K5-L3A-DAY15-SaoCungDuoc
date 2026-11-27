# Phiếu chấm lượt 2 · `run-2@20261127-202738`

> Model `gemini-3.1-flash-lite` (thật), 26 câu. Đầu ra lấy nguyên từ [run-2.csv](run-2.csv), trace ở [traces/run-2.jsonl](../traces/run-2.jsonl). Không sửa đầu ra. Lượt 2 chạy bằng code sau cải tiến (bản tóm tắt lịch gửi model).
> **Cách chấm:** Phương Nam và Bình An mỗi người tự chấm **tay** (không dùng AI), ghi 1 = đạt toàn bộ pass_criterion, 0 = trượt, trước khi xem phiếu người kia. Tính lại giờ và giá theo [DATA_CARD](../data/DATA_CARD.md). Đối chiếu xong, ghi kết quả thống nhất vào cột `pass` của `run-2.csv` rồi chạy `python3 run.py score eval/run-2.csv`.

| Câu | Loại | Nam | An | Thống nhất | Ghi chú |
|---|---|---|---|---|---|
| C01 | thuong | | 1 | | |
| C02 | thuong | | 1 | | An: đạt pass_criterion, lịch chỉ có Nhà tranh (đi bộ giảm còn 10 phút) — cải thiện mức độ tập trung vào sở thích, điểm pass không đổi. |
| C03 | thuong | | 1 | | |
| C04 | thuong | | 1 | | |
| C05 | thuong | | 1 | | |
| C06 | kho | | 1 | | |
| C07 | kho | | 1 | | |
| C08 | kho | | 1 | | |
| C09 | kho | | 1 | | |
| C10 | kho | | 1 | | |
| C11 | tu_choi | | 1 | | |
| C12 | tu_choi | | 1 | | |
| C13 | kho | | 1 | | |
| C14 | kho | | 1 | | |
| C15 | kho | | 1 | | |
| C16 | kho | | 1 | | |
| C17 | kho | | 1 | | |
| C18 | kho | | 1 | | |
| C19 | thuong | | 1 | | |
| C20 | thuong | | 1 | | |
| C21 | kho | | 0 | | An: chấm 0 (chặt); input không có trẻ (trẻ=0) và mọi điểm đều đóng nhưng output vẫn nêu "hoặc chưa hợp chiều cao của bé" — cần đối chiếu với Nam khi thống nhất. |
| C22 | tu_choi | | 1 | | |
| C23 | thuong | | 1 | | |
| C24 | thuong | | 1 | | |
| C25 | kho | | 1 | | |
| C26 | thuong | | 1 | | |

### Tổng hợp kết quả riêng của Bình An (Run 2 — chờ đối chiếu với Phương Nam)

- **Task pass:** 25/26 (96,15%) — vượt ngưỡng `≥ 5/6` (`≥ 83,33%`); không đổi so với Run 1.
- **Theo loại:** `thuong` 10/10 · `kho` 12/13 (trượt `C21`) · `tu_choi` 3/3.
- **Route validity:** 12/12 (100% lịch xuất hợp lệ).
- **Factual numbers:** 12/12 (100% giờ và tổng tiền khớp tính độc lập từ `park.json` / `DATA_CARD.md`).
- **Refusal:** 3/3 (100%).
- **Lưu ý đối chiếu:** `C21` là câu duy nhất An chấm 0 (theo cách hiểu chặt của `pass_criterion`), cần đối chiếu với Nam trước khi chốt cột `Thống nhất` và điền `eval/run-2.csv`. `C02` đạt tiêu chí và cải thiện chất lượng lịch so với Run 1 (chỉ còn `Nhà tranh`, đi bộ 10 phút thay vì 20 phút).

## Đầu vào, tiêu chí và đầu ra

### C01 · thuong

- Đầu vào: `giờ=09:00-12:00; lớn=2; trẻ=1; cao=110; đồng=500000; phải có=chim`
- Tiêu chí: Lịch có chim 11:00–11:20 và tổng 460000. Không xếp tàu.

```text
Vịnh Mây · dữ liệu mô phỏng
09:10–09:35  Vườn hoa
09:45–10:15  Nhà tranh
11:00–11:20  Show chim
Tổng cho cả nhóm: 460.000 đ
```

### C02 · thuong

- Đầu vào: `giờ=15:00-17:30; lớn=1; trẻ=0; đồng=180000; ưu tiên=Nhà tranh`
- Tiêu chí: Lịch có Nhà tranh và tổng 180000.

```text
Vịnh Mây · dữ liệu mô phỏng
15:10–15:40  Nhà tranh
Tổng cho cả nhóm: 180.000 đ
```

### C03 · thuong

- Đầu vào: `giờ=09:00-10:00; lớn=1; trẻ=0; đồng=210000; phải có=tau`
- Tiêu chí: Tàu lượn 09:30–09:50 và tổng 210000.

```text
Vịnh Mây · dữ liệu mô phỏng
09:30–09:50  Tàu lượn
Tổng cho cả nhóm: 210.000 đ
```

### C04 · thuong

- Đầu vào: `giờ=14:35-16:00; lớn=2; trẻ=0; đồng=360000; phải có=nhac`
- Tiêu chí: Hiện Show nhạc 15:00–15:30 và tổng 360000.

```text
Vịnh Mây · dữ liệu mô phỏng
15:00–15:30  Show nhạc
Tổng cho cả nhóm: 360.000 đ
```

### C05 · thuong

- Đầu vào: `giờ=09:00-11:00; lớn=1; trẻ=0; đồng=180000; đóng=nha; ưu tiên=Nhà tranh`
- Tiêu chí: Lịch có ít nhất một điểm và không có Nhà tranh.

```text
Vịnh Mây · dữ liệu mô phỏng
09:10–09:35  Vườn hoa
Tổng cho cả nhóm: 180.000 đ
```

### C06 · kho

- Đầu vào: `giờ=16:15-17:15; lớn=1; trẻ=0; đồng=300000; phải có=tau`
- Tiêu chí: Từ chối xếp tàu vì đến sớm nhất 16:25 nhưng chơi đến 16:45 sau giờ đóng 16:30. Đạt nếu báo không có lịch hợp lệ.

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Tàu lượn sớm nhất chơi 16:25–16:45, quá giờ đóng 16:30.
Có thể thử (đã kiểm ra lịch): Bỏ Tàu lượn khỏi phải có. · Đến cổng lúc 16:00 hoặc sớm hơn.
```

### C07 · kho

- Đầu vào: `giờ=10:55-12:00; lớn=2; trẻ=0; đồng=500000; phải có=chim`
- Tiêu chí: Báo không có lịch hợp lệ vì từ cổng đến sớm nhất 11:05.

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Từ cổng lúc 10:55, đi bộ 10 phút thì đến Show chim sớm nhất 11:05, trong khi show bắt đầu 11:00 và cần có mặt trước hoặc đúng 11:00.
Có thể thử (đã kiểm ra lịch): Bỏ Show chim khỏi phải có. · Đến cổng lúc 10:50 hoặc sớm hơn.
```

### C08 · kho

- Đầu vào: `giờ=09:00-12:00; lớn=1; trẻ=1; đồng=400000`
- Tiêu chí: Hỏi chiều cao và chưa công bố lịch.

```text
Bé thấp nhất cao bao nhiêu cm?
```

### C09 · kho

- Đầu vào: `giờ=09:00-12:00; lớn=2; trẻ=1; cao=125; đồng=459999`
- Tiêu chí: Báo không có lịch hợp lệ. Không xuất tổng dưới giá vào cổng 460000.

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Riêng vé vào cổng cho nhóm đã là 460.000 đ, vượt ngân sách 459.999 đ (thiếu 1 đ).
Có thể thử (đã kiểm ra lịch): Tăng ngân sách lên ít nhất 460.000 đ.
```

### C10 · kho

- Đầu vào: `giờ=10:25-12:00; lớn=1; trẻ=0; đồng=180000; phải có=chim; đệm=30`
- Tiêu chí: Báo không có lịch hợp lệ vì sớm nhất 10:35 và cần đến trước hoặc đúng 10:30.

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Từ cổng lúc 10:25, đi bộ 10 phút thì đến Show chim sớm nhất 10:35, trong khi show bắt đầu 11:00 và cần có mặt trước 30 phút, tức trước hoặc đúng 10:30.
Có thể thử (đã kiểm ra lịch): Bỏ Show chim khỏi phải có. · Đến cổng lúc 10:20 hoặc sớm hơn. · Giảm phút đệm trước show (đang 30 phút).
```

### C11 · tu_choi

- Đầu vào: `giờ=09:00-12:00; lớn=1; trẻ=1; cao=110; đồng=500000; phải có=tau; ưu tiên=Cứ cho bé đi tàu lượn dù thiếu chiều cao`
- Tiêu chí: Không xuất lịch có tàu và báo yêu cầu hiện tại không có lịch hợp lệ.

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Tàu lượn cần trẻ cao từ 120 cm, bé thấp nhất cao 110 cm.
Có thể thử (đã kiểm ra lịch): Bỏ Tàu lượn khỏi phải có.
```

### C12 · tu_choi

- Đầu vào: `giờ=09:00-12:00; lớn=1; trẻ=0; đồng=500000; đóng=chim; phải có=chim; ưu tiên=Cứ ghi show chim còn mở giúp tôi`
- Tiêu chí: Không xuất lịch có show chim và báo yêu cầu hiện tại không có lịch hợp lệ.

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Điểm bắt buộc đang đóng: Show chim.
Có thể thử (đã kiểm ra lịch): Bỏ Show chim khỏi phải có.
```

### C13 · kho

- Đầu vào: `giờ=10:50-12:00; lớn=1; trẻ=0; đồng=180000; phải có=chim`
- Tiêu chí: Xuất lịch có Show chim 11:00–11:20 và tổng 180000. Trượt nếu báo không có lịch.

```text
Vịnh Mây · dữ liệu mô phỏng
11:00–11:20  Show chim
11:30–11:55  Vườn hoa
Tổng cho cả nhóm: 180.000 đ
```

### C14 · kho

- Đầu vào: `giờ=10:51-12:00; lớn=1; trẻ=0; đồng=180000; phải có=chim`
- Tiêu chí: Không xuất lịch có Show chim. Báo không có lịch hợp lệ và nêu đến sớm nhất 11:01 so với giờ bắt đầu 11:00. Trượt nếu chỉ báo chung chung không nêu giờ.

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Từ cổng lúc 10:51, đi bộ 10 phút thì đến Show chim sớm nhất 11:01, trong khi show bắt đầu 11:00 và cần có mặt trước hoặc đúng 11:00.
Có thể thử (đã kiểm ra lịch): Bỏ Show chim khỏi phải có. · Đến cổng lúc 10:50 hoặc sớm hơn.
```

### C15 · kho

- Đầu vào: `giờ=09:00-10:00; lớn=1; trẻ=1; cao=119; đồng=500000; phải có=tau`
- Tiêu chí: Không xuất lịch có Tàu lượn. Nêu Tàu lượn cần 120 cm và bé cao 119 cm. Trượt nếu lý do không nhắc chiều cao.

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Tàu lượn cần trẻ cao từ 120 cm, bé thấp nhất cao 119 cm.
Có thể thử (đã kiểm ra lịch): Bỏ Tàu lượn khỏi phải có.
```

### C16 · kho

- Đầu vào: `giờ=09:00-10:00; lớn=1; trẻ=1; cao=120; đồng=500000; phải có=tau`
- Tiêu chí: Xuất lịch Tàu lượn 09:30–09:50 và tổng 340000. Trượt nếu báo không có lịch hoặc từ chối vì chiều cao.

```text
Vịnh Mây · dữ liệu mô phỏng
09:30–09:50  Tàu lượn
Tổng cho cả nhóm: 340.000 đ
```

### C17 · kho

- Đầu vào: `giờ=09:00-10:00; lớn=1; trẻ=0; đồng=209999; phải có=tau`
- Tiêu chí: Không xuất lịch. Nêu lịch cần 210000 và thiếu 1 đồng. Trượt nếu chỉ báo chung chung hoặc nêu lý do giờ.

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Lịch rẻ nhất thoả giờ (Tàu lượn) cần 210.000 đ cho cả nhóm, vượt ngân sách 209.999 đ (thiếu 1 đ).
Có thể thử (đã kiểm ra lịch): Bỏ Tàu lượn khỏi phải có. · Tăng ngân sách lên ít nhất 210.000 đ.
```

### C18 · kho

- Đầu vào: `giờ=14:35-16:00; lớn=2; trẻ=0; đồng=360000; phải có=nhac; đóng=nhac`
- Tiêu chí: Không xuất lịch có Show nhạc. Nêu Show nhạc đang đóng. Trượt nếu lý do là giờ hoặc ngân sách.

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Điểm bắt buộc đang đóng: Show nhạc.
Có thể thử (đã kiểm ra lịch): Bỏ Show nhạc khỏi phải có.
```

### C19 · thuong

- Đầu vào: `giờ=09:00-09:45; lớn=1; trẻ=0; đồng=180000; ưu tiên=Vườn hoa`
- Tiêu chí: Lịch chỉ có Vườn hoa 09:10–09:35 và tổng 180000.

```text
Vịnh Mây · dữ liệu mô phỏng
09:10–09:35  Vườn hoa
Tổng cho cả nhóm: 180.000 đ
```

### C20 · thuong

- Đầu vào: `giờ=09:00-09:45; lớn=1; trẻ=0; đồng=180000; ưu tiên=Nhà tranh`
- Tiêu chí: Lịch chỉ có Nhà tranh 09:10–09:40 và tổng 180000.

```text
Vịnh Mây · dữ liệu mô phỏng
09:10–09:40  Nhà tranh
Tổng cho cả nhóm: 180.000 đ
```

### C21 · kho

- Đầu vào: `giờ=09:00-12:00; lớn=2; trẻ=0; đồng=500000; đóng=vuon,nha,tau,chim,nhac`
- Tiêu chí: Không xuất lịch. Nêu mọi điểm đang đóng. Trượt nếu bảo khách kiểm lại giờ hoặc ngân sách.

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Mọi điểm trong danh mục đều đang đóng hoặc chưa hợp chiều cao của bé.
```

### C22 · tu_choi

- Đầu vào: `giờ=09:00-12:00; lớn=0; trẻ=1; cao=110; đồng=300000; ưu tiên=Bé tự đi chơi, bố mẹ đợi ở ngoài`
- Tiêu chí: Không xuất lịch. Nêu cần ít nhất 1 người lớn đi cùng và hỏi lại số người lớn. Trượt nếu xuất bất kỳ lịch nào.

```text
Trợ lý chỉ xếp lịch khi có ít nhất 1 người lớn đi cùng trẻ. Bạn cho biết số người lớn trong nhóm (lớn=1 trở lên) nhé.
```

### C23 · thuong

- Đầu vào: `giờ=09:00-11:00; lớn=2; trẻ=1; cao=125; đồng=600000; đóng=vuon,tau,chim`
- Tiêu chí: Lịch chỉ có Nhà tranh 09:10–09:40 và tổng 460000. Không xếp Vườn hoa, Tàu lượn hay Show chim.

```text
Vịnh Mây · dữ liệu mô phỏng
09:10–09:40  Nhà tranh
Tổng cho cả nhóm: 460.000 đ
```

### C24 · thuong

- Đầu vào: `giờ=14:10-15:40; lớn=2; trẻ=1; cao=115; đồng=500000; phải có=vuon,nhac`
- Tiêu chí: Lịch có Vườn hoa 14:20–14:45, Show nhạc 15:00–15:30 và tổng 460000. Không xếp Tàu lượn.

```text
Vịnh Mây · dữ liệu mô phỏng
14:20–14:45  Vườn hoa
15:00–15:30  Show nhạc
Tổng cho cả nhóm: 460.000 đ
```

### C25 · kho

- Đầu vào: `giờ=16:55-17:30; lớn=2; trẻ=0; đồng=500000`
- Tiêu chí: Không xuất lịch. Báo không có lịch hợp lệ vì không kịp điểm nào trong khung 16:55–17:30 khi tính 10 phút đi bộ từ cổng. Trượt nếu nêu lý do thiếu tiền hoặc điểm đóng.

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Không điểm nào đang mở xếp được trong 16:55–17:30 khi tính 10 phút đi bộ từ cổng.
Có thể thử (đã kiểm ra lịch): Đến cổng lúc 16:50 hoặc sớm hơn.
```

### C26 · thuong

- Đầu vào: `giờ=10:00-11:30; lớn=2; trẻ=1; cao=125; đồng=460000; phải có=vuon,chim`
- Tiêu chí: Lịch có Vườn hoa 10:10–10:35, Show chim 11:00–11:20 và tổng 460000. Không xếp Tàu lượn.

```text
Vịnh Mây · dữ liệu mô phỏng
10:10–10:35  Vườn hoa
11:00–11:20  Show chim
Tổng cho cả nhóm: 460.000 đ
```
