"""Multi-park data provider and schema normalization for Vivu.

Supports two strictly separated park schemas:
1. ``vinh_may`` (default): legacy synthetic dataset from ``data/park.json``
   preserved verbatim so CP2/CP3/CP4 evaluations remain reproducible.
2. ``vinwonders_nha_trang``: public-source snapshot from ``data/nha_trang/``
   with explicit provenance, null/0/False preservation, Harbour separation,
   multi-session shows, and fail-closed operational readiness flags.

Synthetic Vịnh Mây parameters are NEVER used to backfill Nha Trang data.
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEGACY_PARK_PATH = ROOT / "data" / "park.json"
NHA_TRANG_DIR = ROOT / "data" / "nha_trang"
NHA_TRANG_REVIEWS_PATH = ROOT / "evidence" / "nha_trang" / "reviews.jsonl"

DEFAULT_PARK_ID = "vinh_may"
NHA_TRANG_PARK_ID = "vinwonders_nha_trang"

PARK_REGISTRY = {
    DEFAULT_PARK_ID: {
        "id": DEFAULT_PARK_ID,
        "name": "Vịnh Mây",
        "label": "Vịnh Mây (dữ liệu mô phỏng · mặc định)",
        "schema_type": "synthetic_legacy",
        "source": "synthetic",
    },
    NHA_TRANG_PARK_ID: {
        "id": NHA_TRANG_PARK_ID,
        "name": "VinWonders Nha Trang",
        "label": "VinWonders Nha Trang (snapshot công khai 2026-11-27)",
        "schema_type": "public_snapshot_v1",
        "source": "public_source_snapshot",
    },
}

KIND_TO_CATEGORY = {
    "ride": "attraction",
    "sight": "attraction",
    "food": "restaurant",
    "shop": "shop",
    "show_venue": "show_venue",
    "facility": "facility",
    "gate": "facility",
    "transport": "facility",
    "cluster": "cluster",
    "placeholder": "placeholder",
}

KIND_LABELS_VI = {
    "ride": "Trò chơi",
    "sight": "Điểm tham quan",
    "food": "Ẩm thực",
    "shop": "Cửa hàng",
    "show_venue": "Sân khấu / Biểu diễn",
    "facility": "Tiện ích",
    "gate": "Cổng",
    "transport": "Di chuyển / Trạm",
    "cluster": "Cụm / Khu vực nhỏ",
    "placeholder": "Đang phát triển / Sắp ra mắt",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _slugify(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text or "")
    ascii_only = "".join(ch for ch in norm if not unicodedata.combining(ch))
    out = []
    prev_sep = False
    for ch in ascii_only.lower():
        if ch.isalnum():
            out.append(ch)
            prev_sep = False
        elif not prev_sep:
            out.append("_")
            prev_sep = True
    return "".join(out).strip("_") or "unknown"


def _clock_to_minutes(value: str | None) -> int | None:
    if value is None:
        return None
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def list_parks() -> list[dict[str, str]]:
    """Return available parks in display order with Vịnh Mây first (default)."""
    return [dict(PARK_REGISTRY[DEFAULT_PARK_ID]), dict(PARK_REGISTRY[NHA_TRANG_PARK_ID])]


def load_legacy_vinh_may(path: Path = LEGACY_PARK_PATH) -> dict[str, Any]:
    """Load the legacy synthetic Vịnh Mây park dictionary verbatim."""
    return _read_json(path)


class WalkingDistanceMatrix:
    """Explicit walking distance lookup that distinguishes missing pairs (None) from 0 minutes."""

    def __init__(self, records: list[dict[str, Any]] | None = None):
        self.records: list[dict[str, Any]] = list(records or [])
        self._by_pair: dict[tuple[str, str], dict[str, Any]] = {}
        for rec in self.records:
            origin = rec.get("from_id")
            dest = rec.get("to_id")
            if origin is not None and dest is not None:
                self._by_pair[(origin, dest)] = dict(rec)
                if rec.get("bidirectional", True) and (dest, origin) not in self._by_pair:
                    self._by_pair[(dest, origin)] = dict(rec)

    @property
    def is_empty(self) -> bool:
        return len(self._by_pair) == 0

    def get_minutes(self, from_id: str, to_id: str) -> int | None:
        """Return verified walking minutes between two locations, or None if unavailable."""
        if from_id == to_id:
            return 0
        rec = self._by_pair.get((from_id, to_id))
        if rec is None:
            return None
        minutes_val = rec.get("minutes")
        return int(minutes_val) if minutes_val is not None else None

    def get_record(self, from_id: str, to_id: str) -> dict[str, Any] | None:
        return self._by_pair.get((from_id, to_id))


def _normalize_catalog_item(raw: dict[str, Any], zone_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Normalize a Nha Trang catalog entry while strictly preserving None vs 0 vs False."""
    zone = zone_map.get(raw.get("zone_id"), {})
    open_time = raw.get("open")
    close_time = raw.get("close")
    status = raw.get("status")
    field_sources = dict(raw.get("field_sources") or {})
    item = {
        "id": raw["id"],
        "map_code": raw.get("map_code"),
        "parent_id": raw.get("parent_id"),
        "name": raw["name"],
        "zone_id": raw.get("zone_id"),
        "zone_name": zone.get("name"),
        "scope": raw.get("scope"),
        "is_harbour": raw.get("scope") == "adjacent_harbour",
        "kind": raw.get("kind"),
        "category": KIND_TO_CATEGORY.get(raw.get("kind"), "other"),
        "source_id": raw.get("source_id"),
        "field_sources": field_sources,
        "map_warning": raw.get("map_warning"),
        # Flat fields preserved for direct schema checks
        "status": status,
        "open": open_time,
        "close": close_time,
        "duration_minutes": raw.get("duration_minutes"),
        "min_height_cm": raw.get("min_height_cm"),
        "max_height_cm": raw.get("max_height_cm"),
        "min_age": raw.get("min_age"),
        "max_age": raw.get("max_age"),
        "min_weight_kg": raw.get("min_weight_kg"),
        "max_weight_kg": raw.get("max_weight_kg"),
        "adult_required": raw.get("adult_required"),
        "extra_vnd": raw.get("extra_vnd"),
        "included_in_ticket": raw.get("included_in_ticket"),
        "lat": raw.get("lat"),
        "lon": raw.get("lon"),
        "scheduling_ready": raw.get("scheduling_ready"),
        # Normalized structured sub-objects
        "opening_hours": {
            "open": open_time,
            "close": close_time,
            "has_published_hours": open_time is not None and close_time is not None,
            "source_ids": {
                k: field_sources[k] for k in ("open", "close") if k in field_sources
            },
        },
        "operation_status": {
            "status": status,
            "live_verified": status == "verified_live_open",
            "scheduling_ready": bool(raw.get("scheduling_ready") is True),
            "map_warning": raw.get("map_warning"),
        },
        "restrictions": {
            "min_height_cm": raw.get("min_height_cm"),
            "max_height_cm": raw.get("max_height_cm"),
            "min_age": raw.get("min_age"),
            "max_age": raw.get("max_age"),
            "min_weight_kg": raw.get("min_weight_kg"),
            "max_weight_kg": raw.get("max_weight_kg"),
            "adult_required": raw.get("adult_required"),
            "complete": False,
        },
        "pricing": {
            "extra_vnd": raw.get("extra_vnd"),
            "included_in_ticket": raw.get("included_in_ticket"),
        },
        "coordinates": {
            "lat": raw.get("lat"),
            "lon": raw.get("lon"),
        },
    }
    return item


def _normalize_shows(
    raw_shows: list[dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    park_meta: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize show sessions and group multi-session shows while keeping distinct session IDs."""
    park_close_min = _clock_to_minutes(park_meta.get("close"))
    sessions: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str | None], dict[str, Any]] = {}

    for raw in raw_shows:
        venue_id = raw.get("venue_id")
        venue = catalog_by_id.get(venue_id) if venue_id is not None else None
        scope = venue["scope"] if venue is not None else (
            "adjacent_harbour" if raw.get("note") and "harbour" in raw["note"].lower() else "park"
        )
        zone_id = venue["zone_id"] if venue is not None else None
        zone_name = venue["zone_name"] if venue is not None else None
        start = raw.get("start")
        end = raw.get("end")
        end_min = _clock_to_minutes(end)
        exceeds_park_close = (
            end_min is not None and park_close_min is not None and end_min > park_close_min
        )
        group_key = (raw["name"].strip().casefold(), venue_id)
        show_id = f"show_{_slugify(raw['name'])}"

        session = {
            "id": raw["id"],
            "session_id": raw["id"],
            "show_id": show_id,
            "name": raw["name"],
            "venue_id": venue_id,
            "venue_name": venue["name"] if venue is not None else None,
            "zone_id": zone_id,
            "zone_name": zone_name,
            "scope": scope,
            "is_harbour": scope == "adjacent_harbour",
            "start": start,
            "end": end,
            "duration_minutes": raw.get("duration_minutes"),
            "has_published_time": start is not None and end is not None,
            "source_id": raw.get("source_id"),
            "conflict_source_id": raw.get("conflict_source_id"),
            "conflict_start": raw.get("conflict_start"),  # giờ nguồn kia ghi (đã có trong note)
            "conflict_end": raw.get("conflict_end"),
            "live_status": raw.get("live_status"),
            "note": raw.get("note"),
            "exceeds_park_close": exceeds_park_close,
            "has_discrepancy": bool(raw.get("conflict_source_id") or exceeds_park_close),
        }
        sessions.append(session)

        if group_key not in grouped:
            grouped[group_key] = {
                "show_id": show_id,
                "name": raw["name"],
                "venue_id": venue_id,
                "venue_name": session["venue_name"],
                "zone_id": zone_id,
                "zone_name": zone_name,
                "scope": scope,
                "is_harbour": session["is_harbour"],
                "sessions": [],
                "session_ids": [],
                "has_published_time": False,
                "has_discrepancy": False,
                "source_ids": [],
                "notes": [],
            }
        grp = grouped[group_key]
        grp["sessions"].append(session)
        grp["session_ids"].append(session["session_id"])
        grp["has_published_time"] = grp["has_published_time"] or session["has_published_time"]
        grp["has_discrepancy"] = grp["has_discrepancy"] or session["has_discrepancy"]
        if session["source_id"] and session["source_id"] not in grp["source_ids"]:
            grp["source_ids"].append(session["source_id"])
        if session["note"] and session["note"] not in grp["notes"]:
            grp["notes"].append(session["note"])

    return list(grouped.values()), sessions


def _normalize_tickets(raw_prices: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize ticket products and height/age price bands without inferring live quote status."""
    bands: list[dict[str, Any]] = []
    products_map: dict[str, dict[str, Any]] = {}

    for raw in raw_prices:
        product_name = raw["product"]
        product_id = f"product_{_slugify(product_name)}"
        band = {
            "id": raw["id"],
            "product_id": product_id,
            "product": product_name,
            "min_height_cm": raw.get("min_height_cm"),
            "max_height_cm_exclusive": raw.get("max_height_cm_exclusive"),
            "min_age": raw.get("min_age"),
            "price_vnd": raw.get("price_vnd"),
            "source_id": raw.get("source_id"),
            "current_quote": raw.get("current_quote"),
            "effective_from": raw.get("effective_from"),
            "effective_until": raw.get("effective_until"),
            "note": raw.get("note"),
            "senior_boundary_ambiguous": raw.get("id") == "standard_senior" or (
                raw.get("min_age") == 60 and raw.get("note") is not None
            ),
        }
        bands.append(band)

        if product_id not in products_map:
            products_map[product_id] = {
                "product_id": product_id,
                "name": product_name,
                "current_quote": bool(raw.get("current_quote") is True),
                "source_ids": [],
                "band_ids": [],
            }
        prod = products_map[product_id]
        prod["band_ids"].append(band["id"])
        if band["source_id"] and band["source_id"] not in prod["source_ids"]:
            prod["source_ids"].append(band["source_id"])

    return list(products_map.values()), bands


def load_nha_trang_dataset(data_dir: Path = NHA_TRANG_DIR) -> dict[str, Any]:
    """Load and normalize the VinWonders Nha Trang public-source snapshot."""
    park_meta = _read_json(data_dir / "park_metadata.json")
    raw_zones = _read_json(data_dir / "zones.json")
    raw_catalog = _read_json(data_dir / "catalog.json")
    raw_shows = _read_json(data_dir / "shows.json")
    raw_tickets = _read_json(data_dir / "ticket_prices.json")
    raw_sources = _read_json(data_dir / "sources.json")
    raw_walking = _read_json(data_dir / "walking_distances.json")
    crawl_report = _read_json(data_dir / "crawl_report.json")
    data_card_path = data_dir / "DATA_CARD.md"
    data_card_text = data_card_path.read_text(encoding="utf-8-sig") if data_card_path.exists() else ""

    blocked_ids = set(crawl_report.get("blocked_direct_sources") or [])
    sources_by_id: dict[str, dict[str, Any]] = {}
    sources_list: list[dict[str, Any]] = []
    for src in raw_sources:
        entry = {
            "id": src["id"],
            "url": src["url"],
            "note": src.get("note"),
            "accessed_on": src.get("accessed_on"),
            "blocked_direct": src["id"] in blocked_ids or ("403" in (src.get("note") or "")),
        }
        sources_by_id[entry["id"]] = entry
        sources_list.append(entry)

    zones: list[dict[str, Any]] = []
    zones_by_id: dict[str, dict[str, Any]] = {}
    for z in raw_zones:
        zone_rec = {
            "id": z["id"],
            "name": z["name"],
            "scope": z["scope"],
            "is_harbour": z["scope"] == "adjacent_harbour",
            "open": z.get("open"),
            "close": z.get("close"),
            "opening_hours": {
                "open": z.get("open"),
                "close": z.get("close"),
                "has_published_hours": z.get("open") is not None and z.get("close") is not None,
            },
            "map_range": list(z.get("map_range") or []),
            "source_id": z.get("source_id"),
            "live_status": z.get("live_status"),
        }
        zones.append(zone_rec)
        zones_by_id[zone_rec["id"]] = zone_rec

    catalog: list[dict[str, Any]] = []
    catalog_by_id: dict[str, dict[str, Any]] = {}
    for raw_item in raw_catalog:
        item = _normalize_catalog_item(raw_item, zones_by_id)
        catalog.append(item)
        catalog_by_id[item["id"]] = item

    shows, show_sessions = _normalize_shows(raw_shows, catalog_by_id, park_meta)
    ticket_products, ticket_prices = _normalize_tickets(raw_tickets)
    walking_matrix = WalkingDistanceMatrix(raw_walking)

    # Category views
    attractions = [i for i in catalog if i["kind"] in ("ride", "sight")]
    restaurants = [i for i in catalog if i["kind"] == "food"]
    shops = [i for i in catalog if i["kind"] == "shop"]
    facilities = [i for i in catalog if i["kind"] in ("facility", "gate", "transport")]

    park = {
        "id": park_meta["id"],
        "name": park_meta["name"],
        "source": park_meta["source"],
        "schema_type": "public_snapshot_v1",
        "timezone": park_meta.get("timezone"),
        "currency": park_meta.get("currency"),
        "open": park_meta.get("open"),
        "close": park_meta.get("close"),
        "source_id": park_meta.get("source_id"),
        "snapshot_date": park_meta.get("snapshot_date"),
        "live_availability": park_meta.get("live_availability"),
        "walk_minutes": park_meta.get("walk_minutes"),
        "notes": list(park_meta.get("notes") or []),
    }

    return {
        "park_id": park["id"],
        "schema_type": "public_snapshot_v1",
        "park": park,
        "zones": zones,
        "zones_by_id": zones_by_id,
        "catalog": catalog,
        "catalog_by_id": catalog_by_id,
        "attractions": attractions,
        "restaurants": restaurants,
        "shops": shops,
        "facilities": facilities,
        "shows": shows,
        "show_sessions": show_sessions,
        "ticket_products": ticket_products,
        "ticket_prices": ticket_prices,
        "sources": sources_list,
        "sources_by_id": sources_by_id,
        "walking_distances": raw_walking,
        "walking_matrix": walking_matrix,
        "crawl_report": crawl_report,
        "data_card": data_card_text,
    }


def load_park_provider(park_id: str = DEFAULT_PARK_ID) -> dict[str, Any]:
    """Unified multi-park entrypoint keeping synthetic and snapshot schemas strictly separated."""
    normalized_id = (park_id or DEFAULT_PARK_ID).strip().lower()
    if normalized_id == DEFAULT_PARK_ID:
        legacy = load_legacy_vinh_may()
        return {
            "park_id": DEFAULT_PARK_ID,
            "schema_type": "synthetic_legacy",
            "park": legacy,
            "legacy": legacy,
        }
    if normalized_id == NHA_TRANG_PARK_ID:
        return load_nha_trang_dataset()
    raise ValueError(f"Không hỗ trợ park_id={park_id!r}. Chỉ hỗ trợ: {DEFAULT_PARK_ID}, {NHA_TRANG_PARK_ID}.")


def filter_catalog(
    dataset: dict[str, Any],
    *,
    include_harbour: bool = False,
    zone_ids: set[str] | list[str] | None = None,
    kinds: set[str] | list[str] | None = None,
    query: str = "",
    only_with_hours: bool = False,
    only_with_restrictions: bool = False,
) -> list[dict[str, Any]]:
    """Filter Nha Trang catalog entries. Excludes adjacent Harbour by default."""
    allowed_zones = set(zone_ids) if zone_ids else None
    allowed_kinds = set(kinds) if kinds else None
    q = (query or "").strip().casefold()

    results = []
    for item in dataset["catalog"]:
        if not include_harbour and item["scope"] == "adjacent_harbour":
            continue
        if allowed_zones is not None and item["zone_id"] not in allowed_zones:
            continue
        if allowed_kinds is not None and item["kind"] not in allowed_kinds:
            continue
        if only_with_hours and not item["opening_hours"]["has_published_hours"]:
            continue
        if only_with_restrictions:
            r = item["restrictions"]
            has_any_rule = any(
                r[k] is not None
                for k in (
                    "min_height_cm",
                    "max_height_cm",
                    "min_age",
                    "max_age",
                    "min_weight_kg",
                    "max_weight_kg",
                    "adult_required",
                )
            ) or item["pricing"]["included_in_ticket"] is False
            if not has_any_rule:
                continue
        if q:
            haystack = " ".join(
                str(x or "")
                for x in (item["name"], item["id"], item["map_code"], item["zone_name"], item["kind"])
            ).casefold()
            if q not in haystack:
                continue
        results.append(item)
    return results


def filter_show_sessions(
    dataset: dict[str, Any],
    *,
    include_harbour: bool = False,
    only_with_times: bool = False,
) -> list[dict[str, Any]]:
    """Filter normalized show sessions. Excludes Harbour shows by default."""
    out = []
    for s in dataset["show_sessions"]:
        if not include_harbour and s["is_harbour"]:
            continue
        if only_with_times and not s["has_published_time"]:
            continue
        out.append(s)
    return out


def validate_snapshot(dataset: dict[str, Any]) -> dict[str, Any]:
    """Validate schema, ID uniqueness, referential integrity, and null semantics."""
    errors: list[str] = []
    warnings: list[str] = []

    if dataset.get("schema_type") != "public_snapshot_v1":
        return {"valid": False, "errors": ["Dataset không đúng schema public_snapshot_v1."], "warnings": []}

    def _check_unique(records: list[dict[str, Any]], label: str, key: str = "id") -> set[str]:
        seen: set[str] = set()
        for rec in records:
            rid = rec.get(key)
            if not rid:
                errors.append(f"{label}: bản ghi thiếu {key}.")
            elif rid in seen:
                errors.append(f"{label}: trùng {key}={rid!r}.")
            else:
                seen.add(rid)
        return seen

    source_ids = _check_unique(dataset["sources"], "sources")
    zone_ids = _check_unique(dataset["zones"], "zones")
    catalog_ids = _check_unique(dataset["catalog"], "catalog")
    _check_unique(dataset["show_sessions"], "show_sessions", key="session_id")
    _check_unique(dataset["ticket_prices"], "ticket_prices")

    park_src = dataset["park"].get("source_id")
    if park_src and park_src not in source_ids:
        errors.append(f"park_metadata: source_id={park_src!r} không tồn tại trong sources.json.")

    for z in dataset["zones"]:
        if z.get("source_id") and z["source_id"] not in source_ids:
            errors.append(f"zone {z['id']}: source_id={z['source_id']!r} không tồn tại.")

    for item in dataset["catalog"]:
        if item["zone_id"] not in zone_ids:
            errors.append(f"catalog {item['id']}: zone_id={item['zone_id']!r} không tồn tại.")
        if item["parent_id"] is not None and item["parent_id"] not in catalog_ids:
            errors.append(f"catalog {item['id']}: parent_id={item['parent_id']!r} không tồn tại.")
        if item["source_id"] not in source_ids:
            errors.append(f"catalog {item['id']}: source_id={item['source_id']!r} không tồn tại.")
        for fname, fsrc in item["field_sources"].items():
            if fsrc not in source_ids:
                errors.append(f"catalog {item['id']}.field_sources[{fname}]={fsrc!r} không tồn tại.")
        zone_scope = dataset["zones_by_id"].get(item["zone_id"], {}).get("scope")
        if zone_scope and item["scope"] != zone_scope:
            errors.append(f"catalog {item['id']}: scope={item['scope']!r} lệch zone scope={zone_scope!r}.")

    for sess in dataset["show_sessions"]:
        if sess["venue_id"] is not None and sess["venue_id"] not in catalog_ids:
            errors.append(f"show {sess['session_id']}: venue_id={sess['venue_id']!r} không tồn tại.")
        if sess["source_id"] not in source_ids:
            errors.append(f"show {sess['session_id']}: source_id={sess['source_id']!r} không tồn tại.")
        if sess.get("conflict_source_id") and sess["conflict_source_id"] not in source_ids:
            errors.append(f"show {sess['session_id']}: conflict_source_id={sess['conflict_source_id']!r} không tồn tại.")
        if sess["has_discrepancy"]:
            warnings.append(f"show {sess['session_id']} ({sess['name']}): có xung đột lịch/giờ đóng cần xác minh.")

    for band in dataset["ticket_prices"]:
        if band["source_id"] not in source_ids:
            errors.append(f"ticket {band['id']}: source_id={band['source_id']!r} không tồn tại.")
        if band.get("senior_boundary_ambiguous"):
            warnings.append(f"ticket {band['id']}: ngưỡng tuổi 60 chưa thống nhất giữa nguồn PRICE và PRICE_NOTICE.")

    if dataset["walking_matrix"].is_empty:
        warnings.append("walking_distances.json rỗng — thiếu ma trận thời gian di chuyển.")
    if dataset["park"].get("live_availability") is False:
        warnings.append("live_availability=false — snapshot không phản ánh trạng thái mở cửa trực tiếp.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "catalog": len(dataset["catalog"]),
            "park_scope_catalog": sum(1 for i in dataset["catalog"] if not i["is_harbour"]),
            "harbour_scope_catalog": sum(1 for i in dataset["catalog"] if i["is_harbour"]),
            "zones_total": len(dataset["zones"]),
            "park_zones": sum(1 for z in dataset["zones"] if not z["is_harbour"]),
            "harbour_zones": sum(1 for z in dataset["zones"] if z["is_harbour"]),
            "show_groups": len(dataset["shows"]),
            "show_sessions": len(dataset["show_sessions"]),
            "show_sessions_with_times": sum(1 for s in dataset["show_sessions"] if s["has_published_time"]),
            "ticket_prices": len(dataset["ticket_prices"]),
            "sources": len(dataset["sources"]),
            "walking_edges": len(dataset["walking_distances"]),
        },
    }
