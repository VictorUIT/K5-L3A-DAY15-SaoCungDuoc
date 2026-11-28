"""Dựng snapshot VinWonders Phú Quốc (schema public_snapshot_v1, giống data/nha_trang/) — người phụ trách: Đỗ Phương Nam.

Dữ liệu nhập tay từ các trang chính thức vinwonders.com đọc ngày 28/11/2026 (xem SOURCES).
Chỉ ghi điều trang viết rõ; không có thì để null, KHÔNG suy đoán. Chạy lại:
    python data/phu_quoc/build_snapshot.py
Chỉ dùng thư viện chuẩn, không gọi mạng.
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATE = "2026-11-28"
PARK_ID = "vinwonders_phu_quoc"

SOURCES = [
    ("PRICE", "https://vinwonders.com/vi/vinwonders-phu-quoc-price-and-regulations/",
     "official price & regulations page; no article date; prices incl. VAT; no validity dates"),
    ("HOURS_VI", "https://vinwonders.com/vi/wonderpedia/news/vinwonders-phu-quoc-gio-mo-cua/",
     "official article published 23/07/2025; park and zone hours, minishow table"),
    ("HOURS_EN", "https://vinwonders.com/en/wonderpedia/news/vinwonders-phu-quoc-opening-hours/",
     "official article dated 01/01/2026; zone hours, show times, mermaid show seasonal note"),
    ("SHOWS", "https://vinwonders.com/en/wonderpedia/news/vinwonders-phu-quoc-show-schedule/",
     "official show schedule article published 18/12/2025; primary source for show sessions"),
    ("MAP_ARTICLE", "https://vinwonders.com/en/wonderpedia/news/vinwonders-phu-quoc-map-your-adventure-navigator/",
     "official map article published 07/12/2025; zone membership of named attractions; show times conflict with SHOWS"),
    ("MAP_PNG", "https://static.vinwonders.com/production/2026/04/ban-do-vinwonders-phu-quoc-en.png",
     "official map image April 2026; link found, NOT inspected for this snapshot"),
    ("PRICE_NEWS", "https://vinwonders.com/vi/wonderpedia/news/gia-ve-vinwonders-phu-quoc-combo-voucher-hot/",
     "official article published 16/01/2026; ticket valid 09:00-19:05, no entry after 19:00"),
    ("HOME", "https://vinwonders.com/en/vinwonders-phu-quoc/",
     "official park page; banner operating time 09:00-19:30"),
    ("HEIGHT", "https://vinwonders.com/en/wonderpedia/news/height-requirements-vinwonders-phu-quoc/",
     "official article published 29/01/2026; rides grouped by 'Guests over X cm'; no per-ride max, age, weight, duration, fee"),
    ("HEIGHT_VI", "https://vinwonders.com/vi/wonderpedia/news/thong-bao-chieu-cao-ap-dung-vinwonders-phu-quoc/",
     "official article published 29/01/2026; Vietnamese counterpart of HEIGHT"),
]

# Giờ khu: HOURS_EN (khớp HOURS_VI). Khu "unassigned" giữ các trò mà nguồn chiều cao chỉ ghi nhóm "Games", chưa nguồn nào nêu khu.
ZONES = [
    ("european_avenue", "European Avenue (Đại lộ châu Âu)", "09:00", "19:30", "HOURS_EN"),
    ("fantasy_world", "Fantasy World (Thế giới cổ tích)", "10:00", "18:00", "HOURS_EN"),
    ("viking_village", "Mysterious Viking Village (Khu làng bí mật)", "10:00", "17:30", "HOURS_EN"),
    ("adventure_world", "Adventure World (Thế giới phiêu lưu)", "10:00", "18:00", "HOURS_EN"),
    ("typhoon_world", "Typhoon World (Thế giới lốc xoáy)", "10:00", "17:30", "HOURS_EN"),
    ("sea_shell", "The Sea Shell (Cung điện Hải Vương)", "10:00", "18:00", "HOURS_EN"),
    ("unassigned", "Chưa rõ khu (nguồn chỉ ghi nhóm 'Games')", None, None, "HEIGHT"),
]

# (tên như nguồn ghi, khu, loại, min_height_cm, nguồn khu, ghi chú)
# min_height_cm = X khi nguồn xếp trò vào nhóm "Guests over X cm"; nguồn không nói rõ "trên X" hay "từ X".
RIDES = [
    # Nhóm >145cm (HEIGHT: "Thor's Adventure (>145cm)"; HEIGHT_VI tiêu đề "Trò chơi (>145cm)")
    ("Thor's Adventure", "viking_village", "ride", 145, "MAP_ARTICLE", None),
    ("The Wrath of Zeus", "adventure_world", "ride", 145, "MAP_ARTICLE", "MAP_ARTICLE: up to 110 km/h"),
    ("Ipanema Skate Ride", "unassigned", "ride", 145, None, None),
    ("Nemesis Spin", "unassigned", "ride", 145, None, None),
    ("Upstream challenge", "typhoon_world", "ride", 145, "HEIGHT", None),
    ("Waikiki Surfing", "typhoon_world", "ride", 145, "HEIGHT", None),
    ("Insanity Drop", "typhoon_world", "ride", 145, "HEIGHT", None),
    ("Mighty Drop", "typhoon_world", "ride", 145, "HEIGHT", None),
    ("Kamikaze", "typhoon_world", "ride", 145, "HEIGHT", None),
    # >140cm
    ("The Obelisk of Osiris", "unassigned", "ride", 140, None, None),
    ("The Icarus Race", "unassigned", "ride", 140, None, None),
    ("Jaguar Jungle", "unassigned", "ride", 140, None, None),
    ("The Eagle Warrior", "adventure_world", "ride", 140, "MAP_ARTICLE",
     "MAP_ARTICLE names \"Wonderous Maya 'Eagle Warrior' Challenge\" in Adventure World"),
    # >130cm
    ("Giant Python Struggle Slide", "unassigned", "ride", 130, None, None),
    ("Eagle Soar Glider", "unassigned", "ride", 130, None, None),
    ("Xibalba Drop", "unassigned", "ride", 130, None, None),
    ("Amazon Volcano", "unassigned", "ride", 130, None, None),
    ("Mystic triangle", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Hawaiian drop", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Racer slide", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Maui Twin Tornadoes", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Serpent's Venom", "typhoon_world", "ride", 130, "HEIGHT", "MAP_ARTICLE: 175 m slide"),
    ("Fiery Dragon", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Rapid whirlwind", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Swing n swim", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Vicious Huricane", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Raging Current", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Kohala Dark Slide", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Kauai Dark Slide", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Invisible Loop", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Storm surge", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Amazing Twister", "typhoon_world", "ride", 130, "HEIGHT", None),
    ("Tsunami Rage", "typhoon_world", "ride", 130, "HEIGHT", None),
    # >120cm
    ("Aladdin's Grand Palace Tour", "unassigned", "ride", 120, None, None),
    # >110cm
    ("The Dragon's Spell", "european_avenue", "ride", 110, "MAP_ARTICLE", "MAP_ARTICLE: at Palace of Dreams"),
    ("Thumbelina Ride", "unassigned", "ride", 110, None, None),
    ("Deputy ranger Patrol", "unassigned", "ride", 110, None, None),
    ("Western Stream Train", "unassigned", "ride", 110, None, None),
    ("Viking River Rapids Ride", "viking_village", "ride", 110, "MAP_ARTICLE", None),
    # >100cm
    ("Hustling Games Village", "unassigned", "ride", 100, None, None),
    ("Down the Rabbit Hole", "unassigned", "ride", 100, None, None),
    ("The Temple of Isis", "unassigned", "ride", 100, None, None),
    ("The Sheriff Academy", "unassigned", "ride", 100, None, None),
    ("The Wheel of Time", "unassigned", "ride", 80, None, "HEIGHT lists it in the 100cm group but marks it '(>80cm)'"),
    ("The house of 7 dwarfs & Snow White", "unassigned", "sight", 100, None, None),
    ("Grim fairy tale village", "unassigned", "sight", 100, None, None),
    ("Moochoo show", "unassigned", "sight", 100, None, None),
    ("Oahu Waves", "typhoon_world", "ride", 100, "HEIGHT", "MAP_ARTICLE: wave pool 4,500 m2, depth up to 2.2 m"),
    ("Hinatuan enchanted river", "typhoon_world", "ride", 100, "HEIGHT", None),
    ("Pirate's ship water play", "typhoon_world", "ride", 100, "HEIGHT", "HEIGHT: 9 slides"),
    ("Kilihune waterplay", "typhoon_world", "ride", 100, "HEIGHT", None),
    ("Magical bamboo", "typhoon_world", "ride", 100, "HEIGHT", None),
    ("The Seashells Aquarium 1st floor", "sea_shell", "sight", 100, "HEIGHT", None),
    ("The Torque's Odyssey (2nd floor, The Seashells Aquarium)", "sea_shell", "sight", 100, "HEIGHT", None),
]

# Điểm có trong MAP_ARTICLE nhưng không có trong trang chiều cao → không có giới hạn chiều cao đã công bố (null).
MAP_ONLY = [
    ("Amazing Kingdom", "fantasy_world", "sight"), ("Hidden Oasis", "fantasy_world", "sight"),
    ("Ancient Valley", "fantasy_world", "sight"), ("Forest of Myths", "fantasy_world", "sight"),
    ("Western Frontier", "fantasy_world", "sight"),
    ("Triumphant Songs of the Vikings", "viking_village", "sight"),
    ("South American Forest", "adventure_world", "ride"), ("Viking Zipline Adventure", "adventure_world", "ride"),
    ("Jellyfish World", "sea_shell", "sight"), ("Giant Fish World", "sea_shell", "sight"),
    ("Colorful Fish World", "sea_shell", "sight"), ("Shark Realm", "sea_shell", "sight"),
    ("Penguin World", "sea_shell", "sight"),
]

# Điểm diễn: nhãn địa điểm như SHOWS ghi.
VENUES = [
    ("pq_v_european", "European Streetmosphere (show area)", "european_avenue"),
    ("pq_v_fire_phoenix", "Fire Phoenix Square", "unassigned"),
    ("pq_v_sea_shell", "The Sea Shell (show area)", "sea_shell"),
    ("pq_v_typhoon", "Typhoon World (show area)", "typhoon_world"),
]

# Suất diễn theo SHOWS (18/12/2025). conflict_source_id = nguồn ghi khác.
SHOWS = [
    ("characters_meet", "Meet and photo with fairy tale characters", "pq_v_european", "09:30", "10:00", None, None),
    ("fish_feeding", "Fish Feeding Show", "pq_v_sea_shell", "11:00", "11:10", "MAP_ARTICLE",
     "MAP_ARTICLE: 15:00-15:15; HOME: 11:00-11:15"),
    ("fountain_1", "Musical Water Fountain", "pq_v_european", "11:30", "11:35", "MAP_ARTICLE",
     "MAP_ARTICLE ends :40; venue differs (HOURS_EN: Central Castle)"),
    ("fountain_2", "Musical Water Fountain", "pq_v_european", "14:00", "14:05", "MAP_ARTICLE",
     "MAP_ARTICLE ends :10; venue differs (HOURS_EN: Central Castle)"),
    ("mermaid_1", "Colors of the Ocean (Mermaid Show)", "pq_v_sea_shell", "14:00", "14:20", "HOURS_EN",
     "HOURS_EN: only 01/01/2026-28/02/2026; MAP_ARTICLE: 11:00-11:10 and 14:00-14:10"),
    ("mermaid_2", "Colors of the Ocean (Mermaid Show)", "pq_v_sea_shell", "15:30", "15:50", "HOURS_EN",
     "HOURS_EN: only 01/01/2026-28/02/2026"),
    ("tropical_dance", "Tropical Dance", "pq_v_typhoon", "16:00", "16:05", None, None),
    ("wild_dance", "Wild Dance", "pq_v_typhoon", "16:30", "16:35", None, None),
    ("characters_interact", "Interact with characters", "pq_v_european", "16:30", "16:35", None, None),
    ("carnival", "Carnival Parade", "pq_v_european", "17:00", "17:30", None, None),
    ("fountain_3", "Musical Water Fountain", "pq_v_european", "17:30", "17:35", "MAP_ARTICLE",
     "MAP_ARTICLE ends :40; venue differs (HOURS_EN: Central Castle)"),
    ("once", "ONCE Show", "pq_v_fire_phoenix", "18:45", "19:05", "MAP_ARTICLE", "MAP_ARTICLE: 18:30"),
]

# Vé theo PRICE (đã gồm VAT). current_quote=false: HOURS_EN ghi giá có thể đổi theo mùa; không có ngày hiệu lực.
TICKETS = [
    ("standard_under_100", 0, 100, None, 0, "Vé vào cổng tiêu chuẩn VinWonders",
     "HOURS_EN: free if 'under 1m tall and under 1 year old'"),
    ("standard_100_139", 100, 140, None, 800000, "Vé vào cổng tiêu chuẩn VinWonders", None),
    ("standard_140_plus", 140, None, None, 1050000, "Vé vào cổng tiêu chuẩn VinWonders", None),
    ("standard_senior", None, None, 60, 800000, "Vé vào cổng tiêu chuẩn VinWonders",
     "PRICE 'từ 60 tuổi trở lên' vs HOURS_VI/PRICE_NEWS 'trên 60 tuổi'; photo ID required"),
    ("combo_safari_1d_140_plus", 140, None, None, 1500000, "Combo 01 ngày VinWonders & Vinpearl Safari", None),
    ("combo_safari_1d_100_139", 100, 140, None, 1100000, "Combo 01 ngày VinWonders & Vinpearl Safari", None),
    ("combo_safari_1d_senior", None, None, 60, 1100000, "Combo 01 ngày VinWonders & Vinpearl Safari",
     "senior boundary wording differs across sources (see standard_senior)"),
]

NULL_FIELDS = ("open", "close", "duration_minutes", "max_height_cm", "min_age", "max_age", "min_weight_kg",
               "max_weight_kg", "adult_required", "extra_vnd", "included_in_ticket", "lat", "lon")


def item(idx, name, zone, kind, min_h, zone_src, note, source_id):
    rec = {"id": "pq_%03d" % idx, "map_code": None, "parent_id": None, "name": name, "zone_id": zone,
           "scope": "park", "kind": kind, "source_id": source_id, "status": "unverified_live"}
    rec.update({k: None for k in NULL_FIELDS})
    rec["min_height_cm"] = min_h
    rec["scheduling_ready"] = False
    fs = {}
    if min_h is not None:
        fs["min_height_cm"] = "HEIGHT"
    if zone_src:
        fs["zone_id"] = zone_src
    rec["field_sources"] = fs
    rec["map_warning"] = note
    order = ["id", "map_code", "parent_id", "name", "zone_id", "scope", "kind", "source_id", "status", "open", "close",
             "duration_minutes", "min_height_cm", "max_height_cm", "min_age", "max_age", "min_weight_kg", "max_weight_kg",
             "adult_required", "extra_vnd", "included_in_ticket", "lat", "lon", "scheduling_ready", "field_sources",
             "map_warning"]
    return {k: rec[k] for k in order}


def build():
    catalog = []
    for i, (name, zone, kind, min_h, zsrc, note) in enumerate(RIDES, 1):
        catalog.append(item(i, name, zone, kind, min_h, zsrc, note, "HEIGHT"))
    # Coco Oasis: chỉ cho trẻ dưới 140cm; EN xếp nhóm 100cm, VI xếp nhóm 130cm → min để null.
    coco = item(len(catalog) + 1, "Coco Oasis (Honolulu water play & Wet n Wild)", "typhoon_world", "ride", None,
                "HEIGHT", "Only for children under 140cm; min height conflicts: HEIGHT groups it >100cm, HEIGHT_VI >130cm",
                "HEIGHT")
    coco["max_height_cm"] = 139
    coco["field_sources"]["max_height_cm"] = "HEIGHT"
    catalog.append(coco)
    for name, zone, kind in MAP_ONLY:
        catalog.append(item(len(catalog) + 1, name, zone, kind, None, "MAP_ARTICLE",
                            "Named in MAP_ARTICLE; not listed on height page — no published limits", "MAP_ARTICLE"))
    for vid, name, zone in VENUES:
        v = item(0, name, zone, "show_venue", None, "SHOWS", "Location label as written in SHOWS", "SHOWS")
        v["id"] = vid
        catalog.append(v)

    zones = [{"id": z, "name": n, "scope": "park", "open": o, "close": c, "source_id": s, "map_range": [],
              "live_status": None} for z, n, o, c, s in ZONES]
    shows = [{"id": sid, "name": n, "venue_id": v, "start": st, "end": en,
              "duration_minutes": (int(en[:2]) * 60 + int(en[3:])) - (int(st[:2]) * 60 + int(st[3:])),
              "source_id": "SHOWS", "conflict_source_id": cs, "live_status": None, "note": note}
             for sid, n, v, st, en, cs, note in SHOWS]
    tickets = [{"id": tid, "min_height_cm": lo, "max_height_cm_exclusive": hi, "min_age": age, "price_vnd": p,
                "product": prod, "source_id": "PRICE", "current_quote": False, "effective_from": None,
                "effective_until": None, "note": note} for tid, lo, hi, age, p, prod, note in TICKETS]
    sources = [{"id": s, "url": u, "note": n, "accessed_on": DATE} for s, u, n in SOURCES]
    meta = {
        "id": PARK_ID, "name": "VinWonders Phú Quốc", "source": "public_source_snapshot",
        "timezone": "Asia/Ho_Chi_Minh", "currency": "VND", "open": "09:00", "close": "19:30",
        "source_id": "HOURS_VI", "snapshot_date": DATE, "live_availability": False, "walk_minutes": None,
        "notes": [
            "PRICE_NEWS: ticket valid 09:00-19:05, no admission after 19:00 (other pages: open until 19:30).",
            "Show times and venues conflict between SHOWS, HOURS_EN, MAP_ARTICLE, HOME; see shows.json notes.",
            "Mermaid show: HOURS_EN limits it to 01/01/2026-28/02/2026; status after that not published.",
            "No per-ride hours, durations, weight limits or travel matrix. Height = 'Guests over X cm' group.",
            "Park rules (PRICE): children under 14 and children under 140cm must be accompanied by an adult.",
            "HEIGHT: guests >=100kg, pregnant, elderly or with heart/blood-pressure/vestibular/neurological "
            "conditions may be restricted from most attractions.",
            "Do not use as legacy park.json.",
        ],
    }
    kinds = {}
    for c in catalog:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    report = {
        "snapshot_date": DATE,
        "method": "web-assisted factual extraction from official vinwonders.com pages and manual normalization; "
                  "not an automated crawl",
        "catalog_count": len(catalog),
        "kind_counts": kinds,
        "park_zone_count": len(ZONES) - 1,
        "unassigned_zone_items": sum(c["zone_id"] == "unassigned" for c in catalog),
        "catalog_points_with_min_height": sum(c["min_height_cm"] is not None for c in catalog),
        "catalog_points_with_hours": 0,
        "show_records": len(shows),
        "show_records_with_conflicts": sum(s["conflict_source_id"] is not None for s in shows),
        "price_rows": len(tickets),
        "review_records": 0,
        "scheduling_ready_points": 0,
        "missing_travel_matrix": True,
        "blocked_direct_sources": [],
        "limitations": [
            "All 10 pages fetched HTTP 200; no access control bypassed, no unofficial API used.",
            "Map image MAP_PNG not inspected; map codes and coordinates absent.",
            "Zones for 'Games' rides only assigned when MAP_ARTICLE names them; others 'unassigned'.",
            "Prices are published list prices, not a current quote for a given date.",
            "No reviews collected for Phu Quoc in this snapshot.",
        ],
    }

    def dump(name, obj):
        (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    dump("park_metadata.json", meta)
    dump("zones.json", zones)
    dump("catalog.json", catalog)
    dump("shows.json", shows)
    dump("ticket_prices.json", tickets)
    dump("sources.json", sources)
    dump("walking_distances.json", [])
    dump("crawl_report.json", report)
    with open(HERE / "catalog.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(catalog[0].keys()))
        w.writeheader()
        for c in catalog:
            w.writerow(dict(c, field_sources=json.dumps(c["field_sources"], ensure_ascii=False)))
    print("catalog %d · shows %d · tickets %d · zones %d" % (len(catalog), len(shows), len(tickets), len(zones)))


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    build()
