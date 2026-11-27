"""Trang chủ web Vịnh Mây. Mọi giờ, giá, thời lượng, chiều cao và lịch show đọc từ data/park.json (mô phỏng).
Không có ảnh, khuyến mãi, quyền lợi vé hay đặt vé: ngoài phạm vi lát cắt (spec.md §4). Trang này không gọi model."""
import html

import streamlit as st

from tools import minutes
from web import planner
from web.common import beach_css, is_show, money, park_data

PAGE_CSS = """
<style>
.block-container {max-width: 1040px;}
.vm-hero {color: #0F3550; border-radius: 20px; padding: 1.6rem 2rem 1.5rem; border: 1px solid #CFE7F5;
  box-shadow: 0 6px 18px rgba(11, 132, 217, .2); margin-bottom: 1rem; min-height: 13rem;}
.vm-brand {display: flex; align-items: center; gap: .7rem; font-size: 3.1rem; font-weight: 800; color: #0B5E96;
  letter-spacing: .01em; line-height: 1.05;}
.vm-hero h1 {color: #0F3550; font-size: 1.3rem; font-weight: 700; line-height: 1.35; margin: .55rem 0 .3rem; padding: 0;}
.vm-hero p {color: #1F4A66; font-size: .92rem; margin: 0; max-width: 32rem; line-height: 1.5;}
.vm-hero .vm-badge {display: inline-block; font-size: .78rem;}
.vm-facts {display: grid; grid-template-columns: repeat(4, 1fr); gap: .75rem; margin: 1.4rem 0 .4rem;}
.vm-fact {background: #FFFFFF; border: 1px solid #E3E9EF; border-radius: 12px; padding: .75rem .9rem;
  box-shadow: 0 2px 8px rgba(28, 43, 57, .06);}
.vm-fact small {display: block; color: #5B6B7A; font-size: .82rem;}
.vm-fact b {font-size: 1.1rem; font-variant-numeric: tabular-nums;}
.vm-section {font-size: 1.35rem; font-weight: 700; margin: 1.4rem 0 .2rem;}
.vm-section-sub {color: #5B6B7A; margin: 0 0 .8rem;}
.vm-cards {display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: .9rem;}
.vm-card {background: #FFFFFF; border: 1px solid #E3E9EF; border-radius: 14px; padding: 1rem 1.1rem;
  box-shadow: 0 2px 8px rgba(28, 43, 57, .06);}
.vm-card h4 {margin: .35rem 0 .5rem; padding: 0; font-size: 1.1rem;}
.vm-card .vm-kind {font-size: .75rem; font-weight: 700; border-radius: 6px; padding: .1rem .5rem;
  background: #E7F3FD; color: #0B84D9;}
.vm-card .vm-kind.show {background: #FFF1E6; color: #D35A00;}
.vm-card dl {margin: 0; display: grid; grid-template-columns: auto 1fr; gap: .25rem .7rem; font-size: .93rem;}
.vm-card dt {color: #5B6B7A;}
.vm-card dd {margin: 0; font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap;}
.vm-steps {display: grid; grid-template-columns: repeat(3, 1fr); gap: .9rem;}
.vm-step {background: #FFFFFF; border: 1px solid #E3E9EF; border-radius: 14px; padding: 1rem 1.1rem;}
.vm-step b {display: inline-flex; align-items: center; justify-content: center; width: 1.8rem; height: 1.8rem;
  border-radius: 50%; background: #0B84D9; color: #FFFFFF; margin-bottom: .4rem;}
.vm-foot {color: #5B6B7A; font-size: .85rem; border-top: 1px solid #DCE3EA; margin-top: 2rem; padding-top: 1rem;}
@media (max-width: 640px) {
  .vm-hero {padding: 1.2rem 1.1rem 1.1rem; min-height: 0;}
  .vm-brand {font-size: 2.5rem;}
  .vm-hero h1 {font-size: 1.12rem;}
  .vm-hero p {font-size: .88rem;}
  .vm-facts {grid-template-columns: repeat(2, 1fr);}
  .vm-steps {grid-template-columns: 1fr;}
}
</style>
"""


park = park_data()
acts = park["activities"]
shows = sorted((a for a in acts if is_show(a)), key=lambda a: minutes(a["open"]))
rides = [a for a in acts if not is_show(a)]
opening = min(acts, key=lambda a: minutes(a["open"]))["open"]
closing = max(acts, key=lambda a: minutes(a["close"]))["close"]

st.markdown(PAGE_CSS, unsafe_allow_html=True)
st.markdown(beach_css(".vm-hero"), unsafe_allow_html=True)
st.markdown(
    '<div class="vm-hero"><div class="vm-brand">Vivu<span class="vm-badge" '
    'title="Khu, giờ, giá và quãng đi bộ do nhóm dựng để thử">Dữ liệu mô phỏng</span></div>'
    '<h1>Gợi ý hoạt động cho chuyến du lịch tuyệt vời</h1>'
    '<p>Cho Vivu biết giờ đến, giờ về, nhóm khách và ngân sách. Vivu xếp lịch ở khu Vịnh Mây kịp giờ diễn, '
    'đủ thời gian đi bộ và hợp chiều cao của bé, kèm tổng tiền cho cả nhóm.</p></div>',
    unsafe_allow_html=True)

# ---- khung chat lên lịch ngay trên trang chủ (dùng chung lịch sử với trang Lên lịch) ----
st.markdown('<p class="vm-section">Lên lịch cùng Vivu</p><p class="vm-section-sub">Gõ kế hoạch của bạn vào ô chat là xong. '
            'Muốn đổi gì cứ nhắn tiếp, ví dụ “đổi giờ về 11h”.</p>', unsafe_allow_html=True)
with st.container(key="vm_home_planner"):
    if planner.setup():
        planner.process()
        planner.conversation(inline=True)
        planner.chat_box()
        planner.trip_form(inline=True)
st.page_link("web/len_lich.py", label="Mở trang Lên lịch đầy đủ (form ở thanh bên)", icon=":material/open_in_new:")

st.markdown(
    '<div class="vm-facts">'
    '<div class="vm-fact"><small>Giờ hoạt động các điểm</small><b>%s–%s</b></div>'
    '<div class="vm-fact"><small>Vé người lớn · cả buổi</small><b>%s</b></div>'
    '<div class="vm-fact"><small>Vé trẻ em · cả buổi</small><b>%s</b></div>'
    '<div class="vm-fact"><small>Đi bộ giữa hai điểm</small><b>%d phút</b></div></div>'
    % (opening, closing, money(park["adult_vnd"]), money(park["child_vnd"]), park["walk_minutes"]),
    unsafe_allow_html=True)


def card(a):
    show = is_show(a)
    rows = [("Suất diễn" if show else "Mở cửa", "%s–%s" % (a["open"], a["close"])), ("Thời lượng", "%d phút" % a["duration"])]
    rows.append(("Chiều cao", "trẻ từ %d cm" % a["min_cm"] if a["min_cm"] else "không giới hạn"))
    rows.append(("Phụ phí", "%s / người" % money(a["extra_vnd"]) if a["extra_vnd"] else "không"))
    dl = "".join("<dt>%s</dt><dd>%s</dd>" % (html.escape(k), html.escape(v)) for k, v in rows)
    return ('<div class="vm-card"><span class="vm-kind%s">%s</span><h4>%s</h4><dl>%s</dl></div>'
            % (" show" if show else "", "Biểu diễn" if show else "Điểm vui chơi", html.escape(a["name"]), dl))


st.markdown('<p class="vm-section">Lịch biểu diễn</p><p class="vm-section-sub">Show bắt đầu đúng giờ; '
            'trợ lý chỉ xếp show khi cả nhà đến kịp trước giờ diễn.</p>', unsafe_allow_html=True)
st.markdown('<div class="vm-cards">%s</div>' % "".join(card(a) for a in shows), unsafe_allow_html=True)

st.markdown('<p class="vm-section">Điểm vui chơi</p><p class="vm-section-sub">Trò phải kết thúc trước giờ đóng cửa. '
            'Mỗi chặng đi bộ tính %d phút, kể cả từ cổng đến điểm đầu.</p>' % park["walk_minutes"],
            unsafe_allow_html=True)
st.markdown('<div class="vm-cards">%s</div>' % "".join(card(a) for a in rides), unsafe_allow_html=True)

st.markdown('<p class="vm-section">Vivu làm gì?</p>', unsafe_allow_html=True)
st.markdown(
    '<div class="vm-steps">'
    '<div class="vm-step"><b>1</b><div>Bạn nhập giờ đến, giờ về, số người lớn, số trẻ, chiều cao bé thấp nhất '
    'và ngân sách, hoặc nhắn tự nhiên.</div></div>'
    '<div class="vm-step"><b>2</b><div>Hệ thống kiểm mọi lịch tối đa 3 điểm: giờ mở, giờ diễn, đi bộ, chiều cao, '
    'ngân sách. AI chỉ chọn một lịch hợp lệ theo sở thích.</div></div>'
    '<div class="vm-step"><b>3</b><div>Bạn nhận lịch từng giờ và tổng tiền cả nhóm. Không có lịch thì trợ lý nói rõ '
    'vì sao và gợi ý đổi gì.</div></div></div>', unsafe_allow_html=True)

st.markdown('<div class="vm-foot">Vivu là trợ lý thử nghiệm; Vịnh Mây là khu vui chơi <b>giả lập</b> do nhóm Sao Cũng Được dựng cho hackathon '
            'AI20K: tên, giờ, giá, chiều cao và quãng đi bộ không phải của khu vui chơi thật. Vivu chỉ đề xuất lịch, '
            'không bán vé hay nhận thanh toán.</div>', unsafe_allow_html=True)
