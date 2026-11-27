"""Web demo C1 · Lịch gia đình tại khu vui chơi (Vịnh Mây, dữ liệu mô phỏng).

Chạy:   streamlit run streamlit_app.py
Dùng chung answer(text) trong codebase/agent.py với `python run.py`, `run.py eval` và `run.py simulate`.

Biến môi trường hoặc Streamlit secret (không commit key):
  MODEL_PROVIDER, MODEL_NAME, API_KEY       model thật (nhóm dùng gemini / gemini-3.1-flash-lite)
  DEMO_MAX_PER_SESSION   số lần bấm tạo lịch tối đa mỗi phiên (mặc định 10)
  DEMO_MAX_PER_HOUR      số lần tối đa mỗi giờ cho toàn bộ web (mặc định 60)
  DEMO_ALLOW_FAKE=1      chỉ dùng khi thử trên máy: cho chạy model giả. Mặc định web báo lỗi nếu thiếu model thật.
"""
import collections
import datetime
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
from agent import answer  # noqa: E402
from tools import load_park  # noqa: E402

MAX_PER_SESSION = int(os.environ.get("DEMO_MAX_PER_SESSION") or 10)
MAX_PER_HOUR = int(os.environ.get("DEMO_MAX_PER_HOUR") or 60)
ALLOW_FAKE = os.environ.get("DEMO_ALLOW_FAKE") == "1"
REAL_MODEL = ai.MODEL_PROVIDER != "fake"

EXAMPLES = {
    "ok": dict(start=datetime.time(9, 0), end=datetime.time(12, 0), adults=2, children=1, height=110,
               budget=500000, required=["chim"], closed=[], preference="", buffer=0),
    "conflict": dict(start=datetime.time(10, 51), end=datetime.time(12, 0), adults=1, children=0, height=110,
                     budget=180000, required=["chim"], closed=[], preference="", buffer=0),
}


@st.cache_resource
def shared():
    """Dùng chung giữa các phiên: khoá cho trace (tracing.py giữ trạng thái toàn cục) và bộ đếm lượt mỗi giờ."""
    return {"lock": threading.Lock(), "calls": collections.deque()}


@st.cache_data
def activities():
    return [(a["id"], a["name"]) for a in load_park()["activities"]]


def clean(text):
    """Ô tự do không được phá cấu trúc tên=giá trị; ký tự ; và = bị thay."""
    return text.replace(";", ",").replace("=", " ").strip()


def build_request(v):
    parts = ["giờ=%s-%s" % (v["start"].strftime("%H:%M"), v["end"].strftime("%H:%M")),
             "lớn=%d" % v["adults"], "trẻ=%d" % v["children"]]
    if v["children"]:
        parts.append("cao=%d" % v["height"])
    parts.append("đồng=%d" % v["budget"])
    if v["required"]:
        parts.append("phải có=" + ",".join(v["required"]))
    if v["closed"]:
        parts.append("đóng=" + ",".join(v["closed"]))
    if clean(v["preference"]):
        parts.append("ưu tiên=" + clean(v["preference"]))
    if v["buffer"]:
        parts.append("đệm=%d" % v["buffer"])
    return "; ".join(parts)


def friendly_error(error):
    text = "%s" % error
    low = text.lower()
    if "429" in text or "quota" in low or "resource_exhausted" in low or "rate" in low:
        return "Model đang hết lượt gọi của gói hiện tại. Vui lòng thử lại sau vài phút."
    if "401" in text or "403" in text or "api key" in low or "api_key" in low:
        return "Máy chủ chưa có key hợp lệ cho model. Người quản trị cần kiểm tra secret API_KEY."
    if "timed out" in low or "urlopen" in low or "connection" in low:
        return "Không kết nối được tới model. Vui lòng thử lại."
    return "Có lỗi khi gọi model (%s). Vui lòng thử lại." % type(error).__name__


def run_request(text):
    """Một lượt: kiểm hạn mức → begin/answer/end trong khoá chung → lưu vào phiên này."""
    state = st.session_state
    if state.used >= MAX_PER_SESSION:
        state.result = {"error": "Phiên này đã dùng hết %d lượt demo. Tải lại trang để bắt đầu phiên mới." % MAX_PER_SESSION}
        return
    pool = shared()
    with pool["lock"]:
        now = time.time()
        while pool["calls"] and now - pool["calls"][0] > 3600:
            pool["calls"].popleft()
        if len(pool["calls"]) >= MAX_PER_HOUR:
            state.result = {"error": "Web demo đã đạt giới hạn %d lượt trong một giờ. Vui lòng thử lại sau." % MAX_PER_HOUR}
            return
        pool["calls"].append(now)
        tracing.begin("web")
        try:
            output, error = answer(text)["output"], None
        except Exception as e:  # lỗi gọi model: báo dễ hiểu, không lộ chi tiết key
            output, error = "", friendly_error(e)
        summary, events = tracing.end()
    state.used += 1
    state.result = {"request": text, "output": output, "error": error, "summary": summary, "events": events}


def load_example(name):
    for key, value in EXAMPLES[name].items():
        st.session_state[key] = value
    st.session_state.result = None


def rerun_with_new_end():
    st.session_state.end = st.session_state.new_end
    st.session_state.pending = True


def show_result(result):
    if result.get("error"):
        st.error(result["error"])
        return
    lines = result["output"].splitlines()
    if lines and lines[0].startswith("Vịnh Mây"):
        st.success("Lịch đề xuất (Python đã kiểm giờ, đi bộ, chiều cao và ngân sách)")
        for line in lines[1:]:
            if line.startswith("Tổng"):
                st.markdown("**%s**" % line)
            else:
                when, _, name = line.partition("  ")
                st.markdown("- **%s** · %s" % (when, name.strip()))
    elif lines and lines[0].startswith("Không có lịch"):
        st.warning(lines[0])
        for line in lines[1:]:
            st.info(line)
    else:
        st.info(result["output"])
    s = result["summary"]
    with st.expander("Chi tiết kỹ thuật của lượt này (chỉ phiên của bạn thấy)"):
        st.write("Yêu cầu gửi vào `answer()`: `%s`" % result["request"])
        st.write("Model: %s · gọi model %d lần · công cụ %d lần · token vào %d / ra %d"
                 % (", ".join(s["models"]) or "không gọi", s["model_calls"], s["tool_calls"], s["tokens_in"], s["tokens_out"]))
        for e in result["events"]:
            st.caption("%s · %s · %s" % (e["kind"], e.get("name", ""), str(e.get("output", ""))[:160]))


st.set_page_config(page_title="Lịch gia đình · Vịnh Mây", page_icon="🎡", layout="centered")
state = st.session_state
for key, value in dict(EXAMPLES["ok"], used=0, result=None, pending=False).items():
    state.setdefault(key, value)

st.title("Lịch đi chơi cho cả nhà")
st.warning("**Dữ liệu mô phỏng.** Khu Vịnh Mây, giờ, giá và quãng đi bộ đều do nhóm dựng để thử. "
           "Không phải giá hay lịch thật của khu vui chơi nào.")

if not REAL_MODEL and not ALLOW_FAKE:
    st.error("Chưa cấu hình model thật. Người quản trị cần đặt MODEL_PROVIDER, MODEL_NAME và API_KEY "
             "trong secret của máy chủ. Web không chạy bằng model giả ở chế độ chính thức.")
    st.stop()
if not REAL_MODEL:
    st.info("Đang thử trên máy bằng model giả (DEMO_ALLOW_FAKE=1). Lượt này không dùng để báo cáo.")

st.caption("Bấm thử một ví dụ:")
c1, c2 = st.columns(2)
c1.button("Lịch khả thi: cả nhà xem Show chim", on_click=load_example, args=("ok",), use_container_width=True)
c2.button("Xung đột: đến cổng 10:51, show 11:00", on_click=load_example, args=("conflict",), use_container_width=True)

names = dict(activities())
a, b = st.columns(2)
a.time_input("Giờ đến cổng", key="start", step=60)
b.time_input("Giờ về", key="end", step=60)
a.number_input("Số người lớn", min_value=0, max_value=20, step=1, key="adults")
b.number_input("Số trẻ", min_value=0, max_value=20, step=1, key="children")
if state.children:
    st.number_input("Chiều cao bé thấp nhất (cm)", min_value=0, max_value=200, step=1, key="height")
st.number_input("Ngân sách cả nhóm (đồng)", min_value=0, step=10000, key="budget")
st.multiselect("Hoạt động bắt buộc", options=list(names), format_func=names.get, key="required")
with st.expander("Tuỳ chọn thêm"):
    st.multiselect("Điểm đang đóng hoặc show bị huỷ", options=list(names), format_func=names.get, key="closed")
    st.text_input("Sở thích (ví dụ: bé thích động vật, cảm giác mạnh)", key="preference", max_chars=120)
    st.number_input("Đến trước giờ show ít nhất (phút)", min_value=0, max_value=120, step=5, key="buffer")

values = {k: state[k] for k in EXAMPLES["ok"]}
if st.button("Tạo lịch", type="primary", use_container_width=True) or state.pending:
    state.pending = False
    with st.spinner("Đang kiểm các lịch khả thi và nhờ model chọn…"):
        run_request(build_request(values))

if state.result:
    show_result(state.result)
    if not state.result.get("error"):
        st.divider()
        st.caption("Muốn về sớm hoặc muộn hơn? Sửa giờ về rồi tạo lại.")
        state.setdefault("new_end", state.end)
        d1, d2 = st.columns([2, 1])
        d1.time_input("Giờ về mới", key="new_end", step=60)
        d2.button("Tạo lại", on_click=rerun_with_new_end, use_container_width=True)

st.caption("Đã dùng %d/%d lượt trong phiên này. Model: %s."
           % (state.used, MAX_PER_SESSION, ai.MODEL_NAME if REAL_MODEL else "giả"))
