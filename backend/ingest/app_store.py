"""Scrape Spotify reviews from Apple App Store."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

import requests

from backend.ingest.constants import REVIEW_LIMIT, SPOTIFY_APP_STORE_ID
from backend.ingest.normalize import normalize_review

APP_STORE_URL = (
    "https://apps.apple.com/us/app/spotify-music-and-podcasts/id324684580"
)
ITUNES_REVIEWS_URL = (
    f"https://itunes.apple.com/rss/customerreviews/id={SPOTIFY_APP_STORE_ID}"
    "/sortBy=mostRecent/page=1/json"
)
APP_STORE_PAGE_PATH = "/app/spotify-music-and-podcasts/id324684580?see-all=reviews&platform=iphone"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_updated(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_rss_entry(entry: dict[str, Any]) -> dict:
    review_id = entry.get("id", {}).get("label", "")
    author = entry.get("author", {}).get("name", {}).get("label")
    title = entry.get("title", {}).get("label")
    content = entry.get("content", {}).get("label", "")
    rating_raw = entry.get("im:rating", {}).get("label")
    score = int(rating_raw) if rating_raw and str(rating_raw).isdigit() else None
    updated = entry.get("updated", {}).get("label")
    link = entry.get("link", {})
    review_url = APP_STORE_URL
    if isinstance(link, dict):
        review_url = link.get("attributes", {}).get("href", APP_STORE_URL)

    return normalize_review(
        source="app_store",
        review_id=str(review_id),
        text=content,
        date=_parse_updated(updated),
        url=review_url,
        score=score,
        title=title,
        author=author,
    )


def _scrape_from_rss(limit: int) -> list[dict]:
    response = requests.get(ITUNES_REVIEWS_URL, timeout=30, headers=HEADERS)
    response.raise_for_status()
    payload = response.json()

    entries = payload.get("feed", {}).get("entry", [])
    review_entries = [
        entry
        for entry in entries
        if isinstance(entry, dict) and "content" in entry
    ][:limit]
    normalized = [_normalize_rss_entry(entry) for entry in review_entries]
    for item in normalized:
        item["country"] = "us"
    return normalized


def _walk_reviews(node: Any, found: list[dict[str, Any]]) -> None:
    if isinstance(node, dict):
        if node.get("$kind") == "Review":
            found.append(node)
        for value in node.values():
            _walk_reviews(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk_reviews(item, found)


def _scrape_from_page(limit: int) -> list[dict]:
    # App Store review scraping in 2026: the legacy RSS feed is unreliable, and the
    # web page SSRs a small set of reviews per storefront. We aggregate across
    # storefronts and dedupe by review id.
    storefronts = [
        "us",
        "gb",
        "ca",
        "au",
        "in",
        "de",
        "fr",
        "es",
        "it",
        "nl",
        "se",
        "no",
        "dk",
        "fi",
        "ie",
        "pt",
        "be",
        "ch",
        "at",
        "pl",
        "cz",
        "hu",
        "ro",
        "gr",
        "tr",
        "br",
        "mx",
        "ar",
        "cl",
        "co",
        "pe",
        "za",
        "sg",
        "hk",
        "jp",
        "kr",
        "tw",
        "th",
        "ph",
        "my",
        "id",
        "vn",
        "nz",
    ]

    normalized: list[dict] = []
    seen: set[str] = set()
    for country in storefronts:
        page_url = f"https://apps.apple.com/{country}{APP_STORE_PAGE_PATH}"
        try:
            response = requests.get(page_url, timeout=30, headers=HEADERS)
            response.raise_for_status()
        except requests.RequestException:
            continue

        match = re.search(
            r'<script[^>]+id="serialized-server-data"[^>]*>(.*?)</script>',
            response.text,
            re.DOTALL,
        )
        if not match:
            continue

        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

        raw_reviews: list[dict[str, Any]] = []
        _walk_reviews(payload, raw_reviews)

        for item in raw_reviews:
            review_id = str(item.get("id") or item.get("reviewId") or "")
            if not review_id or review_id in seen:
                continue
            seen.add(review_id)

            title = item.get("title") or ""
            content = item.get("review") or item.get("content") or ""
            author = item.get("userName") or item.get("author", {}).get("name")
            rating = item.get("rating") or item.get("value")
            score = (
                int(rating)
                if rating is not None and str(rating).isdigit()
                else None
            )
            updated = item.get("date") or item.get("updated")

            normalized.append(
                normalize_review(
                    source="app_store",
                    review_id=review_id,
                    text=str(content),
                    date=_parse_updated(str(updated)) if updated else None,
                    url=page_url,
                    country=country,
                    score=score,
                    title=str(title) if title else None,
                    author=str(author) if author else None,
                )
            )

            if len(normalized) >= limit:
                return normalized[:limit]

    return normalized


def scrape_app_store(limit: int = REVIEW_LIMIT) -> list[dict]:
    """Fetch the newest App Store reviews for Spotify."""
    reviews = _scrape_from_rss(limit)
    if reviews:
        return reviews[:limit]

    return _scrape_from_page(limit)[:limit]
