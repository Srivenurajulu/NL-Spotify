#!/usr/bin/env python3
"""Scrape Spotify reviews from Play Store and App Store, then ingest into ChromaDB."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.ingest.app_store import scrape_app_store
from backend.ingest.chroma_ingest import ingest_reviews, write_stats
from backend.ingest.constants import REVIEW_LIMIT
from backend.ingest.play_store import scrape_play_store

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str))


def main() -> None:
    print(f"Scraping up to {REVIEW_LIMIT} reviews per store...")

    play_reviews = scrape_play_store(limit=REVIEW_LIMIT)
    print(f"  Google Play: {len(play_reviews)} reviews")

    app_reviews = scrape_app_store(limit=REVIEW_LIMIT)
    print(f"  App Store:   {len(app_reviews)} reviews")

    all_reviews = play_reviews + app_reviews
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    save_json(RAW_DIR / f"play_store_{timestamp}.json", play_reviews)
    save_json(RAW_DIR / f"app_store_{timestamp}.json", app_reviews)
    save_json(DATA_DIR / "reviews.json", all_reviews)

    ingest_result = ingest_reviews(all_reviews, reset_collection=True)
    stats_path = write_stats(all_reviews, ingest_result)

    print(f"Saved corpus to {DATA_DIR / 'reviews.json'}")
    print(f"ChromaDB: {ingest_result['total_documents']} documents")
    print(f"Stats: {stats_path}")


if __name__ == "__main__":
    main()
