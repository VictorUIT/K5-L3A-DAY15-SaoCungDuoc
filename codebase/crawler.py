"""Extensible, policy-compliant crawling framework for public/permitted park data sources.

Design guarantees:
- Modular ``SourceAdapter`` interface (permitted JSON API, public page, local export).
- Unbounded pagination (no hardcoded record cap; stops only when exhausted or blocked).
- Persistent checkpoint/resume and incremental crawling (skip already-seen items).
- Deterministic deduplication by record ID and content fingerprint.
- Per-host rate limiting and retry policy for transient errors (5xx/timeouts).
- Strict compliance: checks ``robots.txt`` where applicable; IMMEDIATELY halts and
  records a structured blocker on HTTP 401/403/429, CAPTCHA, or anti-bot gates.
  NEVER attempts to bypass access controls, authentication, or anti-bot walls.
- Mandatory provenance (``source_id``, ``source_url``, ``retrieved_on``) and schema validation.
- Generates a structured ``crawl_report.json`` with counts, validation errors, and blockers.
"""
from __future__ import annotations

import abc
import csv
import datetime
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable


ANTI_BOT_MARKERS = (
    "captcha",
    "recaptcha",
    "hcaptcha",
    "cloudflare",
    "turnstile",
    "verify you are human",
    "access denied",
    "bot protection",
)


class AccessBlockedError(RuntimeError):
    """Raised when a target source blocks access (401/403/429/robots.txt/CAPTCHA). Must halt without bypass."""

    def __init__(self, source_id: str, url: str, reason: str, status_code: int | None = None):
        super().__init__(f"[{source_id}] Blocked ({status_code or 'policy'}): {reason} ({url})")
        self.source_id = source_id
        self.url = url
        self.reason = reason
        self.status_code = status_code


@dataclass
class RetryPolicy:
    max_retries: int = 2
    base_delay_seconds: float = 1.0
    backoff_factor: float = 2.0
    retryable_status_codes: tuple[int, ...] = (500, 502, 503, 504)
    halt_status_codes: tuple[int, ...] = (401, 403, 429)


@dataclass
class PageResult:
    records: list[dict[str, Any]]
    next_cursor: str | None = None
    source_url: str = ""
    http_status: int | None = 200


@dataclass
class BlockerRecord:
    source_id: str
    url: str
    reason: str
    status_code: int | None
    timestamp: str


class RateLimiter:
    """Simple per-host rate limiter with injectable clock/sleep for deterministic offline tests."""

    def __init__(
        self,
        min_interval_seconds: float = 1.0,
        *,
        clock_fn: Callable[[], float] = time.monotonic,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
        self.min_interval_seconds = max(0.0, float(min_interval_seconds))
        self._clock = clock_fn
        self._sleep = sleep_fn
        self._last_hit: dict[str, float] = {}

    def wait(self, host: str) -> float:
        now = self._clock()
        last = self._last_hit.get(host)
        slept = 0.0
        if last is not None and self.min_interval_seconds > 0:
            elapsed = now - last
            if elapsed < self.min_interval_seconds:
                slept = self.min_interval_seconds - elapsed
                self._sleep(slept)
        self._last_hit[host] = self._clock()
        return slept


class CheckpointStore:
    """JSON checkpoint store supporting resume and incremental deduplication across runs."""

    def __init__(self, path: Path | None = None):
        self.path = path
        self.state: dict[str, Any] = {"sources": {}}
        if self.path and self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8-sig"))

    def get_source_state(self, source_id: str) -> dict[str, Any]:
        return dict(
            self.state.setdefault("sources", {}).setdefault(
                source_id,
                {"next_cursor": None, "completed": False, "seen_ids": [], "seen_hashes": [], "pages_fetched": 0},
            )
        )

    def update_source_state(
        self,
        source_id: str,
        *,
        next_cursor: str | None,
        completed: bool,
        seen_ids: set[str],
        seen_hashes: set[str],
        pages_fetched: int,
    ) -> None:
        self.state.setdefault("sources", {})[source_id] = {
            "next_cursor": next_cursor,
            "completed": completed,
            "seen_ids": sorted(seen_ids),
            "seen_hashes": sorted(seen_hashes),
            "pages_fetched": pages_fetched,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")


class Deduplicator:
    """Deterministic deduplicator using primary record ID + canonical content hash."""

    def __init__(self, seen_ids: set[str] | None = None, seen_hashes: set[str] | None = None):
        self.seen_ids: set[str] = set(seen_ids or ())
        self.seen_hashes: set[str] = set(seen_hashes or ())

    @staticmethod
    def fingerprint(record: dict[str, Any]) -> str:
        payload = {
            k: v for k, v in record.items()
            if k not in ("retrieved_on", "accessed_on")
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def is_duplicate(self, record: dict[str, Any]) -> bool:
        rid = record.get("id")
        fp = self.fingerprint(record)
        if rid and str(rid) in self.seen_ids:
            return True
        if fp in self.seen_hashes:
            return True
        return False

    def mark_seen(self, record: dict[str, Any]) -> None:
        rid = record.get("id")
        if rid:
            self.seen_ids.add(str(rid))
        self.seen_hashes.add(self.fingerprint(record))


def validate_crawled_record(record: dict[str, Any], required_fields: tuple[str, ...] = ("id", "source_id")) -> list[str]:
    """Validate provenance and required schema fields without coercing None to 0/False."""
    errors: list[str] = []
    for key in required_fields:
        val = record.get(key)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"Thiếu trường bắt buộc '{key}'.")
    if not record.get("retrieved_on"):
        errors.append("Thiếu dấu thời gian provenance 'retrieved_on'.")
    if not record.get("source_url"):
        errors.append("Thiếu nguồn provenance 'source_url'.")
    return errors


class SourceAdapter(abc.ABC):
    """Base interface for permitted data source adapters."""

    def __init__(self, source_id: str, base_url: str, user_agent: str = "VivuResearchBot/1.0 (+public-permitted)"):
        self.source_id = source_id
        self.base_url = base_url
        self.user_agent = user_agent

    @property
    def host(self) -> str:
        return urllib.parse.urlparse(self.base_url).netloc or self.source_id

    def check_robots_allowed(self, url: str) -> bool:
        """Check robots.txt for HTTP(S) URLs. Defaults to True for local exports."""
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return True
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
        except Exception:
            # If robots.txt cannot be fetched, fail conservatively only on explicit block;
            # network/403 errors on target fetch are handled strictly in fetch_page.
            return True
        return rp.can_fetch(self.user_agent, url)

    @abc.abstractmethod
    def fetch_page(self, cursor: str | None = None) -> PageResult:
        """Fetch one page of permitted records. Must raise AccessBlockedError on 401/403/429/anti-bot."""


class PermittedJsonApiAdapter(SourceAdapter):
    """Adapter for permitted paginated JSON APIs (no hardcoded record limit)."""

    def __init__(
        self,
        source_id: str,
        base_url: str,
        *,
        transport: Callable[[str, dict[str, str]], tuple[int, str]] | None = None,
        items_key: str = "items",
        next_cursor_key: str = "next_cursor",
        check_robots: bool = True,
    ):
        super().__init__(source_id, base_url)
        self._transport = transport or self._default_http_get
        self.items_key = items_key
        self.next_cursor_key = next_cursor_key
        self.check_robots = check_robots

    def _default_http_get(self, url: str, headers: dict[str, str]) -> tuple[int, str]:
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:500]
            return exc.code, body

    def _build_url(self, cursor: str | None) -> str:
        if not cursor:
            return self.base_url
        sep = "&" if "?" in self.base_url else "?"
        return f"{self.base_url}{sep}cursor={urllib.parse.quote(cursor)}"

    def fetch_page(self, cursor: str | None = None) -> PageResult:
        url = self._build_url(cursor)
        if self.check_robots and not self.check_robots_allowed(url):
            raise AccessBlockedError(self.source_id, url, "Disallowed by robots.txt", status_code=None)
        status, body = self._transport(url, {"User-Agent": self.user_agent, "Accept": "application/json"})
        low_body = body.lower()
        if status in (401, 403, 429):
            raise AccessBlockedError(self.source_id, url, f"HTTP {status} access/rate restriction", status_code=status)
        if any(marker in low_body for marker in ANTI_BOT_MARKERS):
            raise AccessBlockedError(self.source_id, url, "Detected CAPTCHA or anti-bot gate", status_code=status)
        if status >= 500:
            raise urllib.error.HTTPError(url, status, f"HTTP {status}", {}, None)
        if status != 200:
            raise AccessBlockedError(self.source_id, url, f"Unexpected HTTP {status}", status_code=status)

        data = json.loads(body)
        records = data.get(self.items_key, []) if isinstance(data, dict) else list(data)
        next_cursor = data.get(self.next_cursor_key) if isinstance(data, dict) else None
        return PageResult(records=records, next_cursor=next_cursor, source_url=url, http_status=status)


class LocalExportAdapter(SourceAdapter):
    """Adapter for permitted local JSON/JSONL/CSV exports with simulated pagination (for offline pipelines/tests)."""

    def __init__(self, source_id: str, export_path: Path, *, page_size: int = 25, source_url: str | None = None):
        super().__init__(source_id, source_url or export_path.as_uri())
        self.export_path = Path(export_path)
        self.page_size = max(1, int(page_size))
        self._records_cache: list[dict[str, Any]] | None = None

    def _load_all(self) -> list[dict[str, Any]]:
        if self._records_cache is not None:
            return self._records_cache
        suffix = self.export_path.suffix.lower()
        if suffix == ".jsonl":
            rows = [
                json.loads(line)
                for line in self.export_path.read_text(encoding="utf-8-sig").splitlines()
                if line.strip()
            ]
        elif suffix == ".json":
            data = json.loads(self.export_path.read_text(encoding="utf-8-sig"))
            rows = data if isinstance(data, list) else [data]
        elif suffix == ".csv":
            with self.export_path.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
        else:
            raise ValueError(f"Định dạng export không hỗ trợ: {suffix}")
        self._records_cache = rows
        return rows

    def fetch_page(self, cursor: str | None = None) -> PageResult:
        all_rows = self._load_all()
        offset = int(cursor) if cursor is not None else 0
        chunk = all_rows[offset : offset + self.page_size]
        next_offset = offset + len(chunk)
        next_cursor = str(next_offset) if next_offset < len(all_rows) else None
        return PageResult(records=chunk, next_cursor=next_cursor, source_url=self.base_url, http_status=200)


class CrawlRunner:
    """Orchestrates pagination, checkpoint/resume, dedup, rate limiting, retries, validation, and reporting."""

    def __init__(
        self,
        *,
        checkpoint_store: CheckpointStore | None = None,
        rate_limiter: RateLimiter | None = None,
        retry_policy: RetryPolicy | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        today_fn: Callable[[], str] | None = None,
    ):
        self.checkpoints = checkpoint_store or CheckpointStore()
        self.rate_limiter = rate_limiter or RateLimiter(min_interval_seconds=1.0, sleep_fn=sleep_fn)
        self.retry_policy = retry_policy or RetryPolicy()
        self._sleep = sleep_fn
        self._today = today_fn or (lambda: datetime.date.today().isoformat())

    def _fetch_with_retry(self, adapter: SourceAdapter, cursor: str | None) -> PageResult:
        attempt = 0
        while True:
            self.rate_limiter.wait(adapter.host)
            try:
                return adapter.fetch_page(cursor)
            except AccessBlockedError:
                raise  # Never retry or bypass access/anti-bot blocks
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
                status = getattr(exc, "code", None)
                if status in self.retry_policy.halt_status_codes:
                    raise AccessBlockedError(adapter.source_id, adapter.base_url, f"HTTP {status}", status_code=status)
                if attempt >= self.retry_policy.max_retries or (
                    status is not None and status not in self.retry_policy.retryable_status_codes
                ):
                    raise
                delay = self.retry_policy.base_delay_seconds * (self.retry_policy.backoff_factor ** attempt)
                self._sleep(delay)
                attempt += 1

    def run(
        self,
        adapters: list[SourceAdapter],
        *,
        required_fields: tuple[str, ...] = ("id", "source_id"),
        incremental: bool = True,
    ) -> dict[str, Any]:
        """Run all adapters until exhausted or blocked; return collected records + structured crawl report."""
        collected: list[dict[str, Any]] = []
        blockers: list[BlockerRecord] = []
        validation_errors: list[dict[str, Any]] = []
        per_source_stats: dict[str, dict[str, Any]] = {}
        today = self._today()

        for adapter in adapters:
            state = self.checkpoints.get_source_state(adapter.source_id)
            if incremental and state.get("completed") and state.get("next_cursor") is None:
                # Start a fresh incremental pass keeping seen IDs/hashes so only new items are emitted
                cursor = None
            else:
                cursor = state.get("next_cursor")

            dedup = Deduplicator(set(state.get("seen_ids") or ()), set(state.get("seen_hashes") or ()))
            pages_fetched = int(state.get("pages_fetched") or 0)
            fetched_count = 0
            new_count = 0
            duplicate_count = 0
            invalid_count = 0
            blocked = False

            while True:
                try:
                    page = self._fetch_with_retry(adapter, cursor)
                except AccessBlockedError as blk:
                    blocked = True
                    blockers.append(
                        BlockerRecord(
                            source_id=blk.source_id,
                            url=blk.url,
                            reason=blk.reason,
                            status_code=blk.status_code,
                            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        )
                    )
                    self.checkpoints.update_source_state(
                        adapter.source_id,
                        next_cursor=cursor,
                        completed=False,
                        seen_ids=dedup.seen_ids,
                        seen_hashes=dedup.seen_hashes,
                        pages_fetched=pages_fetched,
                    )
                    break

                pages_fetched += 1
                for raw in page.records:
                    fetched_count += 1
                    rec = dict(raw)
                    rec.setdefault("source_id", adapter.source_id)
                    rec.setdefault("source_url", page.source_url or adapter.base_url)
                    rec.setdefault("retrieved_on", today)

                    errs = validate_crawled_record(rec, required_fields=required_fields)
                    if errs:
                        invalid_count += 1
                        validation_errors.append({"source_id": adapter.source_id, "id": rec.get("id"), "errors": errs})
                        continue

                    if dedup.is_duplicate(rec):
                        duplicate_count += 1
                        continue

                    dedup.mark_seen(rec)
                    collected.append(rec)
                    new_count += 1

                cursor = page.next_cursor
                completed = cursor is None
                self.checkpoints.update_source_state(
                    adapter.source_id,
                    next_cursor=cursor,
                    completed=completed,
                    seen_ids=dedup.seen_ids,
                    seen_hashes=dedup.seen_hashes,
                    pages_fetched=pages_fetched,
                )
                if completed:
                    break

            per_source_stats[adapter.source_id] = {
                "pages_fetched": pages_fetched,
                "fetched_count": fetched_count,
                "new_count": new_count,
                "duplicate_count": duplicate_count,
                "invalid_count": invalid_count,
                "blocked": blocked,
                "completed": not blocked and cursor is None,
            }

        report = {
            "snapshot_date": today,
            "method": "permitted_adapter_crawl",
            "hard_record_limit": None,
            "sources_run": [a.source_id for a in adapters],
            "total_new_records": len(collected),
            "per_source": per_source_stats,
            "blocked_direct_sources": [b.source_id for b in blockers],
            "blockers": [asdict(b) for b in blockers],
            "validation_error_count": len(validation_errors),
            "validation_errors": validation_errors[:50],
        }
        return {"records": collected, "report": report}
