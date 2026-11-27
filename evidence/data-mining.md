# Quan sát ban đầu cho CP2

Nguồn đã đọc ngày 27/11/2026: [Traveloka, đánh giá VinWonders Nha Trang](https://www.traveloka.com/en-en/user/review/consumption/EXPERIENCE/ATTRACTIONS/5981189656926). Bản tiếng Anh, sắp theo Most Recent, With Text, All Ratings. Trang báo tổng cộng 21 đánh giá; bản trang công cụ đọc được **15 đoạn có nội dung**. Mẫu số dưới đây là 15. Tên và tài khoản đã bỏ. Trích R15 theo bản tiếng Anh hiển thị trên trang.

Đây là lượt đọc thăm dò. Nhãn được xác định sau khi đọc trang. Đếm 1 khi khách kể hoặc khuyên chủ động canh giờ hoạt động/show để xếp lịch. Chỉ khen show, phàn nàn xếp hàng hoặc chậm đổi vé được ghi 0. Thứ tự và chủ đề dưới đây giúp kiểm lại kết quả dù trang có thêm review.

| ID | Chủ đề của review, diễn giải ngắn | Canh giờ |
|---|---|---|
| R01 | Chờ lâu, trò bảo trì | 0 |
| R02 | Nhân viên hỗ trợ | 0 |
| R03 | Combo và xem Tata Show | 0 |
| R04 | Khuyên đến đúng đầu khung vé chiều vì nhiều trò đóng sớm | 1 |
| R05 | Một ngày đi chơi vui | 0 |
| R06 | Đáng tiền | 0 |
| R07 | Nhiều trò đóng, phải xếp hàng | 0 |
| R08 | Đổi vé gặp lỗi khiến nhóm vào muộn | 0 |
| R09 | Gia đình thích biểu diễn nhạc nước | 0 |
| R10 | Khó tìm quầy nhận voucher | 0 |
| R11 | Nhân viên, trò chơi | 0 |
| R12 | Giá ưu đãi | 0 |
| R13 | Hôm đi ít đông | 0 |
| R14 | Giá hợp lý | 0 |
| R15 | Gia đình chụp lịch show, xem trò bảo trì và khuyên đến sớm | 1 |

Kết quả = (R04 + R15) / 15 = **2/15, khoảng 13,3% của mẫu thăm dò**. R15 viết “Making sure you take photos of the show timetables”. Chưa biết hai người này tốn bao nhiêu phút hoặc bao nhiêu gia đình khác gặp vấn đề. R04 và R15 là hai diễn đạt liên quan xếp lịch, không phải hai ca xác nhận lỡ show.

Bước tiếp theo trước CP3: chốt quy tắc trên và chụp mốc thời gian trước khi lấy mẫu mới (30 review có chữ liên tiếp, mọi mức sao, không lọc từ khóa; loại trùng và phản hồi của doanh nghiệp). Phương Nam hỏi phụ huynh ngoài nhóm về lần đi trong tháng qua và thời gian thực sự mất để xếp lại lịch. Mỗi cuộc một ghi chép đã bỏ tên; ghi cả trường hợp lịch ban đầu dùng được.

## Lấy mẫu 30 review Google Maps · chốt TRƯỚC khi đọc

> Soạn lúc 27/11/2026 21:50 (Sơn soạn, Claude Code hỗ trợ). **Trạng thái: chờ Phương Nam duyệt.** Phương Nam duyệt rồi commit, giờ commit là mốc chốt. Chưa ai đọc review nào của mẫu này lúc soạn. Sau mốc chốt không đổi quy tắc; nếu buộc phải đổi (ví dụ trang không đủ 30 review có chữ), ghi giờ, nội dung đổi và lý do ngay dưới mục này, không xoá dòng cũ.

**Vì sao đổi nguồn.** Trang Traveloka ở lượt thăm dò chỉ có 21 review (15 đọc được), không đủ 30. Mẫu mới lấy từ một nguồn khác để không trùng 15 review đã đọc.

**Nguồn và cách chọn mẫu**
- Nguồn: Google Maps, địa điểm **VinWonders Nha Trang**, tab Bài đánh giá, sắp xếp **Mới nhất**. Ghi lại link địa điểm và giờ mở trang khi bắt đầu đọc.
- Mẫu: **30 review có chữ, liên tiếp**, bắt đầu từ review mới nhất lúc mở trang, đi xuống theo thứ tự hiển thị.
- **Mọi mức sao**, mọi ngôn ngữ (review không phải tiếng Việt hay tiếng Anh: đọc bản dịch của Google, ghi ngôn ngữ gốc).
- **Không lọc từ khoá**, không bỏ qua review vì nội dung.
- Bỏ và đếm riêng: review chỉ có sao không có chữ; phản hồi của chủ sở hữu (không tính là review); review trùng nội dung với một review đã lấy.
- Mẫu số **N = 30**, tính cả review không liên quan tới xếp lịch.

**Nhãn chính** (giữ đúng định nghĩa ở lượt thăm dò và trong `label_reviews.py`)
- **1 · canh giờ:** người viết kể đã chủ động canh, kiểm hoặc chụp giờ hoạt động / giờ show để xếp lịch, hoặc khuyên người khác làm vậy. Ví dụ: “chụp bảng giờ show”, “đến đúng đầu giờ vì trò đóng sớm”.
- **0:** mọi trường hợp khác, kể cả chỉ khen hay chê show, phàn nàn xếp hàng, trò bảo trì mà không nói tới việc canh giờ, lỗi vé, giá, nhân viên.
- Ca không chắc: gắn 0 và ghi “không chắc” ở cột ghi chú; không tính vào nhãn 1.

**Nhãn phụ** (đếm thêm, mỗi review có thể có nhiều nhãn phụ; không thay nhãn chính)
- `dong`: nhắc trò đóng, bảo trì hoặc show huỷ.
- `muon`: nhắc vào khu muộn, hết giờ, không kịp chơi hết.
- `lo_show`: nhắc lỡ một show đã định xem.
- `hang`: nhắc xếp hàng lâu.

**Ghi vào `evidence/reviews-sample.csv`** (cột: `id,date,stars,language,text,human_label,sub_labels,note`)
- `id` từ G01 đến G30 theo thứ tự đọc. `date` ghi như Google hiển thị (vd “2 tuần trước”) kèm ngày xem.
- `text`: trích **tối đa 2 câu** chứa căn cứ gắn nhãn (repo công khai; luật dữ liệu mục 5). **Không chép tên** người viết hay ảnh.
- `human_label` do Phương Nam gắn tay khi đọc nguyên review trên trang, **trước** khi chạy `label_reviews.py`.

**Đếm và báo cáo**
- Số chính: **x/30 review có nhãn 1 (y%)**. Thêm: số đếm từng nhãn phụ trên 30, số review bị bỏ theo từng lý do.
- Kiểm lại cách đếm: chạy `python evidence/label_reviews.py` để model gắn nhãn độc lập trên cột `text`, báo độ khớp người–model. Số báo cáo dùng **nhãn người**. Model chỉ thấy đoạn trích tối đa 2 câu, nên độ khớp là cận dưới.
- Ghi ≥5 trích dẫn nguyên văn (mỗi trích dẫn tối đa 2 câu, có id G..) vào `evidence/summary.md`.
- Giới hạn ghi sẵn: người viết review Google Maps không chỉ là phụ huynh có con nhỏ; tỉ lệ trong review không phải tỉ lệ mọi khách; một địa điểm, một thời điểm. Kết luận giả thuyết vẫn dựa chủ yếu vào khảo sát và phỏng vấn (`hypothesis.md`); mẫu review này là nguồn kiểm lại.
