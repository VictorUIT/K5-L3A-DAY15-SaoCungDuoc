"""Test offline cho chatbot Nha Trang (codebase/nha_trang_chat.py). Không gọi mạng, không gọi model.

Chạy: python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT / "codebase"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import agent  # noqa: E402
from nha_trang_chat import answer_nha_trang, find_entities, find_heights  # noqa: E402
from park_provider import NHA_TRANG_PARK_ID, load_nha_trang_dataset  # noqa: E402
from tools import load_park  # noqa: E402

VINH_MAY_NAMES = [a["name"] for a in load_park()["activities"]]


class TestNhaTrangChat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = load_nha_trang_dataset()

    def ask(self, text):
        return answer_nha_trang(text, self.ds)["output"]

    def test_tata_show_shows_both_sources_and_close_conflict(self):
        out = self.ask("Tata Show mấy giờ diễn?")
        self.assertIn("19:30–20:10", out)
        self.assertIn("nguồn MAP · 27/11/2026", out)
        self.assertIn("KLOOK ghi 20:30–21:06", out)
        self.assertIn("sau giờ đóng cửa chung 20:00", out)

    def test_exact_100cm_is_100_to_139_band_reference_price(self):
        out = self.ask("Vé cho bé cao đúng 100 cm bao nhiêu?")
        self.assertIn("nhóm vé từ 100 cm đến dưới 140 cm", out)
        self.assertIn("800.000 đ", out)
        self.assertIn("giá tham khảo", out)
        self.assertIn("chưa phải báo giá hiện hành", out)
        self.assertNotIn("miễn phí", out.split("100 cm →")[1].split("\n")[0])

    def test_walking_between_two_points_fails_closed_without_default_minutes(self):
        out = self.ask("Đi bộ từ Zipline sang Tata Show có kịp không?")
        self.assertIn("chưa thể xác nhận đi từ Zipline tới kịp Tata Show", out)
        self.assertIn("Chưa có thời gian đi bộ từ Zipline đến Tata Show", out)
        self.assertNotIn("10 phút", out)
        self.assertIn("Zipline: mở 09:00–17:00", out)  # phần đã có dữ liệu vẫn được nói ra
        self.assertIn("chưa có thời lượng chơi", out)
        self.assertIn("chưa xác định chính xác địa điểm diễn", out)

    def test_never_mentions_vinh_may_places_or_prices(self):
        for q in ("Show chim mấy giờ?", "vé người lớn bao nhiêu", "lên lịch giúp mình", "xin chào"):
            out = self.ask(q)
            for name in VINH_MAY_NAMES:
                self.assertNotIn(name, out, (q, name))
            self.assertNotIn("Vịnh Mây", out)

    def test_bird_show_alias_maps_to_nha_trang_sessions(self):
        out = self.ask("Show chim mấy giờ?")
        self.assertIn("Biểu diễn chim", out)
        self.assertIn("11:00–11:20", out)
        self.assertIn("15:00–15:20", out)

    def test_exact_age_60_is_not_resolved(self):
        out = self.ask("bà 60 tuổi mua vé gì")
        self.assertIn("chưa xác định được nhóm vé", out)

    def test_height_parsing(self):
        self.assertEqual(find_heights("bé 1m25 và anh 1,7 m, em 100cm"), [125, 170, 100])

    def test_longest_match_wins(self):
        kinds = [(k, o["name"]) for k, o in find_entities("Tata Show và Tata World River Adventure", self.ds)]
        self.assertEqual(kinds, [("show", "Tata Show"), ("item", "Tata World River Adventure")])

    def test_agent_entrypoint_keeps_contract_and_plan(self):
        reply = agent.answer("Tata Show", park_id=NHA_TRANG_PARK_ID)
        self.assertIsInstance(reply["output"], str)
        self.assertIn("chưa xác minh", reply["output"])
        self.assertFalse(reply["plan"]["verified_schedule"])


if __name__ == "__main__":
    unittest.main()
