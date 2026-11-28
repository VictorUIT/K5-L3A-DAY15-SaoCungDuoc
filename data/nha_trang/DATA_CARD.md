# VinWonders Nha Trang · snapshot 2026-11-27

Scope: public directory of six park zones plus adjacent Harbour. 159 catalog entries (99 main, 15 numbered sublocations, 45 named unnumbered children); 80 classified ride/sight records. Not an inventory of operating rides. Map directory name and number from MAP; types are normalized by AI. Some listed facilities are under development. No invented coordinates or hours.

## Provenance and quality
- Source URLs and access status: sources.json. Direct fetch of several official HTML pages failed 403; indexed snippets used only for explicit facts. PDF map March 2026 inspected visually. No claim of live availability.
- 8 catalog entries have published operating hours; 4 have explicit minimum height. Unknown fields are null, never zero. All scheduling_ready=false because duration, complete safety conditions, fees or travel matrix not validated.
- 8 show records, 5 with published times. Tata show time differs between map and Klook, and end time exceeds published park close; recheck on date of visit.
- 4 price bands for one standard product; no verified current quote. Senior age boundary wording differs across official sources; do not resolve by guessing.
- 53 anonymized paraphrases, not verbatim or new interviews. 15 overlap with prior team sample; R15 currently opened wording differs from old team evidence; keep original data-mining.md unchanged. Human labels are null. Snapshot ages may be stale; source pages not random sample.
- No full raw review export or current GPS/queue/walking data. Keep provenance and source restrictions. Only use approved access/API for subsequent retrieval.

## Integration contract
Keep existing data/park.json and all historical evals intact. This is v1 public-source snapshot with separate schema. Catalog browsing may use the full list. Real scheduling must fail closed on unknown safety/cost/availability/travel constraints; a draft planning mode with explicit estimates and no claim of verified schedule requires lead approval. No default 10-minute travel or synthetic ticket fees in real mode.

## Demo estimates (demo_estimates.json)
TỰ ƯỚC TÍNH, không có nguồn, chỉ để web demo điền ô còn trống: giờ khu/điểm chưa công bố (lấy giờ chung HOME), thời lượng và xếp hàng theo loại, quãng đi bộ theo khu, vị trí Tata Show và giờ Welcome show / Cho cá ăn. Không thay giá trị có nguồn, không ước tính chiều cao/tuổi/sức khoẻ hay giá vé. Web gắn nhãn "ước tính demo" cho mọi giá trị này và có công tắc tắt để xem dữ liệu gốc.
