"""Normalize raw store reviews into a shared corpus schema."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any

from backend.ingest.constants import DISCOVERY_KEYWORDS

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_RE = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")


def _strip_pii(text: str) -> str:
    cleaned = EMAIL_RE.sub("[email]", text)
    return PHONE_RE.sub("[phone]", cleaned)


def _behavior_tags(text: str, score: int | None) -> list[str]:
    tags: list[str] = []
    lowered = text.lower()

    for keyword in DISCOVERY_KEYWORDS:
        if keyword in lowered:
            tags.append(keyword.replace(" ", "_"))

    if score is not None and score <= 3:
        tags.append("low_rating")

    if any(word in lowered for word in ("trust", "explain", "why", "reason")):
        tags.append("trust_gap")

    if any(word in lowered for word in ("ad", "ads", "advertisement")):
        tags.append("ads")

    if any(word in lowered for word in ("offline", "download", "downloaded")):
        tags.append("offline")

    return sorted(set(tags))


def _make_id(source: str, review_id: str) -> str:
    raw = f"{source}:{review_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def normalize_review(
    *,
    source: str,
    review_id: str,
    text: str,
    date: datetime | str | None,
    url: str,
    country: str | None = None,
    score: int | None = None,
    title: str | None = None,
    author: str | None = None,
) -> dict[str, Any]:
    """Return a normalized review document."""
    body = _strip_pii(text.strip())
    if title:
        body = f"{title.strip()}. {body}" if body else title.strip()

    if isinstance(date, datetime):
        date_str = date.date().isoformat()
    elif isinstance(date, str) and date:
        date_str = date[:10]
    else:
        date_str = None

    return {
        "id": _make_id(source, review_id),
        "source": source,
        "date": date_str,
        "text": body,
        "url": url,
        "country": country,
        "score": score,
        "author": author,
        "behavior_tags": _behavior_tags(body, score),
    }
