"""Test offline cho codebase/directions.py và câu "có kịp show không". Routes API được giả lập, không gọi mạng.

Chạy: python -m unittest discover -s tests -v
"""
import io
import json
import sys
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT / "codebase"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import directions  # noqa: E402
from directions import DEST_BY_ID, RouteError, compute_route, directions_url, search_url  # noqa: E402
from nha_trang_chat import answer_nha_trang  # noqa: E402
from nha_trang_demo import apply_demo_estimates  # noqa: E402
from park_provider import load_nha_trang_dataset  # noqa: E402

BOAT, CABLE = DEST_BY_ID["speedboat"], DEST_BY_ID["cable"]


def _query(url):
    return dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestMapsLinks(unittest.TestCase):
    def test_directions_from_current_location_has_no_origin(self):
        url = directions_url(BOAT, None, "driving")
        self.assertTrue(url.startswith("https://www.google.com/maps/dir/?api=1&"))
        q = _query(url)
        self.assertEqual(q["destination"], BOAT["query"])
        self.assertNotIn("origin", q)
        self.assertEqual(q["travelmode"], "driving")
        self.assertNotIn(" ", url)  # mã hoá đúng: không còn khoảng trắng, dấu tiếng Việt thành %XX
        self.assertIn("C%E1%BA%A3ng%20Vinpearl", url)

    def test_directions_with_typed_origin(self):
        q = _query(directions_url(BOAT, "  Vinpearl Resort Nha Trang ", "two-wheeler"))
        self.assertEqual(q["origin"], "Vinpearl Resort Nha Trang")
        self.assertEqual(q["travelmode"], "two-wheeler")

    def test_place_id_added_only_when_known(self):
        self.assertNotIn("destination_place_id", _query(directions_url(BOAT)))
        q = _query(directions_url(dict(BOAT, place_id="ChIJtest"), None, None))
        self.assertEqual(q["destination_place_id"], "ChIJtest")

    def test_unverified_destination_is_search_only(self):
        self.assertFalse(CABLE["verified"])
        url = search_url(CABLE)
        self.assertTrue(url.startswith("https://www.google.com/maps/search/?api=1&"))
        self.assertEqual(_query(url)["query"], CABLE["query"])

    def test_every_destination_has_source_and_date(self):
        for d in directions.DESTINATIONS:
            self.assertTrue(d["source_url"].startswith("https://vinwonders.com/"))
            self.assertTrue(d["source_quote"])
        self.assertEqual(directions.CHECKED_ON, "28/11/2026")


class TestRoutesApi(unittest.TestCase):
    def _call(self, payload=None, error=None, origin=(12.2, 109.2)):
        sent = {}

        def fake_urlopen(req, timeout=0):
            sent["body"] = json.loads(req.data)
            sent["headers"] = dict(req.header_items())
            if error:
                raise error
            return FakeResp(json.dumps(payload).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            return compute_route("KEY", origin, BOAT, "driving"), sent

    def test_success_returns_leg_without_origin(self):
        route, sent = self._call({"routes": [{"distanceMeters": 6234, "duration": "1090s"}]})
        self.assertEqual(route["distance_m"], 6234)
        self.assertEqual(route["duration_s"], 1090)
        self.assertEqual(route["dest_name"], "Cảng Vinpearl Nha Trang")
        self.assertNotIn("origin", route)
        self.assertNotIn("12.2", json.dumps(route))
        self.assertEqual(sent["body"]["travelMode"], "DRIVE")
        self.assertEqual(sent["body"]["destination"], {"address": BOAT["query"]})
        self.assertIn("X-goog-fieldmask", sent["headers"])

    def test_typed_address_origin(self):
        _, sent = self._call({"routes": [{"distanceMeters": 1, "duration": "60s"}]}, origin="Vinpearl Resort Nha Trang")
        self.assertEqual(sent["body"]["origin"], {"address": "Vinpearl Resort Nha Trang"})

    def test_errors_are_friendly(self):
        def http(code):
            return urllib.error.HTTPError("u", code, "x", {}, io.BytesIO(b""))
        for code, words in ((429, "hết lượt"), (403, "chưa hợp lệ"), (400, "không hiểu")):
            with self.assertRaises(RouteError) as cm:
                self._call(error=http(code))
            self.assertIn(words, str(cm.exception))
            self.assertNotIn("KEY", str(cm.exception))
        with self.assertRaises(RouteError):
            self._call({"routes": []})
        with self.assertRaises(RouteError):
            self._call(error=urllib.error.URLError("offline"))

    def test_missing_key(self):
        with self.assertRaises(RouteError):
            compute_route("", (12.2, 109.2), BOAT)


class TestArrivalInChat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = apply_demo_estimates(load_nha_trang_dataset())
        cls.route = {"mode": "driving", "mode_label": "Ô tô / taxi", "dest_id": "speedboat",
                     "dest_name": "Cảng Vinpearl Nha Trang", "dest_kind": "bến tàu", "distance_m": 6234,
                     "duration_s": 1090, "at": "17:40"}

    def test_with_route_states_what_is_known_and_missing(self):
        out = answer_nha_trang("Từ resort đi bây giờ có kịp Tata Show không?", self.ds, route=self.route, now=17 * 60 + 40)["output"]
        self.assertIn("mới tính được chặng tới Cảng Vinpearl Nha Trang", out)
        self.assertIn("khoảng 18 phút", out)
        self.assertIn("tới Cảng Vinpearl Nha Trang khoảng 17:58", out)
        self.assertIn("còn khoảng 92 phút trước suất 19:30", out)
        self.assertIn("Thời gian chờ tàu", out)
        self.assertIn("chưa có dữ liệu đáng tin", out)
        self.assertNotIn("10 phút đi bộ", out)

    def test_without_route_asks_to_estimate(self):
        out = answer_nha_trang("Từ resort có kịp Tata Show không?", self.ds, now=17 * 60)["output"]
        self.assertIn("chưa tính được chặng nào", out)
        self.assertIn("Ước tính thời gian đến", out)

    def test_inside_park_walk_question_unchanged(self):
        out = answer_nha_trang("Đi bộ từ Zipline sang Tata Show có kịp không?", self.ds)["output"]
        self.assertIn("rời Zipline trước", out)
        self.assertNotIn("Từ chỗ bạn tới show", out)


if __name__ == "__main__":
    unittest.main()
