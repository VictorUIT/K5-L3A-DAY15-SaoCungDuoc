# SaoCungDuoc · Lịch gia đình tại khu vui chơi

## Bản chạy CP2 của nhóm Sao Cũng Được

[Canvas](canvas.md) · [Thiết kế và chuẩn đạt §7](spec.md) · [12 câu thử](eval/benchmark.csv) · [Metric](eval/metric_spec.yaml) · [Data card](data/DATA_CARD.md) · [Bằng chứng ban đầu](evidence/data-mining.md) · [Phiếu chấm chéo](eval/README.md).

Chạy ngay tại thư mục gốc bằng Python, dùng thư viện chuẩn. CP2 dùng model giả mặc định và khu vui chơi Vịnh Mây mô phỏng. Mỗi yêu cầu là một dòng độc lập. Có thể đổi điều kiện rồi gửi lại dòng đầy đủ.

```sh
python3 run.py
```

```text
giờ=09:00-12:00; lớn=2; trẻ=1; cao=110; đồng=500000; phải có=chim
```

Bắt buộc: giờ đến–giờ kết thúc, số người lớn, số trẻ và ngân sách bằng đồng. Nếu có trẻ, nhập chiều cao thấp nhất bằng cm. Có thể nhập thêm `ưu tiên=Nhà tranh`, `phải có=chim,vuon`, `đóng=tau` hoặc `đệm=15` (phút đến trước show). Mã điểm: `vuon` Vườn hoa, `nha` Nhà tranh, `tau` Tàu lượn, `chim` Show chim, `nhac` Show nhạc. Bản này dùng trường có nhãn cho các ràng buộc cứng.

- `python3 run.py check` kiểm cấu trúc CP2 và nêu thêm các yêu cầu CP3.
- `python3 run.py eval --try 12` đi qua cùng luồng demo và ghi kết quả thử trong `eval/run-try.csv`. Model giả có 0 token. Lượt đánh giá chính thức bắt đầu ở CP3.
- Codex hỗ trợ dựng khung, đối chiếu nguồn và kiểm lệnh. Nam và An phụ trách đối chiếu dữ liệu và chấm độc lập. [Phân công](TEAMS.md)


[Phân công CP1](TEAMS.md) · [Sử dụng AI](docs/ai-usage.md) · [Hướng dẫn nối model cho CP3](docs/connect-model.md)
