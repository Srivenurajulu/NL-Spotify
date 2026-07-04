#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.ingest.chroma_ingest import ingest_reviews, write_stats

DATA_DIR = ROOT / "data"

def main():
    enriched_path = DATA_DIR / "spotify_reviews_enriched.json"
    print(f"Loading enriched reviews from {enriched_path}...")
    reviews = json.loads(enriched_path.read_text())
    
    print(f"Loaded {len(reviews)} reviews. Ingesting into ChromaDB...")
    ingest_result = ingest_reviews(reviews, reset_collection=True)
    stats_path = write_stats(reviews, ingest_result)
    
    print(f"ChromaDB: {ingest_result['total_documents']} documents")
    print(f"Stats: {stats_path}")

if __name__ == "__main__":
    main()
