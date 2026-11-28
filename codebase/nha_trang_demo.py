"""Chế độ demo cho VinWonders Nha Trang: điền ô còn trống của snapshot bằng số TỰ ƯỚC TÍNH (data/nha_trang/demo_estimates.json).

- Không sửa snapshot gốc: trả về bản sao. Giá trị đã có nguồn giữ nguyên.
- Mỗi giá trị ước tính được ghi tên vào item["est"] để giao diện và chatbot gắn nhãn "ước tính demo".
- Không ước tính điều kiện an toàn (chiều cao, tuổi, sức khoẻ) và giá vé.
"""
from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ESTIMATES_PATH = Path(__file__).resolve().parents[1] / "data" / "nha_trang" / "demo_estimates.json"
EST_LABEL = "ước tính demo"


@lru_cache(maxsize=1)
def load_estimates() -> dict[str, Any]:
    return json.loads(ESTIMATES_PATH.read_text(encoding="utf-8"))


class EstimatedWalking:
    """Cùng giao diện với WalkingDistanceMatrix (get_minutes, get_record, is_empty) nhưng tính theo khu, ước tính."""

    def __init__(self, ds: dict[str, Any], est: dict[str, Any]):
        self.zone_of: dict[str, str] = {i["id"]: i["zone_id"] for i in ds["catalog"] if i.get("zone_id")}
        self.zone_of.update({z["id"]: z["id"] for z in ds["zones"]})
        self.order = {z: n for n, z in enumerate(est["zone_order"])}
        self.cfg = est["walk_minutes"]

    is_empty = False
    estimated = True

    def get_minutes(self, from_id: str | None, to_id: str | None) -> int | None:
        if not from_id or not to_id:
            return None
        if from_id == to_id:
            return 0
        za, zb = self.zone_of.get(from_id), self.zone_of.get(to_id)
        if za is None or zb is None or za not in self.order or zb not in self.order:
            return None
        if za == zb:
            return self.cfg["same_zone"]
        minutes = self.cfg["between_zones_base"] + self.cfg["per_zone_step"] * abs(self.order[za] - self.order[zb])
        if "harbour" in (za, zb):
            minutes += self.cfg["harbour_extra"]
        return minutes

    def get_record(self, from_id: str, to_id: str) -> dict[str, Any] | None:
        m = self.get_minutes(from_id, to_id)
        return None if m is None else {"from_id": from_id, "to_id": to_id, "minutes": m, "estimated": True}


def apply_demo_estimates(ds: dict[str, Any]) -> dict[str, Any]:
    """Bản sao của dataset đã điền số ước tính; ds["demo"] = True."""
    est = load_estimates()
    park = ds["park"]
    out = dict(ds)
    zones = copy.deepcopy(ds["zones"])
    catalog = copy.deepcopy(ds["catalog"])
    shows, sessions = copy.deepcopy((ds["shows"], ds["show_sessions"]))  # giữ chung đối tượng suất giữa hai danh sách

    for z in zones:
        z["est"] = []
        if not (z["open"] and z["close"]):
            z["open"], z["close"] = park["open"], park["close"]
            z["est"] += ["open", "close"]
    zones_by_id = {z["id"]: z for z in zones}

    durations, queues = est["duration_minutes_by_kind"], est["queue_minutes_by_kind"]
    included_kinds = set(est["included_in_ticket_default_kinds"])
    for item in catalog:
        item["est"] = []
        if not (item["open"] and item["close"]) and item["kind"] not in ("gate", "placeholder"):
            zone = zones_by_id.get(item["zone_id"]) or {}
            item["open"], item["close"] = zone.get("open") or park["open"], zone.get("close") or park["close"]
            item["opening_hours"].update(open=item["open"], close=item["close"], has_published_hours=True)
            item["est"] += ["open", "close"]
        if item["duration_minutes"] is None and durations.get(item["kind"]):
            item["duration_minutes"] = durations[item["kind"]]
            item["est"].append("duration_minutes")
        item["queue_minutes"] = queues.get(item["kind"], 0)
        if item["queue_minutes"]:
            item["est"].append("queue_minutes")
        if item["pricing"]["included_in_ticket"] is None and item["kind"] in included_kinds:
            item["pricing"]["included_in_ticket"] = item["included_in_ticket"] = True
            item["est"].append("included_in_ticket")
        if item["status"] == "unverified_live":
            item["status"] = "demo_open"
            item["est"].append("status")
    catalog_by_id = {i["id"]: i for i in catalog}

    show_est = est["show_estimates"]
    for s in sessions:
        s["est"] = []
        e = show_est.get(s["id"], {})
        if not s["has_published_time"] and e.get("start"):
            s["start"], s["end"], s["duration_minutes"] = e["start"], e["end"], e["duration_minutes"]
            s["has_published_time"] = True
            s["est"] += ["start", "end"]
        venue = catalog_by_id.get(s["venue_id"]) if s["venue_id"] else None
        s["location_id"] = s["venue_id"] or e.get("zone_id")
        s["zone_id"] = s["zone_id"] or (venue or {}).get("zone_id") or e.get("zone_id")
        if not s["venue_id"] and e.get("venue_text"):
            s["venue_text"] = e["venue_text"]
            s["est"].append("venue")
    for g in shows:
        first = g["sessions"][0]
        g["location_id"] = first.get("location_id")
        g["zone_id"] = g["zone_id"] or first.get("zone_id")
        g["zone_name"] = g["zone_name"] or (zones_by_id.get(g["zone_id"]) or {}).get("name")
        g["venue_text"] = first.get("venue_text")
        g["has_published_time"] = any(s["has_published_time"] for s in g["sessions"])

    out.update(zones=zones, zones_by_id=zones_by_id, catalog=catalog, catalog_by_id=catalog_by_id,
               shows=shows, show_sessions=sessions, demo=True, demo_note=est["_note"],
               demo_live_text=est["live_status_text"], demo_rule_text=est["unknown_restriction_text"])
    out["walking_matrix"] = EstimatedWalking(out, est)
    out["attractions"] = [i for i in catalog if i["kind"] in ("ride", "sight")]
    return out
