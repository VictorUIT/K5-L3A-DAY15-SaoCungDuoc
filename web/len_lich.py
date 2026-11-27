"""Trang "Lên lịch": chatbot đầy đủ, form ở thanh bên (trên điện thoại thu vào nút »), ô chat ghim cuối màn hình."""
from web import planner
from web.common import header

header("Vivu", "Gợi ý hoạt động cho chuyến du lịch tuyệt vời")
if planner.setup():
    planner.process()
    planner.trip_form(inline=False)
    planner.conversation(inline=False)
    planner.chat_box()
