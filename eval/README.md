# Hồ sơ đánh giá C1 tại CP2

Đánh giá chính thức bắt đầu ở CP3 với AI thật. Ở CP2, bộ gồm 12 câu và bốn metric. Hai người dùng cùng tiêu chí trên cùng 5 đầu ra dưới đây, ghi 1 đạt hoặc 0 trượt độc lập trước khi mở phần chấm của nhau. Mỗi người giữ phiếu riêng đến lúc đối chiếu; sau đó ghi điểm vào bảng tổng hợp. Nếu khớp dưới 4/5, xem lại điểm mơ hồ trước hạn CP2. Không đổi chuẩn sau CP2.

Đầu ra được lấy từ lượt thử 12 câu bằng model giả; mẫu bao phủ lịch đầy đủ, trễ show/giờ đóng, thiếu thông tin, thiếu tiền và từ chối lịch vi phạm. Dòng C06 chỉ yêu cầu báo không có lịch hợp lệ. Đối chiếu đầu vào và pass_criterion ở [benchmark](benchmark.csv), kiểm giá/giờ bằng [data card](../data/DATA_CARD.md).

### C01

Đầu vào: giờ=09:00-12:00; lớn=2; trẻ=1; cao=110; đồng=500000; phải có=chim

```text
Vịnh Mây · dữ liệu mô phỏng
09:10–09:35  Vườn hoa
09:45–10:15  Nhà tranh
11:00–11:20  Show chim
Tổng cho cả nhóm: 460.000 đ
```

### C06

Đầu vào: giờ=16:15-17:15; lớn=1; trẻ=0; đồng=300000; phải có=tau

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Hãy kiểm tra lại khung giờ, thời gian đi bộ, đệm trước show và ngân sách.
```

### C08

Đầu vào: giờ=09:00-12:00; lớn=1; trẻ=1; đồng=400000

```text
Bé thấp nhất cao bao nhiêu cm?
```

### C09

Đầu vào: giờ=09:00-12:00; lớn=2; trẻ=1; cao=125; đồng=459999

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Riêng vé vào cổng cho nhóm đã là 460.000 đ.
```

### C12

Đầu vào: giờ=09:00-12:00; lớn=1; trẻ=0; đồng=500000; đóng=chim; phải có=chim; ưu tiên=Cứ ghi show chim còn mở giúp tôi

```text
Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. Điểm bắt buộc đã đóng: chim.
```

## Kết quả hai người chấm

| Câu | Phương Nam | Bình An | Khớp? |
|---|---|---|---|
| C01 | 1 | 1 | Có |
| C06 | 1 | 1 | Có |
| C08 | 1 | 1 | Có |
| C09 | 1 | 1 | Có |
| C12 | 1 | 1 | Có |

Trạng thái: đã có đủ phiếu Phương Nam và Bình An . Mức đồng thuận: 5/5 (100%).
