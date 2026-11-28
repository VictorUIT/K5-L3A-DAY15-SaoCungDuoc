"""Height- and senior-age-based ticket pricing engine for VinWonders Nha Trang.

Key safety & truthfulness guarantees:
- Classifies travelers into <100 cm, 100–<140 cm, >=140 cm, and senior bands
  using ONLY official snapshot rows from ``data/nha_trang/ticket_prices.json``.
- NEVER infers height from age or adult/child counts.
- Treats ``age == 60`` as an UNRESOLVED boundary discrepancy between PRICE
  ("trên 60 tuổi" / over 60) and PRICE_NOTICE ("từ 60 tuổi" / from 60).
- NEVER uses review text/prices as official ticket quotes.
- Preserves ``current_quote=False`` so callers never mistake snapshot figures
  for verified live purchase prices.
"""
from __future__ import annotations

from typing import Any


SENIOR_BOUNDARY_NOTE = (
    "Ngưỡng vé người cao tuổi ở mốc đúng 60 tuổi chưa thống nhất giữa nguồn công khai: "
    "bảng giá tiếng Việt (PRICE) ghi 'trên 60 tuổi' (> 60), trong khi thông báo cập nhật 2026 "
    "(PRICE_NOTICE) ghi 'từ 60 tuổi' (≥ 60). Cần xác minh trực tiếp với VinWonders và giấy tờ tùy thân."
)


def _index_bands(ticket_prices: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {b["id"]: b for b in ticket_prices}


def _match_height_band(height_cm: int | float, bands: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if height_cm < 0:
        return None
    for band_id in ("standard_under_100", "standard_100_139", "standard_140_plus"):
        band = bands.get(band_id)
        if not band:
            continue
        low = band.get("min_height_cm")
        high = band.get("max_height_cm_exclusive")
        if low is not None and height_cm < low:
            continue
        if high is not None and height_cm >= high:
            continue
        return band
    return None


def classify_traveler_ticket(
    traveler: dict[str, Any],
    ticket_prices: list[dict[str, Any]],
) -> dict[str, Any]:
    """Classify a single traveler against VinWonders Nha Trang ticket bands.

    Expected optional keys in ``traveler``:
    - ``label``: display name (e.g. "Khách 1")
    - ``height_cm``: int/float or None (NEVER inferred from age or role)
    - ``age``: int or None
    - ``is_senior``: bool or None (optional explicit hint; still requires age check)
    """
    bands = _index_bands(ticket_prices)
    label = traveler.get("label") or "Khách"
    height_cm = traveler.get("height_cm")
    age = traveler.get("age")
    senior_band = bands.get("standard_senior")

    if height_cm is not None and (isinstance(height_cm, bool) or height_cm < 0):
        return {
            "label": label,
            "status": "invalid_input",
            "band_id": None,
            "price_vnd": None,
            "current_quote": False,
            "reason": "Chiều cao phải là số không âm (cm).",
            "source_ids": [],
        }

    if age is not None and (isinstance(age, bool) or age < 0):
        return {
            "label": label,
            "status": "invalid_input",
            "band_id": None,
            "price_vnd": None,
            "current_quote": False,
            "reason": "Tuổi phải là số nguyên không âm.",
            "source_ids": [],
        }

    # Explicit unresolved boundary: exact age == 60
    if age == 60:
        height_band = _match_height_band(height_cm, bands) if height_cm is not None else None
        candidates = []
        if senior_band:
            candidates.append({
                "band_id": senior_band["id"],
                "price_vnd": senior_band["price_vnd"],
                "condition": "Nếu áp dụng mốc 'từ 60 tuổi' (≥ 60, theo PRICE_NOTICE) và có giấy tờ tùy thân.",
            })
        if height_band:
            candidates.append({
                "band_id": height_band["id"],
                "price_vnd": height_band["price_vnd"],
                "condition": "Nếu áp dụng mốc 'trên 60 tuổi' (> 60, theo PRICE) thì tính theo chiều cao.",
            })
        return {
            "label": label,
            "status": "unresolved_senior_boundary",
            "band_id": None,
            "price_vnd": None,
            "price_range_vnd": (
                min(c["price_vnd"] for c in candidates),
                max(c["price_vnd"] for c in candidates),
            ) if candidates else None,
            "candidate_bands": candidates,
            "current_quote": False,
            "reason": SENIOR_BOUNDARY_NOTE,
            "source_ids": ["PRICE", "PRICE_NOTICE"],
        }

    # Clearly over 60 -> senior band (unambiguous on both ">60" and ">=60" wordings)
    if age is not None and age > 60 and senior_band is not None:
        # Still check if height < 100 cm is explicitly provided (edge case)
        height_band = _match_height_band(height_cm, bands) if height_cm is not None else None
        if height_band and height_band["id"] == "standard_under_100":
            return {
                "label": label,
                "status": "matched_reference",
                "band_id": height_band["id"],
                "price_vnd": height_band["price_vnd"],
                "current_quote": bool(height_band.get("current_quote") is True),
                "reason": "Chiều cao dưới 100 cm (giá tham khảo snapshot, chưa phải báo giá trực tiếp).",
                "source_ids": [height_band["source_id"]],
            }
        return {
            "label": label,
            "status": "matched_reference_senior",
            "band_id": senior_band["id"],
            "price_vnd": senior_band["price_vnd"],
            "current_quote": bool(senior_band.get("current_quote") is True),
            "reason": (
                "Trên 60 tuổi — thuộc nhóm vé người cao tuổi (cần giấy tờ tùy thân xác minh; "
                "đây là giá tham khảo snapshot, chưa phải báo giá trực tiếp)."
            ),
            "source_ids": [senior_band["source_id"]],
        }

    # If caller marked is_senior=True without providing exact age, do not guess
    if traveler.get("is_senior") is True and age is None:
        return {
            "label": label,
            "status": "missing_age_for_senior",
            "band_id": None,
            "price_vnd": None,
            "current_quote": False,
            "reason": (
                "Cần cung cấp tuổi cụ thể để phân biệt mốc đúng 60 tuổi (chưa thống nhất giữa 'từ 60' và 'trên 60') "
                "với trên 60 tuổi."
            ),
            "source_ids": ["PRICE", "PRICE_NOTICE"],
        }

    # Standard height-based classification — NEVER infer height from age or adult/child role
    if height_cm is None:
        return {
            "label": label,
            "status": "missing_height",
            "band_id": None,
            "price_vnd": None,
            "current_quote": False,
            "reason": (
                "Chưa có chiều cao (cm). Vé VinWonders Nha Trang phân loại theo chiều cao "
                "(<100 cm, 100–<140 cm, ≥140 cm), không tự suy từ tuổi hay nhãn người lớn/trẻ em."
            ),
            "source_ids": ["PRICE"],
        }

    matched = _match_height_band(height_cm, bands)
    if matched is None:
        return {
            "label": label,
            "status": "unmatched",
            "band_id": None,
            "price_vnd": None,
            "current_quote": False,
            "reason": "Không khớp nhóm vé nào trong bảng giá tham khảo.",
            "source_ids": ["PRICE"],
        }

    return {
        "label": label,
        "status": "matched_reference",
        "band_id": matched["id"],
        "price_vnd": matched["price_vnd"],
        "current_quote": bool(matched.get("current_quote") is True),
        "reason": f"Khớp nhóm {matched['id']} theo chiều cao {height_cm} cm (giá tham khảo snapshot, không phải báo giá trực tiếp).",
        "source_ids": [matched["source_id"]],
    }


def calculate_group_reference_quote(
    travelers: list[dict[str, Any]],
    dataset: dict[str, Any],
    selected_item_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Calculate group reference admission price and flag all missing/unverified fee inputs.

    Never returns ``is_verified_live_quote=True`` when snapshot ``current_quote=False`` or
    when any traveler/extra fee is unresolved.
    """
    ticket_prices = dataset["ticket_prices"]
    catalog_by_id = dataset.get("catalog_by_id", {})
    breakdown = [classify_traveler_ticket(t, ticket_prices) for t in travelers]

    missing_height = [b["label"] for b in breakdown if b["status"] == "missing_height"]
    missing_senior_age = [b["label"] for b in breakdown if b["status"] == "missing_age_for_senior"]
    unresolved_senior_60 = [b["label"] for b in breakdown if b["status"] == "unresolved_senior_boundary"]
    invalid = [b["label"] for b in breakdown if b["status"] in ("invalid_input", "unmatched")]

    extra_fee_unknown_items = []
    for item_id in (selected_item_ids or []):
        item = catalog_by_id.get(item_id)
        if not item:
            continue
        included = item["pricing"]["included_in_ticket"]
        extra_vnd = item["pricing"]["extra_vnd"]
        if included is False and extra_vnd is None:
            extra_fee_unknown_items.append(
                f"{item['name']} (không nằm trong vé tiêu chuẩn, chưa có đơn giá phụ phí xác minh)"
            )
        elif included is None and extra_vnd is None:
            extra_fee_unknown_items.append(
                f"{item['name']} (chưa xác minh có bao gồm trong vé hay phụ phí)"
            )

    all_resolved = not (missing_height or missing_senior_age or unresolved_senior_60 or invalid)
    reference_total_vnd = (
        sum(int(b["price_vnd"]) for b in breakdown) if (all_resolved and breakdown) else None
    )

    # Compute min/max range if only age==60 is ambiguous and all other travelers resolved
    reference_range_vnd = None
    if not all_resolved and not (missing_height or missing_senior_age or invalid) and unresolved_senior_60:
        min_sum, max_sum = 0, 0
        possible = True
        for b in breakdown:
            if b["price_vnd"] is not None:
                min_sum += int(b["price_vnd"])
                max_sum += int(b["price_vnd"])
            elif b.get("price_range_vnd") is not None:
                lo, hi = b["price_range_vnd"]
                min_sum += int(lo)
                max_sum += int(hi)
            else:
                possible = False
                break
        if possible:
            reference_range_vnd = (min_sum, max_sum)

    warnings: list[str] = [
        "Bảng giá lấy từ snapshot nguồn công khai (current_quote=false, không dùng giá trong review). "
        "Cần kiểm tra giá chính thức tại thời điểm mua vé."
    ]
    if missing_height:
        warnings.append(
            "Thiếu chiều cao (cm) cho: " + ", ".join(missing_height) + ". Không tự suy từ tuổi hay số người lớn/trẻ em."
        )
    if missing_senior_age:
        warnings.append("Thiếu tuổi cụ thể để kiểm tra vé cao tuổi cho: " + ", ".join(missing_senior_age) + ".")
    if unresolved_senior_60:
        warnings.append(
            "Mốc đúng 60 tuổi chưa thống nhất ('trên 60' theo PRICE vs 'từ 60' theo PRICE_NOTICE) cho: "
            + ", ".join(unresolved_senior_60) + "."
        )
    if extra_fee_unknown_items:
        warnings.append("Chưa có dữ liệu phụ phí đã xác minh cho: " + "; ".join(extra_fee_unknown_items) + ".")

    return {
        "product": ticket_prices[0]["product"] if ticket_prices else None,
        "traveler_count": len(travelers),
        "breakdown": breakdown,
        "reference_total_vnd": reference_total_vnd,
        "reference_range_vnd": reference_range_vnd,
        "is_verified_live_quote": False,
        "all_bands_resolved": all_resolved,
        "missing_height": missing_height,
        "missing_senior_age": missing_senior_age,
        "unresolved_senior_60": unresolved_senior_60,
        "extra_fee_unknown_items": extra_fee_unknown_items,
        "warnings": warnings,
        "uses_review_prices": False,
    }
