"""Trang "Lên lịch": hỗ trợ chọn công viên (mặc định Vịnh Mây, hoặc VinWonders Nha Trang snapshot công khai)."""
from web import nha_trang_ui, planner
from web.common import NHA_TRANG_PARK_ID, header, park_selector

selected_park = park_selector("planner")
if selected_park == NHA_TRANG_PARK_ID:
    nha_trang_ui.render_nha_trang_planner()
else:
    header("Vivu", "Gợi ý hoạt động cho chuyến du lịch tuyệt vời")
    if planner.setup():
        planner.process()
        planner.trip_form(inline=False)
        planner.conversation(inline=False)
        planner.chat_box()
