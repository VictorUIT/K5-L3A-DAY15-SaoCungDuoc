"""Phần dùng chung của web Vịnh Mây: CSS, dữ liệu khu chơi (đọc từ data/park.json qua tools.load_park)."""
import streamlit as st

from park_provider import (  # noqa: F401
    DEFAULT_PARK_ID,
    NHA_TRANG_PARK_ID,
    list_parks,
    load_nha_trang_dataset,
    load_park_provider,
)
from review_intel import build_knowledge_base, load_reviews  # noqa: F401
from tools import is_show, load_park, money  # noqa: F401  (money, is_show dùng ở các trang)

START_EXAMPLE = "vm_start_example"   # trang chủ đặt khoá này để trang Lên lịch điền sẵn ca mẫu
PARK_KEY = "selected_park_id"


# Nền bãi biển tự vẽ (SVG): trời, mặt trời, biển xanh trong, bãi cát, hai cây dừa. Không dùng ảnh bên ngoài.
BEACH_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 420' preserveAspectRatio='xMidYMid slice'>"
    "<defs>"
    "<linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#7CCBF3'/>"
    "<stop offset='1' stop-color='#E4F6FF'/></linearGradient>"
    "<linearGradient id='sea' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#0F9FD6'/>"
    "<stop offset='.6' stop-color='#2FC3D3'/><stop offset='1' stop-color='#7BE3D6'/></linearGradient>"
    "<linearGradient id='sand' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#F8E6BC'/>"
    "<stop offset='1' stop-color='#E9C988'/></linearGradient>"
    "</defs>"
    "<rect width='1200' height='420' fill='url(#sky)'/>"
    "<circle cx='1010' cy='78' r='44' fill='#FFF3B8'/><circle cx='1010' cy='78' r='64' fill='#FFF3B8' opacity='.35'/>"
    "<path d='M0 205 H1200 V310 H0 Z' fill='url(#sea)'/>"
    "<path d='M0 232 Q75 226 150 232 T300 232 T450 232 T600 232 T750 232 T900 232 T1050 232 T1200 232' "
    "stroke='#FFFFFF' stroke-opacity='.45' stroke-width='3' fill='none'/>"
    "<path d='M0 262 Q75 256 150 262 T300 262 T450 262 T600 262 T750 262 T900 262 T1050 262 T1200 262' "
    "stroke='#FFFFFF' stroke-opacity='.35' stroke-width='3' fill='none'/>"
    "<path d='M0 305 Q300 276 600 296 T1200 284 V420 H0 Z' fill='url(#sand)'/>"
    "<path d='M0 305 Q300 276 600 296 T1200 284' stroke='#FFFFFF' stroke-opacity='.85' stroke-width='5' fill='none'/>"
    # cây dừa lớn
    "<path d='M1060 420 C1046 345 1062 270 1100 210' stroke='#8A5A2E' stroke-width='15' fill='none' stroke-linecap='round'/>"
    "<g fill='#2E9E5B'>"
    "<path d='M1100 210 C1050 182 995 190 962 228 C1004 204 1052 204 1100 210Z'/>"
    "<path d='M1100 210 C1068 162 1025 142 978 150 C1024 162 1066 184 1100 210Z'/>"
    "<path d='M1100 210 C1100 162 1112 126 1140 100 C1122 136 1110 172 1100 210Z'/>"
    "<path d='M1100 210 C1124 160 1165 140 1212 146 C1165 160 1132 180 1100 210Z'/>"
    "<path d='M1100 210 C1150 196 1196 212 1222 248 C1180 222 1140 216 1100 210Z'/>"
    "</g>"
    "<circle cx='1094' cy='218' r='7.5' fill='#6A4322'/><circle cx='1107' cy='220' r='7.5' fill='#6A4322'/>"
    # cây dừa nhỏ
    "<path d='M920 420 C926 360 914 312 886 272' stroke='#9A6635' stroke-width='11' fill='none' stroke-linecap='round'/>"
    "<g fill='#37AE66'>"
    "<path d='M886 272 C850 252 812 258 790 284 C820 268 852 268 886 272Z'/>"
    "<path d='M886 272 C864 238 834 224 800 230 C834 238 862 254 886 272Z'/>"
    "<path d='M886 272 C904 236 934 222 968 226 C934 238 908 254 886 272Z'/>"
    "<path d='M886 272 C922 262 956 274 974 300 C944 282 914 278 886 272Z'/>"
    "</g>"
    "</svg>"
)


def beach_background(overlay="linear-gradient(90deg, rgba(255,255,255,.88) 0%, rgba(255,255,255,.7) 40%, "
                                "rgba(255,255,255,.1) 72%, rgba(255,255,255,0) 100%)"):
    """CSS background: lớp sáng mờ để chữ dễ đọc + hình bãi biển."""
    from urllib.parse import quote
    return overlay + ", url(\"data:image/svg+xml," + quote(BEACH_SVG) + "\") right bottom / cover no-repeat"


def beach_css(selector):
    """Nền bãi biển cho một khối; điện thoại dùng lớp sáng dày hơn, phủ từ trên xuống, để chữ không đè lên biển."""
    mobile = beach_background("linear-gradient(180deg, rgba(255,255,255,.9) 0%, rgba(255,255,255,.82) 62%, "
                              "rgba(255,255,255,.25) 100%)")
    return ("<style>" + selector + " {background: " + beach_background() + ";}"
            "@media (max-width: 640px) {" + selector + " {background: " + mobile + ";}}</style>")


CSS = """
<style>
.block-container {max-width: 780px; padding-top: 3.4rem; padding-bottom: 7rem;}
@media (min-width: 768px) {
  section[data-testid="stSidebar"] {width: 300px !important; min-width: 300px !important;}
}
:focus-visible {outline: 3px solid #0B84D9 !important; outline-offset: 2px;}
/* nút chính kiểu "đặt ngay": cam */
[data-testid="stBaseButton-primary"] {background: #F96D00 !important; border-color: #F96D00 !important; color: #FFFFFF !important;
  font-weight: 700 !important; box-shadow: 0 2px 6px rgba(249, 109, 0, .28);}
[data-testid="stBaseButton-primary"]:hover {background: #E06200 !important; border-color: #E06200 !important;}
[data-testid="stBaseButton-secondary"] {font-weight: 600;}
section[data-testid="stSidebar"] h3 {color: #0B84D9;}
/* đầu trang có nền bãi biển (nền đặt bằng beach_css): Vivu to, dòng phụ nhỏ */
.vm-head {color: #0F3550; border-radius: 16px; padding: 1.1rem 1.3rem 1.2rem; margin-bottom: 1rem;
  border: 1px solid #CFE7F5; box-shadow: 0 4px 14px rgba(11, 132, 217, .18); min-height: 7rem;}
.vm-title {display: flex; align-items: center; gap: .7rem; flex-wrap: wrap;}
.vm-title h1 {font-size: 2.6rem; font-weight: 800; letter-spacing: .01em; margin: 0; padding: 0; color: #0B5E96; line-height: 1.1;}
.vm-badge {font-size: .78rem; font-weight: 700; color: #FFFFFF; background: #0B84D9; border-radius: 999px;
  padding: .15rem .65rem; white-space: nowrap;}
.vm-sub {margin: .2rem 0 0; color: #1F4A66; font-size: .9rem; font-weight: 500;}
/* hai câu mẫu: canh trái, biểu tượng thẳng hàng */
[class*="st-key-ex_"] button {justify-content: flex-start; text-align: left; padding-left: 1rem;}
[class*="st-key-ex_"] button > div {justify-content: flex-start; width: 100%;}
[class*="st-key-ex_"] button p {text-align: left;}
/* hội thoại */
.vm-user {display: flex; justify-content: flex-end; margin: .9rem 0 .5rem;}
.vm-user > div {background: #E7F3FD; border: 1px solid #C7E2F8; border-radius: 14px 14px 4px 14px;
  padding: .6rem .9rem; max-width: 85%; line-height: 1.45;}
[class*="st-key-vm_bot"] {background: #FFFFFF; border: 1px solid #E3E9EF; border-radius: 14px 14px 14px 4px;
  padding: .9rem 1rem .4rem; box-shadow: 0 2px 8px rgba(28, 43, 57, .08); max-width: 94%;}
.vm-hello {font-size: 1.15rem; font-weight: 700; margin: 0 0 .2rem;}
.vm-muted {color: #5B6B7A; font-size: .92rem; margin: 0 0 .4rem;}
/* lịch */
.vm-plan {margin: .3rem 0 .2rem .35rem;}
.vm-row {position: relative; display: grid; grid-template-columns: max-content 1fr; gap: 1rem; align-items: center;
  padding: .55rem 0 .55rem 1rem; border-left: 2px dashed #B9D9F2;}
.vm-row::before {content: ""; position: absolute; left: -7px; top: 50%; width: 12px; height: 12px;
  border-radius: 50%; background: #0B84D9; border: 3px solid #FFFFFF; box-shadow: 0 0 0 1px #0B84D9;
  transform: translateY(-50%); box-sizing: border-box;}
.vm-time {font-weight: 700; font-size: 1.05rem; font-variant-numeric: tabular-nums; letter-spacing: .01em; white-space: nowrap;}
.vm-name {font-weight: 600;}
.vm-tag {display: inline-block; margin-left: .4rem; padding: .05rem .55rem; border-radius: 6px; font-size: .74rem;
  font-weight: 700; background: #E7F3FD; color: #0B84D9; vertical-align: middle;}
.vm-tag.must {background: #FFF1E6; color: #D35A00;}
.vm-total {display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; margin: .7rem 0 .3rem;
  padding: .75rem 1rem; background: #FFFFFF; border-top: 1px dashed #DCE3EA;}
.vm-total span {font-weight: 600; color: #5B6B7A;}
.vm-total b {font-size: 1.45rem; font-weight: 700; color: #F96D00; font-variant-numeric: tabular-nums; white-space: nowrap;}
.vm-reason {background: #FFF6EC; border: 1px solid #FFD7B0; border-radius: 10px; padding: .65rem .9rem; margin: .2rem 0 .5rem;}
.vm-tips {margin: .2rem 0 .4rem 1.1rem; padding: 0;}
.vm-tips li {margin: .15rem 0;}
.vm-cond {background: #FFFFFF; border: 1px solid #E3E9EF; border-left: 4px solid #0B84D9; border-radius: 12px;
  padding: .8rem 1rem; margin: .4rem 0 .6rem; box-shadow: 0 2px 8px rgba(28, 43, 57, .08);}
.vm-cond div {margin: .15rem 0;}
.vm-cond-line {font-size: .88rem; color: #5B6B7A; margin-top: .1rem;}
/* bộ chọn khu và trả lời Nha Trang */
[class*="st-key-vm_park_"] {background: #FFFFFF; border: 1px solid #CFE7F5; border-radius: 14px; padding: .55rem .9rem .7rem;
  margin-bottom: .8rem; box-shadow: 0 2px 8px rgba(11, 132, 217, .08);}
[class*="st-key-vm_park_"] label p {font-weight: 700; color: #0B5E96;}
.nt-sec-title {font-weight: 700; margin: .55rem 0 .15rem;}
.nt-sec-title.warn {color: #C24D00;}
.nt-lines {margin: 0 0 .3rem 1.1rem; padding: 0;}
.nt-lines li {margin: .12rem 0; line-height: 1.45;}
.nt-lines li.warn {color: #A84300;}
/* khung chào "Chào bạn, mình là Vivu": nền cam, chữ trắng */
.st-key-vm_bot_hello, .st-key-vm_bot_hello_nt {background: linear-gradient(135deg, #FF7A1A 0%, #E85D00 100%); border: 1px solid #E85D00;
  box-shadow: 0 4px 14px rgba(249, 109, 0, .3);}
.st-key-vm_bot_hello_nt .vm-hello, .st-key-vm_bot_hello .vm-hello {color: #FFFFFF;}
.st-key-vm_bot_hello_nt .vm-muted, .st-key-vm_bot_hello .vm-muted {color: rgba(255, 255, 255, .95);}
.st-key-vm_bot_hello_nt [data-testid="stBaseButton-secondary"], .st-key-vm_bot_hello [data-testid="stBaseButton-secondary"] {background: rgba(255, 255, 255, .16) !important;
  border: 1px solid rgba(255, 255, 255, .75) !important; color: #FFFFFF !important;}
.st-key-vm_bot_hello_nt [data-testid="stBaseButton-secondary"]:hover, .st-key-vm_bot_hello [data-testid="stBaseButton-secondary"]:hover {background: rgba(255, 255, 255, .28) !important;
  border-color: #FFFFFF !important;}
.st-key-vm_bot_hello_nt button p, .st-key-vm_bot_hello_nt button span, .st-key-vm_bot_hello button p, .st-key-vm_bot_hello button span {color: #FFFFFF !important;}
.st-key-vm_bot_hello :focus-visible {outline-color: #FFFFFF !important;}
/* form điều kiện nằm trong trang (trang chủ) */
.st-key-vm_trip_inline {background: #FFFFFF; border: 1px solid #E3E9EF; border-radius: 14px; padding: 1rem 1.1rem .6rem;
  box-shadow: 0 2px 8px rgba(28, 43, 57, .08); margin-bottom: .6rem;}
.st-key-vm_trip_inline h3 {color: #0B84D9; font-size: 1.15rem; padding-top: 0;}
@media (max-width: 640px) {
  .block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 3.2rem;}
  .vm-title h1 {font-size: 2.2rem;}
  .vm-row {gap: .7rem;}
  .vm-time {font-size: 1.02rem;}
  .vm-total {padding: .65rem .2rem;}
  .vm-total b {font-size: 1.3rem;}
  [class*="st-key-vm_bot"], .vm-user > div {max-width: 100%;}
}
</style>
"""


@st.cache_data
def park_data():
    return load_park()


@st.cache_data
def nha_trang_data():
    return load_nha_trang_dataset()


@st.cache_data
def nha_trang_reviews():
    return load_reviews()


@st.cache_data
def nha_trang_kb():
    return build_knowledge_base(nha_trang_reviews())


def names():
    return {a["id"]: a["name"] for a in park_data()["activities"]}


PARK_SHORT = {DEFAULT_PARK_ID: "Vịnh Mây · mô phỏng", NHA_TRANG_PARK_ID: "VinWonders Nha Trang"}
# Trạng thái đang chờ xử lý của từng khu: đổi khu thì bỏ, để một tin gõ cho khu này không chạy ở khu kia.
PENDING_KEYS = ("pending", "pending_chat", "preview", "need", "nt_pending")


def _switch_park(widget_key):
    s = st.session_state
    new = s.get(widget_key)
    if not new or new == s.get(PARK_KEY):  # bấm lại nút đang chọn: giữ nguyên
        return
    s["park_switched_from"] = s.get(PARK_KEY)
    s[PARK_KEY] = new
    for key in PENDING_KEYS:
        s[key] = None


def park_selector(key_suffix="top"):
    """Bộ chọn khu dùng chung giữa Trang chủ và Lên lịch (cùng khoá selected_park_id). Mặc định là Vịnh Mây.

    Mỗi khu có lịch sử hội thoại, điều kiện và dữ liệu riêng (Vịnh Mây: history, t_*; Nha Trang: nt_history);
    đổi khu chỉ đổi phần được vẽ và bỏ các lượt đang chờ, không mang điều kiện của khu này sang khu kia.
    """
    s = st.session_state
    s.setdefault(PARK_KEY, DEFAULT_PARK_ID)
    if s[PARK_KEY] not in PARK_SHORT:
        s[PARK_KEY] = DEFAULT_PARK_ID
    widget_key = f"park_pick_{key_suffix}"
    s[widget_key] = s[PARK_KEY]  # trang kia có thể vừa đổi khu: nút ở trang này đi theo
    with st.container(key=f"vm_park_{key_suffix}"):
        st.segmented_control("Khu đang chọn", options=list(PARK_SHORT), format_func=PARK_SHORT.get,
                             key=widget_key, on_change=_switch_park, args=(widget_key,),
                             help="Vịnh Mây là khu giả lập để thử. VinWonders Nha Trang dùng snapshot dữ liệu công khai "
                                  "ngày 27/11/2026: tra cứu được, lịch chỉ xác nhận khi đủ dữ liệu.")
        old = s.pop("park_switched_from", None)
        if old:  # chú thích ngay dưới nút (thông báo nổi che mất nút chọn khu trên điện thoại)
            st.caption(f"Đã chuyển sang {PARK_SHORT[s[PARK_KEY]]}. Hội thoại và điều kiện của "
                       f"{PARK_SHORT.get(old, old)} được giữ riêng, không dùng cho khu này.")
    return s[PARK_KEY]


def header(title, subtitle, badge="Dữ liệu mô phỏng",
           badge_title="Giờ, giá và quãng đi bộ do nhóm dựng để thử, không phải dữ liệu thật"):
    """Đầu trang có nền bãi biển: tên trợ lý to, dòng phụ nhỏ, nhãn nguồn dữ liệu."""
    st.markdown(beach_css(".vm-head"), unsafe_allow_html=True)
    st.markdown('<div class="vm-head"><div class="vm-title"><h1>%s</h1>'
                '<span class="vm-badge" title="%s">%s</span></div><p class="vm-sub">%s</p></div>'
                % (title, badge_title, badge, subtitle),
                unsafe_allow_html=True)
