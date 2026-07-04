from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings


@dataclass(frozen=True)
class RetrievalResult:
    reviews: list[dict[str, Any]]


COLLECTION_NAME = "spotify_reviews"


def _chroma_path() -> str:
    return str(Path(__file__).resolve().parents[2] / "data" / "chroma")


def retrieve(question_query: str, n_results: int = 15) -> RetrievalResult:
    """
    Retrieve relevant reviews from the persisted Chroma collection.
    """
    client = chromadb.PersistentClient(
        path=_chroma_path(),
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_collection(name=COLLECTION_NAME)

    res = collection.query(
        query_texts=[question_query],
        n_results=n_results,
    )

    docs0 = res.get("documents", [[]])[0] or []
    ids0 = res.get("ids", [[]])[0] or []
    metadatas0 = res.get("metadatas", [[]])[0] or []

    reviews: list[dict[str, Any]] = []
    for i, doc in enumerate(docs0):
        meta = metadatas0[i] if i < len(metadatas0) else {}
        if meta is None:
            meta = {}
        reviews.append(
            {
                "id": ids0[i] if i < len(ids0) else None,
                "text": doc,
                "source": meta.get("source"),
                "date": meta.get("date"),
                "url": meta.get("url"),
                "score": meta.get("score"),
                "author": meta.get("author"),
                "country": meta.get("country") or meta.get("country_", "") or "",
                "behavior_tags": meta.get("behavior_tags", "") or "",
            }
        )

    return RetrievalResult(reviews=reviews)

