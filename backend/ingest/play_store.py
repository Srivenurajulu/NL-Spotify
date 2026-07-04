"""Scrape Spotify reviews from Google Play Store."""

from __future__ import annotations

from google_play_scraper import Sort, reviews

from backend.ingest.constants import REVIEW_LIMIT, SPOTIFY_PLAY_APP_ID
from backend.ingest.normalize import normalize_review

PLAY_STORE_URL = (
    "https://play.google.com/store/apps/details?id=com.spotify.music"
)


def scrape_play_store(limit: int = REVIEW_LIMIT) -> list[dict]:
    """Fetch the newest Play Store reviews for Spotify."""
    raw_reviews, _ = reviews(
        SPOTIFY_PLAY_APP_ID,
        lang="en",
        country="us",
        sort=Sort.NEWEST,
        count=limit,
    )

    normalized: list[dict] = []
    for item in raw_reviews:
        review_id = item.get("reviewId") or f"{item.get('userName', 'anon')}-{item.get('at')}"
        normalized.append(
            normalize_review(
                source="google_play",
                review_id=str(review_id),
                text=item.get("content", "") or "",
                date=item.get("at"),
                url=PLAY_STORE_URL,
                country="us",
                score=item.get("score"),
                title=None,
                author=item.get("userName"),
            )
        )

    return normalized
