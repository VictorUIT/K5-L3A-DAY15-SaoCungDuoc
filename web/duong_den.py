"""Mục "Đường đến khu vui chơi" (chỉ cho VinWonders Nha Trang; Vịnh Mây là khu mô phỏng nên không có).

1. Không cần key: chọn cách ra đảo → nút mở Google Maps (chỉ đường từ vị trí hiện tại, hoặc từ resort/địa chỉ nhập).
2. Có GOOGLE_MAPS_ROUTES_API_KEY: "Ước tính thời gian đến" gọi Routes API từ server khi khách bấm.
   Vị trí hiện tại lấy một lần bằng getCurrentPosition, chỉ khi khách bấm nút; giá trị là trigger một lần nên không
   nằm lại trong session. Không lưu toạ độ/địa chỉ vào file, log, trace hay lịch sử chat; không gửi cho model.
   Phiên chỉ giữ kết quả (phương tiện, điểm đến, km, phút) để chatbot trả lời "có kịp show không".
"""
from __future__ import annotations

import collections
import datetime
import html
import os
import threading
import time
from zoneinfo import ZoneInfo

import streamlit as st

from directions import (CHECKED_ON, DEST_BY_ID, DESTINATIONS, TRAVEL_MODES, RouteError, compute_route,
                        describe_route, directions_url, search_url)

ROUTES_MAX_PER_SESSION = int(os.environ.get("ROUTES_MAX_PER_SESSION") or 10)
ROUTES_MAX_PER_HOUR = int(os.environ.get("ROUTES_MAX_PER_HOUR") or 60)

CSS = """
<style>
[class*="st-key-nt_dir_box"] {background: #FFFFFF; border: 1px solid #CFE7F5; border-radius: 14px; padding: 1rem 1.1rem .8rem;
  box-shadow: 0 2px 8px rgba(11, 132, 217, .08);}
[class*="st-key-nt_dir_box"] [data-testid="stLinkButton"] a {min-height: 3.1rem; font-size: 1.05rem; font-weight: 700;}
.nt-dest {background: #F2F8FD; border: 1px solid #CFE7F5; border-radius: 12px; padding: .7rem .9rem; margin: .3rem 0 .7rem;}
.nt-dest b.name {font-size: 1.08rem; color: #0F3550;}
.nt-dest .meta {font-size: .82rem; color: #5B6B7A; margin-top: .3rem; line-height: 1.45;}
.nt-dest .meta a {color: #0B84D9;}
.nt-dest .leg {font-size: .86rem; color: #A84300; margin-top: .35rem;}
.nt-route {background: #EAF7EF; border: 1px solid #BFE5CC; border-radius: 12px; padding: .7rem .9rem; margin: .5rem 0;}
.nt-route b {color: #146C3A;}
</style>
"""

GEO_HTML = '<button class="geo-btn" type="button">📍 Lấy vị trí của tôi và tính</button><div class="geo-msg"></div>'
GEO_CSS = """
.geo-btn {width: 100%; min-height: 3.1rem; font-size: 1.02rem; font-weight: 700; border-radius: 10px; cursor: pointer;
  background: #0B84D9; color: #fff; border: 0; font-family: inherit;}
.geo-btn:disabled {opacity: .6; cursor: wait;}
.geo-msg {font-size: .85rem; color: #5B6B7A; margin-top: .35rem; min-height: 1rem; font-family: inherit;}
"""
GEO_JS = """
export default function(component) {
  const { setTriggerValue, parentElement } = component;
  const btn = parentElement.querySelector('.geo-btn');
  const msg = parentElement.querySelector('.geo-msg');
  btn.onclick = () => {
    if (!window.isSecureContext) { setTriggerValue('error', 'insecure'); return; }
    if (!navigator.geolocation) { setTriggerValue('error', 'unsupported'); return; }
    btn.disabled = true;
    msg.textContent = 'Đang xin quyền vị trí…';
    navigator.geolocation.getCurrentPosition(
      (p) => { btn.disabled = false; msg.textContent = '';
               setTriggerValue('position', {lat: p.coords.latitude, lng: p.coords.longitude}); },
      (e) => { btn.disabled = false; msg.textContent = '';
               setTriggerValue('error', e.code === 1 ? 'denied' : (e.code === 3 ? 'timeout' : 'unavailable')); },
      {enableHighAccuracy: false, timeout: 15000, maximumAge: 60000});
  };
}
"""
GEO_ERRORS = {
    "denied": "Trình duyệt đã chặn quyền vị trí. Bạn nhập tên resort hoặc địa chỉ ở ô bên dưới nhé.",
    "timeout": "Lấy vị trí quá lâu. Bạn thử lại hoặc nhập tên resort/địa chỉ bên dưới.",
    "unavailable": "Không lấy được vị trí trên thiết bị này. Bạn nhập tên resort/địa chỉ bên dưới.",
    "unsupported": "Trình duyệt không hỗ trợ lấy vị trí. Bạn nhập tên resort/địa chỉ bên dưới.",
    "insecure": "Chỉ lấy được vị trí khi web chạy qua HTTPS. Bạn nhập tên resort/địa chỉ bên dưới.",
}

_geo = st.components.v2.component("vivu_geolocation", html=GEO_HTML, css=GEO_CSS, js=GEO_JS)


@st.cache_resource
def _shared():
    return {"lock": threading.Lock(), "calls": collections.deque()}


def _api_key() -> str:
    return os.environ.get("GOOGLE_MAPS_ROUTES_API_KEY", "").strip()


def _now() -> datetime.datetime:
    return datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))


def _run_route(origin, dest, mode) -> None:
    """Một lần tính: kiểm hạn mức → gọi Routes API → giữ kết quả (không giữ origin)."""
    s = st.session_state
    s.nt_route_error = None
    used = s.get("nt_route_used", 0)
    if used >= ROUTES_MAX_PER_SESSION:
        s.nt_route_error = f"Phiên này đã dùng hết {ROUTES_MAX_PER_SESSION} lần ước tính. Bạn vẫn mở chỉ đường được."
        return
    pool = _shared()
    with pool["lock"]:
        now = time.time()
        while pool["calls"] and now - pool["calls"][0] > 3600:
            pool["calls"].popleft()
        if len(pool["calls"]) >= ROUTES_MAX_PER_HOUR:
            s.nt_route_error = "Web demo đã đạt giới hạn ước tính trong giờ này. Bạn vẫn mở chỉ đường được."
            return
        pool["calls"].append(now)
    s.nt_route_used = used + 1
    try:
        with st.spinner("Đang hỏi Google Maps…"):
            route = compute_route(_api_key(), origin, dest, mode)
    except RouteError as e:
        s.nt_route_error = str(e)
        return
    route["at"] = _now().strftime("%H:%M")
    s.nt_route = route


def _dest_card(dest) -> str:
    status = ("Tên điểm có trên trang chính thức của VinWonders" if dest["verified"]
              else "Chưa xác minh được điểm đón cụ thể")
    pid = f"Google Place ID: {html.escape(dest['place_id'])}" if dest.get("place_id") else \
        "Google Place ID: chưa đối chiếu được, Google Maps tìm theo tên"
    return (f'<div class="nt-dest"><b class="name">{html.escape(dest["name"])}</b> · {html.escape(dest["kind"])}'
            f'<div class="meta">{status}: <a href="{html.escape(dest["source_url"])}" target="_blank">'
            f'{html.escape(dest["source"])}</a> · kiểm tra {CHECKED_ON}<br>“{html.escape(dest["source_quote"])}”<br>{pid}'
            + (f'<br>Mở trên Google Maps sẽ hiện: {html.escape(dest["maps_label"])}' if dest.get("maps_label") else "")
            + '</div>'
            f'<div class="leg">{html.escape(dest["next_leg"])}</div></div>')


def render(where: str) -> None:
    """where: 'home' | 'planner' (khoá widget riêng mỗi trang)."""
    s = st.session_state
    s.setdefault("nt_route", None)
    s.setdefault("nt_route_error", None)
    st.markdown(CSS, unsafe_allow_html=True)
    with st.container(key=f"nt_dir_box_{where}"):
        st.markdown('<p class="vm-section" style="margin-top:0">Đường đến khu vui chơi</p>'
                    '<p class="vm-section-sub">VinWonders Nha Trang nằm trên đảo Hòn Tre. Chọn cách ra đảo, Vivu mở chỉ '
                    'đường tới đúng bến trên điện thoại.</p>', unsafe_allow_html=True)
        dest_id = st.radio("Ra đảo bằng", [d["id"] for d in DESTINATIONS], key=f"nt_dir_dest_{where}", horizontal=True,
                           format_func=lambda i: DEST_BY_ID[i]["mode"])
        dest = DEST_BY_ID[dest_id]
        st.markdown(_dest_card(dest), unsafe_allow_html=True)
        mode = st.segmented_control("Đi tới bến bằng", list(TRAVEL_MODES), default="driving",
                                    format_func=lambda m: TRAVEL_MODES[m][0], key=f"nt_dir_mode_{where}") or "driving"
        if dest["verified"]:
            st.link_button("📍 Chỉ đường từ vị trí của tôi", directions_url(dest, None, mode), type="primary",
                           use_container_width=True)
        else:
            st.link_button("🔎 Tìm địa điểm trên Google Maps", search_url(dest), use_container_width=True)
            st.caption("Nút này chỉ mở kết quả tìm kiếm theo tên trên Google Maps, chưa phải chỉ đường tới điểm đã xác minh.")

        with st.expander("Lên kế hoạch trước: xuất phát từ resort hoặc địa chỉ"):
            origin = st.text_input("Tên resort hoặc địa chỉ", key=f"nt_dir_origin_{where}", max_chars=200,
                                   placeholder="vd: Vinpearl Resort Nha Trang, hoặc 78 Trần Phú, Nha Trang")
            if dest["verified"] and origin.strip():
                st.link_button(f"🗺️ Chỉ đường từ “{origin.strip()[:40]}”", directions_url(dest, origin, mode),
                               use_container_width=True)
            elif origin.strip():
                st.caption("Điểm đến này chưa xác minh nên chỉ có nút tìm địa điểm ở trên.")

        if dest["verified"]:
            _estimate(where, dest, mode)


def _estimate(where, dest, mode) -> None:
    s = st.session_state
    st.markdown("**Ước tính thời gian đến**")
    if not _api_key():
        st.info("Ước tính thời gian chưa bật trên máy chủ (thiếu khoá Google Maps Routes). Nút chỉ đường ở trên vẫn dùng được.")
        return
    how = st.radio("Tính từ", ["here", "address"], horizontal=True, key=f"nt_dir_how_{where}",
                   format_func=lambda h: "Dùng vị trí hiện tại" if h == "here" else "Nhập resort/địa chỉ")
    show_address = how == "address"
    if how == "here":
        st.caption("Khi bấm, trình duyệt hỏi quyền vị trí một lần. Vị trí chỉ được gửi tới Google để tính tuyến; "
                   "Vivu không lưu lại và không gửi cho AI.")
        res = _geo(key=f"nt_geo_{where}", on_position_change=lambda: None, on_error_change=lambda: None)
        pos = getattr(res, "position", None)
        err = getattr(res, "error", None)
        if pos:
            try:
                _run_route((float(pos["lat"]), float(pos["lng"])), dest, mode)
            except (KeyError, TypeError, ValueError):
                s.nt_route_error = "Vị trí trình duyệt gửi về không hợp lệ."
        elif err:
            s[f"nt_geo_failed_{where}"] = True
            st.warning(GEO_ERRORS.get(err, GEO_ERRORS["unavailable"]))
        show_address = bool(s.get(f"nt_geo_failed_{where}"))
    if show_address:
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        addr = c1.text_input("Resort hoặc địa chỉ xuất phát", key=f"nt_dir_addr_{where}", max_chars=200,
                             placeholder="vd: Vinpearl Resort Nha Trang")
        if c2.button("Tính thời gian", key=f"nt_dir_go_{where}", use_container_width=True, type="primary"):
            _run_route(addr, dest, mode)
    if s.nt_route_error:
        st.warning(s.nt_route_error)
    route = s.get("nt_route")
    if route and route["dest_id"] == dest["id"]:
        st.markdown(f'<div class="nt-route"><b>{html.escape(describe_route(route))}</b> · tính lúc {route["at"]}<br>'
                    f'Ước tính đến {html.escape(route["dest_name"])} ({route["dest_kind"]}). Chưa gồm thời gian chờ tàu, '
                    'đi tàu ra đảo và vào cổng. Hỏi Vivu “từ resort có kịp Tata Show không?” để xem phần còn thiếu.</div>',
                    unsafe_allow_html=True)
