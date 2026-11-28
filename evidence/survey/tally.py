"""Đếm kết quả khảo sát theo cách đã chốt ở evidence/survey/questions.md.

    python evidence/survey/tally.py anonymize   # raw-survey.csv (không commit) → results.csv (bỏ giờ, gắn mã S01…)
    python evidence/survey/tally.py             # đọc results.csv, in số chính / số phụ theo từng mẫu

Chỉ dùng thư viện chuẩn. Không gọi mạng.
"""
import csv
import os
import re
import sys
from collections import Counter
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw-survey.csv")
RESULTS = os.path.join(HERE, "results.csv")
CLOSE = datetime(2026, 11, 27, 23, 59, 59)      # giờ chốt ghi trong questions.md

COLS = ["id", "ngay", "trong_han", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10"]
SCREEN_OK = ("Trong 30 ngày qua", "Từ 31 đến 90 ngày trước")          # câu 1: hai đáp án đầu = qua sàng lọc
Q6_TRO_NGAI = "Có, ít nhất một lần vì gặp trở ngại"
Q7_GIO_DIEU_KIEN = ("Đến sau giờ vào trò hoặc giờ bắt đầu biểu diễn",
                    "Trò đóng cửa hoặc suất diễn bị hủy, đổi giờ",
                    "Có người chưa đủ điều kiện tham gia (ví dụ chưa đạt chiều cao tối thiểu)")
Q7_XEP_HANG = "Thời gian xếp hàng quá dài"


def parse_time(s):
    m = re.match(r"(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+) (SA|CH)", s.strip())
    y, mo, d, h, mi, se, ap = m.groups()
    h = int(h) % 12 + (12 if ap == "CH" else 0)
    return datetime(int(y), int(mo), int(d), h, int(mi), int(se))


def anonymize():
    with open(RAW, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))[1:]
    rows.sort(key=lambda r: parse_time(r[0]))
    with open(RESULTS, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for i, r in enumerate(rows, 1):
            t = parse_time(r[0])
            answers = [" ".join(a.split()) for a in r[1:11]]      # gộp xuống dòng / khoảng trắng thừa
            w.writerow(["S%02d" % i, t.strftime("%d/%m/%Y"), int(t <= CLOSE)] + answers)
    print("Đã ghi %s: %d phản hồi" % (RESULTS, len(rows)))


def frac(x, n):
    return "%d/%d" % (x, n) + ("" if n < 10 else " (%.0f%%)" % (100.0 * x / n))


def verdict(x, n):
    if n == 0:
        return "không có mẫu"
    r = x / n
    return "đúng" if r >= 0.5 else ("phải đổi" if r >= 0.25 else "sai")


def report(name, rows):
    n = len(rows)
    print("\n=== %s — N = %d ===" % (name, n))
    if not n:
        return
    main = [r for r in rows if r["q6"] == Q6_TRO_NGAI and r["q7"] in Q7_GIO_DIEU_KIEN]
    tro_ngai = [r for r in rows if r["q6"] == Q6_TRO_NGAI]
    print("Số chính (câu 6 trở ngại VÀ câu 7 là giờ/đóng/điều kiện): %s → giả thuyết %s  [%s]"
          % (frac(len(main), n), verdict(len(main), n), ", ".join(r["id"] for r in main)))
    print("Câu 6 — phải đổi vì trở ngại: %s" % frac(len(tro_ngai), n))
    for k, v in Counter(r["q6"] for r in rows).most_common():
        print("    %-50s %d" % (k, v))
    c = len(tro_ngai)
    print("Câu 7 (mẫu số = %d người vào phần C):" % c)
    for k, v in Counter(r["q7"] for r in tro_ngai).most_common():
        print("    %-50s %d" % (k, v))
    print("  xếp hàng quá dài: %s" % frac(sum(r["q7"] == Q7_XEP_HANG for r in tro_ngai), c))
    for q, title, pool in (("q8", "Câu 8 (phần C)", tro_ngai), ("q9", "Câu 9 — phút quyết định lại (phần C)", tro_ngai),
                           ("q5", "Câu 5 — phút chuẩn bị", rows), ("q3", "Câu 3 — đã quyết trước khi vào cổng?", rows),
                           ("q4", "Câu 4 — nguồn chọn hoạt động đầu tiên", rows), ("q2", "Câu 2 — số chuyến trong 30 ngày", rows)):
        print("%s:" % title)
        for k, v in Counter(r[q] for r in pool).most_common():
            print("    %-50s %d" % (k, v))


def main():
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["anonymize"]:
        anonymize()
        return
    with open(RESULTS, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    in_time = [r for r in rows if r["trong_han"] == "1"]
    print("Tổng phản hồi: %d · trong hạn chốt: %d · gửi sau hạn: %d" % (len(rows), len(in_time), len(rows) - len(in_time)))
    print("Câu 1:", dict(Counter(r["q1"] for r in rows)))
    report("CHÍNH: trong hạn, qua sàng lọc câu 1 (≤90 ngày)", [r for r in in_time if r["q1"] in SCREEN_OK])
    report("PHỤ: trong hạn, mọi đáp án câu 1", in_time)
    report("PHỤ: cả 20 phản hồi, kể cả gửi sau hạn", rows)


if __name__ == "__main__":
    main()
