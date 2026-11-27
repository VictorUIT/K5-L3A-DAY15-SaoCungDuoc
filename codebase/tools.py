"""Dữ liệu và kiểm tra lịch của khu Vịnh Mây mô phỏng.

Mọi giờ và tiền mà người dùng thấy đều do các hàm ở đây tính, không do model tính.
"""
import itertools
import json
from pathlib import Path

from tracing import tool

MAX_STOPS = 3
NO_LIMIT = 10 ** 15


def minutes(clock):
    hour, minute = map(int, clock.split(":"))
    return hour * 60 + minute


def clock(minutes_since_midnight):
    return "%02d:%02d" % divmod(minutes_since_midnight, 60)


def money(vnd):
    return f"{vnd:,} đ".replace(",", ".")


def is_show(activity):
    """Show có giờ diễn cố định: khung mở–đóng đúng bằng thời lượng (Show chim 11:00–11:20, 20 phút)."""
    return minutes(activity["close"]) - minutes(activity["open"]) == activity["duration"]


def entry_cost(park, request):
    return request["adults"] * park["adult_vnd"] + request["children"] * park["child_vnd"]


def _place(park, request, activity, current, cost):
    """Thử xếp một điểm sau mốc `current`. Trả (điểm, giờ xong, tiền mới) hoặc (None, lý do, chi tiết)."""
    arrival = current + park["walk_minutes"]
    opening, closing = minutes(activity["open"]), minutes(activity["close"])
    if is_show(activity) and arrival + request["buffer"] > opening:
        return None, "show", {"arrival": arrival, "latest": opening - request["buffer"]}
    start = max(arrival, opening)
    end = start + activity["duration"]
    cost += (request["adults"] + request["children"]) * activity["extra_vnd"]
    if end > closing:
        return None, "close", {"start": start, "end": end}
    if end > request["end"]:
        return None, "window", {"start": start, "end": end}
    if cost > request["budget"]:
        return None, "budget", {"cost": cost}
    stop = {"id": activity["id"], "name": activity["name"], "start": clock(start), "end": clock(end)}
    return stop, end, cost


def available(park, request):
    """Điểm còn mở và hợp chiều cao của bé thấp nhất (người lớn không bị giới hạn)."""
    return [a for a in park["activities"] if a["id"] not in request["closed"]
            and (not request["children"] or a["min_cm"] <= request["min_height"])]


def enumerate_routes(park, request):
    """Liệt kê mọi lịch 1–3 điểm khác nhau thoả mọi ràng buộc. Hàm thuần, không ghi trace."""
    choices = available(park, request)
    routes = []
    for size in range(1, min(MAX_STOPS, len(choices)) + 1):
        for order in itertools.permutations(choices, size):
            if request["required"] - {a["id"] for a in order}:
                continue
            current, cost, stops = request["start"], entry_cost(park, request), []
            for activity in order:
                stop, current, cost = _place(park, request, activity, current, cost)
                if stop is None:
                    break
                stops.append(stop)
            else:
                routes.append({"stops": stops, "total": cost})
    return routes


@tool
def load_park():
    """load_park · đầu vào: không có · đầu ra: danh mục khu chơi từ data/park.json · chỉ đọc file."""
    path = Path(__file__).resolve().parents[1] / "data" / "park.json"
    return json.loads(path.read_text(encoding="utf-8"))


@tool
def feasible_routes(park, request):
    """feasible_routes · đầu vào: khu chơi + yêu cầu đã chuẩn hoá · đầu ra: danh sách lịch hợp lệ
    (mỗi lịch: các điểm kèm giờ bắt đầu/kết thúc và tổng tiền cả nhóm) · chỉ tính toán, không tác động ra ngoài."""
    return enumerate_routes(park, request)


def _single_stop_problem(park, request, activity):
    """Vì sao một điểm bắt buộc không xếp được ngay cả khi đi thẳng từ cổng. None nếu một mình nó xếp được."""
    stop, why, info = _place(park, request, activity, request["start"], entry_cost(park, request))
    if stop is not None:
        return None
    name = activity["name"]
    verb = "diễn" if is_show(activity) else "chơi"
    if why == "show":
        need = f"có mặt trước {request['buffer']} phút, tức trước hoặc đúng {clock(info['latest'])}" \
            if request["buffer"] else f"có mặt trước hoặc đúng {clock(info['latest'])}"
        return (f"Từ cổng lúc {clock(request['start'])}, đi bộ {park['walk_minutes']} phút thì đến {name} "
                f"sớm nhất {clock(info['arrival'])}, trong khi show bắt đầu {activity['open']} và cần {need}.")
    if why == "close":
        return (f"{name} sớm nhất {verb} {clock(info['start'])}–{clock(info['end'])}, "
                f"quá giờ đóng {activity['close']}.")
    if why == "window":
        return (f"{name} sớm nhất {verb} {clock(info['start'])}–{clock(info['end'])}, "
                f"quá giờ kết thúc {clock(request['end'])} bạn đã chọn.")
    return None  # thiếu tiền được giải thích ở bước ngân sách


@tool
def explain_no_route(park, request):
    """explain_no_route · đầu vào: khu chơi + yêu cầu không có lịch hợp lệ · đầu ra: câu nêu ràng buộc cụ thể
    đang chặn, kèm giờ hoặc số tiền tính lại từ park.json · chỉ tính toán, không tác động ra ngoài."""
    by_id = {a["id"]: a for a in park["activities"]}
    required = sorted(request["required"])
    entry = entry_cost(park, request)
    conflict = sorted(request["required"] & request["closed"])
    if conflict:
        return "Điểm bắt buộc đang đóng: " + ", ".join(by_id[i]["name"] for i in conflict) + "."
    if len(required) > MAX_STOPS:
        return f"Bạn yêu cầu {len(required)} điểm bắt buộc, bản này chỉ xếp tối đa {MAX_STOPS} điểm."
    too_short = [by_id[i] for i in required if request["children"] and by_id[i]["min_cm"] > request["min_height"]]
    if too_short:
        return "; ".join(f"{a['name']} cần trẻ cao từ {a['min_cm']} cm, bé thấp nhất cao {request['min_height']} cm"
                         for a in too_short) + "."
    if entry > request["budget"]:
        return (f"Riêng vé vào cổng cho nhóm đã là {money(entry)}, vượt ngân sách {money(request['budget'])} "
                f"(thiếu {money(entry - request['budget'])}).")
    if not available(park, request):
        return "Mọi điểm trong danh mục đều đang đóng hoặc chưa hợp chiều cao của bé."
    unlimited = dict(request, budget=NO_LIMIT)
    routes = enumerate_routes(park, unlimited)
    if routes:
        cheapest = min(routes, key=lambda r: r["total"])
        names = ", ".join(s["name"] for s in cheapest["stops"])
        return (f"Lịch rẻ nhất thoả giờ ({names}) cần {money(cheapest['total'])} cho cả nhóm, "
                f"vượt ngân sách {money(request['budget'])} (thiếu {money(cheapest['total'] - request['budget'])}).")
    problems = [p for p in (_single_stop_problem(park, unlimited, by_id[i]) for i in required) if p]
    if problems:
        return " ".join(problems)
    if required:
        names = ", ".join(by_id[i]["name"] for i in required)
        return (f"Từng điểm bắt buộc ({names}) xếp riêng thì được, nhưng không ghép được cùng nhau trong "
                f"{clock(request['start'])}–{clock(request['end'])} khi tính {park['walk_minutes']} phút đi bộ mỗi chặng.")
    return (f"Không điểm nào đang mở xếp được trong {clock(request['start'])}–{clock(request['end'])} "
            f"khi tính {park['walk_minutes']} phút đi bộ từ cổng.")


def _feasible(park, request, **changes):
    return bool(enumerate_routes(park, dict(request, **changes)))


@tool
def suggest_fixes(park, request):
    """suggest_fixes · đầu vào: khu chơi + yêu cầu không có lịch · đầu ra: tối đa 3 gợi ý đổi điều kiện, mỗi gợi ý
    đã được kiểm lại bằng enumerate_routes là ra ít nhất một lịch · chỉ tính toán, không tác động ra ngoài."""
    by_id = {a["id"]: a for a in park["activities"]}
    tips = []
    if len(request["required"]) > MAX_STOPS:
        return ["Giữ tối đa %d điểm trong phải có." % MAX_STOPS]
    for i in sorted(request["required"]):
        rest = request["required"] - {i}
        if _feasible(park, request, required=rest):
            tips.append("Bỏ %s khỏi phải có." % by_id[i]["name"])
    late = dict(request, budget=NO_LIMIT)
    priced = enumerate_routes(park, late)
    if priced:
        need = min(r["total"] for r in priced)
        tips.append("Tăng ngân sách lên ít nhất %s." % money(need))
    longer = enumerate_routes(park, dict(request, end=24 * 60 - 1))
    if longer:
        need = min(minutes(r["stops"][-1]["end"]) for r in longer)
        if need > request["end"]:
            tips.append("Lùi giờ về đến %s hoặc muộn hơn." % clock(need))
    for gate in range(request["start"] - 1, max(request["start"] - 180, 0) - 1, -1):
        if _feasible(park, request, start=gate):
            tips.append("Đến cổng lúc %s hoặc sớm hơn." % clock(gate))
            break
    if request["buffer"] and _feasible(park, request, buffer=0):
        tips.append("Giảm phút đệm trước show (đang %d phút)." % request["buffer"])
    return tips[:3]
