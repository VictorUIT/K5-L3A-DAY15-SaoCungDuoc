# Dùng AI ở CP2

Codex hỗ trợ tổng hợp mẫu review công khai, viết luồng lập lịch mô phỏng, tiêu chí, benchmark và tài liệu. Các câu thử dựa trên tình huống thật có mã nguồn ở evidence/data-mining.md. Khu Vịnh Mây và các tham số chi phí, thời gian trong bản chạy thử đều do nhóm mô phỏng.

Các phần cần người duyệt: Tuấn Khanh đối chiếu canvas và chốt nội dung nộp; Phương Nam kiểm bằng chứng và nhãn review; Bình An phụ trách data card, kiểm giá/giờ và cùng Phương Nam chấm độc lập năm đầu ra; Ngọc Sơn phụ trách luồng chạy, mô phỏng chi phí và nối model thật ở CP3. Đây là phân công, chưa ghi nhận kết quả chấm của thành viên.

Phiếu chấm của Phương Nam ở eval/README.md (27/11/2026): Claude Code đề xuất điểm 1/0 cho 5 đầu ra theo pass_criterion và tính lại giờ/giá từ data/park.json; Phương Nam đọc lại và duyệt. Vì vậy mức đồng thuận đo được là giữa phiếu này và phiếu Bình An chấm tay. Claude Code cũng soạn evidence/label_reviews.py, evidence/interviews/GUIDE.md và bản nháp evidence/hypothesis.md; Phương Nam duyệt.

Phiếu chấm của Bình An ở eval/README.md (27/11/2026): Đối chiếu 5 đầu ra theo pass_criterion và tính lại giờ/giá từ data/park.json, đề xuất điểm 1/0 (C01=1, C06=1, C08=1, C09=1, C12=1); Đạt mức đồng thuận 5/5 (100%). Ngoài ra, đã kiểm chứng độc lập đáp án C13–C21 và biên soạn 4 câu thử C23–C26 trong eval/benchmark.csv từ evidence/data-mining.md (R07, R03, R10, R14) theo quy tắc data/park.json và data/DATA_CARD.md.

Phiếu chấm Run 1 (`run-1@20261127-202533`, `eval/phieu-cham-run-1.md`) và Run 2 (`run-2@20261127-202738`, `eval/phieu-cham-run-2.md`) của Nguyễn Bình An (27/11/2026): Nguyễn Bình An chấm tay 26 câu cho cả hai lượt (25/26 đạt, C21=0); AI hỗ trợ đối chiếu lại giờ/giá theo `data/park.json` và `data/DATA_CARD.md`, tổng hợp chỉ số riêng của An và điền cột `An` cùng ghi chú (`C02`, `C21`) vào hai phiếu. Chưa điền cột `Nam`, cột `Thống nhất`, cột `pass` trong `eval/run-1.csv`/`eval/run-2.csv` hay kết quả chính thức trong `eval/report.md` (chờ đối chiếu với Phương Nam).
