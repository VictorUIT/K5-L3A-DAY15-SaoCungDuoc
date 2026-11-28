"""Test offline cho AI hiểu câu hỏi Nha Trang (codebase/nha_trang_ai.py). Model được giả lập, không gọi mạng.

Chạy: python -m unittest discover -s tests -v
"""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT / "codebase"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import agent  # noqa: E402
from nha_trang_ai import SCHEMA, catalog_names, system_prompt, validate  # noqa: E402
from park_provider import NHA_TRANG_PARK_ID, load_nha_trang_dataset  # noqa: E402
from tools import load_park  # noqa: E402

VINH_MAY_NAMES = [a["name"] for a in load_park()["activities"]]
ROUTE = {"mode": "driving", "mode_label": "Ô tô / taxi", "dest_id": "speedboat", "dest_name": "Cảng Vinpearl Nha Trang",
         "dest_kind": "bến tàu", "distance_m": 6234, "duration_s": 1090, "at": "17:40"}


def model_returning(payload, seen=None):
    def fake(system, user, schema=None):
        if seen is not None:
            seen.update(system=system, user=user, schema=schema)
        return {"text": json.dumps(payload, ensure_ascii=False), "model": "gemini-test", "tokens_in": 10, "tokens_out": 5}
    return fake


def ask(text, payload, seen=None, **kw):
    with mock.patch("nha_trang_ai.call_model", model_returning(payload, seen)):
        return agent.answer(text, park_id=NHA_TRANG_PARK_ID, demo=True, use_model=True, **kw)


class TestValidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = load_nha_trang_dataset()

    def test_drops_unknown_names_and_bad_values(self):
        v = validate({"intent": "plan", "places": ["Zipline", "Tàu lượn siêu tốc bịa", 7, "Zipline"],
                      "heights_cm": [115, 999, -3], "ages": [8, 200], "start": "25:00", "end": "17:00"}, self.ds)
        self.assertEqual(v["places"], ["Zipline"])
        self.assertEqual(v["heights_cm"], [115])
        self.assertEqual(v["ages"], [8])
        self.assertIsNone(v["start"])
        self.assertEqual(v["end"], "17:00")
        self.assertTrue(any("Tàu lượn siêu tốc bịa" in d for d in v["dropped"]))

    def test_unknown_intent_becomes_other_and_end_before_start_dropped(self):
        v = validate({"intent": "đặt vé hộ tôi", "start": "15:00", "end": "09:00"}, self.ds)
        self.assertEqual(v["intent"], "other")
        self.assertIsNone(v["end"])

    def test_prompt_lists_only_nha_trang_catalog(self):
        prompt = system_prompt(self.ds)
        names = catalog_names(self.ds)
        self.assertIn("Tata Show", names["shows"])
        self.assertIn("Zipline", prompt)
        self.assertNotIn("Stunt Show", names["shows"])  # Harbour: ngoài phạm vi công viên
        for name in VINH_MAY_NAMES:
            self.assertNotIn(name, prompt)
        self.assertEqual(SCHEMA["properties"]["intent"]["enum"][0], "show_info")


class TestAnswerWithModel(unittest.TestCase):
    def test_recommend_uses_ai_places_but_data_for_facts(self):
        r = ask("Bé nhà mình cao 1m15, thích nước, nên chơi gì?",
                {"intent": "recommend", "places": ["Tata World River Adventure", "Zipline"], "heights_cm": [115],
                 "preference": "bé thích nước"})
        out = r["output"]
        self.assertIn("AI chọn theo “bé thích nước”: Tata World River Adventure.", out)
        self.assertIn("Người cao 115 cm: đủ chiều cao tối thiểu 105 cm", out)
        self.assertIn("Bỏ Zipline: cần trẻ từ 130 cm, người thấp nhất trong nhóm cao 115 cm", out)  # theo nguồn
        self.assertIn("nguồn: Quy định trò chơi VinWonders", out)
        self.assertNotIn("Vé vào cổng · giá tham khảo", out)  # không hỏi vé thì không chèn vé

    def test_walk_between_follows_ai_order(self):
        out = ask("từ chỗ trượt dây ziczac sang xem show Tata thì đi bộ bao lâu",
                  {"intent": "walk_between", "places": ["Zipline", "Tata Show"]})["output"]
        self.assertIn("Đi từ Zipline sang Tata Show", out)
        self.assertIn("rời Zipline trước", out)

    def test_ticket_uses_price_table(self):
        out = ask("cho hỏi giá vào cổng của con gái tôi một mét", {"intent": "ticket", "heights_cm": [100]})["output"]
        self.assertIn("nhóm vé từ 100 cm đến dưới 140 cm", out)
        self.assertIn("800.000 đ", out)

    def test_plan_with_ai_times(self):
        out = ask("nhà mình tới lúc chín giờ, năm giờ chiều về, muốn đi thủy cung với xem chim",
                  {"intent": "plan", "places": ["Underwater World", "Biểu diễn chim"], "start": "09:00", "end": "17:00"})["output"]
        self.assertIn("Lịch gợi ý (bản demo)", out)
        self.assertIn("11:00–11:20", out)

    def test_route_and_coordinates_never_reach_model(self):
        seen = {}
        r = ask("từ resort đi giờ có kịp tata không", {"intent": "arrival", "places": ["Tata Show"]}, seen, route=ROUTE)
        self.assertIn("mới tính được chặng tới Cảng Vinpearl Nha Trang", r["output"])
        sent = seen["system"] + seen["user"]
        for secret in ("6234", "1090", "Ô tô / taxi", "17:40", "12.2388", "109.1967"):
            self.assertNotIn(secret, sent)

    def test_recommend_without_places_falls_back_to_data(self):
        r = ask("Bé nhà mình cao 1m15, thích nước, nên chơi gì?",
                {"intent": "recommend", "places": [], "heights_cm": [115], "preference": "thích nước"})
        out = r["output"]
        self.assertIn("AI chưa chọn được trò cụ thể", out)
        self.assertIn("Tata World River Adventure (từ 105 cm)", out)
        self.assertNotIn("Zipline (từ 130 cm)", out)
        self.assertNotIn("Vivu chưa nhận ra", out)
        self.assertEqual(r["model_meta"], {"model": "gemini-test", "tokens_in": 10, "tokens_out": 5})

    def test_hallucinated_place_is_not_used(self):
        r = ask("có trò gì vui", {"intent": "recommend", "places": ["Lâu đài bịa đặt"]})
        self.assertNotIn("Lâu đài bịa đặt", r["output"])
        self.assertIn("tên không có trong danh mục", r["understood"]["dropped"][0])

    def test_model_error_falls_back_to_keywords(self):
        def boom(*a, **k):
            raise RuntimeError("HTTP 401 UNAUTHENTICATED")
        with mock.patch("nha_trang_ai.call_model", boom):
            r = agent.answer("Tata Show mấy giờ diễn?", park_id=NHA_TRANG_PARK_ID, demo=True, use_model=True)
        self.assertIsNotNone(r["model_error"])
        self.assertIsNone(r["understood"])
        self.assertIn("19:30–20:10", r["output"])

    def test_bad_json_falls_back(self):
        with mock.patch("nha_trang_ai.call_model", lambda *a, **k: {"text": "không phải JSON", "model": "x",
                                                                    "tokens_in": 1, "tokens_out": 1}):
            r = agent.answer("Zipline", park_id=NHA_TRANG_PARK_ID, demo=True, use_model=True)
        self.assertIsNotNone(r["model_error"])
        self.assertIn("Zipline", r["output"])

    def test_default_does_not_call_model(self):
        with mock.patch("nha_trang_ai.call_model", side_effect=AssertionError("không được gọi")):
            r = agent.answer("Tata Show", park_id=NHA_TRANG_PARK_ID, demo=True)
        self.assertIsNone(r["understood"])


if __name__ == "__main__":
    unittest.main()
