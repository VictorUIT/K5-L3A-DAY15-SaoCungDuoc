"""Gắn nhãn review "canh giờ" bằng model rồi so với nhãn người gắn — người phụ trách: Đỗ Phương Nam.

Quy tắc nhãn (chốt trong evidence/data-mining.md):
    1 = khách kể hoặc khuyên CHỦ ĐỘNG canh giờ hoạt động/show để xếp lịch.
    0 = chỉ khen show, phàn nàn xếp hàng, chậm đổi vé, hoặc chuyện khác.

Đầu vào:  evidence/reviews-sample.csv  — cột: id,text,human_label
          (text đã bỏ tên/tài khoản; human_label do người gắn TRƯỚC khi chạy script, để trống nếu chưa gắn)
Đầu ra:   evidence/reviews-ai-labels.csv — cột: id,human_label,ai_label,ai_reason,model,tokens_in,tokens_out
          và in ra: tỉ lệ nhãn 1 theo AI, độ khớp người–AI, bảng nhầm lẫn, danh sách ca lệch.

Chạy:     python evidence/label_reviews.py            (đọc MODEL_PROVIDER / MODEL_NAME / API_KEY từ .env)
          python evidence/label_reviews.py --fake     (chạy thử luồng bằng quy tắc từ khoá, KHÔNG dùng làm số liệu)

Không có tác động ra ngoài ngoài việc gọi API model. Chỉ dùng thư viện chuẩn.
Nhãn AI là bản nháp hỗ trợ; số liệu báo cáo trong evidence/ dùng nhãn người, nhãn AI dùng để đo độ khớp.
"""
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IN_CSV = os.path.join(HERE, "reviews-sample.csv")
OUT_CSV = os.path.join(HERE, "reviews-ai-labels.csv")

SYSTEM = """Bạn gắn nhãn review khu vui chơi theo MỘT quy tắc cố định.
Nhãn 1: người viết kể rằng họ đã chủ động canh/kiểm/chụp giờ hoạt động hoặc giờ show để xếp lịch,
hoặc khuyên người khác làm vậy (ví dụ: "chụp bảng giờ show", "đến đúng đầu khung giờ vì trò đóng sớm").
Nhãn 0: mọi trường hợp khác — chỉ khen/chê show, phàn nàn xếp hàng, trò bảo trì mà không nói tới việc canh giờ,
lỗi đổi vé, giá, nhân viên.
Chỉ dựa vào chữ trong review, không suy đoán thêm.
Trả về DUY NHẤT một dòng JSON: {"label": 0 hoặc 1, "reason": "<tối đa 20 từ, trích cụm từ làm căn cứ nếu nhãn 1>"}"""


def load_env(path=os.path.join(ROOT, ".env")):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def post_json(url, headers, body, timeout=60):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers=dict({"Content-Type": "application/json"}, **headers))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError("HTTP %d: %s" % (e.code, e.read().decode("utf-8", "replace")[:300]))


def call_model(provider, model, key, user):
    """Trả (text, tokens_in, tokens_out). Token lấy từ usage của API, không ước lượng."""
    if provider == "openai":
        data = post_json("https://api.openai.com/v1/chat/completions", {"Authorization": "Bearer " + key},
                         {"model": model, "messages": [{"role": "system", "content": SYSTEM},
                                                       {"role": "user", "content": user}]})
        u = data["usage"]
        return data["choices"][0]["message"]["content"], u["prompt_tokens"], u["completion_tokens"]
    if provider == "anthropic":
        data = post_json("https://api.anthropic.com/v1/messages",
                         {"x-api-key": key, "anthropic-version": "2023-06-01"},
                         {"model": model, "max_tokens": 200, "system": SYSTEM,
                          "messages": [{"role": "user", "content": user}]})
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        u = data["usage"]
        return text, u["input_tokens"], u["output_tokens"]
    if provider == "ollama":
        data = post_json("http://localhost:11434/api/chat", {},
                         {"model": model, "stream": False, "messages": [{"role": "system", "content": SYSTEM},
                                                                       {"role": "user", "content": user}]},
                         timeout=300)
        return data["message"]["content"], data.get("prompt_eval_count", 0), data.get("eval_count", 0)
    raise SystemExit("MODEL_PROVIDER=%r chưa hỗ trợ (openai / anthropic / ollama) — hoặc chạy --fake" % provider)


FAKE_PATTERN = re.compile(r"timetable|schedule|show time|lịch show|giờ show|bảng giờ|arrive early|đến sớm|đầu khung",
                          re.IGNORECASE)


def fake_label(text):
    hit = FAKE_PATTERN.search(text)
    return json.dumps({"label": int(bool(hit)), "reason": hit.group(0) if hit else "không thấy từ khoá"}), 0, 0


def parse(text):
    m = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        obj = json.loads(m.group(0)) if m else {}
        label = int(obj.get("label"))
        return (label if label in (0, 1) else None), str(obj.get("reason", ""))
    except (TypeError, ValueError):
        return None, "không đọc được: " + text[:80]


def main():
    for stream in (sys.stdout, sys.stderr):  # console Windows mặc định cp1252, không in được tiếng Việt
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    fake = "--fake" in sys.argv
    load_env()
    provider = "fake" if fake else (os.environ.get("MODEL_PROVIDER") or "").strip().lower()
    model = "fake-keywords" if fake else (os.environ.get("MODEL_NAME") or "").strip()
    key = (os.environ.get("API_KEY") or "").strip()
    if provider in ("", "fake") and not fake:
        raise SystemExit("Chưa có MODEL_PROVIDER trong .env. Điền .env (xem docs/connect-model.md) hoặc chạy --fake.")

    if not os.path.exists(IN_CSV):
        raise SystemExit("Chưa có %s (cột id,text,human_label)." % IN_CSV)
    with open(IN_CSV, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("text") or "").strip()]
    if not rows:
        raise SystemExit("reviews-sample.csv chưa có dòng nào có text.")

    out = []
    for r in rows:
        user = "Review %s:\n%s" % (r["id"], r["text"].strip())
        text, tin, tout = fake_label(r["text"]) if fake else call_model(provider, model, key, user)
        label, reason = parse(text)
        out.append({"id": r["id"], "human_label": (r.get("human_label") or "").strip(), "ai_label": "" if label is None else label,
                    "ai_reason": reason, "model": model, "tokens_in": tin, "tokens_out": tout})
        print("%s  AI=%s  người=%s  %s" % (r["id"], out[-1]["ai_label"], out[-1]["human_label"] or "-", reason))

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    n = len(out)
    ai_ones = sum(1 for o in out if o["ai_label"] == 1)
    unread = sum(1 for o in out if o["ai_label"] == "")
    print("\nMô hình: %s%s" % (model, "  (CHẠY GIẢ — không dùng làm số liệu)" if fake else ""))
    print("Nhãn 1 theo AI: %d/%d · không đọc được: %d" % (ai_ones, n, unread))
    print("Token: vào %d · ra %d" % (sum(int(o["tokens_in"]) for o in out), sum(int(o["tokens_out"]) for o in out)))

    both = [o for o in out if o["human_label"] in ("0", "1") and o["ai_label"] in (0, 1)]
    if not both:
        print("Chưa có nhãn người (cột human_label) để so.")
        return
    cm = {(h, a): 0 for h in (0, 1) for a in (0, 1)}
    for o in both:
        cm[(int(o["human_label"]), o["ai_label"])] += 1
    agree = cm[(0, 0)] + cm[(1, 1)]
    print("Nhãn 1 theo người: %d/%d" % (cm[(1, 0)] + cm[(1, 1)], len(both)))
    print("Khớp người–AI: %d/%d" % (agree, len(both)))
    print("Bảng nhầm lẫn (hàng = người, cột = AI):  0→0 %d · 0→1 %d · 1→0 %d · 1→1 %d"
          % (cm[(0, 0)], cm[(0, 1)], cm[(1, 0)], cm[(1, 1)]))
    lech = [o for o in both if int(o["human_label"]) != o["ai_label"]]
    if lech:
        print("Ca lệch (đọc lại, ghi lý do vào evidence/data-mining.md):")
        for o in lech:
            print("  %s  người=%s AI=%s  %s" % (o["id"], o["human_label"], o["ai_label"], o["ai_reason"]))


if __name__ == "__main__":
    main()
