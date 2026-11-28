"""Trả lời câu chat cho VinWonders Nha Trang. Không gọi model.

Hai chế độ, cùng một hàm answer_nha_trang(text, ds):
- Snapshot gốc (data/nha_trang/): fail-closed. Thiếu giờ, thời lượng, điều kiện hay thời gian đi bộ thì nói rõ thiếu gì.
- Demo (ds đã qua nha_trang_demo.apply_demo_estimates, ds["demo"] = True): ô trống được điền số tự ước tính,
  nên xếp được lịch; mọi số ước tính gắn nhãn "ước tính demo".
Cả hai: mỗi giá trị có nguồn ghi nguồn kèm ngày; giá vé là giá tham khảo; không ước tính điều kiện an toàn;
không dùng mặc định nào của Vịnh Mây (10 phút đi bộ, giá vé, điều kiện trò chơi).

answer_nha_trang(text, ds) -> {"output": str, "header": str, "sections": [{"title", "lines"}], "found": [...]}
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from pricing import SENIOR_BOUNDARY_NOTE, classify_traveler_ticket

EST = "ước tính demo"
SHOW_ALIASES = {  # khoá: tên show đã bỏ dấu, viết thường
    "tata show": ["tata show", "tata"],
    "bieu dien chim": ["bieu dien chim", "show chim", "bird show", "xem chim"],
    "nhac nuoc": ["nhac nuoc", "fountain", "nhac nuoc show"],
    "nang tien ca": ["nang tien ca", "mermaid", "tien ca"],
    "cho ca an": ["cho ca an", "fish feeding"],
    "welcome show": ["welcome show"],
    "stunt show": ["stunt show"],
}
SOURCE_VI = {
    "MAP": "Bản đồ VinWonders", "HOME": "Trang VinWonders Nha Trang", "PRICE": "Bảng giá VinWonders",
    "PRICE_NOTICE": "Thông báo giá VinWonders", "RULES": "Quy định trò chơi VinWonders",
    "RULES_VI": "Quy định trò chơi VinWonders", "RIVER": "Thông tin vận hành VinWonders",
    "SHOW": "Lịch biểu diễn VinWonders", "AQUARIUM": "Trang thuỷ cung VinWonders", "FOOD": "Trang ẩm thực VinWonders",
    "FOOD2": "Trang ẩm thực VinWonders", "FOOD3": "Trang ẩm thực VinWonders", "KLOOK": "Klook",
    "TA": "Tripadvisor", "TVL1": "Traveloka", "TVL2": "Traveloka",
}
TICKET_WORDS = re.compile(r"(?<!\w)(vé|giá|bao nhiêu tiền|mất bao nhiêu|ticket|price)(?!\w)")  # trên chữ còn dấu: "vé" ≠ "về"
PLAN_WORDS = re.compile(r"(di bo|di chuyen|kip|lich|xep|ke hoach|lo trinh|sang|toi kip|walk)")
WALK_WORDS = re.compile(r"(di bo|di chuyen|kip|walk|tu .+ (den|sang|toi|qua) )")
ARRIVAL_WORDS = re.compile(r"(resort|khach san|tu day|cho minh|cho toi|dat lien|bay gio|xuat phat|tu nha|tu ben|di ra dao)")
GATE_ID = "nt_02"  # Central Gate (bản đồ): điểm xuất phát khi khách không nói đi từ đâu


def fold(text: str | None) -> str:
    """Bỏ dấu, viết thường, gom khoảng trắng: so khớp tên không phụ thuộc cách gõ."""
    text = (text or "").replace("’", "'").replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9' ]+", " ", text)).strip()


def _date_vi(iso: str | None) -> str:
    if not iso or len(iso) != 10:
        return iso or "không rõ ngày"
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


def source_name(source_id: str | None) -> str:
    return SOURCE_VI.get(source_id or "", source_id or "chưa rõ")


def source_label(ds: dict[str, Any], source_id: str | None) -> str:
    """'nguồn: Bản đồ VinWonders · 27/11/2026' — tên nguồn kèm ngày truy cập trong sources.json."""
    if not source_id:
        return "chưa rõ nguồn"
    src = ds["sources_by_id"].get(source_id) or {}
    return f"nguồn: {source_name(source_id)} · {_date_vi(src.get('accessed_on'))}"


def _src(ds, obj, field, fallback):
    """Nhãn cạnh một giá trị: 'ước tính demo' nếu do chế độ demo điền, ngược lại là nguồn kèm ngày."""
    if field in (obj.get("est") or []):
        return EST
    return source_label(ds, fallback)


def _money(vnd: int | None) -> str:
    return "—" if vnd is None else f"{vnd:,}".replace(",", ".") + " đ"


def _min(clock: str | None) -> int | None:
    if not clock:
        return None
    h, m = clock.split(":")
    return int(h) * 60 + int(m)


def _clock(total: int) -> str:
    return f"{total // 60:02d}:{total % 60:02d}"


# ------------------------------------------------------------------ nhận diện trong câu chat
def _index(ds: dict[str, Any]) -> list[tuple[str, str, Any]]:
    """(cụm từ đã bỏ dấu, loại, đối tượng); cụm dài xét trước để 'Tata Show' không bị nuốt bởi 'Tata'."""
    entries: list[tuple[str, str, Any]] = []
    for grp in ds["shows"]:
        key = fold(grp["name"])
        for alias in SHOW_ALIASES.get(key, [key]):
            entries.append((alias, "show", grp))
    for item in ds["catalog"]:
        name = fold(item["name"])
        if len(name) >= 4:
            entries.append((name, "item", item))
    for zone in ds["zones"]:
        entries.append((fold(zone["name"]), "zone", zone))
    return sorted(entries, key=lambda e: -len(e[0]))


def find_entities(text: str, ds: dict[str, Any]) -> list[tuple[str, Any]]:
    """Các show, điểm, khu được nhắc tới, theo thứ tự xuất hiện; không trùng, không chồng lấn."""
    folded = " " + fold(text) + " "
    taken: list[tuple[int, int]] = []
    found: list[tuple[int, str, Any]] = []
    seen: set[str] = set()
    for phrase, kind, obj in _index(ds):
        for m in re.finditer(r"(?<=[ ])" + re.escape(phrase) + r"(?=[ ])", folded):
            span = (m.start(), m.end())
            if any(a < span[1] and span[0] < b for a, b in taken):
                continue
            ident = kind + ":" + (obj.get("show_id") or obj["id"])
            taken.append(span)
            if ident not in seen:
                seen.add(ident)
                found.append((span[0], kind, obj))
    show_names = {fold(o["name"]) for _, k, o in found if k == "show"}
    found = [f for f in found if not (f[1] == "item" and fold(f[2]["name"]) in show_names)]
    return [(k, o) for _, k, o in sorted(found, key=lambda f: f[0])]


def find_heights(text: str) -> list[int]:
    """Chiều cao nhắc trong câu: '100 cm', '100cm', '1m25', '1,25 m', '1.4m'."""
    low = (text or "").lower()
    out: list[tuple[int, int]] = []
    for m in re.finditer(r"(\d{2,3})\s*(?:cm|phân)\b", low):
        out.append((m.start(), int(m.group(1))))
    for m in re.finditer(r"\b1\s*m\s*(\d{1,2})\b(?!\s*(?:cm|phút))", low):
        tail = m.group(1)
        out.append((m.start(), 100 + int(tail) * (10 if len(tail) == 1 else 1)))
    for m in re.finditer(r"\b1[\.,](\d{1,2})\s*m\b", low):
        tail = m.group(1)
        out.append((m.start(), 100 + int(tail) * (10 if len(tail) == 1 else 1)))
    return [h for _, h in sorted(out)]


def find_ages(text: str) -> list[int]:
    return [int(m.group(1)) for m in re.finditer(r"(\d{1,3})\s*tuổi", (text or "").lower())]


def find_times(text: str) -> tuple[int | None, int | None]:
    """(giờ đến, giờ về) theo phút: '9h', '9h30', '9 giờ', '17:00', '5 giờ chiều'. Giờ đứng sau 'về/rời' hoặc ngay
    trước 'về' ('5 giờ chiều về') là giờ về; 'chiều/tối' sau giờ < 12 thì cộng 12."""
    low = (text or "").lower()
    start = end = None
    for m in re.finditer(r"\b(\d{1,2})\s*(?:h|giờ|g|:)\s*(\d{2})?(?!\s*(?:phút|cm|tuổi))(\s*(?:sáng|trưa|chiều|tối))?", low):
        hour, minute = int(m.group(1)), int(m.group(2) or 0)
        if hour > 23 or minute > 59:
            continue
        if m.group(3) and m.group(3).strip() in ("chiều", "tối") and hour < 12:
            hour += 12
        before = low[max(0, m.start() - 12):m.start()]
        after = low[m.end():m.end() + 8]
        if re.search(r"(đến|tới|vào)\s*(cổng\s*)?(lúc\s*)?$", before) and start is None:
            start = hour * 60 + minute
        elif re.search(r"(về|ra về|rời|kết thúc|tới khi|đến khi)\s*(lúc\s*)?$", before) or re.match(r"\s*(là\s*)?(về|ra về)\b", after):
            end = hour * 60 + minute
        elif start is None:
            start = hour * 60 + minute
    return start, end


# ------------------------------------------------------------------ mô tả từng loại thông tin
def _venue_text(grp: dict[str, Any]) -> tuple[str, bool]:
    if grp.get("venue_name"):
        return grp["venue_name"] + (f" · khu {grp['zone_name']}" if grp.get("zone_name") else ""), False
    if grp.get("venue_text"):
        return grp["venue_text"], True
    return "chưa xác định chính xác địa điểm diễn", False


def describe_show(ds: dict[str, Any], grp: dict[str, Any]) -> list[str]:
    park = ds["park"]
    venue, est_venue = _venue_text(grp)
    lines = [f"Địa điểm: {venue}" + (f" ({EST})" if est_venue else "")]
    for s in grp["sessions"]:
        if s["has_published_time"]:
            lines.append(f"Suất {s['start']}–{s['end']} ({s['duration_minutes']} phút) · {_src(ds, s, 'start', s['source_id'])}")
        else:
            lines.append(f"Suất chưa có giờ công bố · {source_label(ds, s['source_id'])}")
        if s.get("conflict_source_id"):
            other = f"{s['conflict_start']}–{s['conflict_end']}" if s.get("conflict_start") else "giờ khác"
            lines.append(f"⚠ Hai nguồn ghi khác nhau: {source_name(s['source_id'])} ghi {s['start']}–{s['end']}, "
                         f"{source_name(s['conflict_source_id'])} ghi {other}. Vivu dùng giờ theo {source_name(s['source_id'])}.")
        if s.get("exceeds_park_close"):
            lines.append(f"⚠ Suất này kết thúc {s['end']}, sau giờ đóng cửa chung {park['close']} "
                         f"({source_label(ds, park['source_id'])}); nên hỏi lại khu vui chơi theo ngày đi.")
    if ds.get("demo"):
        lines.append(f"Trạng thái hôm nay: {ds['demo_live_text']}")
    else:
        lines.append("Trạng thái hôm nay: chưa có lịch diễn theo ngày, nên kiểm tra lại khi tới.")
    return lines


def _restriction_text(item: dict[str, Any]) -> str:
    r = item["restrictions"]
    parts = []
    if r["min_height_cm"] is not None:
        parts.append(f"trẻ từ {r['min_height_cm']} cm")
    if r["max_height_cm"] is not None:
        parts.append(f"tối đa {r['max_height_cm']} cm")
    if r["min_age"] is not None:
        parts.append(f"từ {r['min_age']} tuổi")
    if r["adult_required"]:
        parts.append("cần người lớn đi kèm")
    return ", ".join(parts)


def describe_item(ds: dict[str, Any], item: dict[str, Any]) -> list[str]:
    fs = item.get("field_sources") or {}
    lines = [f"Khu: {item['zone_name'] or 'chưa rõ'}" + (f" · số {item['map_code']} trên bản đồ" if item.get("map_code") else "")
             + f" · {source_label(ds, item['source_id'])}"]
    if item["open"] and item["close"]:
        lines.append(f"Giờ hoạt động: {item['open']}–{item['close']} · {_src(ds, item, 'open', fs.get('open') or item['source_id'])}")
    else:
        lines.append("Giờ hoạt động: chưa có dữ liệu")
    rule = _restriction_text(item)
    if rule:
        lines.append(f"Điều kiện: {rule} · {source_label(ds, fs.get('min_height_cm') or item['source_id'])}")
    elif ds.get("demo"):
        lines.append(f"Điều kiện: {ds['demo_rule_text']}")
    else:
        lines.append("Điều kiện tham gia (chiều cao, tuổi, sức khoẻ): chưa có dữ liệu")
    inc, extra = item["pricing"]["included_in_ticket"], item["pricing"]["extra_vnd"]
    if inc is False:
        fee = f"phụ phí {_money(extra)} (giá tham khảo)" if extra is not None else "không nằm trong vé tiêu chuẩn, mua thêm tại điểm chơi"
        lines.append(f"Phí: {fee} · {source_label(ds, fs.get('included_in_ticket') or item['source_id'])}")
    elif inc is True:
        lines.append("Phí: đã gồm trong vé tiêu chuẩn" + (f" · {EST}" if "included_in_ticket" in item.get("est", []) else ""))
    else:
        lines.append("Phí: chưa có dữ liệu có nằm trong vé tiêu chuẩn hay không")
    if item["duration_minutes"]:
        dur = f"Thời lượng: khoảng {item['duration_minutes']} phút"
        if item.get("queue_minutes"):
            dur += f", xếp hàng khoảng {item['queue_minutes']} phút"
        lines.append(dur + (f" · {EST}" if "duration_minutes" in item.get("est", []) else ""))
    else:
        lines.append("Thời lượng: chưa có dữ liệu")
    if ds.get("demo") and item["status"] == "demo_open":
        lines.append(f"Trạng thái hôm nay: {ds['demo_live_text']}")
    if item.get("map_warning"):
        lines.append("⚠ " + item["map_warning"])
    return lines


def describe_zone(ds: dict[str, Any], zone: dict[str, Any]) -> list[str]:
    items = [i for i in ds["catalog"] if i["zone_id"] == zone["id"] and i["kind"] in ("ride", "sight")]
    hours = f"{zone['open']}–{zone['close']}" if zone["open"] and zone["close"] else "chưa có dữ liệu"
    lines = [f"Giờ khu: {hours} · {_src(ds, zone, 'open', zone['source_id'])}",
             f"{len(items)} trò chơi / điểm tham quan: " + ", ".join(i["name"] for i in items[:8])
             + ("…" if len(items) > 8 else "")]
    if zone["is_harbour"]:
        lines.append("Khu lân cận Vinpearl Harbour, ngoài phạm vi công viên chính.")
    return lines


def ticket_lines(ds: dict[str, Any], heights: list[int], ages: list[int]) -> tuple[list[str], int | None]:
    """(các dòng giải thích, tổng tiền tham khảo nếu tính được hết)."""
    bands = {b["id"]: b for b in ds["ticket_prices"]}
    price_src = source_label(ds, "PRICE")
    lines, total, complete = [], 0, True
    for h in heights:
        res = classify_traveler_ticket({"label": f"Người cao {h} cm", "height_cm": h}, ds["ticket_prices"])
        band = bands.get(res.get("band_id") or "")
        if not band:
            lines.append(f"Người cao {h} cm: chưa khớp nhóm vé nào trong bảng giá tham khảo.")
            complete = False
            continue
        low, high = band.get("min_height_cm"), band.get("max_height_cm_exclusive")
        group = f"dưới {high} cm" if not low else f"từ {low} cm đến dưới {high} cm" if high else f"từ {low} cm trở lên"
        edge = f" (mốc đúng {low} cm được tính vào nhóm này)" if h == low else ""
        price = "miễn phí" if band["price_vnd"] == 0 else _money(band["price_vnd"])
        total += band["price_vnd"]
        lines.append(f"Người cao {h} cm → nhóm vé {group}{edge}: {price} · giá tham khảo, {price_src}")
    for a in ages:
        if a >= 60:
            res = classify_traveler_ticket({"label": f"Người {a} tuổi", "age": a}, ds["ticket_prices"])
            if res["status"] == "unresolved_senior_boundary":
                complete = False
                lines.append(f"Người đúng {a} tuổi: chưa xác định được nhóm vé. Nếu áp dụng mốc “từ 60 tuổi”: vé người "
                             f"cao tuổi {_money(bands['standard_senior']['price_vnd'])}; nếu áp dụng “trên 60 tuổi”: tính "
                             f"theo chiều cao. {SENIOR_BOUNDARY_NOTE}")
            elif res.get("price_vnd") is not None:
                total += res["price_vnd"]
                lines.append(f"Người {a} tuổi → vé người cao tuổi: {_money(res['price_vnd'])} · giá tham khảo, {price_src} "
                             "(cần giấy tờ tuỳ thân)")
    return lines, (total if complete and lines else None)


def describe_tickets(ds: dict[str, Any], heights: list[int], ages: list[int]) -> list[str]:
    lines, total = ticket_lines(ds, heights, ages)
    if total is not None and len(lines) > 1:
        lines.append(f"Tổng vé vào cổng cả nhóm: {_money(total)} (giá tham khảo)")
    if not lines:
        for b in ds["ticket_prices"]:
            low, high = b.get("min_height_cm"), b.get("max_height_cm_exclusive")
            if b.get("min_age"):
                group = f"Người cao tuổi (mốc {b['min_age']} tuổi cần xác minh)"
            else:
                group = f"Dưới {high} cm" if not low else f"Từ {low} đến dưới {high} cm" if high else f"Từ {low} cm trở lên"
            lines.append(f"{group}: {'miễn phí' if b['price_vnd'] == 0 else _money(b['price_vnd'])}")
        lines.append(f"Giá tham khảo, {source_label(ds, 'PRICE')}. Vé phân theo chiều cao; nhắn chiều cao từng người "
                     "(vd “bé cao 100 cm”) để Vivu xếp nhóm.")
    lines.append("Vé tiêu chuẩn gồm vào cổng và cáp treo khứ hồi; trò có phụ phí tính riêng. Giá thực tế có thể khác theo ngày.")
    return lines


# ------------------------------------------------------------------ lịch: snapshot gốc (fail-closed)
def schedule_gaps(ds: dict[str, Any], picked: list[tuple[str, Any]], wants_walk: bool) -> tuple[list[str], list[str]]:
    """(phần đã có dữ liệu, phần còn thiếu) cho yêu cầu xếp lịch / đi bộ kịp giờ, khi chưa bật số ước tính."""
    have, missing = [], []
    places = [(k, o) for k, o in picked if k in ("show", "item")]
    for kind, obj in places:
        name = obj["name"]
        if kind == "show":
            timed = [s for s in obj["sessions"] if s["has_published_time"]]
            if timed:
                have.append(f"{name}: giờ diễn " + ", ".join(f"{s['start']}–{s['end']}" for s in timed)
                            + f" ({source_label(ds, timed[0]['source_id'])})")
            else:
                missing.append(f"{name}: chưa có giờ diễn công bố")
            if not obj["venue_id"]:
                missing.append(f"{name}: chưa xác định chính xác địa điểm diễn, nên không đo được đường đi tới đó")
            if any(s.get("conflict_source_id") or s.get("exceeds_park_close") for s in obj["sessions"]):
                missing.append(f"{name}: giờ diễn chưa thống nhất giữa các nguồn / giờ đóng cửa")
        else:
            if obj["open"] and obj["close"]:
                have.append(f"{name}: mở {obj['open']}–{obj['close']}")
            else:
                missing.append(f"{name}: chưa có giờ hoạt động")
            if not obj["duration_minutes"]:
                missing.append(f"{name}: chưa có thời lượng chơi (kể cả thời gian xếp hàng)")
            rule = _restriction_text(obj)
            if rule:
                have.append(f"{name}: điều kiện đã công bố {rule}")
            missing.append(f"{name}: chưa có đủ điều kiện tham gia (sức khoẻ, cân nặng, người đi kèm…)")
    matrix = ds["walking_matrix"]
    ids = [(o.get("venue_id") if k == "show" else o["id"], o["name"]) for k, o in places]
    if wants_walk or len(places) >= 2:
        if len(places) >= 2:
            for (a_id, a_name), (b_id, b_name) in zip(ids, ids[1:]):
                minutes = matrix.get_minutes(a_id, b_id) if a_id and b_id else None
                if minutes is None:
                    missing.append(f"Chưa có thời gian đi bộ từ {a_name} đến {b_name}")
                else:
                    have.append(f"Đi bộ {a_name} → {b_name}: {minutes} phút")
        else:
            missing.append("Cần biết điểm xuất phát: nhắn rõ đi từ đâu tới đâu (vd “từ Zipline sang Tata Show”)")
        if matrix.is_empty:
            missing.append("Chưa có dữ liệu thời gian đi bộ giữa các điểm; Vivu không tự đoán số phút")
    missing.append("Chưa có trạng thái mở cửa hoặc hàng chờ theo ngày")
    return have, missing


# ------------------------------------------------------------------ lịch: chế độ demo (có số ước tính)
def _loc(kind: str, obj: dict[str, Any]) -> str | None:
    return obj.get("location_id") if kind == "show" else obj["id"]


def walk_verdict(ds: dict[str, Any], picked: list[tuple[str, Any]]) -> list[str]:
    """Đi từ A sang B có kịp không (demo): số phút đi bộ ước tính và giờ muộn nhất nên rời A."""
    places = [(k, o) for k, o in picked if k in ("show", "item")]
    (ka, a), (kb, b) = places[0], places[-1]
    minutes = ds["walking_matrix"].get_minutes(_loc(ka, a), _loc(kb, b))
    if minutes is None:
        return [f"Chưa tính được quãng đi bộ từ {a['name']} đến {b['name']}."]
    lines = [f"Đi bộ {a['name']} → {b['name']}: khoảng {minutes} phút ({EST}, tính theo khoảng cách giữa các khu)."]
    if kb == "show":
        for s in b["sessions"]:
            if s["has_published_time"]:
                leave = _min(s["start"]) - minutes - 5
                lines.append(f"Muốn kịp suất {s['start']} của {b['name']}: rời {a['name']} trước {_clock(leave)} "
                             "(đã cộng 5 phút để kịp vào chỗ).")
        if ka == "item" and a.get("close"):
            last = _min(a["close"])
            ok = [s for s in b["sessions"] if s["has_published_time"] and last + minutes + 5 <= _min(s["start"])]
            if ok:
                lines.append(f"{a['name']} đóng cửa {a['close']}, nên chơi tới lúc đóng cửa vẫn kịp suất {ok[0]['start']}. ✅")
    return lines


def find_group(text: str) -> tuple[int | None, int | None, int | None]:
    """(số người lớn, số trẻ, ngân sách đồng) từ câu: '2 người lớn', 'vợ chồng', '1 bé', '3 triệu', '500k'."""
    low = (text or "").lower()
    adults = children = budget = None
    m = re.search(r"(\d+)\s*(?:người lớn|ng lớn|lớn\b|nl\b)", low)
    if m:
        adults = int(m.group(1))
    elif re.search(r"vợ chồng|hai vợ chồng|bố mẹ|ba mẹ", low):
        adults = 2
    m = re.search(r"(\d+)\s*(?:trẻ|bé|cháu|con)\b", low)
    if m:
        children = int(m.group(1))
    elif re.search(r"\b(?:với|và|cùng)\s+(?:bé|con|cháu)\b", low):
        children = 1
    m = re.search(r"(\d+(?:[\.,]\d+)?)\s*(triệu|tr\b|củ)", low)
    if m:
        budget = int(float(m.group(1).replace(",", ".")) * 1_000_000)
    else:
        m = re.search(r"(\d+)\s*(k|nghìn|ngàn)\b", low)
        if m:
            budget = int(m.group(1)) * 1000
    return adults, children, budget


def group_ticket_lines(ds: dict[str, Any], heights: list[int], adults: int | None, children: int | None,
                       budget: int | None, extra_items: list[dict[str, Any]]) -> list[str]:
    """Tiền vé cả nhóm theo bảng giá tham khảo; người lớn chưa cho chiều cao thì ghi rõ giả định ≥ 140 cm."""
    lines, total = [], 0
    child_lines, child_total = ticket_lines(ds, heights, [])
    lines += [l.split(" · giá tham khảo")[0] for l in child_lines]
    if heights and child_total is None:
        return lines + ["Chưa tính được tổng vé (có chiều cao chưa khớp nhóm vé)."]
    total += child_total or 0
    adult_band = next(b for b in ds["ticket_prices"] if b["id"] == "standard_140_plus")
    n_adults = adults or 0
    if n_adults:
        lines.append(f"{n_adults} người lớn × {_money(adult_band['price_vnd'])} (giả định cao từ 140 cm; nhắn chiều cao "
                     "nếu có người thấp hơn)")
        total += n_adults * adult_band["price_vnd"]
    missing_h = max(0, (children or 0) - len(heights))
    if missing_h:
        lines.append(f"Còn {missing_h} trẻ chưa có chiều cao: chưa tính vé (vé theo chiều cao, không đoán theo tuổi).")
    if total:
        label = f"Tổng vé đã tính (chưa gồm {missing_h} trẻ)" if missing_h else "Tổng vé vào cổng"
        lines.append(f"{label}: {_money(total)} (giá tham khảo, {source_label(ds, 'PRICE')})")
        if budget:
            if missing_h:
                lines.append(f"Ngân sách {_money(budget)}: chưa so được vì còn vé chưa tính.")
            elif total <= budget:
                lines.append(f"Trong ngân sách {_money(budget)} (còn khoảng {_money(budget - total)}).")
            else:
                lines.append(f"⚠ Vượt ngân sách {_money(budget)} khoảng {_money(total - budget)}.")
    elif not heights and not n_adults:
        lines.append("Nhắn số người và chiều cao trẻ để Vivu tính tiền vé (vé phân theo chiều cao).")
    fees = [i["name"] for i in extra_items if i["pricing"]["included_in_ticket"] is False]
    if fees:
        lines.append("Chưa gồm phụ phí: " + ", ".join(fees) + " (ngoài vé tiêu chuẩn, chưa có đơn giá).")
    return lines


def build_demo_plan(ds: dict[str, Any], picked: list[tuple[str, Any]], start: int | None, end: int | None,
                    heights: list[int], suggested: list[tuple[str, Any]] | None = None, adults: int | None = None,
                    children: int | None = None, budget: int | None = None) -> list[str] | None:
    """Xếp lịch kiểu Vịnh Mây cho Nha Trang (chế độ demo).

    picked: điểm khách nêu tên (ưu tiên); suggested: điểm AI chọn theo sở thích (đã kiểm tên). Python loại trò không đủ
    chiều cao tối thiểu đã công bố, giữ show đúng giờ diễn, loại show ngoài giờ về, rồi tính vé và so ngân sách.
    Khách chưa nêu điểm nào thì lấy các show có giờ công bố trong khung giờ. None nếu vẫn không có gì để xếp.
    """
    park = ds["park"]
    user_end, user_start = end is not None, start is not None
    start = start if start is not None else _min(park["open"])
    end = end if end is not None else _min(park["close"])
    shortest = min(heights) if heights else None
    skipped: list[str] = []

    def fits(s):  # khách nêu giờ về: suất phải xong trước đó; không nêu: chỉ cần bắt đầu trước giờ đóng cửa chung
        return _min(s["start"]) >= start and (_min(s["end"]) <= end if user_end else _min(s["start"]) < end)
    candidates: list[tuple[str, Any, bool]] = []  # (loại, đối tượng, khách nêu tên?)
    seen: set[str] = set()
    for (kind, obj), named in [(x, True) for x in picked] + [(x, False) for x in (suggested or [])]:
        if kind not in ("show", "item") or (kind == "item" and obj["kind"] in ("gate", "placeholder")):
            continue
        ident = kind + ":" + (obj.get("show_id") or obj["id"])
        if ident in seen:
            continue
        seen.add(ident)
        min_h = obj["restrictions"]["min_height_cm"] if kind == "item" else None
        if shortest is not None and min_h is not None and shortest < min_h:
            skipped.append(f"{obj['name']}: cần trẻ từ {min_h} cm, bé thấp nhất cao {shortest} cm "
                           f"({source_label(ds, (obj.get('field_sources') or {}).get('min_height_cm') or obj['source_id'])})")
            continue
        candidates.append((kind, obj, named))
    added_shows = False
    no_items = not any(k == "item" for k, _, _ in candidates)
    if True:  # thêm các show có giờ diễn trong khung giờ (nhường show khách nêu tên, xem blocks_named)
        have = {o.get("show_id") for k, o, _ in candidates if k == "show"}
        for g in ds["shows"]:
            if g["is_harbour"] or g["show_id"] in have:
                continue
            if any(s["has_published_time"] and fits(s) for s in g["sessions"]):
                candidates.append(("show", g, False))
                added_shows = True
    if not candidates:
        return None
    items = [o for k, o, _ in candidates if k == "item"]
    shows = [o for k, o, _ in candidates if k == "show"]
    matrix = ds["walking_matrix"]
    rows: list[tuple[int, str]] = [(start, f"{_clock(start)}  Vào cổng chính")]
    cur, loc = start, GATE_ID
    placed_items: list[dict[str, Any]] = []

    def try_item(item, limit):
        nonlocal cur, loc
        walk = matrix.get_minutes(loc, item["id"]) or 0
        arrive = max(cur + walk, _min(item["open"]) if item["open"] else cur)
        finish = arrive + (item.get("queue_minutes") or 0) + (item["duration_minutes"] or 0)
        close = _min(item["close"]) if item["close"] else end
        if finish > min(limit, close, end):
            return False
        extra = f"đi bộ {walk}′" + (f", xếp hàng {item['queue_minutes']}′" if item.get("queue_minutes") else "")
        rows.append((arrive, f"{_clock(arrive)}–{_clock(finish)}  {item['name']} ({extra})"))
        cur, loc = finish, item["id"]
        placed_items.append(item)
        return True

    named_shows = {o["show_id"] for k, o, named in candidates if k == "show" and named}
    suggested_shows = {o["show_id"] for k, o in (suggested or []) if k == "show"}
    timed = []
    for g in shows:
        sessions = [s for s in g["sessions"] if s["has_published_time"]]
        if not sessions:
            skipped.append(f"{g['name']}: chưa có giờ diễn")
            continue
        in_window = [s for s in sessions if fits(s)]
        if not in_window and g["show_id"] not in {o.get("show_id") for k, o, n in candidates if k == "show" and (n or (k, o) in (suggested or []))}:
            continue
        if not in_window:
            skipped.append(f"{g['name']}: suất " + ", ".join(s["start"] for s in sessions)
                           + f" nằm ngoài khung {_clock(start)}–{_clock(end)}")
            continue
        timed.append((g, in_window))
    pending = list(items)
    timed.sort(key=lambda t: _min(t[1][0]["start"]))

    def blocks_named(g, s):
        """Show Vivu tự thêm không được làm trượt show khách nêu tên ở sau."""
        if g["show_id"] in named_shows:
            return None
        for g2, ss2 in timed:
            if g2["show_id"] in named_shows and _min(ss2[-1]["start"]) > _min(s["start"]):
                walk2 = matrix.get_minutes(g.get("location_id") or g.get("venue_id"), g2.get("location_id") or g2.get("venue_id")) or 0
                if not any(_min(s["end"]) + walk2 + 5 <= _min(x["start"]) for x in ss2 if _min(x["start"]) > _min(s["start"])):
                    return g2["name"]
        return None

    for g, sessions in timed:
        loc_show = g.get("location_id") or g.get("venue_id")
        chosen = None
        blocked = None
        for s in sessions:
            for item in list(pending):  # chen trò chơi trước suất này nếu vẫn kịp đi bộ tới show
                walk_to_show = matrix.get_minutes(item["id"], loc_show) or 0
                if try_item(item, _min(s["start"]) - walk_to_show - 5):
                    pending.remove(item)
            walk = matrix.get_minutes(loc, loc_show) or 0
            if cur + walk + 5 <= _min(s["start"]):
                blocked = blocks_named(g, s)
                if blocked:
                    continue
                chosen = (s, walk)
                break
        if not chosen:
            if g["show_id"] in named_shows or blocked or g["show_id"] in suggested_shows:
                skipped.append(f"{g['name']}: " + (f"nhường giờ cho {blocked} bạn muốn xem" if blocked
                                                   else "không kịp suất nào sau các điểm trước"))
            continue
        s, walk = chosen
        warn = " ⚠ hai nguồn ghi giờ khác nhau" if s.get("conflict_source_id") else ""
        est = f" · giờ diễn {EST}" if "start" in (s.get("est") or []) else ""
        rows.append((_min(s["start"]), f"{s['start']}–{s['end']}  {g['name']} (đi bộ {walk}′, có mặt trước 5′){warn}{est}"))
        cur, loc = _min(s["end"]), loc_show
    for item in pending:
        if not try_item(item, end):
            skipped.append(f"{item['name']}: không còn đủ thời gian trước {_clock(end)} hoặc giờ đóng cửa {item['close']}")
    lines = []
    auto_names = {o["name"] for k, o, named in candidates if k == "show" and not named and (k, o) not in (suggested or [])}
    placed_auto = any(n in text for _, text in rows for n in auto_names)
    if added_shows and no_items:
        lines.append("Bạn chưa nêu trò cụ thể nên Vivu xếp các show có giờ diễn trong khung giờ của bạn.")
    elif added_shows and placed_auto:
        lines.append("Vivu thêm các show có giờ diễn vào khung giờ còn trống.")
    lines += [text for _, text in sorted(rows, key=lambda r: r[0])]
    lines.append(f"Kết thúc khoảng {_clock(cur)} · " + (f"giờ về dự kiến {_clock(end)}" if user_end
                 else f"giờ đóng cửa chung {_clock(end)} (bạn chưa nêu giờ về)"))
    lines += ["Không xếp được " + x for x in skipped]
    lines += group_ticket_lines(ds, heights, adults, children, budget, placed_items)
    ask = []
    if not user_start and not user_end:
        ask.append("giờ đến, giờ về")
    if (children or 0) > len(heights):
        ask.append("chiều cao của bé")
    if no_items:
        ask.append("trò hoặc sở thích (vd bé thích nước, cảm giác mạnh)")
    if ask:
        lines.append("Nhắn thêm " + ", ".join(ask) + " để Vivu xếp lịch sát hơn.")
    lines.append(f"Thời gian đi bộ, xếp hàng và thời lượng trò chơi là {EST}; giờ show theo nguồn công bố.")
    return lines


# ------------------------------------------------------------------ từ chỗ khách tới show (chặng ngoài công viên)
def _now_vn() -> int:
    import datetime
    from zoneinfo import ZoneInfo
    t = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    return t.hour * 60 + t.minute


def arrival_check(ds: dict[str, Any], show: dict[str, Any] | None, route: dict[str, Any] | None,
                  now: int | None) -> list[dict[str, Any]]:
    """Có kịp show không, tính từ chỗ khách: chỉ cộng chặng Google Maps đã trả về; chặng nào chưa có dữ liệu đáng tin
    thì nói là thiếu. Không dùng quãng đi bộ ước tính trong công viên, không dùng số của Vịnh Mây."""
    have, missing = [], []
    arrive = None
    if route:
        minutes = max(1, round(route["duration_s"] / 60))
        have.append(f"{route['mode_label']} tới {route['dest_name']}: khoảng {minutes} phút, "
                    f"{route['distance_m'] / 1000:.1f} km (Google Maps, tính lúc {route.get('at', '?')})".replace(".", ",", 1))
        if now is not None:
            arrive = now + minutes
            have.append(f"Nếu đi ngay bây giờ ({_clock(now)}), tới {route['dest_name']} khoảng {_clock(arrive)}.")
    else:
        missing.append("Thời gian từ chỗ bạn tới bến tàu: bấm “Ước tính thời gian đến” trong mục Đường đến khu vui chơi")
    timed = [s for s in (show or {}).get("sessions", []) if s["has_published_time"]]
    if show and timed:
        have.append(f"{show['name']}: suất " + ", ".join(s["start"] for s in timed)
                    + f" ({source_label(ds, timed[0]['source_id'])})")
        if arrive is not None:
            upcoming = [s for s in timed if _min(s["start"]) > arrive]
            if upcoming:
                s = upcoming[0]
                have.append(f"Tới bến lúc {_clock(arrive)} thì còn khoảng {_min(s['start']) - arrive} phút trước suất "
                            f"{s['start']} cho các chặng chưa tính bên dưới.")
            else:
                have.append(f"Tới bến lúc {_clock(arrive)} là đã sau suất cuối hôm nay ({timed[-1]['start']}).")
    elif show:
        missing.append(f"{show['name']}: chưa có giờ diễn công bố")
    missing.append("Thời gian chờ tàu hoặc cáp treo: chưa có lịch chuyến theo ngày")
    missing.append("Đi tàu ra đảo: nguồn chính thức ghi tàu cao tốc khoảng 15 phút, cano khoảng 10 phút, chưa rõ theo ngày")
    missing.append("Từ bến trên đảo vào cổng và tới chỗ diễn: chưa có dữ liệu đáng tin")
    reached = f"tới {route['dest_name']}" if route else "nào"
    verdict = (f"Vivu mới tính được chặng {reached}; chưa đủ dữ liệu để khẳng định kịp show."
               if route else "Vivu chưa tính được chặng nào từ chỗ bạn, nên chưa trả lời được có kịp show không.")
    return [{"title": "Từ chỗ bạn tới show", "lines": [verdict]},
            {"title": "Đã tính được", "lines": have or ["Chưa có"]},
            {"title": "Còn thiếu để xác nhận", "lines": missing}]


# ------------------------------------------------------------------ điểm vào
def height_check_lines(item: dict[str, Any], heights: list[int]) -> list[str]:
    """Đủ chiều cao tối thiểu chưa (chỉ khi trò có quy định đã công bố; không đoán điều kiện còn thiếu)."""
    min_h = item["restrictions"]["min_height_cm"]
    if min_h is None or not heights:
        return []
    return [f"Người cao {h} cm: {'đủ' if h >= min_h else 'chưa đủ'} chiều cao tối thiểu {min_h} cm" for h in heights]


def answer_nha_trang(text: str, ds: dict[str, Any], route: dict[str, Any] | None = None,
                     now: int | None = None, understood: dict[str, Any] | None = None,
                     ai_picked: list[tuple[str, Any]] | None = None,
                     ai_suggested: list[tuple[str, Any]] | None = None) -> dict[str, Any]:
    """route: kết quả Routes API của phiên (không có toạ độ hay địa chỉ khách); now: phút trong ngày, giờ Việt Nam.

    understood / ai_picked: kết quả model đã qua nha_trang_ai.validate (ý định, tên trong danh mục, chiều cao…).
    Không có thì dò từ khoá như cũ. Có hay không, mọi giờ, giá, quãng đi bộ vẫn tính từ dữ liệu ở đây.
    """
    park = ds["park"]
    demo = bool(ds.get("demo"))
    folded = fold(text)
    kw_picked = find_entities(text, ds)
    kw_heights, ages = find_heights(text), find_ages(text)
    start, end = find_times(text)
    intent = (understood or {}).get("intent")
    adults, children, budget = find_group(text)
    suggested: list[tuple[str, Any]] = []
    if understood:
        picked = list(ai_picked or []) or kw_picked
        suggested = list(ai_suggested or [])
        heights = understood["heights_cm"] or kw_heights
        ages = understood["ages"] or ages
        start = _min(understood["start"]) if understood.get("start") else start
        end = _min(understood["end"]) if understood.get("end") else end
        adults = understood.get("adults") if understood.get("adults") is not None else adults
        children = understood.get("children") if understood.get("children") is not None else children
        budget = understood.get("budget_vnd") or budget
    else:
        picked, heights = kw_picked, kw_heights
    places = [o["name"] for k, o in picked if k in ("show", "item")]
    # dò từ khoá luôn chạy; AI trả "other" (không xếp loại được) thì dùng kết quả dò từ khoá
    kw_ticket = bool(TICKET_WORDS.search((text or "").lower())) or (bool(heights) and not picked)
    kw_walk = bool(WALK_WORDS.search(folded))
    # câu kiểu Vịnh Mây: có giờ đến/về kèm thông tin nhóm hoặc ngân sách → nhờ xếp lịch
    trip_like = start is not None and (end is not None or adults or children or heights or budget)
    kw_plan = bool(PLAN_WORDS.search(folded)) or (demo and (len(places) >= 2 or trip_like))
    kw_arrival = bool(re.search(r"\bkip\b", folded)) and bool(ARRIVAL_WORDS.search(folded)) and len(places) <= 1
    if understood and intent != "other":
        wants_ticket = intent == "ticket"
        wants_plan = intent in ("plan", "walk_between")
        wants_walk = intent == "walk_between"
        asks_arrival = intent == "arrival"
    else:
        wants_ticket, wants_plan, wants_walk, asks_arrival = kw_ticket, kw_plan, kw_walk, kw_arrival
    sections: list[dict[str, Any]] = []
    shows_picked = [o for k, o in picked if k == "show"]

    if intent == "recommend":
        picked = picked + [x for x in suggested if x not in picked]
    if intent == "recommend" and not picked:
        # AI không chọn được tên hợp lệ: Python gợi ý từ dữ liệu, chỉ những trò có quy định chiều cao đã công bố
        shortest = min(heights) if heights else None
        ruled = [i for i in ds["catalog"] if i["kind"] == "ride" and not i["is_harbour"]
                 and i["restrictions"]["min_height_cm"] is not None
                 and (shortest is None or shortest >= i["restrictions"]["min_height_cm"])]
        lines = ["AI chưa chọn được trò cụ thể cho “" + ((understood or {}).get("preference") or "câu hỏi") + "”."]
        if ruled:
            who = f"người thấp nhất cao {shortest} cm" if shortest else "theo quy định đã công bố"
            lines.append(f"Trò có quy định chiều cao mà {who} đã đủ: " + ", ".join(
                f"{i['name']} (từ {i['restrictions']['min_height_cm']} cm)" for i in ruled) + ".")
        lines.append("Bạn nhắn tên khu (vd “Sea World”) hoặc tên trò để Vivu xem chi tiết.")
        sections.append({"title": "Gợi ý theo sở thích", "lines": lines})
        picked_for_detail = []
    elif intent == "recommend" and picked:
        pref = understood.get("preference") or "câu hỏi của bạn"
        shortest = min(heights) if heights else None
        fit, too_short = [], []
        for kind, obj in picked[:4]:  # Python lọc theo chiều cao tối thiểu đã công bố; không đoán điều kiện còn thiếu
            min_h = obj.get("restrictions", {}).get("min_height_cm") if kind == "item" else None
            (too_short if shortest is not None and min_h is not None and shortest < min_h else fit).append((kind, obj))
        lines = [f"AI chọn theo “{pref}”: " + (", ".join(o["name"] for _, o in fit) or "chưa có trò phù hợp") + "."]
        for _, obj in too_short:
            lines.append(f"Bỏ {obj['name']}: cần trẻ từ {obj['restrictions']['min_height_cm']} cm, người thấp nhất "
                         f"trong nhóm cao {shortest} cm ({source_label(ds, (obj.get('field_sources') or {}).get('min_height_cm') or obj['source_id'])}).")
        lines.append("Giờ, điều kiện và phí bên dưới lấy từ dữ liệu, không do AI đặt ra.")
        sections.append({"title": "Gợi ý theo sở thích", "lines": lines})
        picked_for_detail = fit
    elif asks_arrival:
        sections += arrival_check(ds, shows_picked[0] if shows_picked else None, route,
                                  now if now is not None else _now_vn())
        picked_for_detail = []
    elif wants_plan and demo:
        if wants_walk and len(places) == 2 and not re.search(r"(lich|xep|ke hoach|lo trinh)", folded):
            sections.append({"title": f"Đi từ {places[0]} sang {places[1]}", "lines": walk_verdict(ds, picked)})
        else:
            plan = build_demo_plan(ds, picked, start, end, heights, suggested, adults, children, budget)
            if plan:
                sections.append({"title": "Lịch gợi ý (bản demo)", "lines": plan})
            else:
                sections.append({"title": "Vivu cần biết bạn muốn đi đâu", "lines": [
                    "Nhắn tên trò chơi hoặc show muốn đi, kèm giờ đến (vd “9h đến, Alpine Coaster, Underwater World, "
                    "Biểu diễn chim”). Vivu sẽ xếp theo đúng giờ diễn và tính thời gian đi bộ."]})
        picked_for_detail = [] if (len(places) >= 3 or suggested or not places) else picked
    elif wants_plan:
        have, missing = schedule_gaps(ds, picked, wants_walk)
        if wants_walk and len(places) >= 2:
            verdict = (f"Vivu chưa thể xác nhận đi từ {places[0]} tới kịp {places[-1]}: còn thiếu dữ liệu bên dưới, "
                       "nên chưa tính được thời gian di chuyển.")
        else:
            verdict = "Vivu chưa thể xác nhận một lịch kịp giờ cho VinWonders Nha Trang: còn thiếu dữ liệu bên dưới."
        sections.append({"title": "Chưa xác nhận được lịch", "lines": [verdict]})
        if have:
            sections.append({"title": "Phần đã có dữ liệu", "lines": have})
        sections.append({"title": "Còn thiếu để xác nhận", "lines": missing})
        picked_for_detail = picked
    else:
        picked_for_detail = picked

    for kind, obj in picked_for_detail:
        if kind == "show":
            sections.append({"title": obj["name"] + " · biểu diễn", "lines": describe_show(ds, obj)})
        elif kind == "item":
            sections.append({"title": obj["name"], "lines": describe_item(ds, obj) + height_check_lines(obj, heights)})
        else:
            sections.append({"title": "Khu " + obj["name"], "lines": describe_zone(ds, obj)})

    if understood and intent != "other":
        show_tickets = wants_ticket
    else:
        show_tickets = (wants_ticket or heights or ages) and not (wants_plan and demo and heights and not wants_ticket)
    if show_tickets:
        sections.append({"title": "Vé vào cổng · giá tham khảo", "lines": describe_tickets(ds, heights, ages)})

    if not sections:
        timed = [s for s in ds["show_sessions"] if s["has_published_time"] and not s["is_harbour"]]
        timed.sort(key=lambda s: _min(s["start"]))
        sections.append({"title": "Vivu chưa nhận ra địa điểm hay show trong câu", "lines": [
            "Bạn thử nhắn tên show, trò chơi hoặc khu (vd “Tata Show”, “Zipline”, “Fairy Land”), "
            "hỏi vé theo chiều cao (vd “vé cho bé cao 100 cm”), hoặc nhờ xếp lịch "
            "(vd “9h đến, Alpine Coaster, Underwater World, Biểu diễn chim”).",
            "Show trong ngày: " + ", ".join(f"{s['name']} {s['start']}" for s in timed) + "."]})

    head = f"{park['name']} · dữ liệu công khai {_date_vi(park['snapshot_date'])}"
    head += f" · ô trống điền {EST}" if demo else " · chưa xác minh trực tiếp"
    body = [head]
    for sec in sections:
        body.append(sec["title"] + ":")
        body.extend("- " + line for line in sec["lines"])
    return {"output": "\n".join(body), "sections": sections, "header": head,
            "found": [(k, o["name"]) for k, o in picked], "intent": intent}
