"""Web Vịnh Mây (dữ liệu mô phỏng) · điểm vào của Streamlit.

Chạy:   python -m streamlit run streamlit_app.py --server.runOnSave=true
Trang:  web/trang_chu.py (giới thiệu khu, đọc từ data/park.json) · web/len_lich.py (chatbot lên lịch, gọi answer()).

Biến môi trường hoặc Streamlit secret (không commit key):
  MODEL_PROVIDER, MODEL_NAME, API_KEY       model thật (nhóm dùng gemini / gemini-3.1-flash-lite)
  DEMO_MAX_PER_SESSION   số lần gửi tối đa mỗi phiên (mặc định 15)
  DEMO_MAX_PER_HOUR      số lần gửi tối đa mỗi giờ cho toàn bộ web (mặc định 60)
  DEMO_ALLOW_FAKE=1      chỉ dùng khi thử trên máy: cho chạy model giả. Mặc định web báo lỗi nếu thiếu model thật.
"""
import os
import sys

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
for _path in (os.path.join(ROOT, "codebase"), ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

SETTINGS = ("MODEL_PROVIDER", "MODEL_NAME", "API_KEY", "DEMO_MAX_PER_SESSION", "DEMO_MAX_PER_HOUR", "DEMO_ALLOW_FAKE")
for _name in SETTINGS:  # secret phía máy chủ → biến môi trường, trước khi trang nào nạp ai.py
    try:
        _value = st.secrets.get(_name)
    except Exception:  # chưa có secrets.toml khi chạy trên máy
        _value = None
    if _value is not None:
        os.environ.setdefault(_name, str(_value))

from web.common import CSS  # noqa: E402

st.set_page_config(page_title="Vivu · Gợi ý hoạt động cho chuyến du lịch tuyệt vời", page_icon="🌊", layout="centered")
# Giữ giá trị form khi đổi trang: Streamlit dọn trạng thái của ô nhập khi trang đổi; gán lại ở đầu mỗi lượt vẽ
# để trang chủ và trang Lên lịch dùng chung điều kiện chuyến đi.
for _key in [k for k in st.session_state if k.startswith("t_") or k == "regen_end"]:
    st.session_state[_key] = st.session_state[_key]
st.markdown(CSS, unsafe_allow_html=True)

home = st.Page("web/trang_chu.py", title="Trang chủ", icon=":material/home:", default=True)
planner = st.Page("web/len_lich.py", title="Lên lịch", icon=":material/event_note:", url_path="len-lich")
st.navigation([home, planner], position="top").run()
