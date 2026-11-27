"""Dữ liệu và kiểm tra lịch của khu Vịnh Mây mô phỏng."""
import itertools
import json
from pathlib import Path

from tracing import tool


def minutes(clock):
    hour, minute = map(int, clock.split(":"))
    return hour * 60 + minute


def clock(minutes_since_midnight):
    return "%02d:%02d" % divmod(minutes_since_midnight, 60)


@tool
def load_park():
    """Đọc park.json. Đầu vào rỗng, trả dữ liệu khu chơi. Chỉ đọc."""
    path = Path(__file__).resolve().parents[1] / "data" / "park.json"
    return json.loads(path.read_text(encoding="utf-8"))


@tool
def feasible_routes(park, request):
    """Nhận khu và yêu cầu đã chuẩn hóa, trả các lịch hợp lệ. Chỉ tính toán."""
    adults, children = request["adults"], request["children"]
    entry = adults * park["adult_vnd"] + children * park["child_vnd"]
    choices = [a for a in park["activities"] if a["id"] not in request["closed"]
               and (not children or a["min_cm"] <= request["min_height"])]
    routes = []
    for size in range(1, min(3, len(choices)) + 1):
        for order in itertools.permutations(choices, size):
            if request["required"] - {a["id"] for a in order}:
                continue
            current, cost, stops = request["start"], entry, []
            for activity in order:
                arrival = current + park["walk_minutes"]
                opening = minutes(activity["open"])
                closing = minutes(activity["close"])
                if activity["id"] in {"chim", "nhac"} and arrival + request["buffer"] > opening:
                    break
                start = max(arrival, opening)
                end = start + activity["duration"]
                cost += (adults + children) * activity["extra_vnd"]
                if end > min(closing, request["end"]) or cost > request["budget"]:
                    break
                stops.append({"id": activity["id"], "name": activity["name"],
                              "start": clock(start), "end": clock(end)})
                current = end
            else:
                routes.append({"stops": stops, "total": cost})
    return routes
