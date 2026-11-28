"""Offline unit tests for VinWonders Nha Trang v1 integration and CP3/CP4 preservation.

Run with:
    python -m unittest discover -s tests -v
No live network calls or LLM API calls are made.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODEBASE = ROOT / "codebase"
for p in (str(CODEBASE), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import agent
import ai
from crawler import (
    CheckpointStore,
    CrawlRunner,
    LocalExportAdapter,
    PermittedJsonApiAdapter,
    RateLimiter,
    RetryPolicy,
)
from park_provider import (
    DEFAULT_PARK_ID,
    NHA_TRANG_PARK_ID,
    WalkingDistanceMatrix,
    filter_catalog,
    filter_show_sessions,
    list_parks,
    load_legacy_vinh_may,
    load_nha_trang_dataset,
    load_park_provider,
    validate_snapshot,
)
from planning import build_bounded_candidates, check_scheduling_readiness, plan_nha_trang, validate_itinerary
from pricing import calculate_group_reference_quote, classify_traveler_ticket
from review_intel import (
    analyze_pain_points,
    analyze_wait_times,
    build_knowledge_base,
    load_reviews,
    retrieve_attraction_experiences,
)


class TestDatasetSchemaAndIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = load_nha_trang_dataset()
        cls.reviews = load_reviews()

    def test_snapshot_counts_match_crawl_report(self):
        report = self.ds["crawl_report"]
        self.assertEqual(len(self.ds["catalog"]), 159)
        self.assertEqual(len(self.ds["catalog"]), report["catalog_count"])
        self.assertEqual(len(self.ds["attractions"]), 80)
        self.assertEqual(len(self.ds["restaurants"]), 38)
        self.assertEqual(len(self.ds["shops"]), 22)
        self.assertEqual(sum(1 for z in self.ds["zones"] if not z["is_harbour"]), 6)
        self.assertEqual(sum(1 for z in self.ds["zones"] if z["is_harbour"]), 1)
        self.assertEqual(len(self.ds["show_sessions"]), 8)
        self.assertEqual(sum(1 for s in self.ds["show_sessions"] if s["has_published_time"]), 5)
        self.assertEqual(len(self.ds["ticket_prices"]), 4)
        self.assertEqual(len(self.ds["sources"]), 16)
        self.assertEqual(len(self.reviews), 53)

    def test_id_uniqueness_and_referential_integrity(self):
        result = validate_snapshot(self.ds)
        self.assertTrue(result["valid"], f"Validation errors: {result['errors']}")
        self.assertEqual(result["errors"], [])

        # Verify review IDs are unique and every source_id exists in sources.json
        rev_ids = [r["id"] for r in self.reviews]
        self.assertEqual(len(rev_ids), len(set(rev_ids)))
        for r in self.reviews:
            self.assertIn(r["source_id"], self.ds["sources_by_id"])

    def test_null_zero_false_distinction(self):
        zipline = self.ds["catalog_by_id"]["nt_13"]
        # False vs None must never be conflated
        self.assertIs(zipline["included_in_ticket"], False)
        self.assertIsNone(zipline["extra_vnd"])
        self.assertIsNone(zipline["duration_minutes"])
        self.assertEqual(zipline["min_height_cm"], 130)
        self.assertIs(zipline["scheduling_ready"], False)

        # Unknown item: none of the missing operational fields become 0 or False
        alpine = self.ds["catalog_by_id"]["nt_14"]
        self.assertIsNone(alpine["open"])
        self.assertIsNone(alpine["close"])
        self.assertIsNone(alpine["duration_minutes"])
        self.assertIsNone(alpine["min_height_cm"])
        self.assertIsNone(alpine["extra_vnd"])
        self.assertIsNone(alpine["included_in_ticket"])
        self.assertEqual(alpine["status"], "unverified_live")
        self.assertIs(alpine["operation_status"]["live_verified"], False)

        # Ticket band <100 cm is explicitly 0 (not None), while current_quote is explicitly False
        under_100 = next(b for b in self.ds["ticket_prices"] if b["id"] == "standard_under_100")
        self.assertEqual(under_100["price_vnd"], 0)
        self.assertIsNotNone(under_100["price_vnd"])
        self.assertIs(under_100["current_quote"], False)

        # Provenance preserved
        river = self.ds["catalog_by_id"]["nt_09"]
        self.assertEqual(river["source_id"], "MAP")
        self.assertEqual(river["field_sources"], {"open": "RIVER", "close": "RIVER", "min_height_cm": "RIVER"})


class TestMultiParkAndHarbourSeparation(unittest.TestCase):
    def test_default_park_is_vinh_may_and_schemas_are_separated(self):
        parks = list_parks()
        self.assertEqual(parks[0]["id"], DEFAULT_PARK_ID)
        self.assertEqual(parks[1]["id"], NHA_TRANG_PARK_ID)

        default_provider = load_park_provider()
        self.assertEqual(default_provider["park_id"], DEFAULT_PARK_ID)
        self.assertEqual(default_provider["schema_type"], "synthetic_legacy")

        nt_provider = load_park_provider(NHA_TRANG_PARK_ID)
        self.assertEqual(nt_provider["park_id"], NHA_TRANG_PARK_ID)
        self.assertEqual(nt_provider["schema_type"], "public_snapshot_v1")
        # Must NEVER backfill Nha Trang walk_minutes from Vịnh Mây's 10 minutes
        self.assertIsNone(nt_provider["park"]["walk_minutes"])
        self.assertTrue(nt_provider["walking_matrix"].is_empty)

    def test_harbour_excluded_by_default(self):
        ds = load_nha_trang_dataset()
        park_only = filter_catalog(ds, include_harbour=False)
        with_harbour = filter_catalog(ds, include_harbour=True)
        self.assertEqual(len(park_only), 150)
        self.assertEqual(len(with_harbour), 159)
        self.assertTrue(all(i["scope"] == "park" for i in park_only))
        self.assertEqual(sum(1 for i in with_harbour if i["scope"] == "adjacent_harbour"), 9)

        # Harbour show (Stunt Show at nt_97) excluded by default
        park_shows = filter_show_sessions(ds, include_harbour=False)
        all_shows = filter_show_sessions(ds, include_harbour=True)
        self.assertEqual(len(all_shows), 8)
        self.assertEqual(len(park_shows), 7)
        self.assertNotIn("stunt", [s["session_id"] for s in park_shows])
        self.assertIn("stunt", [s["session_id"] for s in all_shows])

    def test_multiple_show_sessions_and_tata_discrepancy(self):
        ds = load_nha_trang_dataset()
        bird_group = next(g for g in ds["shows"] if g["name"] == "Biểu diễn chim")
        self.assertEqual(bird_group["venue_id"], "nt_39")
        self.assertEqual(bird_group["session_ids"], ["bird_1", "bird_2"])
        self.assertEqual([(s["start"], s["end"]) for s in bird_group["sessions"]], [("11:00", "11:20"), ("15:00", "15:20")])
        # Venue ID is distinct from session IDs
        self.assertNotIn(bird_group["venue_id"], bird_group["session_ids"])

        tata = next(s for s in ds["show_sessions"] if s["session_id"] == "tata")
        self.assertTrue(tata["exceeds_park_close"])
        self.assertEqual(tata["conflict_source_id"], "KLOOK")
        self.assertTrue(tata["has_discrepancy"])


class TestHeightBasedTicketPricing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = load_nha_trang_dataset()

    def test_height_bands_and_senior_rules(self):
        prices = self.ds["ticket_prices"]

        r_under = classify_traveler_ticket({"label": "Bé 1", "height_cm": 95}, prices)
        self.assertEqual(r_under["band_id"], "standard_under_100")
        self.assertEqual(r_under["price_vnd"], 0)
        self.assertIs(r_under["current_quote"], False)

        r_mid = classify_traveler_ticket({"label": "Bé 2", "height_cm": 100}, prices)
        self.assertEqual(r_mid["band_id"], "standard_100_139")
        self.assertEqual(r_mid["price_vnd"], 800000)

        r_mid_edge = classify_traveler_ticket({"label": "Bé 3", "height_cm": 139}, prices)
        self.assertEqual(r_mid_edge["band_id"], "standard_100_139")
        self.assertEqual(r_mid_edge["price_vnd"], 800000)

        r_tall = classify_traveler_ticket({"label": "Người lớn", "height_cm": 140}, prices)
        self.assertEqual(r_tall["band_id"], "standard_140_plus")
        self.assertEqual(r_tall["price_vnd"], 1050000)

        r_senior_65 = classify_traveler_ticket({"label": "Ông", "age": 65, "height_cm": 165}, prices)
        self.assertEqual(r_senior_65["band_id"], "standard_senior")
        self.assertEqual(r_senior_65["price_vnd"], 800000)
        self.assertIs(r_senior_65["current_quote"], False)

    def test_exact_age_60_is_unresolved(self):
        r_60 = classify_traveler_ticket({"label": "Bà 60t", "age": 60, "height_cm": 158}, self.ds["ticket_prices"])
        self.assertEqual(r_60["status"], "unresolved_senior_boundary")
        self.assertIsNone(r_60["band_id"])
        self.assertIsNone(r_60["price_vnd"])
        self.assertEqual(r_60["price_range_vnd"], (800000, 1050000))
        self.assertEqual(set(r_60["source_ids"]), {"PRICE", "PRICE_NOTICE"})

    def test_never_infers_height_from_age_or_role(self):
        r_adult_no_h = classify_traveler_ticket({"label": "Người lớn", "age": 35, "height_cm": None}, self.ds["ticket_prices"])
        self.assertEqual(r_adult_no_h["status"], "missing_height")
        self.assertIsNone(r_adult_no_h["price_vnd"])

        quote = calculate_group_reference_quote(
            [{"label": "Người lớn 1", "age": 35, "height_cm": None}],
            self.ds,
            selected_item_ids=["nt_13"],  # Zipline
        )
        self.assertFalse(quote["is_verified_live_quote"])
        self.assertFalse(quote["uses_review_prices"])
        self.assertIsNone(quote["reference_total_vnd"])
        self.assertEqual(quote["missing_height"], ["Người lớn 1"])
        self.assertEqual(len(quote["extra_fee_unknown_items"]), 1)


class TestFailClosedPlanningAndScalableBeamSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = load_nha_trang_dataset()

    def test_missing_travel_matrix_and_safety_fail_closed(self):
        readiness = check_scheduling_readiness(self.ds)
        self.assertFalse(readiness["ready_for_verified_schedule"])
        self.assertTrue(readiness["missing_fields"]["walking_matrix_empty"])
        self.assertEqual(readiness["missing_fields"]["scheduling_ready_items"], 0)

        plan = plan_nha_trang(
            self.ds,
            {
                "start": "09:00",
                "end": "17:00",
                "travelers": [{"label": "Khách 1", "height_cm": 165}, {"label": "Bé", "height_cm": 120}],
                "preference": "Alpine Coaster",
            },
        )
        self.assertEqual(plan["mode"], "catalog_reference_only")
        self.assertFalse(plan["verified_schedule"])
        self.assertEqual(plan["routes"], [])
        self.assertGreater(len(plan["readiness"]["blockers"]), 0)
        # Must NOT fabricate any verified schedule in agent_for_park either
        reply = agent.answer("muốn đi Alpine Coaster", park_id=NHA_TRANG_PARK_ID)
        self.assertIn("chưa xác minh", reply["output"].lower())
        self.assertFalse(reply["plan"]["verified_schedule"])

    def test_draft_mode_requires_lead_approval(self):
        plan = plan_nha_trang(
            self.ds,
            {"start": "09:00", "end": "17:00", "travelers": [{"label": "Khách 1", "height_cm": 165}]},
            allow_draft_estimates=True,
            lead_approved_draft=False,
        )
        self.assertEqual(plan["mode"], "draft_blocked_pending_lead_approval")
        self.assertFalse(plan["verified_schedule"])
        self.assertEqual(plan["routes"], [])

    def test_missing_safety_constraint_rejected_by_deterministic_validator(self):
        # Even if travel matrix exists, an item with restrictions_verified=False must be rejected
        synthetic_ds = copy.deepcopy(self.ds)
        item = synthetic_ds["catalog_by_id"]["nt_09"]
        item["scheduling_ready"] = True
        item["duration_minutes"] = 20
        item["pricing"] = {"included_in_ticket": True, "extra_vnd": 0}
        item["restrictions_verified"] = False
        synthetic_ds["walking_matrix"] = WalkingDistanceMatrix([{"from_id": "gate", "to_id": "nt_09", "minutes": 8}])
        ok, route, err = validate_itinerary(
            [item],
            synthetic_ds,
            {
                "start": "09:00",
                "end": "12:00",
                "travelers": [{"label": "Khách 1", "height_cm": 165}],
                "verified_admission_total_vnd": 1050000,
                "budget_vnd": 2000000,
            },
        )
        self.assertFalse(ok)
        self.assertIsNone(route)
        self.assertIn("chưa được xác minh", err)

    def test_bounded_beam_search_scales_to_160_items_without_claiming_global_optimality(self):
        # Construct an isolated in-memory complete synthetic dataset of 160 rides + 2 show sessions
        catalog = []
        edges = []
        for idx in range(1, 161):
            cid = f"sim_{idx:03d}"
            zone = f"zone_{(idx % 6) + 1}"
            catalog.append({
                "id": cid,
                "name": f"Ride {idx:03d}",
                "zone_id": zone,
                "zone_name": zone,
                "is_harbour": False,
                "kind": "ride",
                "open": "09:00",
                "close": "18:00",
                "duration_minutes": 20,
                "scheduling_ready": True,
                "restrictions": {"min_height_cm": 100},
                "restrictions_verified": True,
                "pricing": {"included_in_ticket": True, "extra_vnd": 0},
                "opening_hours": {"has_published_hours": True},
            })
            edges.append({"from_id": "gate", "to_id": cid, "minutes": 5})

        # Pairwise edges among top retrieved zone items (zone_1 has 26 items)
        zone1_ids = [c["id"] for c in catalog if c["zone_id"] == "zone_1"]
        for a in zone1_ids:
            for b in zone1_ids:
                if a != b:
                    edges.append({"from_id": a, "to_id": b, "minutes": 6})
            edges.append({"from_id": a, "to_id": "venue_bird", "minutes": 7})
        edges.append({"from_id": "gate", "to_id": "venue_bird", "minutes": 8})

        show_sessions = [
            {
                "session_id": "bird_1",
                "show_id": "show_bird",
                "name": "Bird Show",
                "venue_id": "venue_bird",
                "zone_id": "zone_1",
                "zone_name": "zone_1",
                "is_harbour": False,
                "start": "11:00",
                "end": "11:20",
                "duration_minutes": 20,
                "has_published_time": True,
                "scheduling_ready": True,
                "restrictions": {},
                "restrictions_verified": True,
                "pricing": {"included_in_ticket": True, "extra_vnd": 0},
            },
            {
                "session_id": "bird_2",
                "show_id": "show_bird",
                "name": "Bird Show",
                "venue_id": "venue_bird",
                "zone_id": "zone_1",
                "zone_name": "zone_1",
                "is_harbour": False,
                "start": "15:00",
                "end": "15:20",
                "duration_minutes": 20,
                "has_published_time": True,
                "scheduling_ready": True,
                "restrictions": {},
                "restrictions_verified": True,
                "pricing": {"included_in_ticket": True, "extra_vnd": 0},
            },
        ]
        sim_ds = {
            "catalog": catalog,
            "show_sessions": show_sessions,
            "walking_matrix": WalkingDistanceMatrix(edges),
        }
        res = build_bounded_candidates(
            sim_ds,
            {
                "start": "09:00",
                "end": "12:30",
                "zone_ids": ["zone_1"],
                "required_ids": ["bird_1"],
                "preference": "Bird Show Ride 006",
                "travelers": [{"label": "Khách 1", "height_cm": 150}],
                "verified_admission_total_vnd": 1050000,
                "budget_vnd": 1500000,
            },
            max_candidates=12,
            beam_width=8,
            top_k=5,
        )
        self.assertTrue(res["pruning_applied"])
        self.assertIs(res["is_globally_optimal"], False)
        self.assertGreater(len(res["routes"]), 0)
        self.assertLessEqual(len(res["llm_options"]), 5)
        for route in res["routes"]:
            stop_ids = [s["id"] for s in route["stops"]]
            self.assertIn("bird_1", stop_ids)
            self.assertNotIn("bird_2", stop_ids)  # No duplicate show group


class TestReviewIntelligenceGuardrails(unittest.TestCase):
    def test_reviews_do_not_convert_ai_tags_to_human_labels(self):
        reviews = load_reviews()
        self.assertEqual(len(reviews), 53)
        self.assertTrue(all(r["human_label"] is None for r in reviews))

        kb = build_knowledge_base(reviews)
        self.assertEqual(kb["human_labeled_count"], 0)
        self.assertEqual(kb["ai_tag_only_count"], 53)
        self.assertIs(kb["safe_for_safety_rules"], False)
        self.assertIs(kb["safe_for_live_status"], False)
        self.assertIs(kb["safe_for_official_pricing"], False)

        pains = analyze_pain_points(reviews)
        self.assertFalse(pains["labels_are_human_verified"])
        self.assertGreater(len(pains["pain_points"]), 0)

        waits = analyze_wait_times(reviews)
        self.assertFalse(waits["is_live_wait_time"])
        self.assertGreater(waits["queue_or_delay_mentions"], 0)

        hits = retrieve_attraction_experiences(reviews, "Alpine Coaster")
        self.assertGreaterEqual(len(hits), 2)
        self.assertTrue(all(h["human_label"] is None for h in hits))


class TestCrawlerExtensionOffline(unittest.TestCase):
    def test_pagination_checkpoint_resume_dedup_and_blocker_handling(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            ckpt = CheckpointStore(tmp_dir / "checkpoint.json")

            # Export adapter with 53 reviews paginated in pages of 20 (no hard cap)
            local_adapter = LocalExportAdapter(
                source_id="NT_REVIEWS_EXPORT",
                export_path=ROOT / "evidence" / "nha_trang" / "reviews.jsonl",
                page_size=20,
            )

            # Simulated permitted API adapter that returns 503 once then 200, then 403 on page 2
            calls = {"n": 0}

            def mock_transport(url: str, headers: dict[str, str]) -> tuple[int, str]:
                calls["n"] += 1
                if "cursor=p2" in url:
                    return 403, "Access Denied"
                if calls["n"] == 1:
                    return 503, "Temporary outage"
                return 200, json.dumps({
                    "items": [{"id": "api_1", "name": "Item 1"}],
                    "next_cursor": "p2",
                })

            api_adapter = PermittedJsonApiAdapter(
                source_id="PERMITTED_API",
                base_url="https://example.invalid/api/items",
                transport=mock_transport,
                check_robots=False,
            )

            slept_calls: list[float] = []
            runner = CrawlRunner(
                checkpoint_store=ckpt,
                rate_limiter=RateLimiter(min_interval_seconds=0.0, sleep_fn=slept_calls.append),
                retry_policy=RetryPolicy(max_retries=2, base_delay_seconds=0.01),
                sleep_fn=slept_calls.append,
                today_fn=lambda: "2026-11-28",
            )

            res1 = runner.run([local_adapter, api_adapter])
            report1 = res1["report"]
            self.assertIsNone(report1["hard_record_limit"])
            self.assertEqual(report1["per_source"]["NT_REVIEWS_EXPORT"]["new_count"], 53)
            self.assertEqual(report1["per_source"]["NT_REVIEWS_EXPORT"]["pages_fetched"], 3)
            self.assertEqual(report1["per_source"]["PERMITTED_API"]["new_count"], 1)
            self.assertTrue(report1["per_source"]["PERMITTED_API"]["blocked"])
            self.assertEqual(report1["blocked_direct_sources"], ["PERMITTED_API"])
            self.assertEqual(report1["blockers"][0]["status_code"], 403)

            # Incremental re-run of local export should deduplicate all 53 records -> 0 new
            runner2 = CrawlRunner(
                checkpoint_store=CheckpointStore(tmp_dir / "checkpoint.json"),
                rate_limiter=RateLimiter(min_interval_seconds=0.0, sleep_fn=slept_calls.append),
                sleep_fn=slept_calls.append,
                today_fn=lambda: "2026-11-28",
            )
            res2 = runner2.run([local_adapter], incremental=True)
            self.assertEqual(res2["report"]["per_source"]["NT_REVIEWS_EXPORT"]["new_count"], 0)
            self.assertEqual(res2["report"]["per_source"]["NT_REVIEWS_EXPORT"]["duplicate_count"], 53)


class TestLegacyVinhMayPreservation(unittest.TestCase):
    def test_legacy_park_json_and_default_answer_preserved(self):
        legacy = load_legacy_vinh_may()
        self.assertEqual(legacy["name"], "Vịnh Mây")
        self.assertEqual(legacy["source"], "synthetic")
        self.assertEqual(legacy["walk_minutes"], 10)
        self.assertEqual(len(legacy["activities"]), 5)

        # Verify default agent.answer(text) works identically under fake provider (0 live API calls)
        old_provider = ai.MODEL_PROVIDER
        try:
            ai.MODEL_PROVIDER = "fake"
            r1 = agent.answer("giờ=09:00-12:00; lớn=2; trẻ=1; cao=110; đồng=500000; phải có=chim")["output"]
            self.assertTrue(r1.startswith("Vịnh Mây · dữ liệu mô phỏng"))
            self.assertIn("11:00–11:20  Show chim", r1)
            self.assertIn("460.000 đ", r1)
            self.assertNotIn("Tàu lượn", r1)

            r8 = agent.answer("giờ=09:00-12:00; lớn=1; trẻ=1; đồng=400000")["output"]
            self.assertEqual(r8, "Bé thấp nhất cao bao nhiêu cm?")

            r22 = agent.answer(
                "giờ=09:00-12:00; lớn=0; trẻ=1; cao=110; đồng=300000; ưu tiên=Bé tự đi chơi, bố mẹ đợi ở ngoài"
            )["output"]
            self.assertIn("ít nhất 1 người lớn", r22)
        finally:
            ai.MODEL_PROVIDER = old_provider


if __name__ == "__main__":
    unittest.main()
