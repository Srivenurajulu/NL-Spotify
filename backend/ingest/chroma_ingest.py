"""Embed normalized reviews and persist them in ChromaDB."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

COLLECTION_NAME = "spotify_reviews"
CHROMA_PATH = Path(__file__).resolve().parents[2] / "data" / "chroma"


def ingest_reviews(reviews: list[dict[str, Any]], *, reset_collection: bool = True) -> dict[str, Any]:
    """Upsert review documents into a local Chroma collection."""
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    if reset_collection:
        # Ensure RAG uses only the latest scrape snapshot.
        existing = collection.get()
        existing_ids = existing.get("ids") or []
        if existing_ids:
            collection.delete(ids=existing_ids)

    ids = [review["id"] for review in reviews]
    documents = [review["text"] for review in reviews]
    metadatas = [
        {
            "source": review["source"],
            "date": review.get("date") or "",
            "url": review["url"],
            "country": review.get("country") or "",
            "score": review.get("score") if review.get("score") is not None else -1,
            "author": review.get("author") or "",
            "behavior_tags": ",".join(review.get("behavior_tags", [])),
        }
        for review in reviews
    ]

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    return {
        "collection": COLLECTION_NAME,
        "documents_ingested": len(reviews),
        "total_documents": collection.count(),
        "chroma_path": str(CHROMA_PATH),
    }


def write_stats(reviews: list[dict[str, Any]], ingest_result: dict[str, Any]) -> Path:
    """Write corpus stats for the RDE UI."""
    stats_path = Path(__file__).resolve().parents[2] / "data" / "stats.json"
    by_source: dict[str, int] = {}
    for review in reviews:
        by_source[review["source"]] = by_source.get(review["source"], 0) + 1

    stats = {
        "total_documents": ingest_result["total_documents"],
        "last_scraped": max((r.get("date") or "" for r in reviews), default=""),
        "sources": by_source,
        "collection": ingest_result["collection"],
        "chroma_path": ingest_result["chroma_path"],
    }
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(json.dumps(stats, indent=2))
    return stats_path
