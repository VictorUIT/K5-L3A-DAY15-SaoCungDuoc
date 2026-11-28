"""Scalable multi-park planning engine with fail-closed real-data verification.

Why brute-force permutations fail at Nha Trang scale:
- Legacy Vịnh Mây has 5 activities -> sum_{k=1..3} P(5, k) = 85 permutations.
- VinWonders Nha Trang has 159 catalog entries (80 ride/sight) -> P(159, 3) = 3,944,790
  and P(80, 3) = 492,960 permutations, which is too slow and blows up LLM context.

Pipeline implemented here:
1. Readiness check (fail-closed for incomplete real snapshots like Nha Trang v1).
2. Hard constraint pre-filtering (scope/Harbour, kind, status, restrictions).
3. Zone filtering.
4. Preference-based candidate retrieval (bounded candidate pool).
5. Bounded candidate generation / Beam Search with deterministic step validation.
6. Independent deterministic itinerary validator.
7. Top-K candidate selection for LLM index choice (never claiming global optimality
   when candidate retrieval or beam search prunes the search space).
"""
from __future__ import annotations

import re
from typing import Any

from park_provider import filter_catalog, filter_show_sessions
from pricing import calculate_group_reference_quote


PLAYABLE_KINDS = {"ride", "sight", "show_venue", "show_session"}
DEFAULT_MAX_STOPS = 3
DEFAULT_MAX_CANDIDATES = 24
DEFAULT_BEAM_WIDTH = 12
DEFAULT_TOP_K = 10


def _to_min(clock_str: str | None) -> int | None:
    if not clock_str:
        return None
    h, m = map(int, clock_str.split(":"))
    return h * 60 + m


def _to_clock(total_min: int) -> str:
    return "%02d:%02d" % divmod(total_min, 60)


def check_scheduling_readiness(
    dataset: dict[str, Any],
    request: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Inspect whether a public-snapshot park dataset has sufficient verified data to build a real schedule."""
    park = dataset["park"]
    catalog = dataset["catalog"]
    show_sessions = dataset["show_sessions"]
    walking_matrix = dataset["walking_matrix"]
    ticket_prices = dataset["ticket_prices"]

    blockers: list[str] = []
    missing_fields: dict[str, int | bool] = {}

    if park.get("live_availability") is not True:
        blockers.append(
            "Thiếu trạng thái vận hành trực tiếp theo ngày (live_availability=false; các điểm đang ở trạng thái unverified_live)."
        )
        missing_fields["live_availability"] = False

    if walking_matrix.is_empty:
        blockers.append(
            "Thiếu ma trận thời gian di chuyển giữa cổng và các điểm (walking_distances.json rỗng; không dùng mặc định 10 phút của Vịnh Mây)."
        )
        missing_fields["walking_matrix_empty"] = True

    park_playable = [
        i for i in catalog
        if not i["is_harbour"] and i["kind"] in ("ride", "sight")
    ]
    ready_items = [i for i in park_playable if i["operation_status"]["scheduling_ready"]]
    missing_duration_count = sum(1 for i in park_playable if i["duration_minutes"] is None)
    missing_hours_count = sum(1 for i in park_playable if not i["opening_hours"]["has_published_hours"])
    missing_height_count = sum(1 for i in park_playable if i["restrictions"]["min_height_cm"] is None)
    missing_fee_count = sum(
        1 for i in park_playable
        if i["pricing"]["included_in_ticket"] is None or (
            i["pricing"]["included_in_ticket"] is False and i["pricing"]["extra_vnd"] is None
        )
    )

    missing_fields.update({
        "park_ride_sight_total": len(park_playable),
        "scheduling_ready_items": len(ready_items),
        "missing_duration_count": missing_duration_count,
        "missing_hours_count": missing_hours_count,
        "missing_height_restriction_count": missing_height_count,
        "missing_fee_verification_count": missing_fee_count,
    })

    if not ready_items:
        blockers.append(
            f"0/{len(park_playable)} trò chơi/điểm tham quan đạt scheduling_ready=true "
            f"(thiếu thời lượng chơi: {missing_duration_count}, thiếu giờ mở cửa: {missing_hours_count}, "
            f"thiếu quy định chiều cao/an toàn đầy đủ: {missing_height_count}, thiếu xác minh phụ phí: {missing_fee_count})."
        )

    if any(not bool(b.get("current_quote") is True) for b in ticket_prices):
        blockers.append(
            "Bảng giá vé chỉ là giá tham khảo từ snapshot (current_quote=false), chưa phải báo giá trực tiếp theo ngày đi."
        )
        missing_fields["unverified_ticket_quote"] = True

    discrepant_shows = [s for s in show_sessions if s["has_discrepancy"]]
    if discrepant_shows:
        names = ", ".join(f"{s['name']} ({s['start']}–{s['end']})" for s in discrepant_shows)
        blockers.append(
            f"Có xung đột lịch show cần xác minh: {names} (Tata Show kết thúc 20:10 vượt giờ đóng công viên 20:00 và lệch nguồn Klook 20:30–21:06)."
        )
        missing_fields["show_schedule_discrepancies"] = len(discrepant_shows)

    if request and request.get("travelers"):
        quote = calculate_group_reference_quote(
            request["travelers"], dataset, selected_item_ids=request.get("required_ids")
        )
        if quote["missing_height"]:
            blockers.append(
                "Thiếu chiều cao (cm) cho khách: " + ", ".join(quote["missing_height"]) + "."
            )
        if quote["unresolved_senior_60"]:
            blockers.append(
                "Ngưỡng vé người cao tuổi ở mốc đúng 60 tuổi chưa thống nhất giữa nguồn PRICE ('trên 60') và PRICE_NOTICE ('từ 60')."
            )

    return {
        "ready_for_verified_schedule": len(blockers) == 0,
        "blockers": blockers,
        "missing_fields": missing_fields,
    }


def _preference_score(candidate: dict[str, Any], preference_text: str, required_ids: set[str]) -> float:
    score = 0.0
    cid = candidate["id"]
    if cid in required_ids:
        score += 100.0
    pref = (preference_text or "").strip().casefold()
    if pref:
        haystack = " ".join(
            str(x or "")
            for x in (candidate.get("name"), candidate.get("zone_name"), candidate.get("kind"), cid)
        ).casefold()
        if candidate.get("name", "").casefold() in pref:
            score += 30.0
        tokens = [t for t in re.split(r"[\s,;/\-]+", pref) if len(t) >= 2]
        for tok in tokens:
            if tok in haystack:
                score += 5.0
    if candidate.get("is_show"):
        score += 2.0
    if candidate.get("opening_hours", {}).get("has_published_hours") or candidate.get("has_published_time"):
        score += 1.0
    return score


def _check_restrictions(candidate: dict[str, Any], travelers: list[dict[str, Any]]) -> tuple[bool, str | None]:
    """Fail-closed restriction check: unknown restriction (None) is NOT treated as 'no restriction'."""
    r = candidate.get("restrictions") or {}
    if not candidate.get("restrictions_verified", False):
        return False, f"{candidate['name']}: điều kiện an toàn chưa được xác minh đầy đủ."

    min_h = r.get("min_height_cm")
    max_h = r.get("max_height_cm")
    min_age = r.get("min_age")
    max_age = r.get("max_age")
    min_w = r.get("min_weight_kg")
    max_w = r.get("max_weight_kg")
    adult_req = r.get("adult_required")

    for t in travelers:
        h = t.get("height_cm")
        age = t.get("age")
        w = t.get("weight_kg")
        if min_h is not None:
            if h is None:
                return False, f"{candidate['name']} yêu cầu chiều cao tối thiểu {min_h} cm nhưng thiếu chiều cao khách."
            if h < min_h:
                return False, f"{candidate['name']} yêu cầu tối thiểu {min_h} cm (khách cao {h} cm)."
        if max_h is not None:
            if h is None:
                return False, f"{candidate['name']} có giới hạn chiều cao tối đa {max_h} cm nhưng thiếu chiều cao khách."
            if h > max_h:
                return False, f"{candidate['name']} giới hạn tối đa {max_h} cm (khách cao {h} cm)."
        if min_age is not None:
            if age is None:
                return False, f"{candidate['name']} yêu cầu tuổi tối thiểu {min_age} nhưng thiếu tuổi khách."
            if age < min_age:
                return False, f"{candidate['name']} yêu cầu tối thiểu {min_age} tuổi."
        if max_age is not None:
            if age is None:
                return False, f"{candidate['name']} giới hạn tuổi tối đa {max_age} nhưng thiếu tuổi khách."
            if age > max_age:
                return False, f"{candidate['name']} giới hạn tối đa {max_age} tuổi."
        if min_w is not None:
            if w is None:
                return False, f"{candidate['name']} yêu cầu cân nặng tối thiểu {min_w} kg nhưng thiếu cân nặng."
            if w < min_w:
                return False, f"{candidate['name']} yêu cầu tối thiểu {min_w} kg."
        if max_w is not None:
            if w is None:
                return False, f"{candidate['name']} giới hạn cân nặng tối đa {max_w} kg nhưng thiếu cân nặng."
            if w > max_w:
                return False, f"{candidate['name']} giới hạn tối đa {max_w} kg."

    if adult_req is True:
        has_adult = any((t.get("age") is not None and t["age"] >= 18) or t.get("is_adult") is True for t in travelers)
        if not has_adult:
            return False, f"{candidate['name']} yêu cầu có người lớn đi kèm."
    return True, None


def validate_itinerary(
    stops_candidates: list[dict[str, Any]],
    dataset: dict[str, Any],
    request: dict[str, Any],
) -> tuple[bool, dict[str, Any] | None, str | None]:
    """Deterministic hard validator for a candidate itinerary over a normalized dataset."""
    if not stops_candidates:
        return False, None, "Lịch trình trống."

    max_stops = int(request.get("max_stops") or DEFAULT_MAX_STOPS)
    if len(stops_candidates) > max_stops:
        return False, None, f"Vượt số điểm tối đa ({max_stops})."

    include_harbour = bool(request.get("include_harbour", False))
    closed_ids = set(request.get("closed_ids") or [])
    required_ids = set(request.get("required_ids") or [])
    travelers = request.get("travelers") or []
    start_min = _to_min(request.get("start"))
    end_min = _to_min(request.get("end"))
    buffer_min = int(request.get("buffer_minutes") or 0)
    budget_vnd = request.get("budget_vnd")
    gate_id = request.get("gate_id") or "gate"
    walking_matrix = dataset["walking_matrix"]

    if start_min is None or end_min is None or start_min >= end_min:
        return False, None, "Khung giờ không hợp lệ."

    seen_ids: set[str] = set()
    seen_show_groups: set[str] = set()
    for c in stops_candidates:
        if c["id"] in seen_ids:
            return False, None, f"Trùng điểm {c['id']}."
        seen_ids.add(c["id"])
        if c.get("show_id"):
            if c["show_id"] in seen_show_groups:
                return False, None, f"Trùng show {c['show_id']}."
            seen_show_groups.add(c["show_id"])
        if not include_harbour and c.get("is_harbour"):
            return False, None, f"{c['name']} thuộc khu Harbour ngoài phạm vi công viên."
        if c["id"] in closed_ids:
            return False, None, f"{c['name']} đang đóng."
        if not c.get("scheduling_ready"):
            return False, None, f"{c['name']} chưa đủ dữ liệu xác minh (scheduling_ready=false)."
        ok_r, err_r = _check_restrictions(c, travelers)
        if not ok_r:
            return False, None, err_r

    if required_ids and not required_ids.issubset(seen_ids):
        return False, None, "Thiếu điểm bắt buộc."

    current_time = start_min
    current_loc = gate_id
    total_walk = 0
    extra_cost = 0
    built_stops: list[dict[str, Any]] = []
    num_people = len(travelers)

    for c in stops_candidates:
        loc_id = c.get("venue_id") or c["id"]
        walk = walking_matrix.get_minutes(current_loc, loc_id)
        if walk is None:
            return False, None, f"Thiếu thời gian di chuyển từ {current_loc} tới {loc_id}."
        arrival = current_time + walk
        total_walk += walk

        open_m = _to_min(c.get("start") if c.get("is_show") else c.get("open"))
        close_m = _to_min(c.get("end") if c.get("is_show") else c.get("close"))
        dur = c.get("duration_minutes")
        if open_m is None or close_m is None or dur is None:
            return False, None, f"{c['name']} thiếu giờ hoạt động hoặc thời lượng."

        if c.get("is_show"):
            if arrival + buffer_min > open_m:
                return False, None, f"Đến {c['name']} lúc {_to_clock(arrival)}, không kịp suất {_to_clock(open_m)}."
            start_at = open_m
            end_at = close_m
        else:
            start_at = max(arrival, open_m)
            end_at = start_at + int(dur)
            if end_at > close_m:
                return False, None, f"{c['name']} kết thúc {_to_clock(end_at)} quá giờ đóng {_to_clock(close_m)}."

        if end_at > end_min:
            return False, None, f"{c['name']} kết thúc {_to_clock(end_at)} quá giờ về {_to_clock(end_min)}."

        # Pricing check: unknown extra fee is fail-closed
        pricing_info = c.get("pricing") or {}
        included = pricing_info.get("included_in_ticket")
        extra_per_person = pricing_info.get("extra_vnd")
        if included is True:
            fee = 0
        elif included is False:
            if extra_per_person is None:
                return False, None, f"{c['name']} không nằm trong vé tiêu chuẩn nhưng thiếu đơn giá phụ phí."
            fee = int(extra_per_person) * num_people
        else:
            return False, None, f"{c['name']} chưa xác minh có nằm trong vé tiêu chuẩn hay không."
        extra_cost += fee

        built_stops.append({
            "id": c["id"],
            "name": c["name"],
            "zone_id": c.get("zone_id"),
            "is_show": bool(c.get("is_show")),
            "start": _to_clock(start_at),
            "end": _to_clock(end_at),
            "walk_minutes": walk,
        })
        current_time = end_at
        current_loc = loc_id

    admission_cost = request.get("verified_admission_total_vnd")
    if admission_cost is None:
        return False, None, "Thiếu tổng giá vé vào cổng đã xác minh."
    total_cost = int(admission_cost) + extra_cost
    if budget_vnd is not None and total_cost > int(budget_vnd):
        return False, None, f"Tổng chi phí {total_cost} vượt ngân sách {budget_vnd}."

    return True, {
        "stops": built_stops,
        "total_vnd": total_cost,
        "walk_minutes": total_walk,
        "end_time": built_stops[-1]["end"],
        "show_count": sum(1 for s in built_stops if s["is_show"]),
    }, None


def build_bounded_candidates(
    dataset: dict[str, Any],
    request: dict[str, Any],
    *,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
    beam_width: int = DEFAULT_BEAM_WIDTH,
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, Any]:
    """Bounded candidate retrieval + Beam Search + deterministic validation for large catalogs.

    Never runs full brute-force permutations over all 159 catalog entries.
    Explicitly flags ``is_globally_optimal=False`` whenever pruning occurs.
    """
    include_harbour = bool(request.get("include_harbour", False))
    zone_ids = set(request["zone_ids"]) if request.get("zone_ids") else None
    closed_ids = set(request.get("closed_ids") or [])
    required_ids = set(request.get("required_ids") or [])
    preference = request.get("preference") or ""
    travelers = request.get("travelers") or []
    max_stops = int(request.get("max_stops") or DEFAULT_MAX_STOPS)

    # 1 & 2. Hard constraint pre-filtering + zone filtering
    pool: list[dict[str, Any]] = []
    for item in dataset["catalog"]:
        if not include_harbour and item.get("is_harbour"):
            continue
        if zone_ids is not None and item.get("zone_id") not in zone_ids:
            continue
        if item.get("kind") not in ("ride", "sight"):
            continue
        if item["id"] in closed_ids:
            continue
        if not item.get("scheduling_ready"):
            continue
        ok_r, _ = _check_restrictions(item, travelers)
        if not ok_r:
            continue
        pool.append(dict(item, is_show=False))

    # Add eligible show sessions (each session has its own distinct ID)
    for sess in dataset.get("show_sessions") or []:
        if not include_harbour and sess.get("is_harbour"):
            continue
        if zone_ids is not None and sess.get("zone_id") not in zone_ids:
            continue
        if sess["session_id"] in closed_ids:
            continue
        if not sess.get("scheduling_ready") or not sess.get("has_published_time"):
            continue
        sess_candidate = {
            "id": sess["session_id"],
            "show_id": sess["show_id"],
            "name": sess["name"],
            "venue_id": sess.get("venue_id"),
            "zone_id": sess.get("zone_id"),
            "zone_name": sess.get("zone_name"),
            "is_harbour": sess.get("is_harbour", False),
            "kind": "show_session",
            "is_show": True,
            "start": sess["start"],
            "end": sess["end"],
            "duration_minutes": sess["duration_minutes"],
            "has_published_time": sess["has_published_time"],
            "scheduling_ready": sess["scheduling_ready"],
            "restrictions": sess.get("restrictions") or {},
            "restrictions_verified": sess.get("restrictions_verified", True),
            "pricing": sess.get("pricing") or {"included_in_ticket": True, "extra_vnd": 0},
        }
        pool.append(sess_candidate)

    # 3. Preference-based candidate retrieval (bounded pool)
    pool.sort(key=lambda c: (-_preference_score(c, preference, required_ids), c["id"]))
    pruning_applied = len(pool) > max_candidates
    selected_pool = pool[:max_candidates]
    selected_ids = {c["id"] for c in selected_pool}
    for c in pool[max_candidates:]:
        if c["id"] in required_ids and c["id"] not in selected_ids:
            selected_pool.append(c)
            selected_ids.add(c["id"])

    # 4. Bounded Beam Search (step-by-step expansion up to max_stops)
    beam: list[tuple[float, list[dict[str, Any]]]] = [(0.0, [])]
    validated_routes: list[tuple[float, dict[str, Any]]] = []
    seen_route_keys: set[tuple[str, ...]] = set()

    for depth in range(1, max_stops + 1):
        next_states: list[tuple[float, list[dict[str, Any]]]] = []
        for acc_score, seq in beam:
            used_ids = {c["id"] for c in seq}
            used_shows = {c["show_id"] for c in seq if c.get("show_id")}
            for cand in selected_pool:
                if cand["id"] in used_ids:
                    continue
                if cand.get("show_id") and cand["show_id"] in used_shows:
                    continue
                new_seq = seq + [cand]
                # Validate prefix without enforcing final required_ids yet
                prefix_req = dict(request, required_ids=[])
                ok_prefix, prefix_route, _ = validate_itinerary(new_seq, dataset, prefix_req)
                if not ok_prefix or prefix_route is None:
                    continue
                step_score = (
                    acc_score
                    + _preference_score(cand, preference, required_ids)
                    + 5.0
                    - 0.05 * prefix_route["walk_minutes"]
                )
                next_states.append((step_score, new_seq))

                # 5. Deterministic full validation when required_ids are satisfied
                if required_ids.issubset({c["id"] for c in new_seq}):
                    ok_full, full_route, _ = validate_itinerary(new_seq, dataset, request)
                    if ok_full and full_route is not None:
                        rkey = tuple(s["id"] for s in full_route["stops"])
                        if rkey not in seen_route_keys:
                            seen_route_keys.add(rkey)
                            validated_routes.append((step_score, full_route))

        next_states.sort(key=lambda pair: (-pair[0], tuple(c["id"] for c in pair[1])))
        if len(next_states) > beam_width:
            pruning_applied = True
        beam = next_states[:beam_width]
        if not beam:
            break

    # 6. Top-K candidate selection for LLM index choice
    validated_routes.sort(
        key=lambda pair: (-pair[0], -len(pair[1]["stops"]), pair[1]["total_vnd"], pair[1]["walk_minutes"])
    )
    if len(validated_routes) > top_k:
        pruning_applied = True
    top_routes = [r for _, r in validated_routes[:top_k]]

    llm_options = [
        {
            "i": i,
            "plan": " → ".join(f"{s['name']} {s['start']}–{s['end']}" for s in r["stops"]),
            "ids": [s["id"] for s in r["stops"]],
            "so_diem": len(r["stops"]),
            "phut_di_bo": r["walk_minutes"],
            "gio_xong": r["end_time"],
            "tong_tien": r["total_vnd"],
            "so_show": r["show_count"],
        }
        for i, r in enumerate(top_routes)
    ]

    return {
        "candidates_considered": len(pool),
        "candidates_retrieved": len(selected_pool),
        "routes": top_routes,
        "llm_options": llm_options,
        "pruning_applied": pruning_applied,
        "is_globally_optimal": False if pruning_applied else None,
        "optimality_note": (
            "Ứng viên đã được lọc trước và cắt tỉa bằng beam search/top-K; "
            "không tuyên bố đây là lịch tối ưu tuyệt đối trên toàn bộ danh mục."
            if pruning_applied
            else "Không áp dụng cắt tỉa trên tập ứng viên hợp lệ hiện tại."
        ),
    }


def plan_nha_trang(
    dataset: dict[str, Any],
    request: dict[str, Any],
    *,
    allow_draft_estimates: bool = False,
    lead_approved_draft: bool = False,
) -> dict[str, Any]:
    """Fail-closed planner entrypoint for VinWonders Nha Trang public-source snapshot.

    - Never silently falls back to synthetic Vịnh Mây parameters.
    - Returns catalog & published showtime references with explicit missing-data reasons
      whenever real operational fields are incomplete.
    - Blocks draft-estimation mode unless explicitly approved by the team lead.
    """
    include_harbour = bool(request.get("include_harbour", False))
    zone_ids = request.get("zone_ids")
    preference = request.get("preference") or ""
    travelers = request.get("travelers") or []
    required_ids = list(request.get("required_ids") or [])

    readiness = check_scheduling_readiness(dataset, request)
    quote = calculate_group_reference_quote(travelers, dataset, selected_item_ids=required_ids)

    # Draft mode governance gate
    if allow_draft_estimates and not lead_approved_draft:
        return {
            "park_id": dataset["park_id"],
            "mode": "draft_blocked_pending_lead_approval",
            "verified_schedule": False,
            "is_globally_optimal": False,
            "routes": [],
            "readiness": readiness,
            "ticket_reference": quote,
            "message": (
                "Chế độ lập lịch nháp dùng tham số ước tính (draft) đang bị khóa: "
                "cần đội trưởng duyệt trước (lead_approved_draft=True) và gắn nhãn rõ không phải lịch đã xác minh."
            ),
            "catalog_references": [],
            "show_references": [],
        }

    # If the dataset is genuinely scheduling-ready (e.g., future verified feed or test fixture), run beam search
    if readiness["ready_for_verified_schedule"] and quote["all_bands_resolved"] and quote["reference_total_vnd"] is not None:
        search_req = dict(request, verified_admission_total_vnd=quote["reference_total_vnd"])
        search_res = build_bounded_candidates(dataset, search_req)
        return {
            "park_id": dataset["park_id"],
            "mode": "verified_bounded_search",
            "verified_schedule": bool(search_res["routes"]),
            "is_globally_optimal": search_res["is_globally_optimal"],
            "pruning_applied": search_res["pruning_applied"],
            "optimality_note": search_res["optimality_note"],
            "routes": search_res["routes"],
            "llm_options": search_res["llm_options"],
            "readiness": readiness,
            "ticket_reference": quote,
            "message": (
                f"Đã kiểm tra {len(search_res['routes'])} lịch ứng viên hợp lệ bằng bộ kiểm xác định."
                if search_res["routes"]
                else "Không tìm thấy lịch hợp lệ thoả toàn bộ ràng buộc."
            ),
        }

    # Fail-closed real snapshot mode -> return transparent catalog & published showtime references
    filtered_items = filter_catalog(
        dataset,
        include_harbour=include_harbour,
        zone_ids=zone_ids,
        kinds={"ride", "sight"},
        query="",
    )
    req_set = set(required_ids)
    filtered_items.sort(key=lambda i: (-_preference_score(i, preference, req_set), i["id"]))
    catalog_refs = [
        {
            "id": i["id"],
            "map_code": i["map_code"],
            "name": i["name"],
            "zone_id": i["zone_id"],
            "zone_name": i["zone_name"],
            "kind": i["kind"],
            "open": i["open"],
            "close": i["close"],
            "min_height_cm": i["min_height_cm"],
            "included_in_ticket": i["included_in_ticket"],
            "status": i["status"],
            "source_id": i["source_id"],
            "field_sources": i["field_sources"],
            "map_warning": i["map_warning"],
        }
        for i in filtered_items[:12]
    ]

    show_refs = filter_show_sessions(dataset, include_harbour=include_harbour, only_with_times=True)
    return {
        "park_id": dataset["park_id"],
        "mode": "catalog_reference_only",
        "verified_schedule": False,
        "is_globally_optimal": False,
        "pruning_applied": False,
        "routes": [],
        "llm_options": [],
        "readiness": readiness,
        "ticket_reference": quote,
        "catalog_references": catalog_refs,
        "show_references": show_refs,
        "message": (
            "Chưa thể tạo lịch trình đã xác minh cho VinWonders Nha Trang từ snapshot hiện tại vì thiếu "
            "trạng thái mở cửa trực tiếp, thời lượng từng trò, ma trận thời gian di chuyển, điều kiện an toàn đầy đủ "
            "và báo giá trực tiếp. Hệ thống chỉ hiển thị danh mục tham khảo và các suất show công bố (chưa xác minh trực tiếp)."
        ),
    }
