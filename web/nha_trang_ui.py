"""Giao diện VinWonders Nha Trang trên web Vivu: tra cứu, giá vé tham khảo và chatbot (không gọi model).

Dữ liệu gốc: snapshot công khai data/nha_trang/ (27/11/2026). Công tắc "Điền ước tính demo" (mặc định bật) điền các
ô còn trống bằng số tự ước tính trong data/nha_trang/demo_estimates.json; mọi số đó có nhãn "ước tính demo".
Không dùng dữ liệu, giá hay quãng đi bộ của Vịnh Mây.
"""
from __future__ import annotations

import html
import re
import time
from typing import Any

import streamlit as st

import ai
import tracing
from agent import answer
from nha_trang_ai import INTENTS
from nha_trang_chat import EST, source_label, source_name, ticket_lines
from nha_trang_demo import apply_demo_estimates
from park_provider import KIND_LABELS_VI, NHA_TRANG_PARK_ID, filter_catalog
from pricing import SENIOR_BOUNDARY_NOTE
from review_intel import retrieve_attraction_experiences
from tools import money
from web import duong_den, planner
from web.common import beach_css, header, nha_trang_data, nha_trang_kb, nha_trang_reviews

DEMO_KEY = "nt_demo"
NT_CSS = """
<style>
.nt-tag {display: inline-block; font-size: .7rem; font-weight: 600; border-radius: 6px; padding: .05rem .4rem;
  margin-left: .35rem; vertical-align: middle; white-space: nowrap;}
.nt-tag.src {background: #EEF5FB; color: #36607F;}
.nt-tag.est {background: #FFF3E0; color: #B25400; border: 1px dashed #F3B675;}
.nt-tag.warn {background: #FFF1E6; color: #C24D00;}
.nt-tag.harbour {background: #EEF2F7; color: #3D5166;}
.nt-note {font-size: .84rem; color: #5B6B7A; margin-top: .45rem; line-height: 1.4;}
.nt-note.warn {color: #A84300;}
.nt-info {background: #F2F8FD; border: 1px solid #CFE7F5; border-left: 4px solid #0B84D9; border-radius: 12px;
  padding: .75rem 1rem; margin: .4rem 0 .6rem; font-size: .92rem; line-height: 1.55; color: #1F4A66;}
.vm-card dd .nt-tag {font-weight: 600;}
.vm-card dd {white-space: normal;}
.nt-h {font-weight: 800; font-size: 1.08rem; color: #0F3550; margin: .1rem 0 .4rem;}
.nt-sub {font-weight: 700; color: #0F3550; margin: .8rem 0 .3rem;}
.nt-tlwrap {border-left: 2px dashed #9FD1F2; margin: .3rem 0 .3rem .45rem; padding-left: .2rem;}
.nt-tl {display: grid; grid-template-columns: 6.6rem 1.6rem 1fr; align-items: start; gap: .35rem; padding: .32rem 0 .32rem .4rem;
  border-bottom: 1px solid #EEF3F7;}
.nt-tl:last-child {border-bottom: 0;}
.nt-tl .t {font-weight: 700; font-variant-numeric: tabular-nums; color: #0B5E96; white-space: nowrap;}
.nt-tl .ic {font-size: 1.1rem; line-height: 1.3;}
.nt-tl b {font-weight: 650;}
.nt-tl small {display: block; color: #6B7B8A; font-size: .8rem; margin-top: .05rem;}
.nt-grid {display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: .6rem; margin: .3rem 0 .5rem;}
.nt-card {background: #F8FBFE; border: 1px solid #DCEBF6; border-radius: 12px; padding: .65rem .8rem;}
.nt-card.wide {margin: .4rem 0 .5rem;}
.nt-card.miss {background: #FFF9F2; border-color: #FFE0BF;}
.nt-card-h {display: flex; gap: .45rem; align-items: center; font-weight: 750; color: #0F3550; margin-bottom: .35rem;}
.nt-card-h span {font-size: 1.15rem;}
.nt-kv {display: grid; grid-template-columns: 1.4rem 1fr; gap: .3rem; font-size: .9rem; line-height: 1.45; margin: .12rem 0;}
.nt-kv .ic {text-align: center;}
.nt-est {font-size: .72rem; font-weight: 600; color: #B25400; background: #FFF3E0; border: 1px dashed #F3B675;
  border-radius: 5px; padding: 0 .3rem; margin-left: .3rem; white-space: nowrap;}
.nt-cardsrc {font-size: .74rem; color: #6B7B8A; border-top: 1px dashed #DCEBF6; margin-top: .45rem; padding-top: .35rem;}
.nt-kv.warn {color: #A84300;}
.nt-lead {display: grid; grid-template-columns: 1.8rem 1fr; gap: .4rem; background: #F2F8FD; border: 1px solid #CFE7F5;
  border-radius: 12px; padding: .65rem .8rem; margin: .2rem 0 .5rem;}
.nt-lead > span {font-size: 1.3rem; line-height: 1.2;}
.nt-note {font-size: .86rem; color: #36607F; margin: .1rem 0 .3rem;}
.nt-foot {font-size: .8rem; color: #6B7B8A; margin: .25rem 0;}
.nt-hint {background: #FFF7E8; border: 1px solid #FFDDA8; color: #7A4B00; border-radius: 10px; padding: .45rem .7rem;
  font-size: .88rem; margin: .5rem 0 .2rem;}
.nt-skip {font-size: .85rem; color: #6B4A2B; margin: .35rem 0;}
.nt-skip summary {cursor: pointer; font-weight: 600;}
.nt-skip div {margin: .15rem 0 .15rem .4rem;}
.nt-badges {display: flex; flex-wrap: wrap; gap: .35rem; margin: .2rem 0;}
.nt-badge {font-size: .82rem; font-weight: 600; border-radius: 999px; padding: .15rem .65rem;}
.nt-badge.ok {background: #E6F6EC; color: #146C3A;}
.nt-badge.bad {background: #FFEDE3; color: #B23C00;}
.nt-chips {display: flex; flex-wrap: wrap; gap: .3rem; align-items: center; margin: .55rem 0 .15rem;}
.nt-chips .lbl {font-size: .78rem; color: #5B6B7A; font-weight: 600; margin-right: .1rem;}
.nt-chip {font-size: .76rem; background: #EEF5FB; color: #315472; border-radius: 999px; padding: .1rem .55rem;}
@media (max-width: 640px) {
  .nt-tl {grid-template-columns: 6.4rem 1.3rem 1fr; gap: .25rem; padding-left: .25rem;}
  .nt-tl .t {font-size: .88rem;}
  .nt-grid {grid-template-columns: 1fr;}
}
</style>
"""


# ---------------------------------------------------------------- dữ liệu
@st.cache_resource
def _demo_dataset():
    return apply_demo_estimates(nha_trang_data())


def demo_on() -> bool:
    st.session_state.setdefault(DEMO_KEY, True)
    return bool(st.session_state[DEMO_KEY])


def dataset() -> dict[str, Any]:
    return _demo_dataset() if demo_on() else nha_trang_data()


def _toggle_demo(widget_key: str) -> None:
    st.session_state[DEMO_KEY] = bool(st.session_state.get(widget_key))


def demo_switch(where: str) -> None:
    """Công tắc dùng chung hai trang (giá trị giữ ở nt_demo, widget mỗi trang một khoá)."""
    key = f"nt_demo_{where}"
    st.session_state[key] = demo_on()
    st.toggle("Điền ước tính demo cho ô còn trống", key=key, on_change=_toggle_demo, args=(key,),
              help="Bật: giờ khu, thời lượng, xếp hàng, quãng đi bộ còn trống được điền số nhóm tự ước tính, có nhãn "
                   "“ước tính demo”. Tắt: chỉ hiện dữ liệu công khai, ô trống để trống. Không ước tính chiều cao "
                   "tối thiểu hay giá vé.")


# ---------------------------------------------------------------- nhãn và định dạng
def tag_src(ds, source_id) -> str:
    return f'<span class="nt-tag src">{html.escape(source_label(ds, source_id).replace("nguồn: ", ""))}</span>'


def tag_est() -> str:
    return f'<span class="nt-tag est">{EST}</span>'


def tag_for(ds, obj, field, source_id) -> str:
    return tag_est() if field in (obj.get("est") or []) else tag_src(ds, source_id)


def _val(text: str, tag: str = "") -> str:
    return html.escape(text) + tag


def _card(kind_label: str, title: str, rows: list[tuple[str, str]], notes: str = "", kind_class: str = "",
          extra_badge: str = "") -> str:
    dl = "".join(f"<dt>{html.escape(k)}</dt><dd>{v}</dd>" for k, v in rows)
    return (f'<div class="vm-card"><span class="vm-kind{kind_class}">{html.escape(kind_label)}</span>{extra_badge}'
            f'<h4>{html.escape(title)}</h4><dl>{dl}</dl>{notes}</div>')


def _status_text(ds, status) -> str:
    if status == "planned_or_unavailable":
        return "Đang xây dựng, chưa mở"
    if status == "demo_open":
        return ds["demo_live_text"]
    return "Chưa có thông tin theo ngày"


def item_card(ds, item) -> str:
    fs = item.get("field_sources") or {}
    r = item["restrictions"]
    rows = [("Khu", _val(item["zone_name"] or "—"))]
    if item["open"] and item["close"]:
        rows.append(("Giờ mở", _val(f"{item['open']}–{item['close']}", tag_for(ds, item, "open", fs.get("open") or item["source_id"]))))
    else:
        rows.append(("Giờ mở", _val("Chưa công bố")))
    if r["min_height_cm"] is not None:
        rows.append(("Chiều cao", _val(f"Trẻ từ {r['min_height_cm']} cm", tag_src(ds, fs.get("min_height_cm") or item["source_id"]))))
    elif item["kind"] == "ride":
        rows.append(("Chiều cao", _val(ds.get("demo_rule_text") or "Chưa công bố")))
    inc, extra = item["pricing"]["included_in_ticket"], item["pricing"]["extra_vnd"]
    if inc is False:
        fee = f"Phụ phí {money(extra)}" if extra is not None else "Mua thêm, ngoài vé"
        rows.append(("Phí", _val(fee, tag_src(ds, fs.get("included_in_ticket") or item["source_id"]))))
    elif inc is True:
        rows.append(("Phí", _val("Gồm trong vé", tag_for(ds, item, "included_in_ticket", fs.get("included_in_ticket") or item["source_id"]))))
    if item["duration_minutes"]:
        dur = f"{item['duration_minutes']} phút" + (f" · chờ ~{item['queue_minutes']} phút" if item.get("queue_minutes") else "")
        rows.append(("Thời lượng", _val(dur, tag_for(ds, item, "duration_minutes", item["source_id"]))))
    rows.append(("Hôm nay", _val(_status_text(ds, item["status"]), tag_est() if "status" in item.get("est", []) else "")))
    notes = f'<div class="nt-note warn">⚠ {html.escape(item["map_warning"])}</div>' if item.get("map_warning") else ""
    harbour = '<span class="nt-tag harbour">Vinpearl Harbour</span>' if item["is_harbour"] else ""
    title = (f"{item['map_code']} · " if item.get("map_code") else "") + item["name"]
    return _card(KIND_LABELS_VI.get(item["kind"], item["kind"]), title, rows, notes, extra_badge=harbour)


def show_card(ds, grp) -> str:
    park = ds["park"]
    times = []
    for s in grp["sessions"]:
        if s["has_published_time"]:
            times.append(_val(f"{s['start']}–{s['end']}", tag_for(ds, s, "start", s["source_id"])))
        else:
            times.append(_val("Chưa công bố"))
    if grp.get("venue_name"):
        venue = _val(grp["venue_name"] + (f" · {grp['zone_name']}" if grp.get("zone_name") else ""))
    elif grp.get("venue_text"):
        venue = _val(grp["venue_text"], tag_est())
    else:
        venue = _val("Chưa xác định")
    rows = [("Suất diễn", "<br>".join(times)), ("Địa điểm", venue)]
    first = grp["sessions"][0]
    if first.get("duration_minutes"):
        rows.append(("Thời lượng", _val(f"{first['duration_minutes']} phút")))
    rows.append(("Hôm nay", _val(ds["demo_live_text"], tag_est()) if ds.get("demo") else _val("Chưa có thông tin theo ngày")))
    notes = ""
    for s in grp["sessions"]:
        if s.get("conflict_source_id"):
            notes += (f'<div class="nt-note warn">⚠ Hai nguồn ghi khác nhau: {html.escape(source_name(s["source_id"]))} '
                      f'{s["start"]}–{s["end"]} · {html.escape(source_name(s["conflict_source_id"]))} '
                      f'{s.get("conflict_start") or "?"}–{s.get("conflict_end") or "?"}. Vivu dùng giờ theo '
                      f'{html.escape(source_name(s["source_id"]))}.</div>')
        if s.get("exceeds_park_close"):
            notes += (f'<div class="nt-note warn">⚠ Kết thúc {s["end"]}, sau giờ đóng cửa chung {park["close"]}: '
                      'nên hỏi lại khu vui chơi theo ngày đi.</div>')
    badge = '<span class="nt-tag warn">Giờ chưa thống nhất</span>' if grp["has_discrepancy"] else ""
    if grp["is_harbour"]:
        badge += '<span class="nt-tag harbour">Vinpearl Harbour</span>'
    return _card("Biểu diễn", grp["name"], rows, notes, kind_class=" show", extra_badge=badge)


def zone_card(ds, z) -> str:
    items = [i for i in ds["catalog"] if i["zone_id"] == z["id"] and i["kind"] in ("ride", "sight")]
    total = sum(1 for i in ds["catalog"] if i["zone_id"] == z["id"])
    mr = f"{z['map_range'][0]}–{z['map_range'][1]}" if len(z["map_range"]) == 2 else "—"
    hours = (_val(f"{z['open']}–{z['close']}", tag_for(ds, z, "open", z["source_id"])) if z["open"] and z["close"]
             else _val("Chưa công bố"))
    rows = [("Giờ mở", hours), ("Số trên bản đồ", _val(mr)),
            ("Điểm trong khu", _val(f"{total} điểm · {len(items)} trò chơi/tham quan"))]
    if items:
        rows.append(("Nổi bật", _val(", ".join(i["name"] for i in items[:4]))))
    badge = '<span class="nt-tag harbour">Khu lân cận</span>' if z["is_harbour"] else ""
    return _card("Phân khu", z["name"], rows, f'<div class="nt-note">{tag_src(ds, z["source_id"])}</div>', extra_badge=badge)


def price_card(ds, b) -> str:
    if b.get("min_age"):
        cond = "Người cao tuổi"
    else:
        low, high = b.get("min_height_cm"), b.get("max_height_cm_exclusive")
        cond = f"Dưới {high} cm" if not low else f"Từ {low} đến dưới {high} cm" if high else f"Từ {low} cm trở lên"
    rows = [("Giá tham khảo", _val("Miễn phí" if b["price_vnd"] == 0 else money(b["price_vnd"]), tag_src(ds, b["source_id"]))),
            ("Gồm", _val("Vào cổng + cáp treo khứ hồi"))]
    note = ('<div class="nt-note warn">⚠ Mốc đúng 60 tuổi: hai nguồn ghi “từ 60” và “trên 60”, cần hỏi lại khi mua.</div>'
            if b.get("min_age") else "")
    return _card("Vé vào cổng", cond, rows, note)


# ---------------------------------------------------------------- chatbot
NT_EXAMPLES = {
    "lich": "Nhà mình 2 vợ chồng với bé cao 1m25, 9 giờ tới, 5 giờ chiều về, có 3 triệu, bé thích cảm giác mạnh",
    "lich2": "9h đến, về 17h, Alpine Coaster, Underwater World, Biểu diễn chim, Sky Wheel, bé cao 1m15",
    "tata": "Tata Show mấy giờ diễn?",
    "ve100": "Vé cho bé cao đúng 100 cm bao nhiêu?",
    "dibo": "Đi bộ từ Zipline sang Tata Show có kịp không?",
    "kip": "Từ resort đi bây giờ có kịp Tata Show không?",
    "goiy": "Bé nhà mình cao 1m15, thích nước, nên chơi gì?",
}


def nt_setup() -> None:
    """Lịch sử riêng của Nha Trang (nt_history): không đọc lịch sử hay điều kiện t_* của Vịnh Mây."""
    st.session_state.setdefault("nt_history", [])
    st.session_state.setdefault("nt_pending", None)


def _on_nt_chat() -> None:
    st.session_state.nt_pending = st.session_state.get("nt_chat")


def _send_nt_example(key: str) -> None:
    st.session_state.nt_pending = NT_EXAMPLES[key]


def _nt_reset() -> None:
    st.session_state.nt_history, st.session_state.nt_pending = [], None


def _understood_text(u: dict[str, Any] | None) -> str:
    if not u:
        return ""
    parts = [] if u["intent"] == "other" else [INTENTS.get(u["intent"], u["intent"])]  # "other": đã dùng dò từ khoá
    if u["places"]:
        parts.append(", ".join(u["places"]))
    if u.get("suggested"):
        parts.append("gợi ý: " + ", ".join(u["suggested"]))
    if u.get("adults") or u.get("children"):
        parts.append(f"{u.get('adults') or 0} người lớn, {u.get('children') or 0} trẻ")
    if u.get("budget_vnd"):
        parts.append(f"ngân sách {u['budget_vnd']:,}".replace(",", ".") + " đ")
    if u["heights_cm"]:
        parts.append("cao " + ", ".join(f"{h} cm" for h in u["heights_cm"]))
    if u["ages"]:
        parts.append(", ".join(f"{a} tuổi" for a in u["ages"]))
    if u.get("start") or u.get("end"):
        parts.append(f"{u.get('start') or '?'}–{u.get('end') or '?'}")
    if u.get("preference"):
        parts.append("sở thích: " + u["preference"])
    return " · ".join(parts)


def nt_process() -> None:
    """Một tin: (nếu có model thật và còn lượt) model đọc hiểu câu → Python kiểm và tính → lưu vào phiên.

    Dùng chung khoá trace, hạn mức mỗi phiên và mỗi giờ với chatbot Vịnh Mây (web/planner.py). Hết lượt hay model lỗi
    thì vẫn trả lời bằng dò từ khoá. Kết quả chỉ đường (nt_route) chỉ vào phần Python, không gửi cho model.
    """
    s = st.session_state
    text, s.nt_pending = s.get("nt_pending"), None
    if not text:
        return
    s.setdefault("used", 0)
    s.nt_history.append({"role": "user", "text": text})
    use_model, note, summary = ai.MODEL_PROVIDER != "fake", None, None
    if not use_model:
        note = "Máy chủ chưa cấu hình model thật: trả lời bằng dò từ khoá."
    elif s.used >= planner.MAX_PER_SESSION:
        use_model, note = False, f"Phiên đã dùng hết {planner.MAX_PER_SESSION} lượt AI: trả lời bằng dò từ khoá."
    pool = planner.shared()
    try:
        with pool["lock"]:
            if use_model:
                now = time.time()
                while pool["calls"] and now - pool["calls"][0] > 3600:
                    pool["calls"].popleft()
                if len(pool["calls"]) >= planner.MAX_PER_HOUR:
                    use_model, note = False, "Web đã đạt giới hạn lượt AI trong giờ này: trả lời bằng dò từ khoá."
                else:
                    pool["calls"].append(now)
                    tracing.begin("web")
            try:
                with st.spinner("Vivu đang đọc câu hỏi…" if use_model else "Vivu đang tra dữ liệu…"):
                    reply = answer(text, park_id=NHA_TRANG_PARK_ID, demo=demo_on(), route=s.get("nt_route"),
                                   use_model=use_model)
            finally:
                if use_model:
                    summary, _events = tracing.end()
        if use_model:
            s.used += 1
        if reply.get("model_error") is not None:
            note = planner.friendly_error(reply["model_error"]) + " Vivu trả lời bằng dò từ khoá."
        s.nt_history.append({"role": "bot", "header": reply["header"], "sections": reply["sections"],
                             "found": reply["found"], "understood": _understood_text(reply.get("understood")),
                             "dropped": (reply.get("understood") or {}).get("dropped", []),
                             "note": note, "summary": summary, "model_meta": reply.get("model_meta")})
    except Exception as e:  # dữ liệu hỏng hay lỗi khác: báo gọn
        s.nt_history.append({"role": "bot", "error": f"Có lỗi khi đọc dữ liệu Nha Trang ({type(e).__name__})."})


# ---------------------------------------------------------------- hiển thị câu trả lời: gọn, có icon
LINE_ICONS = [  # (tiền tố dòng, icon, bỏ tiền tố khi hiện?)
    ("Khu:", "🗺️", True), ("Giờ hoạt động:", "🕘", True), ("Giờ khu:", "🕘", True), ("Điều kiện:", "📏", True),
    ("Phí:", "💳", True), ("Thời lượng:", "⏱️", True), ("Trạng thái hôm nay:", "🟢", True), ("Địa điểm:", "📍", True),
    ("Suất", "⏰", False), ("Người cao", "📏", False), ("Đi bộ", "🚶", False), ("Muốn kịp", "⏰", False),
    ("Nếu đi ngay", "🚗", False), ("Tới bến", "⏳", False),
]
SECTION_ICONS = [("Lịch gợi ý", "🗓️"), ("Gợi ý theo sở thích", "✨"), ("Vé vào cổng", "🎟️"), ("Đi từ", "🚶"),
                 ("Từ chỗ bạn", "🧭"), ("Đã tính được", "✅"), ("Phần đã có dữ liệu", "✅"), ("Còn thiếu", "❓"),
                 ("Chưa xác nhận", "⛔"), ("Khu ", "🗺️"), ("Vivu chưa nhận ra", "💬"), ("Vivu cần biết", "💬")]
ROW_RE = re.compile(r"^(\d\d:\d\d)(?:–(\d\d:\d\d))?\s+(.+?)(?:\s+\((.+?)\))?(\s*⚠ hai nguồn ghi giờ khác nhau)?"
                    r"(\s*·\s*giờ diễn ước tính demo)?$")


def _rich(text: str) -> str:
    """Escape + tách 'nguồn: …' thành nhãn nhỏ, 'ước tính demo' thành nhãn cam."""
    body, _, src = text.partition(" · nguồn: ")
    out = html.escape(body).replace(" · " + EST, " " + tag_est()).replace("(" + EST + ")", tag_est()).replace(EST, tag_est())
    if src:
        out += f'<span class="nt-tag src">{html.escape(src.rstrip(")."))}</span>'
    return out


def _short_est() -> str:
    return '<span class="nt-est">ước tính</span>'


def _kv(line: str, sources: list[str] | None = None) -> str:
    """Một dòng có icon. sources != None: tách nguồn ra (gom ở cuối thẻ), ước tính hiện thành chữ ngắn."""
    if sources is not None:
        line, _, src = line.partition(" · nguồn: ")
        if src:
            name = src.rstrip(").").split(" · ")[0]
            if name not in sources:
                sources.append(name)
        line = line.replace(" · " + EST, "\x00").replace(" (" + EST + ")", "\x00").replace(EST, "\x00")
    warn = line.startswith("⚠")
    icon, text = "•", line
    if warn:
        icon, text = "⚠️", line.lstrip("⚠ ").strip()
    else:
        for prefix, ic, strip in LINE_ICONS:
            if line.startswith(prefix):
                icon, text = ic, (line[len(prefix):].strip() if strip else line)
                break
    if line.startswith("Người cao") and ("chưa đủ" in line or "đủ chiều cao" in line):
        icon = "❌" if "chưa đủ" in line else "✅"
    body = _rich(text) if sources is None else html.escape(text).replace("\x00", _short_est())
    return f'<div class="nt-kv{" warn" if warn else ""}"><span class="ic">{icon}</span><span>{body}</span></div>'


def _reply_card(icon: str, title: str, lines: list[str], wide: bool = False) -> str:
    sources: list[str] = []
    rows = "".join(_kv(l, sources) for l in lines)
    foot = f'<div class="nt-cardsrc">📎 {html.escape(" · ".join(sources))} · 27/11/2026</div>' if sources else ""
    return (f'<div class="nt-card{" wide" if wide else ""}"><div class="nt-card-h"><span>{icon}</span>{html.escape(title)}</div>'
            + rows + foot + "</div>")


def _section_icon(title: str) -> str:
    if title.endswith("· biểu diễn"):
        return "🎭"
    return next((ic for p, ic in SECTION_ICONS if title.startswith(p)), "🎢")


def _ticket_block(lines: list[str]) -> str:
    rows, total, badges = [], None, []
    price_src = next((l.split("nguồn: ", 1)[1].rstrip(").") for l in lines if "nguồn: Bảng giá" in l), None)
    for l in lines:
        if l.startswith(("Tổng vé", "Tổng vé đã tính")):
            label, _, rest = l.partition(": ")
            amount = rest.split(" (")[0]
            total = (label, amount, rest[len(amount):].strip(" ()"))
        elif l.startswith("Trong ngân sách"):
            badges.append(f'<span class="nt-badge ok">✅ {html.escape(l.rstrip("."))}</span>')
        elif l.startswith(("⚠ Vượt ngân sách", "Ngân sách")):
            badges.append(f'<span class="nt-badge bad">⚠️ {html.escape(l.lstrip("⚠ ").rstrip("."))}</span>')
        elif l.startswith(("Vé tiêu chuẩn", "Giá tham khảo")):
            rows.append(f'<div class="nt-foot">{_rich(l)}</div>')
        elif l.startswith(("Chưa gồm phụ phí", "Còn ")):
            rows.append(f'<div class="nt-kv"><span class="ic">ℹ️</span><span>{_rich(l)}</span></div>')
        else:
            text = re.sub(r"^Người cao (\d+) cm → nhóm vé ", r"Bé/người cao \1 cm · ", l).split(" · giá tham khảo")[0]
            rows.append(f'<div class="nt-kv"><span class="ic">🎟️</span><span>{_rich(text)}</span></div>')
    out = "".join(rows)
    if total:
        out += (f'<div class="vm-total"><span>{html.escape(total[0])}</span><b>{html.escape(total[1])}</b></div>'
                f'<div class="nt-foot">{_rich(total[2]) if total[2] else ""}</div>')
    if badges:
        out += '<div class="nt-badges">' + "".join(badges) + "</div>"
    if price_src and not total:
        out += f'<div class="nt-cardsrc">📎 {html.escape(price_src)} · giá tham khảo</div>'
    return out


def _plan_block(lines: list[str]) -> str:
    timeline, skipped, tickets, notes, hints, end_line = [], [], [], [], [], ""
    for l in lines:
        m = ROW_RE.match(l)
        if m:
            start, end, name, detail, conflict, est = m.groups()
            icon = "🚪" if name.startswith("Vào cổng") else ("🎭" if detail and "có mặt trước" in detail else "🎢")
            tags = ""
            if est:
                tags += tag_est().replace(EST, "giờ ước tính")
            if conflict:
                tags += '<span class="nt-tag warn">⚠ 2 nguồn lệch giờ</span>'
            when = start + (f"–{end}" if end else "")
            timeline.append(f'<div class="nt-tl"><span class="t">{when}</span><span class="ic">{icon}</span>'
                            f'<span><b>{html.escape(name)}</b>{tags}'
                            + (f'<small>{html.escape(detail)}</small>' if detail else "") + "</span></div>")
        elif l.startswith("Không xếp được "):
            skipped.append(l[len("Không xếp được "):])
        elif l.startswith(("Người cao", "Tổng vé", "Trong ngân sách", "⚠ Vượt", "Ngân sách", "Còn ", "Chưa gồm phụ phí", "Nhắn số người"))\
                or re.match(r"\d+ người lớn ×", l):
            tickets.append(l)
        elif l.startswith("Nhắn thêm"):
            hints.append(l)
        elif l.startswith("Kết thúc khoảng"):
            end_line = l
        else:
            notes.append(l)
    out = ""
    for n in notes:
        if not n.startswith("Thời gian đi bộ"):
            out += f'<div class="nt-note">{_rich(n)}</div>'
    out += '<div class="nt-tlwrap">' + "".join(timeline) + "</div>"
    if end_line:
        out += f'<div class="nt-foot">🏁 {html.escape(end_line)}</div>'
    if skipped:
        out += ('<details class="nt-skip"><summary>⛔ Không xếp được ' + str(len(skipped)) + " điểm</summary>"
                + "".join(f"<div>• {_rich(s)}</div>" for s in skipped) + "</details>")
    if tickets:
        out += '<div class="nt-sub">🎟️ Vé vào cổng · giá tham khảo</div>' + _ticket_block(tickets)
    for h in hints:
        out += f'<div class="nt-hint">💬 {html.escape(h)}</div>'
    est_note = next((n for n in notes if n.startswith("Thời gian đi bộ")), None)
    if est_note:
        out += f'<div class="nt-foot">{_rich(est_note)}</div>'
    return out


def _render_sections(sections: list[dict[str, Any]]) -> None:
    cards: list[str] = []

    def flush():
        if cards:
            st.markdown('<div class="nt-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)
            cards.clear()

    for sec in sections:
        title, lines, icon = sec["title"], sec["lines"], _section_icon(sec["title"])
        if title.startswith("Lịch gợi ý"):
            flush()
            st.markdown(f'<div class="nt-h">{icon} {html.escape(title)}</div>' + _plan_block(lines), unsafe_allow_html=True)
        elif title.startswith("Vé vào cổng"):
            flush()
            st.markdown(f'<div class="nt-card wide"><div class="nt-card-h"><span>{icon}</span>{html.escape(title)}</div>'
                        + _ticket_block(lines) + "</div>", unsafe_allow_html=True)
        elif title.startswith(("Gợi ý theo sở thích", "Vivu chưa nhận ra", "Vivu cần biết", "Chưa xác nhận",
                               "Từ chỗ bạn", "Đi từ")):
            flush()
            first, rest = lines[0], lines[1:]
            body = "".join(_kv(l) for l in rest)
            st.markdown(f'<div class="nt-lead"><span>{icon}</span><div><b>{html.escape(title)}</b>'
                        f'<div>{_rich(first)}</div>{body}</div></div>', unsafe_allow_html=True)
        elif title.startswith(("Đã tính được", "Phần đã có dữ liệu", "Còn thiếu")):
            flush()
            ic = "✅" if not title.startswith("Còn thiếu") else "❓"
            st.markdown(f'<div class="nt-card wide {"miss" if ic == "❓" else ""}"><div class="nt-card-h"><span>{ic}</span>'
                        f'{html.escape(title)}</div>'
                        + "".join(f'<div class="nt-kv"><span class="ic">{"✓" if ic == "✅" else "·"}</span>'
                                  f'<span>{_rich(l)}</span></div>' for l in lines) + "</div>", unsafe_allow_html=True)
        else:  # thẻ trò chơi / show / khu
            cards.append(_reply_card(icon, title.replace(" · biểu diễn", ""), lines))
    flush()


def _render_nt_bot(i: int, msg: dict[str, Any]) -> None:
    with st.container(key=f"vm_bot_nt_{i}"):
        if msg.get("error"):
            st.error(msg["error"])
            return
        _render_sections(msg["sections"])
        chips = []
        if msg.get("understood"):
            chips += [f'<span class="nt-chip">{html.escape(p)}</span>' for p in msg["understood"].split(" · ")]
        foot = ""
        if chips:
            foot += '<div class="nt-chips"><span class="lbl">🤖 Vivu hiểu</span>' + "".join(chips) + "</div>"
        if msg.get("note"):
            foot += f'<div class="nt-foot">ℹ️ {html.escape(msg["note"])}</div>'
        foot += f'<div class="nt-foot">📚 {html.escape(msg["header"])}</div>'
        st.markdown(foot, unsafe_allow_html=True)
        with st.expander("Chi tiết kỹ thuật"):
            found = ", ".join(name for _, name in msg["found"]) or "không có"
            mm, sm = msg.get("model_meta"), msg.get("summary")
            if mm:
                st.caption("AI đọc hiểu câu hỏi · Model: %s · gọi model 1 lần · token vào %s / ra %s"
                           % (mm.get("model") or "?", mm.get("tokens_in"), mm.get("tokens_out")))
            elif sm and sm.get("model_calls"):
                st.caption("AI đọc hiểu câu hỏi · Model: %s · gọi model %d lần (lỗi) · token vào %d / ra %d"
                           % (", ".join(sm["models"]), sm["model_calls"], sm["tokens_in"], sm["tokens_out"]))
            else:
                st.caption("Không gọi model lần này (dò từ khoá).")
            st.caption(f"Điểm dùng để trả lời: {found}. Giờ, giá, quãng đi bộ và nguồn do Python tính từ dữ liệu "
                       "công khai 27/11/2026; không dùng dữ liệu của Vịnh Mây; không gửi vị trí của bạn cho AI.")
            if msg.get("dropped"):
                st.caption("Python đã bỏ phần AI trả không hợp lệ: " + "; ".join(msg["dropped"]))


def nt_conversation(inline: bool) -> None:
    s = st.session_state
    if not s.nt_history:
        with st.container(key="vm_bot_hello_nt"):
            st.markdown('<p class="vm-hello">Chào bạn, mình là Vivu. Bạn muốn chơi gì ở VinWonders Nha Trang?</p>'
                        '<p class="vm-muted">Nhắn giờ đến và các trò, show muốn đi, mình xếp lịch kịp giờ diễn. '
                        'Hoặc hỏi giờ show, vé theo chiều cao, đi bộ giữa hai điểm. Bấm thử:</p>',
                        unsafe_allow_html=True)
            for key, text in NT_EXAMPLES.items():
                st.button(f"“{text}”", key=f"ex_nt_{key}", use_container_width=True, on_click=_send_nt_example,
                          args=(key,), icon=":material/send:")
    for i, msg in enumerate(s.nt_history):
        if msg["role"] == "user":
            st.markdown(f'<div class="vm-user"><div><b>{html.escape(msg["text"])}</b></div></div>', unsafe_allow_html=True)
        else:
            _render_nt_bot(i, msg)
    if s.nt_history:
        st.button("Bắt đầu cuộc mới", key="nt_reset_chat" + ("_in" if inline else ""), on_click=_nt_reset,
                  icon=":material/restart_alt:")


def nt_chat_box() -> None:
    st.chat_input("Nhắn kế hoạch, vd: 9h đến, Alpine Coaster, Biểu diễn chim, bé 1m15", key="nt_chat",
                  on_submit=_on_nt_chat)


def _info_box(ds) -> None:
    text = ("Giờ show, giá vé, chiều cao tối thiểu lấy từ bản đồ, bảng giá và trang thông tin công khai của VinWonders "
            "(truy cập 27/11/2026); nguồn ghi ngay cạnh từng số. Giá là <b>giá tham khảo</b>, có thể khác theo ngày.")
    if ds.get("demo"):
        text += (f" Ô có nhãn {tag_est()} do nhóm tự điền để chạy thử (giờ khu, thời lượng, xếp hàng, đi bộ), "
                 "không phải số chính thức.")
    st.markdown(f'<div class="nt-info">{text}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- trang chủ
def render_nha_trang_home() -> None:
    raw = nha_trang_data()
    st.markdown(NT_CSS, unsafe_allow_html=True)
    st.markdown(beach_css(".vm-hero"), unsafe_allow_html=True)
    park = raw["park"]
    st.markdown(
        '<div class="vm-hero"><div class="vm-brand">Vivu<span class="vm-badge" '
        'title="Tổng hợp từ nguồn công khai ngày 27/11/2026">Dữ liệu công khai</span></div>'
        f'<h1>{html.escape(park["name"])} · Tra cứu và lên lịch</h1>'
        f'<p>Mở cửa {html.escape(park["open"])}–{html.escape(park["close"])} · 6 phân khu · show nhạc nước, biểu diễn chim, '
        'Tata Show. Vivu xếp lịch kịp giờ diễn và tính tiền vé theo chiều cao từng người.</p></div>',
        unsafe_allow_html=True)
    demo_switch("home")
    ds = dataset()
    _info_box(ds)

    st.markdown('<p class="vm-section">Lên lịch cùng Vivu</p><p class="vm-section-sub">Gõ giờ đến và các trò, show '
                'muốn đi. Muốn hỏi riêng một show hay giá vé cũng được.</p>', unsafe_allow_html=True)
    with st.container(key="vm_home_planner"):
        nt_setup()
        nt_process()
        nt_conversation(inline=True)
        nt_chat_box()
    st.page_link("web/len_lich.py", label="Mở trang Lên lịch đầy đủ (tính tiền vé ở thanh bên)", icon=":material/open_in_new:")
    duong_den.render("home")

    rides = sum(1 for i in ds["catalog"] if i["kind"] == "ride" and not i["is_harbour"])
    timed = [s for s in ds["show_sessions"] if s["has_published_time"] and not s["is_harbour"]]
    child = next(b for b in ds["ticket_prices"] if b["id"] == "standard_100_139")["price_vnd"]
    adult = next(b for b in ds["ticket_prices"] if b["id"] == "standard_140_plus")["price_vnd"]
    st.markdown(
        '<div class="vm-facts">'
        f'<div class="vm-fact"><small>Giờ mở cửa</small><b>{park["open"]}–{park["close"]}</b></div>'
        f'<div class="vm-fact"><small>Trò chơi trong công viên</small><b>{rides} trò</b></div>'
        f'<div class="vm-fact"><small>Vé từ 140 cm · tham khảo</small><b>{money(adult)}</b></div>'
        f'<div class="vm-fact"><small>Vé 100–dưới 140 cm · tham khảo</small><b>{money(child)}</b></div>'
        '</div>', unsafe_allow_html=True)

    t_shows, t_rides, t_zones, t_price, t_reviews, t_src = st.tabs(
        ["Lịch biểu diễn", "Trò chơi & tham quan", "Phân khu", "Giá vé", "Khách nói gì", "Nguồn dữ liệu"])

    with t_shows:
        st.markdown(f'<p class="vm-section">Lịch biểu diễn trong ngày</p><p class="vm-section-sub">{len(timed)} suất có giờ. '
                    'Một show có thể có nhiều suất.</p>', unsafe_allow_html=True)
        show_harbour = st.checkbox("Hiện cả show ở Vinpearl Harbour", value=False, key="nt_show_harbour")
        groups = [g for g in ds["shows"] if show_harbour or not g["is_harbour"]]
        groups.sort(key=lambda g: min((s["start"] for s in g["sessions"] if s["has_published_time"]), default="99"))
        st.markdown(f'<div class="vm-cards">{"".join(show_card(ds, g) for g in groups)}</div>', unsafe_allow_html=True)

    with t_rides:
        c1, c2 = st.columns([2, 1])
        query = c1.text_input("Tìm theo tên hoặc số trên bản đồ", placeholder="vd: Zipline, Alpine, Sky Wheel, 56", key="nt_search")
        include_harbour = c2.checkbox("Gồm Vinpearl Harbour", value=False, key="nt_inc_harbour")
        zones = [z for z in ds["zones"] if include_harbour or not z["is_harbour"]]
        zl = {z["id"]: z["name"] for z in zones}
        c3, c4 = st.columns(2)
        picked_zones = c3.multiselect("Phân khu", options=list(zl), format_func=zl.get, key="nt_zones", placeholder="Tất cả")
        picked_kinds = c4.multiselect("Loại", options=list(KIND_LABELS_VI), format_func=KIND_LABELS_VI.get,
                                      default=["ride", "sight"], key="nt_kinds", placeholder="Tất cả")
        only_rules = st.checkbox("Chỉ hiện trò có quy định chiều cao hoặc phụ phí", value=False, key="nt_only_rules")
        matched = filter_catalog(ds, include_harbour=include_harbour, zone_ids=picked_zones or None,
                                 kinds=picked_kinds or None, query=query, only_with_restrictions=only_rules)
        st.caption(f"{len(matched)} điểm khớp.")
        if matched:
            st.markdown(f'<div class="vm-cards">{"".join(item_card(ds, i) for i in matched)}</div>', unsafe_allow_html=True)
        else:
            st.info("Không có điểm nào khớp.")

    with t_zones:
        st.markdown('<p class="vm-section">6 phân khu và Vinpearl Harbour</p><p class="vm-section-sub">Harbour là khu lân cận, '
                    'tìm kiếm mặc định không gồm khu này.</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="vm-cards">{"".join(zone_card(ds, z) for z in ds["zones"])}</div>', unsafe_allow_html=True)

    with t_price:
        st.markdown('<p class="vm-section">Giá vé vào cổng · tham khảo</p><p class="vm-section-sub">Vé tính theo chiều cao, '
                    'không theo tuổi (trừ vé người cao tuổi). Giá có thể thay đổi theo ngày và chương trình.</p>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="vm-cards">{"".join(price_card(ds, b) for b in ds["ticket_prices"])}</div>',
                    unsafe_allow_html=True)
        st.markdown('<p class="vm-section">Trò có quy định chiều cao hoặc phụ phí</p>', unsafe_allow_html=True)
        ruled = filter_catalog(ds, include_harbour=True, only_with_restrictions=True)
        st.markdown(f'<div class="vm-cards">{"".join(item_card(ds, i) for i in ruled)}</div>', unsafe_allow_html=True)

    with t_reviews:
        kb, reviews = nha_trang_kb(), nha_trang_reviews()
        st.markdown(f'<p class="vm-section">Khách nói gì</p><p class="vm-section-sub">Tóm tắt từ {kb["record_count"]} review '
                    'công khai (Traveloka, Klook, Tripadvisor), đã diễn giải và ẩn danh. Chỉ để tham khảo trải nghiệm, '
                    'không thay quy định hay giờ mở cửa.</p>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Điều khách hay phàn nàn**")
            for pp in kb["pain_points"]["pain_points"]:
                st.write(f"- {pp['label']}: {pp['count']}/{kb['record_count']} review")
        with c2:
            wt = kb["wait_time_insights"]
            st.markdown("**Chuyện xếp hàng**")
            st.write(f"- Nhắc tới chờ đợi hoặc trễ: {wt['queue_or_delay_mentions']}/{kb['record_count']} review")
            st.write(f"- Chờ lâu, nhiều giờ hoặc hết lượt: {wt['severe_wait_mentions']}/{kb['record_count']} review")
        rev_q = st.text_input("Tìm review theo trò chơi", placeholder="vd: Alpine Coaster, Zipline, Tata Show", key="nt_rev_q")
        if rev_q:
            hits = retrieve_attraction_experiences(reviews, rev_q, limit=8)
            for h in hits:
                st.write(f"- {h['summary']} *({source_name(h['source_id'])}, {h['rating']}/{h['rating_scale']}, "
                         f"{h['review_time_as_displayed']})*")
            if not hits:
                st.caption("Không có review khớp.")

    with t_src:
        st.markdown('<p class="vm-section">Nguồn dữ liệu</p><p class="vm-section-sub">Tất cả truy cập ngày 27/11/2026.</p>',
                    unsafe_allow_html=True)
        for src in raw["sources"]:
            st.markdown(f"- **{source_name(src['id'])}** · [{src['url'][:60]}…]({src['url']})")
        if ds.get("demo"):
            st.caption("Số ước tính demo: data/nha_trang/demo_estimates.json (nhóm tự ước tính, không có nguồn).")


# ---------------------------------------------------------------- trang Lên lịch
def render_nha_trang_planner() -> None:
    st.markdown(NT_CSS, unsafe_allow_html=True)
    header("Vivu · VinWonders Nha Trang", "Lên lịch kịp giờ show, tính tiền vé theo chiều cao",
           badge="Dữ liệu công khai", badge_title="Tổng hợp từ nguồn công khai ngày 27/11/2026")
    demo_switch("planner")
    ds = dataset()

    with st.sidebar:
        st.markdown("### Tính tiền vé")
        n = st.number_input("Số người", min_value=1, max_value=10, value=3, step=1, key="nt_p_count")
        st.caption("Vé tính theo chiều cao từng người. Người từ 60 tuổi nhập thêm tuổi.")
        heights, ages = [], []
        for i in range(int(n)):
            c1, c2 = st.columns(2)
            h = c1.number_input(f"Người {i + 1} · cao (cm)", min_value=0, max_value=220,
                                value=[170, 160, 115][i] if i < 3 else 0, step=1, key=f"nt_h_{i}")
            a = c2.number_input("Tuổi (không bắt buộc)", min_value=0, max_value=120, value=0, step=1, key=f"nt_a_{i}")
            if a >= 60:
                ages.append(int(a))
            elif h > 0:
                heights.append(int(h))
        lines, total = ticket_lines(ds, heights, ages)
        for line in lines:
            st.caption("• " + line.split(" · giá tham khảo")[0])
        if total is not None:
            st.success(f"Tổng vé vào cổng: **{money(total)}** (giá tham khảo)")
        elif 60 in ages:
            st.warning(SENIOR_BOUNDARY_NOTE)
        st.markdown("### Show trong ngày")
        for s in sorted((s for s in ds["show_sessions"] if s["has_published_time"] and not s["is_harbour"]),
                        key=lambda s: s["start"]):
            est = " · ước tính" if "start" in s.get("est", []) else ""
            st.caption(f"**{s['start']}** {s['name']}{est}" + (" ⚠" if s["has_discrepancy"] else ""))

    _info_box(ds)
    with st.expander("🧭 Đường đến khu vui chơi", expanded=False):
        duong_den.render("planner")
    nt_setup()
    nt_process()
    nt_conversation(inline=False)
    nt_chat_box()
