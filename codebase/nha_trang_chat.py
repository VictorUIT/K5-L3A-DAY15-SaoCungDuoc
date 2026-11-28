"""Trả lời câu chat cho VinWonders Nha Trang từ snapshot công khai (data/nha_trang/). Không gọi model.

Nguyên tắc (data/nha_trang/DATA_CARD.md · Integration contract):
- Chỉ xác nhận phần có dữ liệu; mỗi giá trị kèm mã nguồn và ngày truy cập nguồn.
- Thiếu giờ, thời lượng, điều kiện tham gia hay thời gian đi bộ thì nói rõ thiếu gì, không đoán.
- Không dùng bất kỳ mặc định nào của Vịnh Mây (10 phút đi bộ, giá vé, điều kiện trò chơi).
- Giá vé luôn là giá tham khảo (current_quote=false), không phải báo giá hiện hành.

answer_nha_trang(text, ds) -> {"output": str, "sections": [{"title", "lines"}], "found": [...]}
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from pricing import SENIOR_BOUNDARY_NOTE, classify_traveler_ticket

# Tên gọi khác của show trong câu chat (khoá: tên show đã bỏ dấu, viết thường).
SHOW_ALIASES = {
    "tata show": ["tata show", "tata"],
    "bieu dien chim": ["bieu dien chim", "show chim", "bird show", "xem chim"],
    "nhac nuoc": ["nhac nuoc", "fountain", "nhac nuoc show"],
    "nang tien ca": ["nang tien ca", "mermaid", "tien ca"],
    "cho ca an": ["cho ca an", "fish feeding"],
    "welcome show": ["welcome show"],
    "stunt show": ["stunt show"],
}
TICKET_WORDS = re.compile(r"\b(ve|gia|bao nhieu tien|mat bao nhieu|ticket|price)\b")
PLAN_WORDS = re.compile(r"(di bo|di chuyen|kip|lich|xep|ke hoach|lo trinh|sang|toi kip|walk)")
WALK_WORDS = re.compile(r"(di bo|di chuyen|kip|walk|tu .+ (den|sang|toi|qua) )")


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


def source_label(ds: dict[str, Any], source_id: str | None) -> str:
    """'nguồn MAP · 27/11/2026' — mã nguồn kèm ngày truy cập trong sources.json."""
    if not source_id:
        return "chưa rõ nguồn"
    src = ds["sources_by_id"].get(source_id) or {}
    return f"nguồn {source_id} · {_date_vi(src.get('accessed_on'))}"


def _money(vnd: int | None) -> str:
    return "—" if vnd is None else f"{vnd:,}".replace(",", ".") + " đ"


# ------------------------------------------------------------------ nhận diện trong câu chat
def _index(ds: dict[str, Any]) -> list[tuple[str, str, Any]]:
    """Danh sách (cụm từ đã bỏ dấu, loại, đối tượng); cụm dài xét trước để 'Tata Show' không bị nuốt bởi 'Tata'."""
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
    """Các show, điểm, khu được nhắc tới, theo thứ tự xuất hiện trong câu; không trùng, không chồng lấn."""
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
    # Show đã nhận ra thì bỏ điểm diễn trùng tên (vd Stunt Show vừa là show vừa là địa điểm).
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


# ------------------------------------------------------------------ mô tả từng loại thông tin
def describe_show(ds: dict[str, Any], grp: dict[str, Any]) -> list[str]:
    park = ds["park"]
    lines = []
    venue = grp["venue_name"] or "chưa xác định chính xác địa điểm diễn"
    lines.append(f"Địa điểm: {venue}" + (f" · khu {grp['zone_name']}" if grp.get("zone_name") else ""))
    for s in grp["sessions"]:
        if s["has_published_time"]:
            lines.append(f"Suất {s['start']}–{s['end']} ({s['duration_minutes']} phút) · {source_label(ds, s['source_id'])}")
        else:
            lines.append(f"Suất chưa có giờ công bố · {source_label(ds, s['source_id'])}")
        if s.get("conflict_source_id"):
            other = (f"{s['conflict_start']}–{s['conflict_end']}" if s.get("conflict_start") else "giờ khác")
            lines.append(f"⚠ Hai nguồn ghi khác nhau: {s['source_id']} ghi {s['start']}–{s['end']}, "
                         f"{s['conflict_source_id']} ghi {other} ({source_label(ds, s['conflict_source_id'])}).")
        if s.get("exceeds_park_close"):
            lines.append(f"⚠ Giờ kết thúc {s['end']} sau giờ đóng cửa chung {park['close']} "
                         f"({source_label(ds, park['source_id'])}); cần hỏi lại khu vui chơi theo ngày đi.")
    lines.append("Trạng thái hôm nay: chưa xác minh trực tiếp (snapshot không có lịch diễn theo ngày).")
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
    lines = [f"Khu: {item['zone_name'] or 'chưa rõ'}" + (f" · mã bản đồ #{item['map_code']}" if item.get("map_code") else "")
             + f" · {source_label(ds, item['source_id'])}"]
    if item["open"] and item["close"]:
        lines.append(f"Giờ hoạt động: {item['open']}–{item['close']} · {source_label(ds, fs.get('open') or item['source_id'])}")
    else:
        lines.append("Giờ hoạt động: chưa có dữ liệu")
    rule = _restriction_text(item)
    if rule:
        lines.append(f"Điều kiện đã công bố: {rule} · {source_label(ds, fs.get('min_height_cm') or item['source_id'])} "
                     "(chưa phải bộ điều kiện đầy đủ)")
    else:
        lines.append("Điều kiện tham gia (chiều cao, tuổi, sức khoẻ): chưa có dữ liệu")
    inc, extra = item["pricing"]["included_in_ticket"], item["pricing"]["extra_vnd"]
    if inc is False:
        fee = f"phụ phí {_money(extra)} (giá tham khảo)" if extra is not None else "không nằm trong vé tiêu chuẩn, chưa có đơn giá"
        lines.append(f"Phí: {fee} · {source_label(ds, fs.get('included_in_ticket') or item['source_id'])}")
    elif inc is True:
        lines.append("Phí: đã gồm trong vé tiêu chuẩn")
    else:
        lines.append("Phí: chưa có dữ liệu có nằm trong vé tiêu chuẩn hay không")
    lines.append("Thời lượng: " + (f"{item['duration_minutes']} phút" if item["duration_minutes"] else "chưa có dữ liệu"))
    if item.get("map_warning"):
        lines.append("⚠ " + item["map_warning"])
    return lines


def describe_zone(ds: dict[str, Any], zone: dict[str, Any]) -> list[str]:
    count = sum(1 for i in ds["catalog"] if i["zone_id"] == zone["id"] and i["kind"] in ("ride", "sight"))
    hours = f"{zone['open']}–{zone['close']}" if zone["open"] and zone["close"] else "chưa có dữ liệu"
    lines = [f"Giờ khu: {hours} · {source_label(ds, zone['source_id'])}",
             f"{count} trò chơi / điểm tham quan trong danh mục"]
    if zone["is_harbour"]:
        lines.append("Khu lân cận Vinpearl Harbour, ngoài phạm vi công viên chính.")
    return lines


def describe_tickets(ds: dict[str, Any], heights: list[int], ages: list[int]) -> list[str]:
    bands = {b["id"]: b for b in ds["ticket_prices"]}
    price_src = source_label(ds, "PRICE")
    lines = []
    for h in heights:
        res = classify_traveler_ticket({"label": f"Người cao {h} cm", "height_cm": h}, ds["ticket_prices"])
        band = bands.get(res.get("band_id") or "")
        if not band:
            lines.append(f"Người cao {h} cm: chưa khớp nhóm vé nào trong bảng giá tham khảo.")
            continue
        low, high = band.get("min_height_cm"), band.get("max_height_cm_exclusive")
        group = (f"dưới {high} cm" if not low else f"từ {low} cm đến dưới {high} cm" if high else f"từ {low} cm trở lên")
        edge = f" (mốc đúng {low} cm được tính vào nhóm này)" if h == low else ""
        price = "miễn phí" if band["price_vnd"] == 0 else _money(band["price_vnd"])
        lines.append(f"Người cao {h} cm → nhóm vé {group}{edge}: {price} · giá tham khảo, {price_src}, chưa phải báo giá hiện hành")
    for a in ages:
        if a >= 60:
            res = classify_traveler_ticket({"label": f"Người {a} tuổi", "age": a}, ds["ticket_prices"])
            if res["status"] == "unresolved_senior_boundary":
                lines.append(f"Người đúng {a} tuổi: chưa xác định được nhóm vé. Nếu áp dụng mốc “từ 60 tuổi”: vé người "
                             f"cao tuổi {_money(bands['standard_senior']['price_vnd'])}; nếu áp dụng “trên 60 tuổi”: tính "
                             f"theo chiều cao. {SENIOR_BOUNDARY_NOTE}")
            elif res.get("price_vnd") is not None:
                lines.append(f"Người {a} tuổi → vé người cao tuổi: {_money(res['price_vnd'])} · giá tham khảo, {price_src} "
                             "(cần giấy tờ tuỳ thân)")
    if not lines:
        for b in ds["ticket_prices"]:
            low, high = b.get("min_height_cm"), b.get("max_height_cm_exclusive")
            if b.get("min_age"):
                group = f"người cao tuổi (mốc {b['min_age']} tuổi cần xác minh)"
            else:
                group = f"dưới {high} cm" if not low else f"từ {low} đến dưới {high} cm" if high else f"từ {low} cm trở lên"
            lines.append(f"{group}: {'miễn phí' if b['price_vnd'] == 0 else _money(b['price_vnd'])}")
        lines.append(f"Giá tham khảo, {price_src}, chưa phải báo giá hiện hành. Vé phân theo chiều cao; "
                     "nhắn chiều cao từng người (vd “bé cao 100 cm”) để Vivu xếp nhóm.")
    lines.append("Vé tiêu chuẩn gồm vào cổng và cáp treo khứ hồi; trò có phụ phí tính riêng.")
    return lines


def schedule_gaps(ds: dict[str, Any], picked: list[tuple[str, Any]], wants_walk: bool) -> tuple[list[str], list[str]]:
    """(phần đã có dữ liệu, phần còn thiếu) cho yêu cầu xếp lịch / đi bộ kịp giờ giữa các điểm đã nhắc."""
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
            missing.append("Snapshot chưa có dữ liệu thời gian đi bộ giữa các điểm (walking_distances.json đang trống); "
                           "Vivu không dùng số phút ước lượng")
    missing.append("Chưa có trạng thái mở cửa hoặc hàng chờ theo ngày (live_availability=false)")
    return have, missing


# ------------------------------------------------------------------ điểm vào
def answer_nha_trang(text: str, ds: dict[str, Any]) -> dict[str, Any]:
    park = ds["park"]
    folded = fold(text)
    picked = find_entities(text, ds)
    heights, ages = find_heights(text), find_ages(text)
    wants_ticket = bool(TICKET_WORDS.search(folded)) or (bool(heights) and not picked)
    wants_plan = bool(PLAN_WORDS.search(folded))
    wants_walk = bool(WALK_WORDS.search(folded))
    sections: list[dict[str, Any]] = []

    if wants_plan:
        have, missing = schedule_gaps(ds, picked, wants_walk)
        places = [o["name"] for k, o in picked if k in ("show", "item")]
        if wants_walk and len(places) >= 2:
            verdict = (f"Vivu chưa thể xác nhận đi từ {places[0]} tới kịp {places[-1]}: còn thiếu dữ liệu bên dưới, "
                       "nên chưa tính được thời gian di chuyển.")
        else:
            verdict = "Vivu chưa thể xác nhận một lịch kịp giờ cho VinWonders Nha Trang: còn thiếu dữ liệu bên dưới."
        sections.append({"title": "Chưa xác nhận được lịch", "lines": [verdict]})
        if have:
            sections.append({"title": "Phần đã có dữ liệu", "lines": have})
        sections.append({"title": "Còn thiếu để xác nhận", "lines": missing})

    for kind, obj in picked:
        if kind == "show":
            sections.append({"title": obj["name"] + " · biểu diễn", "lines": describe_show(ds, obj)})
        elif kind == "item":
            sections.append({"title": obj["name"], "lines": describe_item(ds, obj)})
        else:
            sections.append({"title": "Khu " + obj["name"], "lines": describe_zone(ds, obj)})

    if wants_ticket or heights or ages:
        sections.append({"title": "Vé vào cổng · giá tham khảo", "lines": describe_tickets(ds, heights, ages)})

    if not sections:
        timed = [s for s in ds["show_sessions"] if s["has_published_time"] and not s["is_harbour"]]
        sections.append({"title": "Vivu chưa nhận ra địa điểm hay show trong câu", "lines": [
            "Bạn thử nhắn tên show, trò chơi hoặc khu (vd “Tata Show”, “Zipline”, “Fairy Land”), "
            "hỏi vé theo chiều cao (vd “vé cho bé cao 100 cm”), hoặc hỏi đi từ điểm nào sang điểm nào.",
            "Show có giờ công bố: " + ", ".join(f"{s['name']} {s['start']}" for s in timed)
            + f" ({source_label(ds, 'MAP')})."]})

    head = (f"{park['name']} · snapshot công khai {_date_vi(park['snapshot_date'])} · chưa xác minh trực tiếp")
    body = [head]
    for sec in sections:
        body.append(sec["title"] + ":")
        body.extend("- " + line for line in sec["lines"])
    return {"output": "\n".join(body), "sections": sections, "header": head,
            "found": [(k, o["name"]) for k, o in picked]}
