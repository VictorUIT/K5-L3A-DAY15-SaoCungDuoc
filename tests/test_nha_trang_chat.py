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
from nha_trang_chat import answer_nha_trang, find_entities, find_heights, find_times  # noqa: E402
from nha_trang_demo import apply_demo_estimates  # noqa: E402
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
        self.assertIn("nguồn: Bản đồ VinWonders · 27/11/2026", out)
        self.assertIn("Klook ghi 20:30–21:06", out)
        self.assertIn("kết thúc 20:10, sau giờ đóng cửa chung 20:00", out)

    def test_exact_100cm_is_100_to_139_band_reference_price(self):
        out = self.ask("Vé cho bé cao đúng 100 cm bao nhiêu?")
        self.assertIn("nhóm vé từ 100 cm đến dưới 140 cm", out)
        self.assertIn("800.000 đ", out)
        self.assertIn("giá tham khảo", out)
        self.assertIn("Giá thực tế có thể khác theo ngày", out)
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


class TestNhaTrangDemoEstimates(unittest.TestCase):
    """Chế độ demo: điền ô trống bằng số tự ước tính, có nhãn; không đụng giá trị có nguồn, giá vé, chiều cao."""

    @classmethod
    def setUpClass(cls):
        cls.raw = load_nha_trang_dataset()
        cls.ds = apply_demo_estimates(cls.raw)

    def ask(self, text):
        return answer_nha_trang(text, self.ds)["output"]

    def test_snapshot_untouched_and_sourced_values_kept(self):
        self.assertIsNone(self.raw["catalog_by_id"]["nt_14"]["open"])  # bản gốc vẫn trống
        zipline = self.ds["catalog_by_id"]["nt_13"]
        self.assertEqual((zipline["open"], zipline["close"]), ("09:00", "17:00"))  # có nguồn: giữ
        self.assertNotIn("open", zipline["est"])
        alpine = self.ds["catalog_by_id"]["nt_14"]
        self.assertIn("open", alpine["est"])
        self.assertIsNone(alpine["min_height_cm"])  # không ước tính điều kiện an toàn
        self.assertEqual(self.ds["ticket_prices"], self.raw["ticket_prices"])  # không đụng giá vé

    def test_estimated_values_are_labelled(self):
        out = self.ask("Alpine Coaster")
        self.assertIn("09:00–20:00 · ước tính demo", out)
        self.assertIn("Theo quy định tại điểm chơi", out)

    def test_walk_verdict_uses_estimate_not_vinh_may_default(self):
        out = self.ask("Đi bộ từ Zipline sang Tata Show có kịp không?")
        self.assertIn("ước tính demo", out)
        self.assertIn("rời Zipline trước", out)
        walk = [l for l in out.splitlines() if l.startswith("- Đi bộ Zipline → Tata Show")][0]
        self.assertNotIn("10 phút", walk)  # không dùng 10 phút của Vịnh Mây cho quãng đi bộ

    def test_demo_plan_respects_show_times_and_prices_tickets(self):
        out = self.ask("9h đến, về 17h, Alpine Coaster, Underwater World, Biểu diễn chim, bé cao 1m15, mẹ 160 cm")
        self.assertIn("09:00  Vào cổng chính", out)
        self.assertIn("11:00–11:20  Biểu diễn chim", out)
        self.assertIn("Tổng vé vào cổng: 1.850.000 đ", out)  # 800.000 + 1.050.000 theo bảng giá
        times = [l[2:7] for l in out.splitlines() if l[2:4].isdigit() and l[4] == ":"]
        self.assertEqual(times, sorted(times))
        for name in VINH_MAY_NAMES:
            self.assertNotIn(name, out)

    def test_time_parsing(self):
        self.assertEqual(find_times("9h đến, về 17h30"), (540, 1050))
        self.assertEqual(find_times("đến 10:15 ra về lúc 16 giờ"), (615, 960))
        self.assertEqual(find_times("9 giờ tới, 5 giờ chiều về"), (540, 1020))
        self.assertEqual(find_times("10h50 tới cổng, 12h về"), (650, 720))

    def test_vinh_may_style_request_builds_plan_without_model(self):
        out = self.ask("Nhà mình 2 vợ chồng với bé cao 1m25, 9 giờ tới, 5 giờ chiều về, có 3 triệu, muốn xem Tata Show")
        self.assertIn("Lịch gợi ý (bản demo)", out)
        self.assertIn("Không xếp được Tata Show: suất 19:30 nằm ngoài khung 09:00–17:00", out)
        self.assertIn("11:00–11:20  Biểu diễn chim", out)
        self.assertIn("2 người lớn × 1.050.000 đ (giả định cao từ 140 cm", out)
        self.assertIn("Tổng vé vào cổng: 2.900.000 đ", out)
        self.assertIn("Trong ngân sách 3.000.000 đ (còn khoảng 100.000 đ)", out)

    def test_named_show_has_priority_over_auto_shows(self):
        out = self.ask("2 người lớn, 1 bé 110 cm, 9h đến, xem Tata Show")
        self.assertIn("19:30–20:10  Tata Show", out)
        self.assertIn("Không xếp được Nhạc nước: nhường giờ cho Tata Show", out)
        self.assertIn("giờ đóng cửa chung 20:00 (bạn chưa nêu giờ về)", out)
        self.assertIn("Welcome show (đi bộ 5′, có mặt trước 5′) · giờ diễn ước tính demo", out)

    def test_over_budget_and_missing_child_height(self):
        out = self.ask("3 người lớn, 2 bé, 1 bé cao 120 cm, 9h đến 15h về, ngân sách 2 triệu, Alpine Coaster")
        self.assertIn("Còn 1 trẻ chưa có chiều cao", out)
        self.assertIn("chưa so được vì còn vé chưa tính", out)
        out = self.ask("2 người lớn, 9h đến 15h về, ngân sách 1 triệu, Alpine Coaster")
        self.assertIn("⚠ Vượt ngân sách 1.000.000 đ khoảng 1.100.000 đ", out)

    def test_find_group(self):
        from nha_trang_chat import find_group
        self.assertEqual(find_group("Nhà mình 2 vợ chồng với bé, có 3 triệu"), (2, 1, 3_000_000))
        self.assertEqual(find_group("3 người lớn 2 trẻ ngân sách 500k"), (3, 2, 500_000))


if __name__ == "__main__":
    unittest.main()
