"""Web demo C1 · Chatbox xếp lịch gia đình tại khu vui chơi (Vịnh Mây, dữ liệu mô phỏng).

Chạy:   streamlit run streamlit_app.py
Mỗi tin nhắn: model rút điều kiện (extract_request) → web nhớ điều kiện của phiên → cùng answer(text) trong
codebase/agent.py như `python run.py`, `run.py eval` và `run.py simulate` (Python kiểm lịch, model chọn lịch).

Biến môi trường hoặc Streamlit secret (không commit key):
  MODEL_PROVIDER, MODEL_NAME, API_KEY       model thật (nhóm dùng gemini / gemini-3.1-flash-lite)
  DEMO_MAX_PER_SESSION   số tin nhắn tối đa mỗi phiên (mặc định 15)
  DEMO_MAX_PER_HOUR      số tin nhắn tối đa mỗi giờ cho toàn bộ web (mặc định 60)
  DEMO_ALLOW_FAKE=1      chỉ dùng khi thử trên máy: cho chạy model giả. Mặc định web báo lỗi nếu thiếu model thật.
"""
import collections
import os
import sys
import threading
import time

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "codebase"))

SETTINGS = ("MODEL_PROVIDER", "MODEL_NAME", "API_KEY", "DEMO_MAX_PER_SESSION", "DEMO_MAX_PER_HOUR", "DEMO_ALLOW_FAKE")
for _name in SETTINGS:  # secret phía máy chủ → biến môi trường, trước khi nạp ai.py
    try:
        _value = st.secrets.get(_name)
    except Exception:  # chưa có secrets.toml khi chạy trên máy
        _value = None
    if _value is not None:
        os.environ.setdefault(_name, str(_value))

import ai  # noqa: E402
import tracing  # noqa: E402
from agent import ASK, answer, extract_request, to_line  # noqa: E402
from tools import load_park, money  # noqa: E402

MAX_PER_SESSION = int(os.environ.get("DEMO_MAX_PER_SESSION") or 15)
MAX_PER_HOUR = int(os.environ.get("DEMO_MAX_PER_HOUR") or 60)
ALLOW_FAKE = os.environ.get("DEMO_ALLOW_FAKE") == "1"
REAL_MODEL = ai.MODEL_PROVIDER != "fake"

EXAMPLES = {
    "Lịch khả thi": "Nhà mình 2 người lớn và 1 bé cao 110 cm, đến cổng 9h, về 12h, ngân sách 500k, muốn xem Show chim",
    "Lịch xung đột": "Mình đi 1 người lớn, đến cổng lúc 10h51, về 12h, có 180k, nhất định phải xem Show chim",
}
GREETING = ("Chào bạn! Mình giúp xếp lịch một buổi ở khu Vịnh Mây (dữ liệu mô phỏng). Bạn cho mình biết: "
            + ", ".join(ASK.values()) + ", và nếu có trẻ thì chiều cao bé thấp nhất. Có điểm nào nhất định muốn đi "
            "(Vườn hoa, Nhà tranh, Tàu lượn, Show chim, Show nhạc) hay sở thích gì cứ nói nhé.")


@st.cache_resource
def shared():
    """Dùng chung giữa các phiên: khoá cho trace (tracing.py giữ trạng thái toàn cục) và bộ đếm tin nhắn mỗi giờ."""
    return {"lock": threading.Lock(), "calls": collections.deque()}


@st.cache_data
def park_data():
    return load_park()


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


def understood(fields):
    """Điều kiện của phiên, viết lại cho người đọc kiểm."""
    names = {a["id"]: a["name"] for a in park_data()["activities"]}
    parts = []
    if fields.get("giờ"):
        parts.append(fields["giờ"].replace("-", "–"))
    if fields.get("lớn"):
        parts.append("%s người lớn" % fields["lớn"])
    if fields.get("trẻ"):
        kid = "%s trẻ" % fields["trẻ"]
        parts.append(kid + (" (thấp nhất %s cm)" % fields["cao"] if fields.get("cao") and fields["trẻ"] != "0" else ""))
    if fields.get("đồng"):
        parts.append(money(int(fields["đồng"])))
    for key, label in (("phải có", "phải có"), ("đóng", "đang đóng")):
        if fields.get(key):
            parts.append(label + ": " + ", ".join(names[i] for i in fields[key].split(",")))
    if fields.get("ưu tiên"):
        parts.append("sở thích: " + fields["ưu tiên"])
    if fields.get("đệm"):
        parts.append("đến trước show %s phút" % fields["đệm"])
    return " · ".join(parts)


def handle(message):
    """Một tin nhắn: kiểm hạn mức → (khoá chung) begin → rút điều kiện → answer() → end → lưu vào phiên này."""
    state = st.session_state
    state.messages.append({"role": "user", "content": message})
    if state.used >= MAX_PER_SESSION:
        state.messages.append({"role": "assistant", "error": "Phiên này đã dùng hết %d tin nhắn demo. "
                               "Bấm “Bắt đầu lại” hoặc tải lại trang để mở phiên mới." % MAX_PER_SESSION})
        return
    pool = shared()
    with pool["lock"]:
        now = time.time()
        while pool["calls"] and now - pool["calls"][0] > 3600:
            pool["calls"].popleft()
        if len(pool["calls"]) >= MAX_PER_HOUR:
            state.messages.append({"role": "assistant", "error": "Web demo đã đạt giới hạn %d tin nhắn trong một giờ. "
                                   "Bạn thử lại sau nhé." % MAX_PER_HOUR})
            return
        pool["calls"].append(now)
        tracing.begin("web")
        try:
            fields = extract_request(message, state.fields, park_data())
            line = to_line(fields)
            output = answer(line)["output"] if line else ("Mình chưa thấy điều kiện nào. " + GREETING)
            error = None
        except Exception as e:  # lỗi gọi model: báo dễ hiểu, không lộ chi tiết key
            fields, line, output, error = state.fields, "", "", friendly_error(e)
        summary, events = tracing.end()
    state.used += 1
    state.fields = fields
    state.messages.append({"role": "assistant", "output": output, "error": error, "line": line,
                           "understood": understood(fields), "summary": summary, "events": events})


def render(msg):
    if msg["role"] == "user":
        st.markdown(msg["content"])
        return
    if msg.get("error"):
        st.error(msg["error"])
        return
    lines = msg["output"].splitlines()
    if lines and lines[0].startswith("Vịnh Mây"):
        st.markdown("Đây là lịch mình đề xuất. Giờ và tiền do Python tính và đã kiểm giờ mở, giờ show, "
                    "10 phút đi bộ mỗi chặng, chiều cao và ngân sách:")
        for line in lines[1:]:
            if line.startswith("Tổng"):
                st.markdown("**%s**" % line)
            else:
                when, _, name = line.partition("  ")
                st.markdown("- **%s** · %s" % (when, name.strip()))
        st.caption("Muốn đổi gì cứ nhắn, ví dụ “đổi giờ về 11h” hoặc “bé thích cảm giác mạnh”.")
    elif lines and lines[0].startswith("Không có lịch"):
        st.warning(lines[0])
        for line in lines[1:]:
            st.info(line)
    else:
        st.markdown(msg["output"])
    if msg.get("understood"):
        st.caption("Mình đang hiểu: " + msg["understood"])
    s = msg["summary"]
    with st.expander("Chi tiết kỹ thuật (chỉ phiên của bạn thấy)"):
        st.write("Dòng gửi vào `answer()`: `%s`" % (msg["line"] or "—"))
        st.write("Model: %s · gọi model %d lần · công cụ %d lần · token vào %d / ra %d"
                 % (", ".join(s["models"]) or "không gọi", s["model_calls"], s["tool_calls"], s["tokens_in"], s["tokens_out"]))
        for e in msg["events"]:
            st.caption("%s · %s · %s" % (e["kind"], e.get("name", ""), str(e.get("output", ""))[:160]))


def reset():
    st.session_state.messages = []
    st.session_state.fields = {}


st.set_page_config(page_title="Lịch gia đình · Vịnh Mây", page_icon="🎡", layout="centered")
state = st.session_state
state.setdefault("messages", [])
state.setdefault("fields", {})
state.setdefault("used", 0)

st.title("Trợ lý lịch đi chơi cho cả nhà")
st.warning("**Dữ liệu mô phỏng.** Khu Vịnh Mây, giờ, giá và quãng đi bộ đều do nhóm dựng để thử. "
           "Không phải giá hay lịch thật của khu vui chơi nào.")

if not REAL_MODEL and not ALLOW_FAKE:
    st.error("Chưa cấu hình model thật. Người quản trị cần đặt MODEL_PROVIDER, MODEL_NAME và API_KEY "
             "trong secret của máy chủ. Web không chạy bằng model giả ở chế độ chính thức.")
    st.stop()
if not REAL_MODEL:
    st.info("Đang thử trên máy bằng model giả (DEMO_ALLOW_FAKE=1): chỉ hiểu câu đơn giản, không dùng để báo cáo.")

c1, c2, c3 = st.columns([2, 2, 1])
clicked = None
if c1.button("Thử: lịch khả thi", use_container_width=True):
    reset(); clicked = EXAMPLES["Lịch khả thi"]
if c2.button("Thử: lịch xung đột", use_container_width=True):
    reset(); clicked = EXAMPLES["Lịch xung đột"]
c3.button("Bắt đầu lại", on_click=reset, use_container_width=True)

with st.chat_message("assistant"):
    st.markdown(GREETING)
for msg in state.messages:
    with st.chat_message(msg["role"]):
        render(msg)

typed = st.chat_input("Nhắn điều kiện chuyến đi…")
message = clicked or typed
if message:
    with st.chat_message("user"):
        st.markdown(message)
    with st.chat_message("assistant"):
        with st.spinner("Đang đọc điều kiện, kiểm các lịch khả thi và nhờ model chọn…"):
            handle(message)
        render(state.messages[-1])

st.caption("Đã dùng %d/%d tin nhắn trong phiên này. Model: %s."
           % (state.used, MAX_PER_SESSION, ai.MODEL_NAME if REAL_MODEL else "giả"))
