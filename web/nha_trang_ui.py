"""Giao diện Streamlit cho chế độ VinWonders Nha Trang (snapshot công khai 2026-11-27).

Giữ nguyên phong cách bãi biển / thẻ trắng của Vivu nhưng tách hoàn toàn khỏi dữ liệu mô phỏng
Vịnh Mây, hiển thị rõ trạng thái chưa xác minh, nguồn dữ liệu, ngày cập nhật, phân khu Harbour
tách biệt, bảng giá theo chiều cao/tuổi và chế độ lập lịch fail-closed.
"""
from __future__ import annotations

import datetime
import html
from typing import Any

import streamlit as st

from agent import answer
from nha_trang_chat import source_label
from park_provider import KIND_LABELS_VI, NHA_TRANG_PARK_ID, filter_catalog, filter_show_sessions
from planning import plan_nha_trang
from pricing import SENIOR_BOUNDARY_NOTE, calculate_group_reference_quote
from review_intel import retrieve_attraction_experiences
from tools import money
from web.common import beach_css, header, nha_trang_data, nha_trang_kb, nha_trang_reviews

NT_EXTRA_CSS = """
<style>
.nt-badge-warn {display: inline-block; font-size: .74rem; font-weight: 700; border-radius: 6px;
  padding: .1rem .55rem; background: #FFF1E6; color: #C24D00; margin-left: .35rem; vertical-align: middle;}
.nt-badge-harbour {display: inline-block; font-size: .74rem; font-weight: 700; border-radius: 6px;
  padding: .1rem .55rem; background: #EEF2F7; color: #3D5166; margin-left: .35rem; vertical-align: middle;}
.nt-badge-src {display: inline-block; font-size: .72rem; font-weight: 600; border-radius: 6px;
  padding: .08rem .45rem; background: #F1F6FA; color: #315472; margin-right: .25rem;}
.nt-note {font-size: .84rem; color: #5B6B7A; margin-top: .45rem; line-height: 1.4;}
.nt-warn-box {background: #FFF6EC; border: 1px solid #FFD7B0; border-left: 4px solid #F96D00;
  border-radius: 12px; padding: .8rem 1rem; margin: .6rem 0 1rem; font-size: .92rem; line-height: 1.5;}
</style>
"""


FIELD_VI = {"open": "Giờ mở", "close": "Giờ đóng", "min_height_cm": "Chiều cao", "included_in_ticket": "Phí",
            "extra_vnd": "Phụ phí", "min_age": "Tuổi"}


def _fmt_hours(open_t: str | None, close_t: str | None) -> str:
    if open_t and close_t:
        return f"{open_t}–{close_t}"
    return "Chưa xác minh"


def _fmt_height(item: dict[str, Any]) -> str:
    min_h = item["restrictions"]["min_height_cm"]
    max_h = item["restrictions"]["max_height_cm"]
    if min_h is not None and max_h is not None:
        return f"{min_h}–{max_h} cm"
    if min_h is not None:
        return f"Từ {min_h} cm"
    if max_h is not None:
        return f"Tối đa {max_h} cm"
    return "Chưa xác minh"


def _fmt_fee(item: dict[str, Any]) -> str:
    inc = item["pricing"]["included_in_ticket"]
    extra = item["pricing"]["extra_vnd"]
    if inc is False and extra is None:
        return "Ngoài vé tiêu chuẩn (chưa có đơn giá)"
    if inc is False and extra is not None:
        return f"Phụ phí {money(extra)}"
    if inc is True:
        return "Bao gồm trong vé"
    return "Chưa xác minh"


def _fmt_status(status: str | None) -> str:
    mapping = {
        "unverified_live": "Chưa xác minh trực tiếp",
        "planned_or_unavailable": "Đang phát triển / chưa hoạt động",
        "verified_live_open": "Đã xác minh đang mở",
    }
    return mapping.get(status or "", status or "Chưa xác minh")


def _render_catalog_card(item: dict[str, Any], ds: dict[str, Any]) -> str:
    kind_label = KIND_LABELS_VI.get(item["kind"], item["kind"])
    harbour_badge = '<span class="nt-badge-harbour">Vinpearl Harbour (lân cận)</span>' if item["is_harbour"] else ""
    map_tag = f"#{item['map_code']} · " if item.get("map_code") else ""
    src_badges = [f'<span class="nt-badge-src">Danh mục: {html.escape(source_label(ds, item["source_id"]))}</span>']
    for k, v in item.get("field_sources", {}).items():
        src_badges.append(f'<span class="nt-badge-src">{html.escape(FIELD_VI.get(k, k))}: {html.escape(source_label(ds, v))}</span>')

    rows = [
        ("Phân khu", item["zone_name"] or item["zone_id"] or "Chưa rõ"),
        ("Giờ hoạt động", _fmt_hours(item["open"], item["close"])),
        ("Chiều cao", _fmt_height(item)),
        ("Phí / Vé", _fmt_fee(item)),
        ("Trạng thái", _fmt_status(item["status"])),
    ]
    dl = "".join(f"<dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd>" for k, v in rows)
    warn_html = (
        f'<div class="nt-note">⚠ {html.escape(item["map_warning"])}</div>'
        if item.get("map_warning")
        else ""
    )
    return (
        f'<div class="vm-card">'
        f'<span class="vm-kind">{html.escape(kind_label)}</span>{harbour_badge}'
        f'<h4>{html.escape(map_tag + item["name"])}</h4>'
        f'<dl>{dl}</dl>'
        f'<div class="nt-note">{"".join(src_badges)}</div>'
        f'{warn_html}'
        f'</div>'
    )


def render_nha_trang_home() -> None:
    """Trang chủ đầy đủ cho VinWonders Nha Trang (snapshot công khai 2026-11-27)."""
    ds = nha_trang_data()
    park = ds["park"]
    report = ds["crawl_report"]
    kb = nha_trang_kb()
    reviews = nha_trang_reviews()

    st.markdown(NT_EXTRA_CSS, unsafe_allow_html=True)
    st.markdown(beach_css(".vm-hero"), unsafe_allow_html=True)
    st.markdown(
        '<div class="vm-hero"><div class="vm-brand">Vivu'
        '<span class="vm-badge" title="Snapshot dữ liệu công khai, không có trạng thái vận hành trực tiếp">'
        'Snapshot công khai · chưa xác minh trực tiếp</span></div>'
        f'<h1>{html.escape(park["name"])} · Danh mục &amp; Lịch tham khảo</h1>'
        f'<p>Dữ liệu công khai tổng hợp ngày <b>{html.escape(park["snapshot_date"])}</b> '
        f'(giờ mở cửa chung công bố: <b>{html.escape(park["open"])}–{html.escape(park["close"])}</b>, '
        'nguồn HOME). Mọi giá trị thiếu được giữ nguyên là <b>Chưa xác minh</b>, không tự suy từ dữ liệu mô phỏng Vịnh Mây.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="nt-warn-box"><b>Lưu ý minh bạch dữ liệu (snapshot 2026-11-27):</b> '
        'Không có trạng thái mở cửa trực tiếp (<code>live_availability=false</code>), chưa có thời lượng từng trò, '
        'ma trận thời gian đi bộ (<code>walking_distances.json</code> rỗng) và điều kiện an toàn đầy đủ '
        '(<code>0/159</code> điểm đạt <code>scheduling_ready</code>). '
        'Tata Show công bố kết thúc <b>20:10</b> vượt giờ đóng cửa chung <b>20:00</b> và lệch nguồn Klook (20:30–21:06) — cần kiểm tra lại ngày đi.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<p class="vm-section">Hỏi Vivu về VinWonders Nha Trang</p><p class="vm-section-sub">Gõ tên show, trò chơi, '
                'khu hoặc hỏi vé theo chiều cao. Vivu chỉ xác nhận phần có dữ liệu và ghi nguồn bên cạnh.</p>',
                unsafe_allow_html=True)
    with st.container(key="vm_home_planner"):
        nt_setup()
        nt_process()
        nt_conversation(inline=True)
        nt_chat_box()

    st.markdown(
        '<div class="vm-facts">'
        f'<div class="vm-fact"><small>Tổng danh mục (snapshot)</small><b>{report["catalog_count"]} điểm</b></div>'
        f'<div class="vm-fact"><small>Phân khu công viên</small><b>{report["park_zone_count"]} khu (+{report["adjacent_zone_count"]} Harbour)</b></div>'
        f'<div class="vm-fact"><small>Bản ghi show</small><b>{report["show_records"]} ({report["show_records_with_times"]} có giờ)</b></div>'
        f'<div class="vm-fact"><small>Nguồn tham chiếu</small><b>{len(ds["sources"])} nguồn</b></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.page_link("web/len_lich.py", label="Mở trang Lên lịch / Tính giá tham khảo cho VinWonders Nha Trang", icon=":material/event_note:")

    tab_zones, tab_catalog, tab_shows, tab_prices, tab_reviews, tab_sources = st.tabs([
        "Phân khu",
        "Danh mục & Bộ lọc",
        "Lịch biểu diễn",
        "Giá vé & Quy định",
        "Trải nghiệm khách (53 review)",
        "Nguồn & Trạng thái",
    ])

    # ---- Tab 1: Phân khu ----
    with tab_zones:
        st.markdown('<p class="vm-section">6 phân khu công viên &amp; khu Harbour lân cận</p>'
                    '<p class="vm-section-sub">Khu Vinpearl Harbour (mã 91–99) thuộc phạm vi lân cận, được tách riêng và mặc định loại trừ khỏi tìm kiếm trong công viên.</p>',
                    unsafe_allow_html=True)
        zone_cards = []
        for z in ds["zones"]:
            cnt = sum(1 for i in ds["catalog"] if i["zone_id"] == z["id"])
            ride_sight_cnt = sum(1 for i in ds["catalog"] if i["zone_id"] == z["id"] and i["kind"] in ("ride", "sight"))
            badge = '<span class="nt-badge-harbour">Khu lân cận (Harbour)</span>' if z["is_harbour"] else '<span class="vm-kind">Phân khu công viên</span>'
            mr = f"{z['map_range'][0]}–{z['map_range'][1]}" if len(z["map_range"]) == 2 else "—"
            rows = [
                ("Mã bản đồ", mr),
                ("Giờ khu", _fmt_hours(z["open"], z["close"])),
                ("Số điểm danh mục", f"{cnt} ({ride_sight_cnt} trò/tham quan)"),
                ("Trạng thái trực tiếp", "Chưa xác minh"),
                ("Nguồn", z["source_id"] or "—"),
            ]
            dl = "".join(f"<dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd>" for k, v in rows)
            zone_cards.append(f'<div class="vm-card">{badge}<h4>{html.escape(z["name"])}</h4><dl>{dl}</dl></div>')
        st.markdown(f'<div class="vm-cards">{"".join(zone_cards)}</div>', unsafe_allow_html=True)

    # ---- Tab 2: Danh mục & Bộ lọc ----
    with tab_catalog:
        st.markdown('<p class="vm-section">Tìm kiếm &amp; lọc danh mục (159 bản ghi)</p>', unsafe_allow_html=True)
        c1, c2 = st.columns([2, 1])
        query = c1.text_input("Tìm theo tên, mã bản đồ hoặc ID", placeholder="vd: Zipline, Tata, Sky Wheel, 56", key="nt_search")
        include_harbour = c2.checkbox("Bao gồm Vinpearl Harbour lân cận", value=False, key="nt_inc_harbour")

        selectable_zones = [z for z in ds["zones"] if include_harbour or not z["is_harbour"]]
        zone_labels = {z["id"]: z["name"] for z in selectable_zones}
        c3, c4 = st.columns(2)
        picked_zones = c3.multiselect("Lọc phân khu", options=list(zone_labels), format_func=zone_labels.get, key="nt_zones")
        picked_kinds = c4.multiselect(
            "Lọc loại địa điểm",
            options=list(KIND_LABELS_VI),
            format_func=KIND_LABELS_VI.get,
            default=["ride", "sight"],
            key="nt_kinds",
        )
        c5, c6 = st.columns(2)
        only_hours = c5.checkbox("Chỉ hiện mục có giờ hoạt động công bố (8 mục)", value=False, key="nt_only_hours")
        only_rules = c6.checkbox("Chỉ hiện mục có quy định chiều cao / phí riêng", value=False, key="nt_only_rules")

        matched = filter_catalog(
            ds,
            include_harbour=include_harbour,
            zone_ids=picked_zones or None,
            kinds=picked_kinds or None,
            query=query,
            only_with_hours=only_hours,
            only_with_restrictions=only_rules,
        )
        st.caption(f"Hiển thị **{len(matched)}** điểm khớp điều kiện (tổng danh mục snapshot: {len(ds['catalog'])}; Harbour đang {'bật' if include_harbour else 'tắt mặc định'}).")
        if matched:
            st.markdown(f'<div class="vm-cards">{"".join(_render_catalog_card(i, ds) for i in matched)}</div>', unsafe_allow_html=True)
        else:
            st.info("Không có điểm nào khớp bộ lọc hiện tại.")

    # ---- Tab 3: Lịch biểu diễn theo suất ----
    with tab_shows:
        st.markdown('<p class="vm-section">Lịch biểu diễn theo suất (8 bản ghi · 5 có giờ công bố)</p>'
                    '<p class="vm-section-sub">Tách rõ mã địa điểm (venue_id) và mã suất diễn (session_id). Một show có thể có nhiều suất trong ngày.</p>',
                    unsafe_allow_html=True)
        inc_harbour_shows = st.checkbox("Hiển thị show khu Harbour lân cận (Stunt Show)", value=False, key="nt_show_harbour")
        show_cards = []
        for grp in ds["shows"]:
            if not inc_harbour_shows and grp["is_harbour"]:
                continue
            sessions_str = ", ".join(
                f"{s['start']}–{s['end']}" if s["has_published_time"] else "Chưa có giờ"
                for s in grp["sessions"]
            )
            warn_badge = '<span class="nt-badge-warn">Xung đột lịch / giờ đóng</span>' if grp["has_discrepancy"] else ""
            hb_badge = '<span class="nt-badge-harbour">Harbour</span>' if grp["is_harbour"] else ""
            venue_text = f"{grp['venue_name']} ({grp['venue_id']})" if grp["venue_id"] else "Chưa ánh xạ venue_id"
            rows = [
                ("Số suất", str(len(grp["sessions"]))),
                ("Giờ công bố", sessions_str),
                ("Địa điểm", venue_text),
                ("Trạng thái trực tiếp", "Chưa xác minh"),
                ("Nguồn", " · ".join(source_label(ds, x) for x in grp["source_ids"])),
            ]
            dl = "".join(f"<dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd>" for k, v in rows)
            diffs = []
            for s in grp["sessions"]:
                if s.get("conflict_source_id"):
                    diffs.append(f"Hai nguồn ghi khác nhau: {s['source_id']} {s['start']}–{s['end']} · "
                                 f"{s['conflict_source_id']} {s.get('conflict_start') or '?'}–{s.get('conflict_end') or '?'} "
                                 f"({source_label(ds, s['conflict_source_id'])})")
                if s.get("exceeds_park_close"):
                    diffs.append(f"Kết thúc {s['end']} sau giờ đóng cửa chung {park['close']} ({source_label(ds, park['source_id'])})")
            notes_html = "".join(f'<div class="nt-note" style="color:#A84300">⚠ {html.escape(d)}</div>' for d in diffs)
            notes_html += "".join(f'<div class="nt-note">ℹ {html.escape(n)}</div>' for n in grp["notes"])
            show_cards.append(
                f'<div class="vm-card"><span class="vm-kind show">Biểu diễn</span>{warn_badge}{hb_badge}'
                f'<h4>{html.escape(grp["name"])}</h4><dl>{dl}</dl>{notes_html}</div>'
            )
        st.markdown(f'<div class="vm-cards">{"".join(show_cards)}</div>', unsafe_allow_html=True)

    # ---- Tab 4: Bảng giá tham khảo & Quy định ----
    with tab_prices:
        st.markdown('<p class="vm-section">Bảng giá vé tham khảo (4 nhóm · <code>current_quote=false</code>)</p>'
                    '<p class="vm-section-sub">Phân loại theo chiều cao (&lt;100 cm, 100–&lt;140 cm, ≥140 cm) và người cao tuổi. Không dùng giá review làm bảng giá chính thức.</p>',
                    unsafe_allow_html=True)
        price_cards = []
        for b in ds["ticket_prices"]:
            if b["id"] == "standard_under_100":
                cond = "Chiều cao < 100 cm"
            elif b["id"] == "standard_100_139":
                cond = "Chiều cao 100 đến < 140 cm"
            elif b["id"] == "standard_140_plus":
                cond = "Chiều cao ≥ 140 cm"
            else:
                cond = "Người cao tuổi (mốc 60 tuổi cần xác minh)"
            rows = [
                ("Điều kiện", cond),
                ("Giá tham khảo", "0 đ (miễn phí tham khảo)" if b["price_vnd"] == 0 else money(b["price_vnd"])),
                ("Sản phẩm", b["product"]),
                ("Báo giá trực tiếp", "Không (snapshot)"),
                ("Nguồn", source_label(ds, b["source_id"])),
            ]
            dl = "".join(f"<dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd>" for k, v in rows)
            note_html = f'<div class="nt-note">⚠ {html.escape(b["note"])}</div>' if b.get("note") else ""
            price_cards.append(
                f'<div class="vm-card"><span class="vm-kind">Giá tham khảo</span>'
                f'<h4>{html.escape(cond)}</h4><dl>{dl}</dl>{note_html}</div>'
            )
        st.markdown(f'<div class="vm-cards">{"".join(price_cards)}</div>', unsafe_allow_html=True)
        st.warning(SENIOR_BOUNDARY_NOTE)

        st.markdown('<p class="vm-section">Quy định tham gia đã công bố</p>'
                    '<p class="vm-section-sub">Chỉ 4 trò chơi có mức chiều cao tối thiểu rõ ràng từ nguồn công khai và 1 trò (Zipline) ghi rõ không nằm trong vé tiêu chuẩn. Các điểm còn lại giữ trạng thái chưa xác minh.</p>',
                    unsafe_allow_html=True)
        ruled_items = filter_catalog(ds, include_harbour=True, only_with_restrictions=True)
        st.markdown(f'<div class="vm-cards">{"".join(_render_catalog_card(i, ds) for i in ruled_items)}</div>', unsafe_allow_html=True)

    # ---- Tab 5: Review Intelligence ----
    with tab_reviews:
        st.markdown('<p class="vm-section">Phân tích trải nghiệm khách (53 bản ghi diễn giải ẩn danh)</p>', unsafe_allow_html=True)
        st.info(kb["disclaimer"])
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Pain points nổi bật (AI topic tags)")
            for pp in kb["pain_points"]["pain_points"]:
                st.write(f"- **{pp['label']}** (`{pp['topic']}`): **{pp['count']}/53** ({pp['share_pct']}%)")
        with c2:
            st.markdown("#### Phản ánh thời gian chờ (lịch sử, không phải trực tiếp)")
            wt = kb["wait_time_insights"]
            st.write(f"- Tổng bản ghi nhắc chờ đợi / trễ: **{wt['queue_or_delay_mentions']}/53**")
            st.write(f"- Bản ghi phản ánh chờ lâu / nhiều giờ / hết lượt: **{wt['severe_wait_mentions']}/53**")
            for ex in wt["severe_examples"][:6]:
                st.caption(f"• [{ex['id']} · {ex['source_id']}] {ex['summary']}")

        rev_q = st.text_input("Tra cứu trải nghiệm khách theo trò chơi / từ khóa", placeholder="vd: Alpine Coaster, Zipline, Tata Show, máng trượt", key="nt_rev_q")
        if rev_q:
            hits = retrieve_attraction_experiences(reviews, rev_q, limit=8)
            if hits:
                for h in hits:
                    st.write(
                        f"- **[{h['id']} · {h['source_id']}]** ({h['rating']}/{h['rating_scale']}, {h['review_time_as_displayed']}): "
                        f"{h['summary']} *(AI tags: {', '.join(h['topics'])}; human_label=null)*"
                    )
            else:
                st.caption("Không tìm thấy review khớp từ khóa.")

    # ---- Tab 6: Nguồn dữ liệu & Báo cáo crawl ----
    with tab_sources:
        st.markdown('<p class="vm-section">16 nguồn tham chiếu &amp; trạng thái thu thập</p>', unsafe_allow_html=True)
        st.write(f"- **Ngày snapshot:** `{park['snapshot_date']}`")
        st.write(f"- **Phương pháp:** `{report['method']}`")
        st.write(f"- **Nguồn bị chặn fetch trực tiếp (HTTP 403):** `{', '.join(report['blocked_direct_sources'])}`")
        for src in ds["sources"]:
            blk = " · **[403 bị chặn fetch trực tiếp]**" if src["blocked_direct"] else ""
            st.markdown(f"- **`{src['id']}`** ({src['accessed_on']}){blk}: {src['url']} — _{src['note']}_")
        with st.expander("Hạn chế đã ghi nhận trong crawl_report.json"):
            for lim in report["limitations"]:
                st.write(f"- {lim}")


def render_nha_trang_planner() -> None:
    """Giao diện lập lịch phù hợp với dữ liệu thực tế cho VinWonders Nha Trang (fail-closed)."""
    ds = nha_trang_data()
    park = ds["park"]
    reviews = nha_trang_reviews()

    st.markdown(NT_EXTRA_CSS, unsafe_allow_html=True)
    header(
        "Vivu · VinWonders Nha Trang",
        f"Chế độ tham khảo & kiểm tra điều kiện (snapshot {park['snapshot_date']} · chưa xác minh trực tiếp)",
        badge="Snapshot công khai",
        badge_title="Dữ liệu tổng hợp từ nguồn công khai ngày 2026-11-27; không phải trạng thái trực tiếp",
    )

    with st.sidebar:
        st.markdown("### Thông tin chuyến đi (Nha Trang)")
        c1, c2 = st.columns(2)
        t_start = c1.time_input("Giờ dự kiến đến", value=datetime.time(9, 0), step=900, key="nt_p_start")
        t_end = c2.time_input("Giờ dự kiến về", value=datetime.time(18, 0), step=900, key="nt_p_end")

        num_travelers = st.number_input("Số khách trong nhóm", min_value=1, max_value=10, value=2, step=1, key="nt_p_count")
        travelers: list[dict[str, Any]] = []
        st.caption("Nhập **chiều cao (cm)** từng khách (để 0 nếu chưa biết — hệ thống KHÔNG tự suy từ tuổi hay người lớn/trẻ em).")
        for idx in range(int(num_travelers)):
            tc1, tc2 = st.columns(2)
            h_val = tc1.number_input(f"Cao khách {idx + 1} (cm)", min_value=0, max_value=220, value=160 if idx == 0 else 120, step=1, key=f"nt_h_{idx}")
            age_val = tc2.number_input(f"Tuổi khách {idx + 1} (0=trống)", min_value=0, max_value=120, value=0, step=1, key=f"nt_a_{idx}")
            travelers.append({
                "label": f"Khách {idx + 1}",
                "height_cm": int(h_val) if h_val > 0 else None,
                "age": int(age_val) if age_val > 0 else None,
            })

        include_harbour = st.checkbox("Bao gồm Vinpearl Harbour lân cận", value=False, key="nt_p_harbour")
        park_zones = [z for z in ds["zones"] if include_harbour or not z["is_harbour"]]
        zone_map = {z["id"]: z["name"] for z in park_zones}
        picked_zones = st.multiselect("Phân khu quan tâm", options=list(zone_map), format_func=zone_map.get, key="nt_p_zones")

        playable = filter_catalog(ds, include_harbour=include_harbour, zone_ids=picked_zones or None, kinds={"ride", "sight"})
        item_map = {i["id"]: f"{i['name']} ({i['zone_name']})" for i in playable}
        picked_req = st.multiselect("Điểm muốn ưu tiên", options=list(item_map), format_func=item_map.get, key="nt_p_req")
        pref = st.text_input("Sở thích / từ khóa", placeholder="vd: Alpine Coaster, Tata Show, thủy cung", key="nt_p_pref")
        draft_req = st.checkbox("Thử chế độ lập lịch nháp (cần đội trưởng duyệt)", value=False, key="nt_p_draft")

    nt_setup()
    nt_process()
    nt_conversation(inline=False)
    nt_chat_box()
    st.markdown('<p class="vm-section">Kiểm tra theo thông tin ở thanh bên</p><p class="vm-section-sub">Nhập giờ, '
                'chiều cao từng khách và điểm muốn đi ở thanh bên (trên điện thoại bấm »).</p>', unsafe_allow_html=True)

    request = {
        "start": t_start.strftime("%H:%M"),
        "end": t_end.strftime("%H:%M"),
        "travelers": travelers,
        "zone_ids": picked_zones or None,
        "required_ids": picked_req,
        "preference": pref,
        "include_harbour": include_harbour,
    }
    result = plan_nha_trang(ds, request, allow_draft_estimates=draft_req, lead_approved_draft=False)

    # 1. Fail-closed readiness banner
    if result["mode"] == "draft_blocked_pending_lead_approval":
        st.error(result["message"])
    else:
        st.warning(result["message"])

    with st.expander("Chi tiết các dữ liệu còn thiếu / đang chặn tạo lịch xác minh", expanded=True):
        for blk in result["readiness"]["blockers"]:
            st.write(f"- {blk}")

    # 2. Height-based reference ticket quote
    st.markdown("### Ước tính giá vé tham khảo theo chiều cao / tuổi")
    quote = result["ticket_reference"]
    for b in quote["breakdown"]:
        price_str = (
            f"**{money(b['price_vnd'])}**"
            if b["price_vnd"] is not None
            else (
                f"**{money(b['price_range_vnd'][0])} – {money(b['price_range_vnd'][1])}** *(chưa xác minh mốc 60 tuổi)*"
                if b.get("price_range_vnd")
                else "**Chưa tính được**"
            )
        )
        st.write(f"- **{b['label']}**: {price_str} — {b['reason']}")

    if quote["reference_total_vnd"] is not None:
        st.info(f"Tổng giá vé vào cổng tham khảo (chưa gồm phụ phí trò chơi, `current_quote=false`): **{money(quote['reference_total_vnd'])}**")
    elif quote["reference_range_vnd"] is not None:
        lo, hi = quote["reference_range_vnd"]
        st.info(f"Khoảng giá vé tham khảo (do mốc đúng 60 tuổi chưa thống nhất): **{money(lo)} – {money(hi)}**")
    for w in quote["warnings"]:
        st.caption(f"⚠ {w}")

    # 3. Published show references
    st.markdown("### Suất biểu diễn có giờ công bố (tham khảo, chưa xác minh trực tiếp)")
    shows = filter_show_sessions(ds, include_harbour=include_harbour, only_with_times=True)
    for s in shows:
        warn = " · ⚠ *Có xung đột giờ đóng/nguồn Klook — cần kiểm tra lại*" if s["has_discrepancy"] else ""
        st.write(f"- **{s['name']}**: **{s['start']}–{s['end']}** · {source_label(ds, s['source_id'])}{warn}")

    # 4. Catalog suggestions (unverified reference only)
    if result.get("catalog_references"):
        st.markdown("### Gợi ý danh mục theo phân khu & sở thích (tham khảo — chưa phải lịch đã xác minh)")
        for ref in result["catalog_references"][:8]:
            hrs = _fmt_hours(ref["open"], ref["close"])
            hgt = f"từ {ref['min_height_cm']} cm" if ref["min_height_cm"] is not None else "chiều cao chưa xác minh"
            st.write(f"- **{ref['name']}** ({ref['zone_name']}) · giờ: `{hrs}` · `{hgt}` · {source_label(ds, ref['source_id'])}")

    # 5. Related review notes (explicitly non-operational)
    if pref.strip():
        hits = retrieve_attraction_experiences(reviews, pref, limit=4)
        if hits:
            st.markdown("### Kinh nghiệm khách phản ánh liên quan (chỉ tham khảo trải nghiệm)")
            for h in hits:
                st.caption(f"• [{h['id']} · {h['source_id']}] {h['summary']} *(AI tags, không dùng cho quy định an toàn/giờ mở cửa)*")


# ================================================================ chatbot Nha Trang (không gọi model)
NT_EXAMPLES = {
    "tata": "Tata Show mấy giờ diễn?",
    "ve100": "Vé cho bé cao đúng 100 cm bao nhiêu?",
    "dibo": "Đi bộ từ Zipline sang Tata Show có kịp không?",
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


def nt_process() -> None:
    """Chạy tin đang chờ qua answer(text, park_id=Nha Trang): trả lời từ snapshot, fail-closed."""
    s = st.session_state
    text, s.nt_pending = s.get("nt_pending"), None
    if not text:
        return
    s.nt_history.append({"role": "user", "text": text})
    try:
        reply = answer(text, park_id=NHA_TRANG_PARK_ID)
        s.nt_history.append({"role": "bot", "header": reply["header"], "sections": reply["sections"],
                             "found": reply["found"]})
    except Exception as e:  # dữ liệu hỏng hay lỗi khác: báo gọn, không lộ chi tiết
        s.nt_history.append({"role": "bot", "error": f"Có lỗi khi đọc dữ liệu Nha Trang ({type(e).__name__})."})


def _render_nt_bot(i: int, msg: dict[str, Any]) -> None:
    with st.container(key=f"vm_bot_nt_{i}"):
        if msg.get("error"):
            st.error(msg["error"])
            return
        st.caption(msg["header"])
        for sec in msg["sections"]:
            warn = sec["title"].startswith(("Chưa xác nhận", "Còn thiếu"))
            items = "".join(
                f'<li class="{"warn" if line.startswith("⚠") else ""}">{html.escape(line)}</li>' for line in sec["lines"])
            st.markdown(f'<p class="nt-sec-title{" warn" if warn else ""}">{html.escape(sec["title"])}</p>'
                        f'<ul class="nt-lines">{items}</ul>', unsafe_allow_html=True)
        with st.expander("Chi tiết kỹ thuật"):
            found = ", ".join(name for _, name in msg["found"]) or "không có"
            st.caption("Trả lời bằng Python từ snapshot data/nha_trang/ (27/11/2026) · không gọi model · "
                       f"nhận ra: {found}. Không dùng dữ liệu, giá hay 10 phút đi bộ của Vịnh Mây.")


def nt_conversation(inline: bool) -> None:
    s = st.session_state
    if not s.nt_history:
        with st.container(key="vm_bot_hello_nt"):
            st.markdown('<p class="vm-hello">Chào bạn, mình là Vivu. Bạn muốn biết gì về VinWonders Nha Trang?</p>'
                        '<p class="vm-muted">Hỏi về show, trò chơi, khu hoặc vé theo chiều cao. Mình trả lời từ dữ liệu '
                        'công khai ngày 27/11/2026, kèm nguồn; phần nào chưa đủ dữ liệu mình sẽ nói rõ. Hoặc bấm thử:</p>',
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
    st.chat_input("Hỏi về VinWonders Nha Trang, vd: Tata Show mấy giờ? vé bé cao 100 cm?", key="nt_chat",
                  on_submit=_on_nt_chat)
