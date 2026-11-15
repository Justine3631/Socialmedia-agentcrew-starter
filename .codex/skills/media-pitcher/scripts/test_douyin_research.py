#!/usr/bin/env python3

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from douyin_research import (
    merge_detail,
    normalize_search_rows,
    read_cache,
    summarize_rows,
    write_cache,
)


class DouyinResearchTest(unittest.TestCase):
    def test_search_placeholders_become_null(self):
        rows = normalize_search_rows([
            {
                "url": "https://www.douyin.com/video/1234567890123456789",
                "likes": 10,
                "plays": 0,
                "comments": 0,
                "shares": 0,
            }
        ])
        self.assertEqual(rows[0]["aweme_id"], "1234567890123456789")
        self.assertIsNone(rows[0]["plays"])
        self.assertIsNone(rows[0]["comments"])
        self.assertIsNone(rows[0]["shares"])

    def test_detail_merge(self):
        row = {"likes": 1}
        merge_detail(row, {
            "play_count": None,
            "digg_count": 10,
            "comment_count": 3,
            "share_count": 2,
            "collect_count": 4,
            "sec_uid": "uid",
        }, "enriched")
        self.assertEqual(row, {
            "plays": None,
            "likes": 10,
            "comments": 3,
            "shares": 2,
            "collects": 4,
            "sec_uid": "uid",
            "detail_status": "enriched",
        })

    def test_summary_keeps_candidate_fields_only(self):
        rows = summarize_rows([{
            "rank": 1,
            "desc": "title",
            "author": "author",
            "likes": 10,
            "collects": None,
            "plays": 100,
            "detail_error": "hidden",
        }])
        self.assertEqual(rows, [{
            "rank": 1,
            "desc": "title",
            "author": "author",
            "likes": 10,
        }])

    def test_cache_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "detail.json"
            value = {"aweme_id": "1", "comment_count": 2}
            write_cache(path, value)
            self.assertEqual(read_cache(path, datetime.now(timezone.utc)), value)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), value)


if __name__ == "__main__":
    unittest.main()
