"""Review intelligence module for VinWonders Nha Trang (research & UX reference only).

Reads ``evidence/nha_trang/reviews.jsonl`` (53 anonymized paraphrased records).
Strict guardrails:
- NEVER used as a source for safety restrictions, ticket prices, or live operating status.
- NEVER converts AI-generated ``topics`` into ``human_label`` (keeps ``human_label`` untouched).
- Does NOT modify the locked CP2/CP3 benchmark or ``evidence/data-mining.md``.
"""
from __future__ import annotations

import collections
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEWS_PATH = ROOT / "evidence" / "nha_trang" / "reviews.jsonl"

PAIN_TOPICS = {
    "queue": "Xếp hàng / chờ lâu",
    "closure": "Trò đóng cửa / bảo trì",
    "planning": "Khó sắp xếp lịch / thiếu thời gian",
    "navigation": "Khó tìm đường / bản đồ",
    "walking": "Đi bộ nhiều / khu rộng",
    "height": "Vướng giới hạn chiều cao trẻ em",
    "restriction": "Vướng quy định tham gia",
    "delay": "Trễ giờ / chờ đổi vé hoặc voucher",
    "weather": "Ảnh hưởng thời tiết (mưa)",
    "food": "Ẩm thực / buffet chưa như kỳ vọng",
    "voucher": "Khó tìm quầy nhận voucher",
    "price": "Chi phí / giá vé",
}

NEED_TOPICS = {
    "family": "Nhu cầu đi cùng gia đình / trẻ nhỏ",
    "show": "Quan tâm xem show (Tata Show, nhạc nước, show chiều)",
    "planning": "Cần gợi ý lộ trình / phân bổ thời gian",
    "fastpass": "Quan tâm lối ưu tiên / giảm chờ",
    "ticket": "Mua vé trước / vé QR / combo",
    "value": "Đánh giá tính đáng tiền",
    "service": "Trải nghiệm nhân viên hỗ trợ",
}

WAIT_PATTERNS = re.compile(
    r"(chờ|xếp hàng|hàng dài|giờ|hết lượt|đổi vé|fastpass|ưu tiên|ít đông|đông)",
    re.IGNORECASE,
)


def load_reviews(path: Path = DEFAULT_REVIEWS_PATH) -> list[dict[str, Any]]:
    """Load anonymized review paraphrases from JSONL while preserving provenance and null human_label."""
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            records.append(rec)
    return records


def analyze_pain_points(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize pain-point topics from AI topic tags (explicitly marked as non-human labels)."""
    counts: collections.Counter[str] = collections.Counter()
    by_topic_ids: dict[str, list[str]] = collections.defaultdict(list)
    for rec in reviews:
        for topic in rec.get("topics") or []:
            if topic in PAIN_TOPICS:
                counts[topic] += 1
                by_topic_ids[topic].append(rec["id"])

    ranked = [
        {
            "topic": topic,
            "label": PAIN_TOPICS[topic],
            "count": count,
            "share_pct": round(count * 100.0 / len(reviews), 1) if reviews else 0.0,
            "review_ids": by_topic_ids[topic],
        }
        for topic, count in counts.most_common()
    ]
    return {
        "total_reviews": len(reviews),
        "pain_points": ranked,
        "labels_are_human_verified": all(r.get("human_label") is not None for r in reviews) and bool(reviews),
        "caveat": (
            "Thống kê dựa trên AI topic tags (human_label=null, mẫu không ngẫu nhiên từ 4 trang công khai). "
            "Không đại diện tỷ lệ toàn công viên và không dùng cho quy định an toàn hay trạng thái mở cửa hiện tại."
        ),
    }


def analyze_needs_and_preferences(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate visitor needs and preferences from paraphrased review topics."""
    counts: collections.Counter[str] = collections.Counter()
    examples: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for rec in reviews:
        for topic in rec.get("topics") or []:
            if topic in NEED_TOPICS:
                counts[topic] += 1
                if len(examples[topic]) < 4:
                    examples[topic].append({
                        "id": rec["id"],
                        "source_id": rec["source_id"],
                        "summary": rec["summary"],
                    })

    ranked = [
        {
            "topic": topic,
            "label": NEED_TOPICS[topic],
            "count": count,
            "examples": examples[topic],
        }
        for topic, count in counts.most_common()
    ]
    return {
        "total_reviews": len(reviews),
        "needs": ranked,
        "labels_are_human_verified": False,
    }


def retrieve_attraction_experiences(
    reviews: list[dict[str, Any]],
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Retrieve anonymized guest review paraphrases matching an attraction name or keyword."""
    q = (query or "").strip().casefold()
    if not q:
        return []
    tokens = [t for t in re.split(r"[\s,;/\-]+", q) if len(t) >= 2]
    scored: list[tuple[int, dict[str, Any]]] = []
    for rec in reviews:
        summary = (rec.get("summary") or "").casefold()
        topics_text = " ".join(rec.get("topics") or []).casefold()
        score = 0
        if q in summary:
            score += 5
        for tok in tokens:
            if tok in summary:
                score += 2
            if tok in topics_text:
                score += 1
        if score > 0:
            scored.append((score, rec))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
    return [
        {
            "id": r["id"],
            "source_id": r["source_id"],
            "rating": r.get("rating"),
            "rating_scale": r.get("rating_scale"),
            "review_time_as_displayed": r.get("review_time_as_displayed"),
            "summary": r["summary"],
            "topics": list(r.get("topics") or []),
            "human_label": r.get("human_label"),
            "annotation_kind": r.get("annotation_kind"),
        }
        for _, r in scored[:limit]
    ]


def analyze_wait_times(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract historical wait-time and crowding reflections from reviews (anecdotal, not live)."""
    mentions = []
    long_wait_mentions = []
    for rec in reviews:
        topics = set(rec.get("topics") or [])
        summary = rec.get("summary") or ""
        if "queue" in topics or "delay" in topics or WAIT_PATTERNS.search(summary):
            item = {
                "id": rec["id"],
                "source_id": rec["source_id"],
                "review_time_as_displayed": rec.get("review_time_as_displayed"),
                "summary": summary,
                "topics": list(rec.get("topics") or []),
            }
            mentions.append(item)
            if any(k in summary.lower() for k in ("giờ", "hàng dài", "chờ lâu", "hết lượt")):
                long_wait_mentions.append(item)
    return {
        "total_reviews": len(reviews),
        "queue_or_delay_mentions": len(mentions),
        "severe_wait_mentions": len(long_wait_mentions),
        "examples": mentions,
        "severe_examples": long_wait_mentions,
        "is_live_wait_time": False,
        "caveat": "Phản ánh lịch sử từ review công khai, không phải thời gian chờ trực tiếp hôm nay.",
    }


def build_knowledge_base(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    """Build supplementary experience knowledge base strictly separated from operational truth."""
    source_counts = dict(collections.Counter(r["source_id"] for r in reviews))
    human_labeled_count = sum(1 for r in reviews if r.get("human_label") is not None)
    return {
        "record_count": len(reviews),
        "source_counts": source_counts,
        "human_labeled_count": human_labeled_count,
        "ai_tag_only_count": len(reviews) - human_labeled_count,
        "safe_for_safety_rules": False,
        "safe_for_live_status": False,
        "safe_for_official_pricing": False,
        "pain_points": analyze_pain_points(reviews),
        "needs_and_preferences": analyze_needs_and_preferences(reviews),
        "wait_time_insights": analyze_wait_times(reviews),
        "featured_attraction_notes": {
            "Alpine Coaster": retrieve_attraction_experiences(reviews, "Alpine Coaster", limit=5),
            "Zipline": retrieve_attraction_experiences(reviews, "Zipline", limit=5),
            "Tata Show": retrieve_attraction_experiences(reviews, "Tata Show", limit=5),
            "Nhạc nước": retrieve_attraction_experiences(reviews, "nhạc nước", limit=5),
        },
        "disclaimer": (
            "Cơ sở tri thức bổ sung từ 53 bản diễn giải review ẩn danh (evidence/nha_trang/reviews.jsonl). "
            "Tất cả nhãn topic là AI-generated chờ người kiểm duyệt (human_label=null). "
            "Tuyệt đối không dùng thay cho quy định an toàn, bảng giá chính thức hoặc trạng thái vận hành hiện tại."
        ),
    }
