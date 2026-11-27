"""Chatbot lên lịch của web Vịnh Mây, dùng ở trang chủ (form nằm trong trang) và trang Lên lịch (form ở thanh bên).

Form tạo đúng dòng tên=giá trị cho answer(text) trong codebase/agent.py — cùng luồng với `python run.py`, `run.py eval`
và `run.py simulate`. Ô chat nhận câu tự nhiên: extract_request (model rút điều kiện, Python kiểm từng trường) cập nhật
form rồi cũng đi qua answer(). Mỗi lần gửi gọi answer() đúng một lần; mở trang hay chỉnh một ô trong form không gọi
model. Hai trang dùng chung lịch sử và điều kiện trong session_state.
"""
import collections
import datetime
import html
import os
import re
import threading
import time

import streamlit as st

import ai  # noqa: E402
import tracing  # noqa: E402
from agent import answer, extract_request, to_line  # noqa: E402
from web.common import START_EXAMPLE, header, is_show, money, names, park_data  # noqa: E402

MAX_PER_SESSION = int(os.environ.get("DEMO_MAX_PER_SESSION") or 15)
MAX_PER_HOUR = int(os.environ.get("DEMO_MAX_PER_HOUR") or 60)
ALLOW_FAKE = os.environ.get("DEMO_ALLOW_FAKE") == "1"
REAL_MODEL = ai.MODEL_PROVIDER != "fake"
NO_ROUTE = "Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. "

DEFAULTS = {"t_start": datetime.time(9, 0), "t_end": datetime.time(12, 0), "t_adults": 2, "t_children": 0,
            "t_height": 0, "t_budget": 0, "t_required": [], "t_closed": [], "t_buffer": 0, "t_pref": ""}
# Điều kiện mẫu lấy từ các ca đã kiểm trong eval/benchmark.csv (C01, C13), đầu ra đã được bộ kiểm độc lập xác nhận.
EXAMPLES = {
    "show_chim": {"label": "Lên lịch để kịp Show chim", "case": "C01",
                  "text": "2 người lớn, 1 bé cao 110 cm, đến 9h về 12h, ngân sách 500k, muốn xem Show chim",
                  "values": {"t_start": datetime.time(9, 0), "t_end": datetime.time(12, 0), "t_adults": 2,
                             "t_children": 1, "t_height": 110, "t_budget": 500000, "t_required": ["chim"]}},
    "sat_gio": {"label": "Thử một lịch sát giờ về", "case": "C13",
                "text": "1 người lớn, đến cổng 10h50, về 12h, có 180k, nhất định xem Show chim",
                "values": {"t_start": datetime.time(10, 50), "t_end": datetime.time(12, 0), "t_adults": 1,
                           "t_children": 0, "t_height": 0, "t_budget": 180000, "t_required": ["chim"]}},
}
FIELD_LABEL = {"budget": "Ngân sách cả nhóm", "height": "Chiều cao bé thấp nhất", "adults": "Số người lớn",
               "time": "Giờ đến và giờ về"}




@st.cache_resource
def shared():
    """Dùng chung giữa các phiên: khoá cho trace (tracing.py giữ trạng thái toàn cục) và bộ đếm lượt gửi mỗi giờ."""
    return {"lock": threading.Lock(), "calls": collections.deque()}


def clean(text):
    """Ô tự do không được phá cấu trúc tên=giá trị; ký tự ; và = bị thay."""
    return (text or "").replace(";", ",").replace("=", " ").strip()


def form_fields():
    """Giá trị form → các trường tên=giá trị. 0 ở chiều cao hoặc ngân sách = chưa điền, để backend hỏi lại."""
    s = st.session_state
    f = {"giờ": "%s-%s" % (s.t_start.strftime("%H:%M"), s.t_end.strftime("%H:%M")),
         "lớn": str(s.t_adults), "trẻ": str(s.t_children)}
    if s.t_children and s.get("t_height"):
        f["cao"] = str(s.t_height)
    if s.t_budget:
        f["đồng"] = str(s.t_budget)
    if s.t_required:
        f["phải có"] = ",".join(sorted(s.t_required))
    if s.t_closed:
        f["đóng"] = ",".join(sorted(s.t_closed))
    if clean(s.t_pref):
        f["ưu tiên"] = clean(s.t_pref)
    if s.t_buffer:
        f["đệm"] = str(s.t_buffer)
    return f


def apply_fields(f):
    """Điều kiện đã kiểm (sau khi rút từ câu chat) → các ô của form. Gọi trước khi form được vẽ."""
    s = st.session_state
    if f.get("giờ"):
        a, _, b = f["giờ"].partition("-")
        s.t_start, s.t_end = [datetime.datetime.strptime(x, "%H:%M").time() for x in (a, b)]
    for field, key in (("lớn", "t_adults"), ("trẻ", "t_children"), ("cao", "t_height"),
                       ("đồng", "t_budget"), ("đệm", "t_buffer")):
        if f.get(field):
            s[key] = int(f[field])
    s.t_required = sorted(filter(None, f.get("phải có", "").split(",")))
    s.t_closed = sorted(filter(None, f.get("đóng", "").split(",")))
    s.t_pref = f.get("ưu tiên", s.t_pref)


def summary_lines(f):
    """Điều kiện viết lại cho người đọc kiểm, có biểu tượng nhỏ."""
    n = names()
    rows = []
    if f.get("giờ"):
        rows.append("🕘 " + f["giờ"].replace("-", "–"))
    group = "%s người lớn" % f.get("lớn", "?")
    if f.get("trẻ") and f["trẻ"] != "0":
        group += ", %s trẻ" % f["trẻ"] + (" (thấp nhất %s cm)" % f["cao"] if f.get("cao") else "")
    rows.append("👨‍👩‍👧 " + group)
    rows.append("💰 " + (money(int(f["đồng"])) if f.get("đồng") else "chưa điền ngân sách"))
    if f.get("phải có"):
        rows.append("🎯 Muốn có: " + ", ".join(n[i] for i in f["phải có"].split(",")))
    if f.get("đóng"):
        rows.append("⛔ Đang đóng: " + ", ".join(n[i] for i in f["đóng"].split(",")))
    if f.get("ưu tiên"):
        rows.append("💬 Sở thích: " + f["ưu tiên"])
    if f.get("đệm"):
        rows.append("⏱ Có mặt trước show %s phút" % f["đệm"])
    return rows


def friendly_error(error):
    text = "%s" % error
    low = text.lower()
    if "429" in text or "quota" in low or "resource_exhausted" in low or "rate" in low:
        return "Model đang hết lượt gọi của gói hiện tại. Bạn thử lại sau vài phút nhé."
    if "401" in text or "403" in text or "api key" in low or "api_key" in low:
        return "Máy chủ chưa có key hợp lệ cho model. Người quản trị cần kiểm tra secret API_KEY."
    if "timed out" in low or "urlopen" in low or "connection" in low:
        return "Không kết nối được tới model. Bạn thử lại nhé."
    return "Có lỗi khi gọi model (%s). Bạn thử lại nhé." % type(error).__name__


def missing_field(output):
    """Câu hỏi lại của backend → ô cần điền trên form."""
    low = output.lower()
    if "ngân sách" in low:
        return "budget"
    if "cao bao nhiêu" in low:
        return "height"
    if "người lớn" in low:
        return "adults"
    if "giờ" in low:
        return "time"
    return None


def run(kind, label, text=None):
    """Một lần gửi: kiểm hạn mức → (khoá chung) begin → [rút điều kiện] → answer() một lần → end → lưu vào phiên."""
    s = st.session_state
    s.history.append({"role": "user", "text": label, "cond": [] if kind == "chat" else summary_lines(form_fields())})
    if s.used >= MAX_PER_SESSION:
        s.history.append({"role": "bot", "error": "Phiên này đã dùng hết %d lượt demo. Bấm “Bắt đầu lại” "
                          "hoặc tải lại trang để mở phiên mới." % MAX_PER_SESSION})
        return
    pool = shared()
    with pool["lock"]:
        now = time.time()
        while pool["calls"] and now - pool["calls"][0] > 3600:
            pool["calls"].popleft()
        if len(pool["calls"]) >= MAX_PER_HOUR:
            s.history.append({"role": "bot", "error": "Web demo đã đạt giới hạn %d lượt trong một giờ. "
                              "Bạn thử lại sau nhé." % MAX_PER_HOUR})
            return
        pool["calls"].append(now)
        tracing.begin("web")
        try:
            fields = extract_request(text, form_fields(), park_data()) if kind == "chat" else form_fields()
            line = to_line(fields)
            output, error = answer(line)["output"], None
        except Exception as e:  # lỗi gọi model: báo dễ hiểu, không lộ chi tiết key
            fields, line, output, error = form_fields(), "", "", friendly_error(e)
        summary, events = tracing.end()
    s.used += 1
    if kind == "chat" and not error:
        apply_fields(fields)
    s.need = missing_field(output) if output and not output.startswith(("Vịnh Mây", NO_ROUTE)) else None
    s.regen_end = s.t_end
    s.preview = None
    s.history.append({"role": "bot", "output": output, "error": error, "fields": fields, "line": line,
                      "summary": summary, "events": events})


# ---- thao tác của người dùng (callback chỉ đặt cờ; luồng chạy ở đầu lượt vẽ kế tiếp) ----
def queue_form(label):
    st.session_state.pending = label


def pick_example(key):
    s = st.session_state
    for k, v in DEFAULTS.items():
        s[k] = v
    for k, v in EXAMPLES[key]["values"].items():
        s[k] = v
    s.preview = key
    s.need = None


def send_example(key):
    """Một cú bấm: điền điều kiện mẫu và chạy luôn (bong bóng của khách hiện đúng câu mẫu)."""
    pick_example(key)
    st.session_state.pending = EXAMPLES[key]["text"]


def change_end():
    s = st.session_state
    s.t_end = s.regen_end
    s.pending = "Đổi giờ về " + s.regen_end.strftime("%H:%M")


def reset():
    s = st.session_state
    s.history, s.preview, s.need, s.pending = [], None, None, None
    for k, v in DEFAULTS.items():
        s[k] = v


# ---- vẽ kết quả ----
def render_route(lines, fields):
    by_name = {a["name"]: a for a in park_data()["activities"]}
    required = set(filter(None, fields.get("phải có", "").split(",")))
    rows, total = [], None
    for line in lines[1:]:
        m = re.match(r"(\d\d:\d\d)–(\d\d:\d\d)\s+(.+)$", line)
        if m:
            start, end, name = m.groups()
            act = by_name.get(name.strip())
            tags = ""
            if act and is_show(act):
                tags += '<span class="vm-tag">Suất diễn</span>'
            if act and act["id"] in required:
                tags += '<span class="vm-tag must">Bắt buộc</span>'
            rows.append('<div class="vm-row"><span class="vm-time">%s–%s</span><span class="vm-name">%s%s</span></div>'
                        % (start, end, html.escape(name.strip()), tags))
        elif line.startswith("Tổng cho cả nhóm: "):
            total = line.split(": ", 1)[1]
    if not rows or not total:  # định dạng lạ: hiện nguyên kết quả backend
        st.text("\n".join(lines))
        return
    st.markdown('<p class="vm-muted">Lịch đề xuất · giờ và tiền do Python tính, đã kiểm giờ mở, giờ diễn, '
                '10 phút đi bộ mỗi chặng, chiều cao và ngân sách</p>', unsafe_allow_html=True)
    st.markdown('<div class="vm-plan">%s</div><div class="vm-total"><span>Tổng tiền cho cả nhóm</span><b>%s</b></div>'
                % ("".join(rows), html.escape(total)), unsafe_allow_html=True)


def render_bot(i, msg, latest):
    with st.container(key="vm_bot_%d" % i):
        if msg.get("error"):
            st.error(msg["error"])
            return
        out = msg["output"]
        lines = out.splitlines()
        if lines and lines[0].startswith("Vịnh Mây"):
            render_route(lines, msg["fields"])
        elif lines and lines[0].startswith(NO_ROUTE.strip()):
            reason = lines[0][len(NO_ROUTE):] if lines[0].startswith(NO_ROUTE) else lines[0]
            st.markdown("**Chưa có lịch phù hợp**")
            st.markdown('<div class="vm-reason">%s</div>' % html.escape(reason), unsafe_allow_html=True)
            for line in lines[1:]:
                head, _, rest = line.partition(": ")
                tips = [t for t in rest.split(" · ") if t] if rest else []
                if tips:
                    st.markdown('<p class="vm-muted">%s:</p><ul class="vm-tips">%s</ul>'
                                % (html.escape(head), "".join("<li>%s</li>" % html.escape(t) for t in tips)),
                                unsafe_allow_html=True)
                else:
                    st.markdown(html.escape(line))
            st.caption("Chỉnh điều kiện ở phần **Chuyến đi của bạn** rồi bấm Tạo lịch, hoặc đổi giờ về ngay bên dưới.")
        else:
            st.markdown(html.escape(out))
            need = missing_field(out)
            if need:
                st.caption("👉 Nhắn thêm **%s** ở ô chat (hoặc điền ô đó trong phần Chuyến đi của bạn)." % FIELD_LABEL[need].lower())
        if latest and msg["fields"].get("giờ") and (lines[0].startswith(("Vịnh Mây", NO_ROUTE.strip()))):
            c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
            c1.time_input("Đổi giờ về", key="regen_end", step=300)
            c2.button("Tạo lại lịch", key="regen_go", on_click=change_end, use_container_width=True)
        if msg.get("fields"):
            st.caption("Vivu hiểu: " + " · ".join(r.split(" ", 1)[1] for r in summary_lines(msg["fields"])))
        s = msg["summary"]
        with st.expander("Chi tiết kỹ thuật"):
            st.caption("Dòng gửi vào answer(): %s" % (msg["line"] or "—"))
            st.caption("Model: %s · gọi model %d lần · công cụ %d lần · token vào %d / ra %d"
                       % (", ".join(s["models"]) or "không gọi", s["model_calls"], s["tool_calls"],
                          s["tokens_in"], s["tokens_out"]))


# ================================================================ các phần ghép vào trang
def on_chat():
    """Callback của ô chat: chỉ ghi lại tin; luồng chạy ở process() trước khi form được vẽ."""
    st.session_state.pending_chat = st.session_state.get("vm_chat")


def setup():
    """Khởi tạo trạng thái phiên. Trả False nếu thiếu model thật ở chế độ chính thức (trang tự quyết hiện gì khác)."""
    s = st.session_state
    for key, value in dict(DEFAULTS, history=[], used=0, preview=None, need=None, pending=None,
                           pending_chat=None).items():
        s.setdefault(key, value)
    s.setdefault("regen_end", s.t_end)
    if s.get(START_EXAMPLE) in EXAMPLES:  # đến từ nút "Thử ngay": chỉ điền sẵn, chưa gọi model
        pick_example(s.pop(START_EXAMPLE))
    if not REAL_MODEL and not ALLOW_FAKE:
        st.error("Chưa cấu hình model thật. Người quản trị cần đặt MODEL_PROVIDER, MODEL_NAME và API_KEY "
                 "trong secret của máy chủ. Web không chạy bằng model giả ở chế độ chính thức.")
        return False
    if not REAL_MODEL:
        st.info("Đang thử trên máy bằng model giả (DEMO_ALLOW_FAKE=1). Không dùng để báo cáo.")
    return True


def process():
    """Chạy lượt đang chờ (tin chat hoặc nút Tạo lịch). Gọi trước trip_form để kịp cập nhật các ô."""
    s = st.session_state
    text, s.pending_chat = s.pending_chat, None
    if text or s.pending:
        with st.spinner("Đang kiểm các lịch khả thi và nhờ model chọn…"):
            if text:
                run("chat", text, text)
            else:
                label, s.pending = s.pending, None
                run("form", label)


def _need_note(where, field, text):
    if st.session_state.need == field:
        where.markdown(":red[%s]" % text)


def trip_form(inline):
    """Form "Chuyến đi của bạn": inline=True nằm trong trang (trang chủ), False ở thanh bên (trang Lên lịch)."""
    s = st.session_state
    n = names()
    if inline:
        box = st.expander("Chỉnh từng ô (không bắt buộc)", expanded=False, icon=":material/tune:")
    else:
        box = st.sidebar
    with box:
        st.markdown("### Chuyến đi của bạn" if not inline else "#### Chuyến đi của bạn")
        if inline:
            r = st.columns(4)
        else:
            r = st.columns(2) + st.columns(2)
        r[0].time_input("🕘 Giờ đến", key="t_start", step=300)
        r[1].time_input("Giờ về", key="t_end", step=300)
        r[2].number_input("👨‍👩‍👧 Người lớn", key="t_adults", min_value=0, max_value=20, step=1)
        r[3].number_input("Trẻ em", key="t_children", min_value=0, max_value=20, step=1)
        _need_note(st, "adults", "Cần ít nhất 1 người lớn đi cùng.")
        if inline:
            row = st.columns([1, 1, 2]) if s.t_children else [None] + st.columns([1, 2])
        else:
            row = [st, st, st]
        if s.t_children:
            row[0].number_input("Chiều cao bé thấp nhất (cm)", key="t_height", min_value=0, max_value=200, step=1,
                                help="Tàu lượn cần trẻ cao từ 120 cm. Để 0 nếu chưa đo, trợ lý sẽ hỏi lại.")
            _need_note(row[0], "height", "Cần điền ô này để tạo lịch.")
        row[1].number_input("💰 Ngân sách cả nhóm (đồng)", key="t_budget", min_value=0, step=10000,
                            help="Gồm vé vào cổng và phụ phí trò chơi.")
        row[1].caption(money(s.t_budget) if s.t_budget else "Chưa điền ngân sách")
        _need_note(row[1], "budget", "Cần điền ô này để tạo lịch.")
        row[2].multiselect("🎯 Hoạt động muốn có", options=list(n), format_func=n.get, key="t_required",
                           placeholder="Chọn điểm nhất định phải đi")
        row = st.columns([2, 2]) if inline else [st, st]
        row[0].text_input("💬 Sở thích", key="t_pref", max_chars=120, placeholder="vd: bé thích động vật, ít đi bộ")
        with row[1].expander("Tuỳ chọn thêm"):
            st.multiselect("Điểm đang đóng hoặc show bị huỷ", options=list(n), format_func=n.get,
                           key="t_closed", placeholder="Không có")
            st.number_input("Có mặt trước giờ show (phút)", key="t_buffer", min_value=0, max_value=120, step=5)
        row = st.columns([3, 1]) if inline else [st, st]
        row[0].button("Tạo lịch", type="primary", use_container_width=True, key="go_form",
                      on_click=queue_form, args=("Tạo lịch",))
        row[1].button("Bắt đầu lại", use_container_width=True, key="reset", on_click=reset)
        st.caption("Đã dùng %d/%d lượt · Model: %s" % (s.used, MAX_PER_SESSION, ai.MODEL_NAME if REAL_MODEL else "giả"))


def conversation(inline):
    """Lời chào + lịch mẫu (bấm là chạy) khi chưa có tin, sau đó là lịch sử hội thoại."""
    s = st.session_state
    if not s.history:
        with st.container(key="vm_bot_hello"):
            st.markdown('<p class="vm-hello">Chào bạn, mình là Vivu. Bạn muốn chơi gì ở Vịnh Mây?</p>'
                        '<p class="vm-muted">Nhập kế hoạch trong một câu ở ô bên dưới: giờ đến, giờ về, số người lớn, '
                        'số trẻ (và chiều cao bé thấp nhất), ngân sách, điểm muốn đi. Thiếu gì mình sẽ hỏi lại. '
                        'Hoặc bấm thử một kế hoạch mẫu:</p>', unsafe_allow_html=True)
            for key in EXAMPLES:
                st.button("“%s”" % EXAMPLES[key]["text"], key="ex_" + key, use_container_width=True,
                          on_click=send_example, args=(key,), icon=":material/send:")
    last_bot = max((i for i, m in enumerate(s.history) if m["role"] == "bot"), default=-1)
    for i, msg in enumerate(s.history):
        if msg["role"] == "user":
            cond = "".join('<div class="vm-cond-line">%s</div>' % html.escape(r) for r in msg.get("cond", []))
            st.markdown('<div class="vm-user"><div><b>%s</b>%s</div></div>' % (html.escape(msg["text"]), cond),
                        unsafe_allow_html=True)
        else:
            render_bot(i, msg, i == last_bot)
    if inline and s.history:
        st.button("Bắt đầu cuộc mới", key="reset_chat", on_click=reset, icon=":material/restart_alt:")


def chat_box():
    """Ô chat. Gọi ở gốc trang thì ghim cuối màn hình; gọi trong một container thì nằm ngay trong khung."""
    st.chat_input("Nhập kế hoạch, vd: 2 người lớn, 1 bé 110 cm, 9h–12h, 500k, xem Show chim",
                  key="vm_chat", on_submit=on_chat)
