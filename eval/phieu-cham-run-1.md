# Phiếu chấm lượt 1 · `run-1@20261127-190323`

> Model `gemini-3.1-flash-lite` (thật). Đầu ra lấy nguyên từ [run-1.csv](run-1.csv), trace ở [traces/run-1.jsonl](../traces/run-1.jsonl). Không sửa đầu ra.
> **Cách chấm:** Phương Nam và Bình An mỗi người tự chấm **tay** (không dùng AI), ghi 1 = đạt toàn bộ pass_criterion, 0 = trượt, trước khi xem phiếu người kia. Tính lại giờ và giá theo [DATA_CARD](../data/DATA_CARD.md). Sau khi đối chiếu, ghi kết quả thống nhất vào cột `pass` của `run-1.csv` rồi chạy `python3 run.py score eval/run-1.csv`.

| Câu | Loại | Nam | An | Thống nhất | Ghi chú |
|---|---|---|---|---|---|
| C01 | thuong | | | | |
| C02 | thuong | | | | |
| C03 | thuong | | | | |
| C04 | thuong | | | | |
| C05 | thuong | | | | |
| C06 | kho | | | | |
| C07 | kho | | | | |
| C08 | kho | | | | |
| C09 | kho | | | | |
| C10 | kho | | | | |
| C11 | tu_choi | | | | |
| C12 | tu_choi | | | | |
| C13 | kho | | | | |
| C14 | kho | | | | |
| C15 | kho | | | | |
| C16 | kho | | | | |
| C17 | kho | | | | |
| C18 | kho | | | | |
| C19 | thuong | | | | |
| C20 | thuong | | | | |
| C21 | kho | | | | |
| C22 | tu_choi | | | | |
| C23 | kho | | | | |
| C24 | thuong | | | | |

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
15:10–15:35  Vườn hoa
15:45–16:15  Nhà tranh
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

### C23 · kho

- Đầu vào: `giờ=09:00-12:00; lớn=2; trẻ=1; cao=125; đồng=600000; đóng=tau,nha`
- Tiêu chí: Xuất lịch có ít nhất một điểm; không có Tàu lượn hay Nhà tranh; tổng 460000. Trượt nếu báo không có lịch.

```text
Vịnh Mây · dữ liệu mô phỏng
09:10–09:35  Vườn hoa
11:00–11:20  Show chim
Tổng cho cả nhóm: 460.000 đ
```

### C24 · thuong

- Đầu vào: `giờ=14:00-16:30; lớn=2; trẻ=2; cao=115; đồng=560000; phải có=nhac`
- Tiêu chí: Lịch có Show nhạc 15:00–15:30; không có Tàu lượn; tổng 560000.

```text
Vịnh Mây · dữ liệu mô phỏng
14:10–14:35  Vườn hoa
15:00–15:30  Show nhạc
15:40–16:10  Nhà tranh
Tổng cho cả nhóm: 560.000 đ
```
