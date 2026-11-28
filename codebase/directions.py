"""Đường đến VinWonders Nha Trang: điểm đến đã đối chiếu nguồn chính thức, link Google Maps, Routes API (tuỳ chọn).

- Không cần API key: directions_url / search_url chỉ tạo link Google Maps (api=1). Khi khách đi từ vị trí hiện tại,
  link bỏ tham số origin để Google Maps trên điện thoại tự lấy vị trí.
- Có GOOGLE_MAPS_ROUTES_API_KEY (Streamlit Secrets phía server): compute_route gọi Routes API computeRoutes.
- Không ghi toạ độ hay địa chỉ của khách vào file, log, trace; không gửi cho model AI. Hàm ở đây không lưu gì.
Chỉ dùng thư viện chuẩn của Python.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

CHECKED_ON = "28/11/2026"  # ngày nhóm đối chiếu các trang nguồn bên dưới

# Điểm đến theo phương tiện. verified=True: tên điểm có trên trang chính thức của VinWonders → nút chỉ đường.
# verified=False: chưa xác minh được điểm đón cụ thể → chỉ có nút tìm địa điểm. Chưa đối chiếu được Google Place ID
# (không trang chính thức nào ghi), nên place_id để None và link tìm theo tên.
DESTINATIONS: list[dict[str, Any]] = [
    {
        "id": "speedboat",
        "mode": "Tàu cao tốc / cano ra đảo",
        "name": "Cảng Vinpearl Nha Trang",
        "short": "Cảng Vinpearl",
        # Đúng tên trên trang chính thức. Thêm "Cầu Đá" vào chuỗi thì Google bắt sang bến công cộng Cảng Cầu Đá
        # (14b Trần Phú); "Bến tàu Vinpearl" lại ra bến phía đảo. Đã mở thử link ngày 28/11/2026.
        "query": "Cảng Vinpearl Nha Trang",
        "maps_label": "Vinpearl Land Terminal (Nam Nha Trang, ngay sau Cảng Cầu Đá theo hướng đi)",
        "place_id": None,
        "verified": True,
        "kind": "bến tàu",
        "source": "VinWonders · “Vinpearl Harbour ở đâu?” (đăng 16/08/2025)",
        "source_url": "https://vinwonders.com/vi/wonderpedia/news/vinpearl-harbour-o-dau/",
        "source_quote": "Đường Trần Phú → Viện Hải Dương Học → Cảng Cầu Đá → Cảng Vinpearl Nha Trang → Vinpearl Harbour trên đảo Hòn Tre",
        "next_leg": "Từ bến đi tàu ra đảo: nguồn chính thức ghi tàu cao tốc khoảng 15 phút, cano khoảng 10 phút; "
                    "không có lịch chuyến hay thời gian chờ tàu.",
        "next_leg_sources": [
            "VinWonders · “Địa chỉ Vinpearl Nha Trang” (đăng 14/12/2025)",
        ],
    },
    {
        "id": "cable",
        "mode": "Cáp treo vượt biển",
        "name": "Ga cáp treo Vinpearl (đường Trần Phú)",
        "short": "Ga cáp treo",
        "query": "Ga cáp treo Vinpearl Nha Trang",
        "maps_label": None,
        "place_id": None,
        "verified": False,
        "kind": "ga cáp treo",
        "source": "VinWonders · “How to get to Vinpearl Nha Trang” (đăng 20/12/2025)",
        "source_url": "https://vinwonders.com/en/wonderpedia/news/how-to-get-to-vinpearl-nha-trang/",
        "source_quote": "its station residing on Tran Phu Street",
        "next_leg": "Nguồn chính thức chưa ghi địa chỉ cụ thể của ga. Trang “Địa chỉ Vinpearl Nha Trang” (14/12/2025) ghi "
                    "cáp treo “hiện đang tạm dừng hoạt động”; nên gọi tổng đài 1900 6677 trước khi đi.",
        "next_leg_sources": [],
    },
]
DEST_BY_ID = {d["id"]: d for d in DESTINATIONS}

# Phương tiện để tới bến: (nhãn, travelmode của link Google Maps, travelMode của Routes API)
TRAVEL_MODES = {
    "driving": ("Ô tô / taxi", "driving", "DRIVE"),
    "two-wheeler": ("Xe máy", "two-wheeler", "TWO_WHEELER"),
    "walking": ("Đi bộ", "walking", "WALK"),
}

ROUTES_ENDPOINT = "https://routes.googleapis.com/directions/v2:computeRoutes"
FIELD_MASK = "routes.distanceMeters,routes.duration,routes.localizedValues"


def directions_url(dest: dict[str, Any], origin: str | None = None, travelmode: str | None = None) -> str:
    """Link Google Maps Directions (api=1). origin=None: Google Maps tự dùng vị trí hiện tại của điện thoại."""
    params = {"api": "1", "destination": dest["query"]}
    if dest.get("place_id"):
        params["destination_place_id"] = dest["place_id"]
    if origin and origin.strip():
        params["origin"] = origin.strip()
    if travelmode in {"driving", "walking", "bicycling", "two-wheeler", "transit"}:
        params["travelmode"] = travelmode
    return "https://www.google.com/maps/dir/?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)


def search_url(dest: dict[str, Any]) -> str:
    """Link Google Maps Search (api=1): chỉ mở kết quả tìm kiếm theo tên, không phải chỉ đường tới điểm đã xác minh."""
    params = {"api": "1", "query": dest["query"]}
    if dest.get("place_id"):
        params["query_place_id"] = dest["place_id"]
    return "https://www.google.com/maps/search/?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)


class RouteError(Exception):
    """Lỗi dễ hiểu cho khách; không chứa key, toạ độ hay địa chỉ."""


def _parse_duration(text: str | None) -> int | None:
    if not text or not text.endswith("s"):
        return None
    try:
        return round(float(text[:-1]))
    except ValueError:
        return None


def compute_route(api_key: str, origin: tuple[float, float] | str, dest: dict[str, Any], mode: str = "driving",
                  timeout: float = 10.0) -> dict[str, Any]:
    """Gọi Routes API computeRoutes một lần. origin: (lat, lng) hoặc địa chỉ/tên resort khách nhập.

    Trả {"mode", "mode_label", "dest_name", "dest_kind", "distance_m", "duration_s"}; không trả lại origin.
    """
    if not api_key:
        raise RouteError("Chưa cấu hình khoá Google Maps Routes trên máy chủ.")
    label, _, api_mode = TRAVEL_MODES.get(mode, TRAVEL_MODES["driving"])
    if isinstance(origin, tuple):
        lat, lng = origin
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise RouteError("Vị trí không hợp lệ.")
        origin_obj: dict[str, Any] = {"location": {"latLng": {"latitude": lat, "longitude": lng}}}
    else:
        text = (origin or "").strip()
        if len(text) < 3:
            raise RouteError("Nhập tên resort hoặc địa chỉ (ít nhất 3 ký tự).")
        origin_obj = {"address": text[:200]}
    dest_obj = {"placeId": dest["place_id"]} if dest.get("place_id") else {"address": dest["query"]}
    body = {"origin": origin_obj, "destination": dest_obj, "travelMode": api_mode, "languageCode": "vi", "units": "METRIC"}
    if api_mode in ("DRIVE", "TWO_WHEELER"):
        body["routingPreference"] = "TRAFFIC_AWARE"
    req = urllib.request.Request(
        os.environ.get("GOOGLE_MAPS_ROUTES_ENDPOINT") or ROUTES_ENDPOINT,  # biến này chỉ để test bằng máy chủ giả lập
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": api_key, "X-Goog-FieldMask": FIELD_MASK},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise RouteError("Google Maps đang hết lượt tính tuyến của gói hiện tại. Bạn vẫn mở chỉ đường được.") from None
        if e.code in (401, 403):
            raise RouteError("Khoá Google Maps Routes trên máy chủ chưa hợp lệ hoặc chưa bật Routes API.") from None
        if e.code == 400:
            raise RouteError("Google Maps không hiểu điểm xuất phát này. Thử nhập rõ hơn, vd tên resort kèm “Nha Trang”.") from None
        raise RouteError(f"Google Maps báo lỗi ({e.code}).") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RouteError("Không kết nối được tới Google Maps. Bạn thử lại sau nhé.") from None
    routes = data.get("routes") or []
    if not routes:
        raise RouteError(f"Google Maps không tìm được tuyến {label.lower()} tới {dest['name']}.")
    r = routes[0]
    duration = _parse_duration(r.get("duration"))
    if duration is None or r.get("distanceMeters") is None:
        raise RouteError("Google Maps trả về tuyến thiếu quãng đường hoặc thời gian.")
    return {"mode": mode, "mode_label": label, "dest_id": dest["id"], "dest_name": dest["name"], "dest_kind": dest["kind"],
            "distance_m": int(r["distanceMeters"]), "duration_s": duration}


def describe_route(route: dict[str, Any]) -> str:
    km = route["distance_m"] / 1000
    minutes = max(1, round(route["duration_s"] / 60))
    return (f"{route['mode_label']} · ước tính đến {route['dest_name']}: {km:.1f} km, khoảng {minutes} phút "
            "(Google Maps)").replace(".", ",", 1)
