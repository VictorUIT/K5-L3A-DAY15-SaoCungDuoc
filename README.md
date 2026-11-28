# SaoCungDuoc · Lịch gia đình tại khu vui chơi

## Bản chạy CP3 của nhóm Sao Cũng Được

[Canvas](canvas.md) · [Thiết kế và chuẩn đạt §7](spec.md) · [26 câu thử](eval/benchmark.csv) · [Metric](eval/metric_spec.yaml) · [Data card](data/DATA_CARD.md) · [Bằng chứng ban đầu](evidence/data-mining.md) · [Phiếu chấm chéo CP2](eval/README.md) · [Phiếu chấm lượt 1](eval/phieu-cham-run-1.md) · [lượt 2](eval/phieu-cham-run-2.md).

Một phụ huynh nhập khung giờ, nhóm khách, ngân sách và hoạt động bắt buộc. Python liệt kê và kiểm mọi lịch khả thi (giờ mở, giờ show, 10 phút đi bộ mỗi chặng, chiều cao, ngân sách). Model chọn một lịch theo sở thích. Không có lịch thì hệ thống nêu ràng buộc đang chặn và gợi ý thay đổi đã kiểm là ra lịch. **Dữ liệu khu Vịnh Mây là mô phỏng**, không phải giá hay lịch thật.

## Chạy trong 3 phút

```sh
cp .env.example .env        # điền MODEL_PROVIDER=gemini, MODEL_NAME=gemini-3.1-flash-lite, API_KEY=<key của nhóm>
python3 run.py              # bản chạy thử dòng lệnh
```

```text
giờ=09:00-12:00; lớn=2; trẻ=1; cao=110; đồng=500000; phải có=chim
```

Bắt buộc: giờ đến–giờ kết thúc, số người lớn (≥1), số trẻ và ngân sách bằng đồng. Nếu có trẻ, nhập chiều cao thấp nhất bằng cm. Có thể nhập thêm `ưu tiên=bé thích động vật`, `phải có=chim,vuon`, `đóng=tau` hoặc `đệm=15` (phút đến trước show). Mã điểm: `vuon` Vườn hoa, `nha` Nhà tranh, `tau` Tàu lượn, `chim` Show chim, `nhac` Show nhạc. Thiếu `.env` thì chạy model giả (0 token, không dùng để báo cáo).

- `python3 run.py check` kiểm bộ câu thử và metric.
- `python3 run.py eval --wait 4` chạy cả bộ bằng model thật → `eval/run-N.csv` + `traces/run-N.jsonl`. Lượt 1 `run-1@20261127-202533` và lượt 2 `run-2@20261127-202738`: gemini-3.1-flash-lite, 26/26 câu chạy, 0 lỗi. Chấm tay (Bình An, Tuấn Khanh): **25/26 → 25/26** (trượt C21) · [hồ sơ đánh giá](eval/README.md) · [phiếu lượt 1](eval/phieu-cham-run-1.md) · [phiếu lượt 2](eval/phieu-cham-run-2.md)).
- `python3 run.py simulate --wait 4` mô phỏng chi phí → `cost/simulate-N.csv`. Bản nộp: `simulate-2@20261128-120240`, $0,00020 / task thành công ([cost-estimate](cost/cost-estimate.md)).

## Web demo (Streamlit, dạng chatbox)

**Video demo 26 giây** (thao tác thật, gọi model thật, dùng làm video dự phòng): https://drive.google.com/file/d/163YYxVCp81kX1ixeHPpIcfg5yK9pNAlm/view?usp=sharing

Phụ huynh nhắn tự nhiên, ví dụ “2 người lớn, 1 bé cao 110 cm, 9h đến 12h, 500k, muốn xem Show chim”. Model rút điều kiện (`extract_request`), Python kiểm từng trường; web nhớ điều kiện qua nhiều tin (“đổi giờ về 11h” chỉ sửa giờ về) và hiện “Mình đang hiểu: …” để khách kiểm. Sau đó đi cùng `answer(text)` trong `codebase/agent.py` như dòng lệnh và eval. File khởi động: **`streamlit_app.py`** (điều hướng hai trang: `web/trang_chu.py` giới thiệu khu Vịnh Mây, mọi giờ và giá đọc từ `data/park.json`; `web/len_lich.py` chatbot lên lịch). CSS dùng chung ở `web/common.py`, theme ở `.streamlit/config.toml`. `python3 run.py` cũng nhận câu tự nhiên (không có dấu `=`).

```sh
python3 -m pip install -r requirements.txt     # cần Python 3.10+ (Streamlit)
streamlit run streamlit_app.py                  # mở http://localhost:8501
```

Trên máy, web đọc model từ `.env` hoặc `.streamlit/secrets.toml` (mẫu: [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example)). Không có model thật thì web báo lỗi và không chạy; chỉ khi thử trên máy mới đặt `DEMO_ALLOW_FAKE=1` để dùng model giả.

| Biến / secret | Ý nghĩa | Mặc định |
|---|---|---|
| `MODEL_PROVIDER` | `gemini` (nhóm dùng), hoặc `openai`, `anthropic`, `ollama` | bắt buộc trên web |
| `MODEL_NAME` | `gemini-3.1-flash-lite` | bắt buộc trên web |
| `API_KEY` | key của nhóm, chỉ đặt ở secret phía máy chủ | bắt buộc trên web |
| `DEMO_MAX_PER_SESSION` | số tin nhắn tối đa mỗi phiên | 15 |
| `DEMO_MAX_PER_HOUR` | số tin nhắn tối đa mỗi giờ cho cả web | 60 |
| `DEMO_ALLOW_FAKE` | `1` = cho phép model giả, chỉ dùng trên máy | tắt |

Model chỉ được gọi khi gửi tin nhắn (mỗi tin tối đa 2 lần: rút điều kiện, chọn lịch). Mỗi phiên có kết quả và trace riêng; trace của khung được bọc trong một khoá chung để hai người bấm cùng lúc không lẫn lượt. Hết quota thì web báo "Model đang hết lượt gọi", không hiện chi tiết key.

### Chatbot VinWonders Nha Trang

AI đọc hiểu câu hỏi, Python tính số: `codebase/nha_trang_ai.py` gọi model một lần mỗi tin để rút ý định (hỏi show, hỏi vé, xếp lịch, đi bộ giữa hai điểm, có kịp show, gợi ý theo sở thích), tên điểm (chỉ tên có trong danh mục `data/nha_trang/`), chiều cao, tuổi, giờ. Python kiểm từng trường rồi `codebase/nha_trang_chat.py` tính giờ, giá, quãng đi bộ và ghi nguồn. Dùng chung hạn mức `DEMO_MAX_PER_SESSION` / `DEMO_MAX_PER_HOUR` với Vịnh Mây. Không có model thật, hết lượt hoặc model lỗi thì chatbot vẫn trả lời bằng dò từ khoá và ghi rõ điều đó.

### Đường đến khu vui chơi (VinWonders Nha Trang)

Mục này chỉ có khi chọn khu VinWonders Nha Trang; Vịnh Mây là khu mô phỏng nên không có chỉ đường thực địa. Code: `codebase/directions.py`, `web/duong_den.py`.

- **Không cần key:** nút “Chỉ đường từ vị trí của tôi” mở Google Maps Directions (`api=1`, không có `origin` để điện thoại tự lấy vị trí) tới **Cảng Vinpearl Nha Trang** (tên theo trang chính thức VinWonders, tuyến “… → Cảng Cầu Đá → Cảng Vinpearl Nha Trang”; Google Maps hiện là *Vinpearl Land Terminal*). Có ô nhập tên resort/địa chỉ để lên kế hoạch trước. Cáp treo chưa xác minh được ga cụ thể (và có nguồn chính thức ghi đang tạm dừng) nên chỉ có nút “Tìm địa điểm trên Google Maps”. Chưa đối chiếu được Google Place ID.
- **Có key (tuỳ chọn):** “Ước tính thời gian đến” gọi Routes API (`computeRoutes`) từ server khi khách bấm, từ vị trí hiện tại (xin quyền trình duyệt một lần) hoặc từ địa chỉ nhập. Kết quả là chặng tới bến; thời gian chờ tàu, đi tàu và vào cổng chưa có dữ liệu đáng tin nên không cộng. Toạ độ/địa chỉ khách không ghi vào file, log, trace, lịch sử chat và không gửi cho model.

Bật Routes API cho demo:
1. Google Cloud Console → chọn (hoặc tạo) project → **Billing**: gắn tài khoản thanh toán (Routes API bắt buộc có billing).
2. **APIs & Services → Library** → bật **Routes API**.
3. **APIs & Services → Credentials → Create credentials → API key**. Ở key vừa tạo: *API restrictions* → *Restrict key* → chỉ chọn **Routes API**. Key được gọi từ server Streamlit Cloud (IP thay đổi) nên không dùng giới hạn theo website/IP.
4. **APIs & Services → Routes API → Quotas**: hạ *Compute Routes requests per minute* (vd 30) và đặt giới hạn mỗi ngày (vd 300) cho demo; nên đặt thêm **Budget alert** trong Billing.
5. Dán key vào Streamlit Secrets (bên dưới). Web còn tự giới hạn `ROUTES_MAX_PER_SESSION` và `ROUTES_MAX_PER_HOUR`.

| Secret | Ý nghĩa | Mặc định |
|---|---|---|
| `GOOGLE_MAPS_ROUTES_API_KEY` | key Routes API, chỉ đặt ở Secrets phía server; thiếu thì chỉ ẩn phần ước tính | trống |
| `ROUTES_MAX_PER_SESSION` | số lần ước tính tối đa mỗi phiên | 10 |
| `ROUTES_MAX_PER_HOUR` | số lần ước tính tối đa mỗi giờ cho cả web | 60 |

**Deploy lên Streamlit Community Cloud** (share.streamlit.io): New app → repo `VictorUIT/K5-L3A-DAY15-SaoCungDuoc`, branch `son/cp3-web` (hoặc `main` sau khi gộp), main file `streamlit_app.py`, Advanced settings → Python 3.12 và dán nội dung secret theo mẫu ở trên vào ô Secrets.

---

Codex và Claude Code hỗ trợ dựng khung, viết code, đối chiếu nguồn và kiểm lệnh; thành viên đứng tên duyệt. Nam và An chấm độc lập. [Phân công](TEAMS.md) · [Sử dụng AI](docs/ai-usage.md) · [Nối model](docs/connect-model.md)
