#!/usr/bin/env python3
"""Search Douyin with OpenCLI and optionally enrich shortlisted rows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


CACHE_TTL = timedelta(hours=24)


def video_id(value: str) -> str:
    tail = value.rstrip("/").rsplit("/", 1)[-1]
    return tail if tail.isdigit() else ""


def normalize_search_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for source in rows:
        row = dict(source)
        row["aweme_id"] = video_id(str(row.get("url", "")))
        # These three values are placeholders in OpenCLI's search adapter.
        row["plays"] = None
        row["comments"] = None
        row["shares"] = None
        row["collects"] = None
        row["sec_uid"] = None
        row["detail_status"] = "not_requested"
        normalized.append(row)
    return normalized


def merge_detail(row: dict[str, Any], detail: dict[str, Any], status: str) -> None:
    row["plays"] = detail.get("play_count")
    row["likes"] = detail.get("digg_count", row.get("likes"))
    row["comments"] = detail.get("comment_count")
    row["shares"] = detail.get("share_count")
    row["collects"] = detail.get("collect_count")
    row["sec_uid"] = detail.get("sec_uid") or None
    row["detail_status"] = status


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = (
        "rank",
        "aweme_id",
        "desc",
        "author",
        "published_at",
        "likes",
        "collects",
        "sec_uid",
        "url",
        "detail_status",
    )
    return [
        {field: row.get(field) for field in fields if row.get(field) is not None}
        for row in rows
    ]


def run_opencli(args: list[str], timeout: int) -> Any:
    completed = subprocess.run(
        ["opencli", *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(message or f"OpenCLI exited with {completed.returncode}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenCLI returned non-JSON output: {completed.stdout[:300]}") from exc


def read_cache(path: Path, now: datetime) -> dict[str, Any] | None:
    if not path.exists():
        return None
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    if now - modified > CACHE_TTL:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def write_cache(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def enrich_rows(
    rows: list[dict[str, Any]],
    profile: str,
    enrich_limit: int,
    cache_dir: Path,
    delay: float,
    timeout: int,
) -> None:
    now = datetime.now(timezone.utc)
    for index, row in enumerate(rows[:enrich_limit]):
        aweme_id = row.get("aweme_id")
        if not aweme_id:
            row["detail_status"] = "invalid_url"
            continue
        cache_path = cache_dir / f"{aweme_id}.json"
        detail = read_cache(cache_path, now)
        if detail is not None:
            merge_detail(row, detail, "cached")
            continue
        error = ""
        for attempt in range(2):
            try:
                detail = run_opencli(
                    [
                        "--profile", profile, "douyin", "detail", aweme_id,
                        "--site-session", "ephemeral", "-f", "json",
                    ],
                    timeout,
                )
                if not isinstance(detail, dict):
                    raise RuntimeError("Douyin detail returned a non-object")
                write_cache(cache_path, detail)
                merge_detail(row, detail, "enriched")
                break
            except (RuntimeError, subprocess.TimeoutExpired) as exc:
                error = str(exc)
                if attempt == 0:
                    time.sleep(delay)
        else:
            row["detail_status"] = "failed"
            row["detail_error"] = error[:300]
        if index + 1 < min(enrich_limit, len(rows)):
            time.sleep(delay)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--enrich-limit", type=int, default=5)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--summary",
        action="store_true",
        help="print only compact candidate fields instead of full normalized rows",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write full normalized rows to this JSON file",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path.home() / ".cache" / "crew-douyin-research" / "details",
    )
    args = parser.parse_args()
    if not 1 <= args.limit <= 30:
        parser.error("--limit must be between 1 and 30")
    if not 0 <= args.enrich_limit <= args.limit:
        parser.error("--enrich-limit must be between 0 and --limit")
    rows = run_opencli(
        [
            "--profile", args.profile, "douyin", "search", args.query,
            "--limit", str(args.limit), "--site-session", "ephemeral", "-f", "json",
        ],
        args.timeout,
    )
    if not isinstance(rows, list):
        raise RuntimeError("Douyin search returned a non-list")
    normalized = normalize_search_rows(rows)
    enrich_rows(
        normalized,
        args.profile,
        args.enrich_limit,
        args.cache_dir,
        args.delay,
        args.timeout,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    json.dump(
        summarize_rows(normalized) if args.summary else normalized,
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
