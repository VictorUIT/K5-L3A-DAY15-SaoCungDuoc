"""Khung CP2. Một dòng yêu cầu chứa các trường ngăn bằng dấu chấm phẩy."""
import json
import re

from ai import call_model
from tools import feasible_routes, load_park, minutes


class InputError(ValueError):
    pass


def read_request(text, park):
    fields = {}
    supported = {"giờ", "lớn", "trẻ", "cao", "đồng", "ưu tiên", "phải có", "đóng", "đệm"}
    for part in text.strip().strip(";").split(";"):
        key, separator, value = part.strip().partition("=")
        key = key.strip().lower()
        if not separator or key not in supported or key in fields or not value.strip():
            raise InputError("Hãy dùng các trường duy nhất như ví dụ trong README, mỗi trường dạng tên=giá trị.")
        fields[key] = value.strip()
    missing = [k for k in ("giờ", "lớn", "trẻ", "đồng") if k not in fields]
    if missing:
        raise InputError("Bạn bổ sung " + ", ".join(missing) + " được không?")
    def integer(key, default="0"):
        value = fields.get(key, default)
        if not re.fullmatch(r"[0-9]{1,12}", value):
            raise InputError("Cần số nguyên không âm cho trường " + key + ".")
        return int(value)
    times = re.fullmatch(r"((?:[01]?\d|2[0-3]):[0-5]\d)\s*[-–]\s*((?:[01]?\d|2[0-3]):[0-5]\d)", fields["giờ"])
    if not times:
        raise InputError("Bạn cho biết giờ đến và giờ kết thúc theo dạng 09:00-12:00 nhé.")
    start, end = map(minutes, times.groups())
    if start >= end:
        raise InputError("Giờ kết thúc phải sau giờ đến trong cùng ngày.")
    adults, children = integer("lớn"), integer("trẻ")
    if adults + children == 0:
        raise InputError("Có bao nhiêu người trong nhóm đi chơi?")
    if children and not integer("cao"):
        raise InputError("Bé thấp nhất cao bao nhiêu cm?")
    names = {a["id"] for a in park["activities"]}
    def ids(key):
        values = {s.strip().lower() for s in fields.get(key, "").split(",") if s.strip()}
        if values - names:
            raise InputError("Không có dữ liệu cho mã " + ", ".join(sorted(values - names)) + ".")
        return values
    return {"start": start, "end": end, "adults": adults, "children": children,
            "min_height": integer("cao"), "budget": integer("đồng"),
            "buffer": integer("đệm"), "required": ids("phải có"), "closed": ids("đóng"),
            "preference": fields.get("ưu tiên", "")}


def answer(text):
    park = load_park()
    try:
        request = read_request(text, park)
    except InputError as error:
        return {"output": str(error)}
    options = feasible_routes(park, request)
    if not options:
        ticket = request["adults"] * park["adult_vnd"] + request["children"] * park["child_vnd"]
        conflict = request["required"] & request["closed"]
        too_short = [a["name"] for a in park["activities"] if a["id"] in request["required"]
                     and request["children"] and a["min_cm"] > request["min_height"]]
        if conflict:
            reason = "Điểm bắt buộc đã đóng: " + ", ".join(sorted(conflict)) + "."
        elif too_short:
            reason = "Chiều cao của bé chưa đủ để chơi " + ", ".join(too_short) + "."
        elif ticket > request["budget"]:
            reason = f"Riêng vé vào cổng cho nhóm đã là {ticket:,} đ.".replace(",", ".")
        else:
            reason = "Hãy kiểm tra lại khung giờ, thời gian đi bộ, đệm trước show và ngân sách."
        return {"output": "Không có lịch hợp lệ trong phạm vi tối đa 3 điểm. " + reason}
    prompt = json.dumps({"preference": request["preference"], "options": options}, ensure_ascii=False)
    reply = call_model("Chọn một lịch theo sở thích. Trả chỉ số nguyên từ 0 của lịch đã có.", prompt)
    try:
        chosen = json.loads(reply["text"])
    except (ValueError, TypeError):
        chosen = None
    if type(chosen) is not int or not 0 <= chosen < len(options):
        return {"output": "Chưa chọn được lịch hợp lệ. Vui lòng thử lại."}
    route = options[chosen]
    lines = ["Vịnh Mây · dữ liệu mô phỏng"]
    lines.extend(f"{s['start']}–{s['end']}  {s['name']}" for s in route["stops"])
    lines.append(f"Tổng cho cả nhóm: {route['total']:,} đ".replace(",", "."))
    return {"output": "\n".join(lines)}
