# VinWonders Phú Quốc · snapshot 2026-11-28

Người phụ trách: Đỗ Phương Nam. Cùng schema `public_snapshot_v1` với [data/nha_trang/](../nha_trang/) — đọc được bằng `load_nha_trang_dataset(Path("data/phu_quoc"))` trong `codebase/park_provider.py` (nhánh `binhan`); `validate_snapshot` trả `valid: True`, 0 lỗi. Dựng lại: `python data/phu_quoc/build_snapshot.py`.

## Phạm vi

72 bản ghi: 55 trò/điểm có trong trang yêu cầu chiều cao (gồm Coco Oasis), 13 điểm chỉ có trong bài bản đồ, 4 điểm diễn. 6 khu + 1 khu `unassigned`. 12 suất diễn (9 show). 7 mức giá (vé tiêu chuẩn và combo 1 ngày kèm Vinpearl Safari). Không gồm Vinpearl Safari, Grand World, nhà hàng, cửa hàng, review.

## Nguồn và cách lấy

- 10 trang chính thức vinwonders.com, đọc ngày 28/11/2026, đều HTTP 200 — danh sách, ngày đăng và ghi chú ở [sources.json](sources.json). Trích thủ công các điều trang viết rõ; không dùng API không công khai, không vượt chặn truy cập. Ảnh bản đồ `MAP_PNG` có link nhưng **chưa xem**.
- Mỗi trường có nguồn riêng ở `field_sources`; trường nguồn không nêu để `null` (không phải 0).

## Chất lượng — đọc trước khi dùng

- **Chiều cao:** trang nguồn xếp trò theo nhóm "Guests over X cm"; ghi `min_height_cm = X`. Nguồn không nói ranh giới là "trên X" hay "từ X". Không có chiều cao tối đa (trừ Coco Oasis chỉ cho trẻ dưới 140cm), tuổi, cân nặng, thời lượng, phụ phí hay giờ riêng từng trò.
- **Khu của trò:** trang chiều cao chỉ ghi nhóm "Games" hoặc "Typhoon World". Trò chỉ được gán khu khi bài bản đồ nêu tên; 21 trò và điểm diễn Fire Phoenix Square để `unassigned`.
- **Mâu thuẫn giữa các trang** (ghi ở `conflict_source_id`, `note`, `map_warning`): giờ đóng 19:30 so với vé dùng đến 19:05, ngừng nhận khách sau 19:00; ONCE Show 18:45 so với 18:30; giờ và địa điểm show nhạc nước, cho cá ăn, tiên cá; Coco Oasis nhóm >100cm (EN) so với >130cm (VI); ngưỡng người cao tuổi "từ 60" so với "trên 60"; miễn vé "dưới 100cm" so với "dưới 1m và dưới 1 tuổi".
- **Show tiên cá:** HOURS_EN ghi chỉ diễn 01/01–28/02/2026; sau đó không có nguồn → không chắc còn diễn ngày 28/11.
- **Giá:** giá niêm yết đã gồm VAT, không có ngày hiệu lực, "có thể thay đổi theo mùa" → `current_quote: false`.
- **Không có:** trạng thái mở cửa trực tiếp, thời gian xếp hàng, tọa độ, ma trận đi bộ (`walking_distances.json` rỗng). Mọi điểm `scheduling_ready: false`.

## Hợp đồng tích hợp

Giữ nguyên `data/park.json` và các lượt eval cũ. Như Nha Trang: xếp lịch thật phải dừng (fail closed) khi thiếu giờ, thời lượng, quãng đi hoặc điều kiện an toàn; không mặc định 10 phút đi bộ hay giá giả cho chế độ thật. Đăng ký `park_id = "vinwonders_phu_quoc"` trong `load_park_provider` là việc của người giữ `park_provider.py`.
